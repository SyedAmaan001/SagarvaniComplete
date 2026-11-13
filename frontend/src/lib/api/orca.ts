import { AgentStatus, ConversationTurn, Readout, Alert, EvidenceItem } from "../types";

import { apiUrl, readApiError } from "../config";

export interface OrcaQueryResponse {
  /** undefined when the answer did not involve the agent pipeline (e.g. greeting) */
  agent_states?: AgentStatus[];
  turn: ConversationTurn;
  readouts?: Readout[];
  alerts?: Alert[];
  conversationId: string;
  raw?: any;
}

/**
 * Ask the ORCA backend. `sessionId` must be reused across calls to keep conversation context.
 */
export async function queryOrca(query: string, sessionId?: string, language: string = "auto"): Promise<OrcaQueryResponse> {
  const res = await fetch(apiUrl("/api/orca/chat"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, session_id: sessionId, language_override: language, execute_pipeline: true }),
  });
  if (!res.ok) throw new Error(await readApiError(res));

  const data = await res.json();
  const pipe = data.pipeline_result;
  const dec = pipe?.decision_package;
  const live: boolean = Boolean(pipe?.data_integrity?.conditions_live);
  const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const turnBase: ConversationTurn = {
    id: `turn-sag-${Date.now()}`,
    role: "sagarvani",
    text: data.assistant_text,
    timestamp: now,
    intent: data.intent,
    usesMockData: Boolean(data.uses_mock_data),
    mockComponents: data.mock_components || [],
  };

  // Conversational answers (greeting, weather, questions for more info...) - no agent pipeline.
  if (!pipe || !dec) {
    return { turn: turnBase, conversationId: data.conversation_id, raw: data };
  }

  const verdictRaw: string = dec.verdict || "REASSESS";
  const verdict: "SAFE" | "CAUTION" | "HAZARD" | "ADVISORY" =
    verdictRaw === "GO" ? "SAFE" : verdictRaw === "AVOID" ? "HAZARD" : !live ? "ADVISORY" : "CAUTION";

  const evidenceList: EvidenceItem[] = (pipe.evidence_trail?.evidence_trail || []).map((ev: any) => ({
    source: ev.source,
    parameter: ev.data_point,
    value: String(ev.status),
    summary: `${ev.data_point}: ${ev.status}`,
    confidence: ev.verified ? "Validated" : "Degraded",
    timestamp: ev.timestamp,
  }));

  const cond = dec.conditions || {};
  const agentState = live ? "validated" : "degraded";
  const agentStates: AgentStatus[] = [
    { name: "Marine Data Agent", role: "Ocean Observations", state: agentState, source: "Open-Meteo Marine (model forecast)",
      details: cond.wave_m != null ? `Wave: ${cond.wave_m} m` : "Wave data unavailable" },
    { name: "Weather Agent", role: "Atmospheric Context", state: agentState, source: "Open-Meteo Weather (model forecast)",
      details: cond.wind_kmh != null ? `Wind: ${cond.wind_kmh} km/h` : "Wind data unavailable" },
    { name: "GIS Agent", role: "Geospatial Layering", state: "validated", source: "Reference geofences",
      details: pipe.route_calculation ? `Route: ${pipe.route_calculation.safe_route_distance_km} km` : "Spatial boundaries aligned." },
    { name: "Ocean Analytics Agent", role: "Multi-Sensor Analytics", state: "degraded", source: "Static reference registry",
      details: "PFZ / SST / chlorophyll are static reference data, not live." },
    { name: "Risk Agent", role: "Decision Safety Analysis", state: agentState, source: "ORCA Risk Engine & Gate",
      details: `Safety score: ${dec.safety_score ?? "N/A"}. Gate: ${pipe.hard_safety_gate?.gate_status ?? "N/A"}` },
    { name: "Spatial Reasoning Agent", role: "Topological Reasoning", state: "validated", source: "ORCA Spatial Knowledge Engine",
      details: "Geofence and corridor check complete." },
  ];

  const turn: ConversationTurn = {
    ...turnBase,
    recommendation: {
      verdict,
      headline: `${dec.best_zone && dec.best_zone !== "None" ? dec.best_zone : "Marine Area"} - ${dec.verdict_label || verdictRaw}`,
      summary: dec.why || data.assistant_text,
      confidenceScore: dec.confidence ? `${Math.round(dec.confidence * 100)}%` : "N/A",
      validationState: live ? "validated" : "degraded",
      evidence: evidenceList,
    },
    evidence: evidenceList,
    validationTrace: (pipe.steps_trace || []).map((st: any) => `${st.step}. ${st.name} - ${st.detail}`),
  };

  const readouts: Readout[] = [
    { label: "Wave Height", value: cond.wave_m != null ? String(cond.wave_m) : "-", unit: "m", isActive: true },
    { label: "Wind Speed", value: cond.wind_kmh != null ? String(cond.wind_kmh) : "-", unit: "km/h" },
    { label: "Safety Score", value: dec.safety_score != null ? String(dec.safety_score) : "N/A", unit: dec.safety_score != null ? "/100" : "" },
    { label: "Live Data", value: live ? "Yes" : "No", unit: "" },
  ];

  const alerts: Alert[] = [];
  if (verdict === "HAZARD") {
    alerts.push({ id: `alert-${Date.now()}`, type: "danger", title: "Marine Hazard Warning",
      message: dec.why || "Sea conditions exceed limits for this craft.", source: "ORCA Risk Engine",
      timestamp: new Date().toLocaleTimeString() });
  } else if (!live) {
    alerts.push({ id: `alert-${Date.now()}`, type: "warning", title: "Live data unavailable",
      message: "Wave/wind feeds failed - no safety judgement was made.", source: "ORCA Marine Gateway",
      timestamp: new Date().toLocaleTimeString() });
  }

  return { agent_states: agentStates, turn, readouts, alerts, conversationId: data.conversation_id, raw: data };
}

/**
 * Check backend status and connectivity.
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(apiUrl("/api/health"), { signal: AbortSignal.timeout(3000) });
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
    const res = await fetch(apiUrl(`/api/weather/marine/${lat}/${lon}`));
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
    const res = await fetch(apiUrl(`/api/satellite/composite?lat=${lat}&lon=${lon}`));
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
    const res = await fetch(apiUrl(`/api/tide/predict?station=${encodeURIComponent(station)}&hours=${hours}`));
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}
