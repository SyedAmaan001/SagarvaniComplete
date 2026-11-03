import { AgentStatus, ConversationTurn, Readout, Alert, EvidenceItem } from "../types";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

// ── Live map ────────────────────────────────────────────────────────────────

export interface GeoFeature {
  type: "Feature";
  geometry: { type: string; coordinates: any };
  properties: Record<string, any>;
}
export interface GeoCollection {
  type: "FeatureCollection";
  features: GeoFeature[];
}

export interface LiveMap {
  generated_at: string;
  center: { lat: number; lon: number };
  radius_km: number;
  live: boolean;
  data_valid_time: string | null;
  data_age_minutes: number | null;
  fetched_at: string;
  refresh_seconds: number;
  ocean_point_count: number;
  conditions: {
    wave_height_m: number | null;
    wind_kmh: number | null;
    sst_c: number | null;
    current_ms: number | null;
    valid_time: string | null;
    distance_from_centre_km: number | null;
  } | null;
  sources: { name: string; role: string; ok: boolean }[];
  errors: string[];
  layers: {
    waves: GeoCollection;
    sst: GeoCollection;
    currents: GeoCollection;
    wave_warnings: GeoCollection;
    pfz: GeoCollection;
    restricted: GeoCollection;
  };
  not_connected: { layer: string; needs: string }[];
}

