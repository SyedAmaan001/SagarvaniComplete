"use client";

import { useEffect, useMemo, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  CircleMarker,
  Polyline,
  Polygon,
  LayerGroup,
  ZoomControl,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { MapLayer } from "@/lib/types";
import type { LiveMap, GeoCollection, GeoFeature } from "@/lib/api/orca";

// Helper to smoothly animate map to new coordinates
function MapViewController({ coords, zoom }: { coords?: [number, number]; zoom?: number }) {
  const map = useMap();
  useEffect(() => {
    if (coords) {
      map.flyTo(coords, zoom || 9, { duration: 1.2 });
    }
  }, [coords, zoom, map]);
  return null;
}

// Inline SVG marker factory — no external CDN, always loads correctly
function makeSvgIcon(color: string) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="26" height="42" viewBox="0 0 26 42"><path d="M13 1C6.4 1 1 6.4 1 13c0 9.8 12 28 12 28s12-18.2 12-28C25 6.4 19.6 1 13 1z" fill="${color}" stroke="rgba(0,0,0,0.45)" stroke-width="1.5"/><circle cx="13" cy="13" r="5" fill="rgba(255,255,255,0.88)"/></svg>`;
  return new L.Icon({
    iconUrl: `data:image/svg+xml;base64,${btoa(svg)}`,
    iconSize: [26, 42],
    iconAnchor: [13, 42],
    popupAnchor: [0, -38],
  });
}

const cyanMarkerIcon  = makeSvgIcon("#00FFFF");
const greenMarkerIcon = makeSvgIcon("#22E29A");

// GeoJSON is [lon, lat]; Leaflet wants [lat, lon]
const toLatLng = (c: number[]): [number, number] => [c[1], c[0]];
const pointOf = (f: GeoFeature): [number, number] => toLatLng(f.geometry.coordinates);

const WAVE_COLORS: Record<string, string> = {
  NORMAL: "#00FFFF",
  CAUTION: "#FFD43B",
  HIGH: "#FFA94D",
  DANGER: "#FF4D6D",
};

/** Blue (cold) to red (warm), scaled to the temperatures actually present. */
function sstColor(t: number, min: number, max: number): string {
  const span = Math.max(0.5, max - min);
  const hue = 240 - 240 * Math.min(1, Math.max(0, (t - min) / span));
  return `hsl(${hue}, 85%, 55%)`;
}

const istTime = (iso: string | null | undefined) =>
  iso
    ? new Date(iso).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Kolkata" }) + " IST"
    : "—";

interface MapCanvasProps {
  activeLayers: MapLayer[];
  center?: [number, number];
  zoom?: number;
  focusedCoordinates?: [number, number];
  liveMap?: LiveMap | null;
  liveLoading?: boolean;
  /** GeoJSON from the last chat decision (route, recommended zone) */
  pipelineGeoJson?: GeoCollection | null;
}

export default function MapCanvas({
  activeLayers,
  center = [13.1, 74.4],
  zoom = 8,
  focusedCoordinates,
  liveMap,
  liveLoading = false,
  pipelineGeoJson,
}: MapCanvasProps) {
  const [mapReady, setMapReady] = useState(false);

  useEffect(() => {
    setMapReady(true);
  }, []);

  const sstRange = useMemo(() => {
    const vals = (liveMap?.layers.sst.features ?? []).map(f => f.properties.sst_c as number);
    return vals.length ? { min: Math.min(...vals), max: Math.max(...vals) } : { min: 26, max: 31 };
  }, [liveMap]);

  if (!mapReady) {
    return (
      <div className="w-full h-full bg-bg-sunken flex flex-col items-center justify-center gap-2 text-text-secondary font-mono text-xs">
        <span className="size-3 rounded-full bg-primary animate-ping" />
        <span>Initializing Spatial Map Engine...</span>
      </div>
    );
  }

  const layers = liveMap?.layers;
  const on = (l: MapLayer) => activeLayers.includes(l);

  let status: { text: string; tone: string };
  if (liveLoading && !liveMap) {
    status = { text: "Fetching live marine data…", tone: "text-text-secondary" };
  } else if (liveMap?.live) {
    const age = liveMap.data_age_minutes;
    status = {
      text: `LIVE · model data valid ${istTime(liveMap.data_valid_time)}${age !== null ? ` · ${Math.round(age)} min old` : ""} · ${liveMap.ocean_point_count} sea points`,
      tone: age !== null && age > 90 ? "text-warning" : "text-success",
    };
  } else {
    status = {
      text: "LIVE DATA UNAVAILABLE — layers are empty on purpose; nothing here is simulated",
      tone: "text-danger",
    };
  }

  return (
    <div className="relative w-full h-full bg-bg-sunken z-0 select-none">
      <MapContainer
        center={focusedCoordinates || center}
        zoom={zoom}
        style={{ width: "100%", height: "100%", background: "#02051C" }}
        zoomControl={false}
      >
        <MapViewController coords={focusedCoordinates} zoom={zoom} />
        <ZoomControl position="bottomright" />

        {/* Dark basemap — ESRI World Dark Gray (free, no API key required) */}
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          attribution="&copy; Esri · Marine data: Open-Meteo"
          maxZoom={16}
        />

        {/* Restricted zones are safety-critical, so they are always visible */}
        {layers && (
          <LayerGroup>
            {layers.restricted.features.map((f, i) => (
              <Polygon
                key={`rz-${i}`}
                positions={(f.geometry.coordinates[0] as number[][]).map(toLatLng)}
                pathOptions={{ fillColor: "#DC2626", color: "#DC2626", fillOpacity: 0.3, weight: 1.5 }}
              >
                <Popup>
                  <div className="font-mono text-xs p-1">
                    <span className="font-bold text-danger block">⛔ {f.properties.name}</span>
                    <span className="block">{f.properties.restriction_level}</span>
                    <span className="block text-text-secondary">{f.properties.authority}</span>
                    <span className="block text-text-secondary">{f.properties.legal_basis}</span>
                  </div>
                </Popup>
              </Polygon>
            ))}
          </LayerGroup>
        )}

        {/* Wave height (colour = level against vessel limits) */}
        {layers && on("Wave Height") && (
          <LayerGroup>
            {layers.waves.features.map((f, i) => (
              <CircleMarker
                key={`wv-${i}`}
                center={pointOf(f)}
                radius={7}
                pathOptions={{
                  color: WAVE_COLORS[f.properties.level] ?? "#00FFFF",
                  fillColor: WAVE_COLORS[f.properties.level] ?? "#00FFFF",
                  fillOpacity: 0.5,
                  weight: 1,
                }}
              >
                <Popup>
                  <div className="font-mono text-xs p-1">
                    <span className="font-bold text-primary block">Wave height {f.properties.wave_height_m} m</span>
                    <span className="block">Period: {f.properties.wave_period_s ?? "—"} s</span>
                    <span className="block">Wind: {f.properties.wind_kmh ?? "—"} km/h</span>
                    <span className="block text-text-secondary">Valid {istTime(f.properties.valid_time)}</span>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </LayerGroup>
        )}

        {/* Sea-surface temperature */}
        {layers && on("SST") && (
          <LayerGroup>
            {layers.sst.features.map((f, i) => {
              const c = sstColor(f.properties.sst_c, sstRange.min, sstRange.max);
              return (
                <CircleMarker
                  key={`sst-${i}`}
                  center={pointOf(f)}
                  radius={9}
                  pathOptions={{ color: c, fillColor: c, fillOpacity: 0.45, weight: 0 }}
                >
                  <Popup>
                    <div className="font-mono text-xs p-1">
                      <span className="font-bold text-primary block">SST {f.properties.sst_c} °C</span>
                      <span className="block text-text-secondary">Valid {istTime(f.properties.valid_time)}</span>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}
          </LayerGroup>
        )}

        {/* Ocean current vectors */}
        {layers && on("Currents") && (
          <LayerGroup>
            {layers.currents.features.map((f, i) => (
              <Polyline
                key={`cur-${i}`}
                positions={(f.geometry.coordinates as number[][]).map(toLatLng)}
                pathOptions={{ color: "#00FFFF", weight: 2, opacity: 0.85 }}
              >
                <Popup>
                  <div className="font-mono text-xs p-1">
                    <span className="font-bold text-primary block">Current {f.properties.speed_ms} m/s</span>
                    <span className="block">Direction {f.properties.direction_deg}°</span>
                  </div>
                </Popup>
              </Polyline>
            ))}
          </LayerGroup>
        )}

        {/* SST-front fishing candidates (derived; not official INCOIS PFZ) */}
        {layers && on("PFZ") && (
          <LayerGroup>
            {layers.pfz.features.map((f, i) => (
              <div key={`pfz-${i}`}>
                <Circle
                  center={pointOf(f)}
                  radius={6000}
                  pathOptions={{ fillColor: "#22E29A", color: "#22E29A", fillOpacity: 0.2, weight: 1.5 }}
                />
                <Marker position={pointOf(f)} icon={greenMarkerIcon}>
                  <Popup>
                    <div className="font-mono text-xs p-1">
                      <span className="font-bold text-success block">{f.properties.name}</span>
                      <span className="block">SST {f.properties.sst_c} °C · gradient {f.properties.sst_gradient_c_per_km} °C/km</span>
                      <span className="block text-text-secondary">Front strength score {f.properties.score}/100</span>
                      <span className="block mt-1 text-text-secondary">
                        Model-derived candidate, not an official INCOIS PFZ. No chlorophyll feed connected.
                      </span>
                    </div>
                  </Popup>
                </Marker>
              </div>
            ))}
          </LayerGroup>
        )}

        {/* High-wave warnings */}
        {layers && on("High Wave Warnings") && (
          <LayerGroup>
            {layers.wave_warnings.features.map((f, i) => (
              <CircleMarker
                key={`hw-${i}`}
                center={pointOf(f)}
                radius={14}
                pathOptions={{
                  color: WAVE_COLORS[f.properties.level],
                  fillColor: WAVE_COLORS[f.properties.level],
                  fillOpacity: 0.3,
                  weight: 1.5,
                }}
              >
                <Popup>
                  <div className="font-mono text-xs p-1">
                    <span className="font-bold text-warning block">
                      {f.properties.level} · {f.properties.wave_height_m} m
                    </span>
                    <span className="block text-text-secondary">Valid {istTime(f.properties.valid_time)}</span>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </LayerGroup>
        )}

        {/* Route and departure point from the last decision */}
        {pipelineGeoJson && (
          <LayerGroup>
            {pipelineGeoJson.features.map((f, i) => {
              const t = f.properties.type;
              if (f.geometry.type === "LineString" && t === "SAFE_NAVIGATION_COURSE") {
                return (
                  <Polyline
                    key={`rt-${i}`}
                    positions={(f.geometry.coordinates as number[][]).map(toLatLng)}
                    pathOptions={{ color: "#00F2FF", weight: 4 }}
                  >
                    <Popup><div className="font-mono text-xs p-1">{f.properties.title}</div></Popup>
                  </Polyline>
                );
              }
              if (f.geometry.type === "LineString" && t === "AVOIDED_DIRECT_SEGMENT") {
                return (
                  <Polyline
                    key={`rt-${i}`}
                    positions={(f.geometry.coordinates as number[][]).map(toLatLng)}
                    pathOptions={{ color: "#EF4444", weight: 3, dashArray: "5, 5" }}
                  >
                    <Popup><div className="font-mono text-xs p-1">{f.properties.title}</div></Popup>
                  </Polyline>
                );
              }
              if (t === "USER_BASE_LOCATION") {
                return (
                  <Marker key={`rt-${i}`} position={pointOf(f)} icon={cyanMarkerIcon}>
                    <Popup>
                      <div className="font-mono text-xs p-1">
                        <span className="font-bold text-primary block">{f.properties.title}</span>
                        <span className="block">Gate: {f.properties.safety_status}</span>
                      </div>
                    </Popup>
                  </Marker>
                );
              }
              return null;
            })}
          </LayerGroup>
        )}

        {/* Fixed reference ports (real locations) */}
        <Marker position={[12.9141, 74.856]} icon={cyanMarkerIcon}>
          <Popup>
            <div className="font-mono text-xs p-1">
              <span className="font-bold text-primary block">Mangalore Old Port</span>
              <span>Coordinates: 12.9141° N, 74.8560° E</span>
            </div>
          </Popup>
        </Marker>

        <Marker position={[13.35, 74.7]} icon={cyanMarkerIcon}>
          <Popup>
            <div className="font-mono text-xs p-1">
              <span className="font-bold text-primary block">Malpe Fishing Harbour</span>
              <span>Coordinates: 13.3500° N, 74.7000° E</span>
            </div>
          </Popup>
        </Marker>

        <Marker position={[14.81, 74.13]} icon={cyanMarkerIcon}>
          <Popup>
            <div className="font-mono text-xs p-1">
              <span className="font-bold text-primary block">Karwar Port</span>
              <span>Coordinates: 14.8100° N, 74.1300° E</span>
            </div>
          </Popup>
        </Marker>
      </MapContainer>

      {/* Data status + honesty notes */}
      <div className="absolute bottom-3 left-3 z-[1000] max-w-[min(92%,420px)] flex flex-col gap-1.5 pointer-events-none">
        <div className={`bg-bg-elevated/90 backdrop-blur-md border border-border rounded-lg px-2.5 py-1.5 font-mono text-[10px] font-semibold ${status.tone}`}>
          {status.text}
        </div>
        {on("Cyclone") && (
          <div className="bg-bg-elevated/90 backdrop-blur-md border border-border rounded-lg px-2.5 py-1.5 font-mono text-[10px] text-warning">
            Cyclone layer: no live IMD feed is connected, so no cyclone is drawn. Check IMD bulletins directly.
          </div>
        )}
        {liveMap && liveMap.errors.length > 0 && (
          <div className="bg-bg-elevated/90 backdrop-blur-md border border-border rounded-lg px-2.5 py-1.5 font-mono text-[10px] text-warning">
            Partial data: {liveMap.errors[0].slice(0, 90)}
          </div>
        )}
      </div>
    </div>
  );
}
