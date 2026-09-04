# ORCA Backend — API Reference

## Base URL
```
http://localhost:8000
```

## Authentication
No auth required for prototype. Add API key middleware before production.

---

## System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check + endpoint map |
| `GET` | `/api/status` | Full system status + key check |
| `GET` | `/docs` | Swagger UI (interactive) |
| `GET` | `/redoc` | ReDoc documentation |

---

## ORCA Marine Intelligence & Gateway Endpoints (SIH26176)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/orca/query?lat=&lon=&vessel=&language=&intent=` | **Complete 10-Step Decision Pipeline** (Page 3 & 4) with Bilingual English/Kannada output |
| `GET` | `/api/gateway/normalized?lat=&lon=` | Authoritative **Marine Data Gateway** telemetry record (`Parameter \| value \| unit \| source \| quality`) |
| `GET` | `/api/pfz/candidates?lat=&lon=` | Active **INCOIS Potential Fishing Zones** with Chlorophyll-a & SST |
| `GET` | `/api/geofence/restricted-zones` | **Marine Protected Areas (MPAs)** & Defense Firing Geofences |
| `GET` | `/api/orchestrate?lat=&lon=&language=` | Multi-Agent Orchestrator Pipeline trace (6 Domain Agents + Validator) |

---

## Weather Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/weather/{lat}/{lon}` | Combined weather + marine forecast |
| `GET` | `/api/weather/marine/{lat}/{lon}` | Marine-only (waves, swell, currents) |

---

## Risk Engine Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/risk/point?lat=&lon=&region=` | Risk score for specific location |
| `GET` | `/api/risk-zones` | Full risk map GeoJSON (12 zones) |

### Risk Score Response
```json
{
  "lat": 15.0,
  "lon": 72.0,
  "risk_score": 42.5,
  "risk_level": "CAUTION",
  "risk_color": "#eab308",
  "risk_emoji": "🟡",
  "advice": "Exercise caution. Moderate sea conditions.",
  "breakdown": {
    "wave_height": { "value_m": 1.5, "score": 25.0, "weight": 0.30 },
    "wind_speed":  { "value_kmh": 32, "score": 38.5, "weight": 0.25 },
    "ocean_current": { "value_ms": 0.4, "score": 20.0, "weight": 0.20 },
    "cyclone_proximity": { "nearest_cyclone": null, "score": 0.0, "weight": 0.15 },
    "lulc_vulnerability": { "region": "open_sea", "score": 30, "weight": 0.10 }
  }
}
```

---

## Cyclone Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/cyclone-track` | Active cyclones + GeoJSON danger zones |
| `GET` | `/api/cyclone/impact?lat=&lon=` | Cyclone threat for a fishing zone |

---

## IMD Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/imd/cyclones` | Active cyclones from IMD RSMC |
| `GET` | `/api/imd/warning?lat=&lon=` | IMD warning level for location |
| `GET` | `/api/imd/fishing-zones` | Advisories for Indian fishing zones |

---

## Copernicus CMEMS Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/copernicus/status` | Credential check + products |
| `GET` | `/api/copernicus/ocean-data?lat=&lon=` | Live ocean data (requires toolbox) |

---

## AI Advisory Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/advisory` | Generate Gemini advisory (full) |
| `GET` | `/api/advisory/quick?lat=&lon=&language=` | Quick advisory (GET version) |

### POST /api/advisory Request Body
```json
{
  "lat": 15.0,
  "lon": 72.0,
  "language": "both",
  "auto_alert": false
}
```

---

## Alert Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/send-alert` | Send SMS or WhatsApp via Twilio |
| `POST` | `/api/send-bulk-alert` | Send to multiple numbers |
| `GET` | `/api/message-status/{sid}` | Check delivery status |

### POST /api/send-alert Request Body
```json
{
  "to_number": "+919035195941",
  "message": "High waves expected. Stay ashore.",
  "risk_level": "DANGER",
  "channel": "whatsapp",
  "lat": 15.0,
  "lon": 72.0
}
```

---

## Risk Score Formula

```
Risk Score (0–100) =
  0.30 × Wave Height Score        (0m=0, ≥6m=100)
  0.25 × Wind Speed Score         (0m/s=0, ≥25m/s=100)
  0.20 × Ocean Current Score      (0m/s=0, ≥2m/s=100)
  0.15 × Cyclone Proximity Score  (≥1000km=0, ≤200km=100)
  0.10 × LULC Vulnerability       (region-based, 30–65)
```

## Risk Levels

| Score | Level | Color | Action |
|-------|-------|-------|--------|
| 0–25 | 🟢 SAFE | #22c55e | Safe to fish |
| 26–50 | 🟡 CAUTION | #eab308 | Exercise caution |
| 51–75 | 🟠 WARNING | #f97316 | Avoid deep sea |
| 76–100 | 🔴 DANGER | #ef4444 | Stay ashore + Auto Alert |