/** Live conditions + map layers from the backend (cached server-side for ~10 minutes). */
export async function fetchLiveMap(lat = 13.35, lon = 74.7, radiusKm = 60): Promise<LiveMap | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/live/map?lat=${lat}&lon=${lon}&radius_km=${radiusKm}`, {
      signal: AbortSignal.timeout(45000),
    });
    if (!res.ok) return null;
    return (await res.json()) as LiveMap;
  } catch {
    return null;
  }
}

const num = (v: number | null | undefined, digits = 1): string =>
  v === null || v === undefined ? "—" : String(Number(v.toFixed(digits)));

/** Readout strip values from real numbers only; "—" when a value is missing. */
export function liveReadouts(map: LiveMap | null): Readout[] {
  const c = map?.conditions;
  const seaState = (h: number | null | undefined) =>
    h === null || h === undefined ? "—" :
    h < 0.1 ? "Calm" : h < 0.5 ? "Rippled" : h < 1.25 ? "Slight" : h < 2.5 ? "Moderate" :
    h < 4 ? "Rough" : "Very rough";
  return [
    { label: "Sea State", value: seaState(c?.wave_height_m), unit: "" },
    { label: "Wind Speed", value: num(c?.wind_kmh), unit: "km/h", trend: "stable" },
    { label: "Wave Height", value: num(c?.wave_height_m, 2), unit: "m", isActive: true, trend: "stable" },
    { label: "SST Surface", value: num(c?.sst_c), unit: "°C" },
    { label: "Current", value: num(c?.current_ms, 2), unit: "m/s" },
  ];
}

// ── Chat / decision pipeline ────────────────────────────────────────────────

export interface OrcaQueryResponse {
  agent_states: AgentStatus[];
  turn: ConversationTurn;
  readouts?: Readout[];
  alerts?: Alert[];
  raw?: any;
}

/**
 * Execute a query against the ORCA FastAPI backend.
 */
export async function queryOrca(query: string, sessionId?: string, language: string = "auto"): Promise<OrcaQueryResponse> {
  const payload = {
    query: query,
    session_id: sessionId || `session_${Date.now()}`,
    language_override: language,
    execute_pipeline: true
  };

  const res = await fetch(`${BACKEND_URL}/api/orca/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(errorData.detail || `ORCA API error: ${res.status}`);
  }

  const data = await res.json();
  const pipe = data.pipeline_result;
  const dataUnavailable = pipe?.execution_status === "DATA_UNAVAILABLE";

  // Extract verdict and decision. A missing verdict is never treated as "safe".
  const dec = pipe?.decision_package;
  const verdictRaw = dec?.verdict || "REASSESS";
  const verdict: 'SAFE' | 'CAUTION' | 'HAZARD' | 'ADVISORY' =
    verdictRaw === "GO" ? "SAFE" : (verdictRaw === "AVOID" ? "HAZARD" : "CAUTION");

  // Evidence items come straight from the backend's audit (real timestamps / statuses)
  const evidenceList: EvidenceItem[] = (pipe?.evidence_trail?.evidence_trail || []).map((ev: any) => ({
    source: ev.source || "ORCA Marine Gateway",
    parameter: ev.data_point || "Marine Factor",
    value: String(ev.status || "Unknown"),
    summary: `${ev.data_point || 'Data'}: ${ev.status || 'Unknown'}`,
    confidence: ev.verified ? "Validated" : "Unverified",
    timestamp: ev.timestamp || ""
  }));

  const cond = dec?.conditions || {};
  const live = !!pipe?.data_status?.live;
  const agentState: AgentStatus["state"] = live ? 'validated' : 'degraded';

  const agentStates: AgentStatus[] = [
    {
      name: 'Marine Data Agent',
      role: 'Ocean Observations',
      state: agentState,
      source: 'Open-Meteo Marine (live model data)',
      details: cond.wave_m !== undefined ? `Wave: ${cond.wave_m}m, SST: ${cond.sst_c ?? '—'}°C` : 'No live marine data.',
    },
    {
      name: 'Weather Agent',
      role: 'Atmospheric Context',
      state: agentState,
      source: 'Open-Meteo Weather (live)',
      details: cond.wind_kmh !== undefined ? `Wind: ${cond.wind_kmh} km/h` : 'No live wind data.',
    },
    {
      name: 'GIS Agent',
      role: 'Geospatial Layering',
      state: 'validated',
      source: 'Curated geofence layer (static)',
      details: pipe?.cartography ? `Route: ${pipe.cartography.distance_km ?? 0} km` : 'Spatial boundaries loaded.',
    },
    {
      name: 'Ocean Analytics Agent',
      role: 'Thermal-front detection',
      state: agentState,
      source: 'SST gradient from live model grid',
      details: `${pipe?.candidate_pfz_count ?? 0} candidate front(s); chlorophyll feed not connected.`,
    },
    {
      name: 'Risk Agent',
      role: 'Decision Safety Analysis',
      state: live ? 'validated' : 'degraded',
      source: 'ORCA Risk Engine & Gate',
      details: dec ? `Safety score: ${dec.safety_score}/100. Gate: ${dec.safety_gate}` : 'No decision available.',
    },
    {
      name: 'Spatial Reasoning Agent',
      role: 'Topological Reasoning',
      state: 'validated',
      source: 'ORCA Spatial Knowledge Engine',
      details: dec?.restricted_intersections
        ? `Route crosses ${dec.restricted_intersections} restricted zone(s)!`
        : 'Route clear of restricted zones.',
    }
  ];

  // Extract response text
  const adv = pipe?.multilingual_advisory;
  const advisoryText = adv?.regional || adv?.english || dec?.why || "No advisory could be generated.";

  const confidencePct = typeof dec?.confidence === "number" ? `${Math.round(dec.confidence * 100)}%` : "—";

  const turn: ConversationTurn = {
    id: `turn-sag-${Date.now()}`,
    role: 'sagarvani',
    text: advisoryText,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    intent: data.intent || "safe_fishing_advisory",
    recommendation: {
      verdict: verdict,
      headline: `${dec?.recommended_zone || 'Marine Area'} — ${verdictRaw}`,
      summary: dec?.why || advisoryText,
      confidenceScore: confidencePct,
      validationState: live ? 'validated' : 'degraded',
      evidence: evidenceList
    },
    evidence: evidenceList,
    validationTrace: (pipe?.steps_trace || []).map((s: any) => `${s.step}. ${s.name}: ${s.detail}`)
  };

  const readouts: Readout[] = [
    { label: 'Sea State', value: cond.sea_state ?? '—', unit: '' },
    { label: 'Wind Speed', value: num(cond.wind_kmh), unit: 'km/h', trend: 'stable' },
    { label: 'Wave Height', value: num(cond.wave_m, 2), unit: 'm', isActive: true, trend: 'stable' },
    { label: 'SST Surface', value: num(cond.sst_c), unit: '°C' },
    { label: 'Safety Score', value: dec ? String(dec.safety_score) : '—', unit: '/100' },
  ];

  const alerts: Alert[] = [];
  if (verdict === "HAZARD" || dataUnavailable) {
    alerts.push({
      id: `alert-${Date.now()}`,
      type: 'danger',
      title: dataUnavailable ? 'Live Data Unavailable' : 'Marine Hazard Warning',
      message: dec?.why || 'Hazardous sea conditions detected for specified craft.',
      source: 'ORCA Risk Engine',
      timestamp: new Date().toLocaleTimeString()
    });
  }
  if (dec?.route_warning) {
    alerts.push({
      id: `alert-route-${Date.now()}`,
      type: 'danger',
      title: 'Route Warning',
      message: dec.route_warning,
      source: 'ORCA Spatial Engine',
      timestamp: new Date().toLocaleTimeString()
    });
  }

  return {
    agent_states: agentStates,
    turn: turn,
    readouts: readouts,
    alerts: alerts,
    raw: data
  };
}

/**
 * Check backend status and connectivity.
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/status`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

/**
 * Fetch real-time marine weather metrics from Open-Meteo via backend.
 */
export async function fetchMarineWeather(lat: number = 13.35, lon: number = 74.70) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/weather/marine/${lat}/${lon}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/**
 * Fetch ISRO satellite composite (SST, Chl-a, thermal front).
 */
export async function fetchSatelliteComposite(lat: number = 13.35, lon: number = 74.70) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/satellite/composite?lat=${lat}&lon=${lon}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/**
 * Fetch INCOIS harmonic tidal predictions.
 */
export async function fetchTidePrediction(station: string = "Malpe", hours: number = 24) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/tide/predict?station=${encodeURIComponent(station)}&hours=${hours}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}
