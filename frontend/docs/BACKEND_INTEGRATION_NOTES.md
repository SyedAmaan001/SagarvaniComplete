
# Sagarvani Frontend — Backend Integration Notes

This document provides a record of how the Sagarvani frontend interacts with the backend, environment settings, and integration details.

---

## 1. Overview
- **Frontend URL (Local Dev)**: `http://localhost:3000`
- **Backend API URL**: `http://localhost:8000`
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`

---

## 2. Environment Variables & Settings
The frontend is built with vanilla HTML5/CSS/JavaScript and connects to `API = 'http://localhost:8000'`.
To customize the backend endpoint, change `const API = 'http://localhost:8000'` in `frontend/app.js` or configure a reverse proxy.

In the backend (`backend/.env`):
```env
PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080
```

---

## 3. Integrated & Verified Endpoints

| Feature / UI Area | Backend Endpoint | Method | Status |
| :--- | :--- | :--- | :--- |
| **Server Status Indicator** | `/api/status` | `GET` | ✅ Integrated |
| **Ask ORCA Chat Assistant** | `/api/orca/chat` | `POST` | ✅ Integrated |
| **Voice STT & Translation** | `/api/orca/stt` | `POST` | ✅ Integrated |
| **10-Step Decision Loop** | `/api/orca/query` | `GET` | ✅ Integrated |
| **Small Vessel Advisory (SVA)** | `/api/vessel/sva/all` | `GET` | ✅ Integrated |
| **ISRO Oceansat-3 Composite** | `/api/satellite/composite` | `GET` | ✅ Integrated |
| **Harmonic Tidal Forecast** | `/api/tide/predict` | `GET` | ✅ Integrated |
| **Weather & Marine Forecast** | `/api/weather/marine/{lat}/{lon}` | `GET` | ✅ Integrated |
| **IMD Weather Warnings** | `/api/imd/warning` | `GET` | ✅ Integrated |
| **Active Cyclone Alerts** | `/api/imd/cyclones` | `GET` | ✅ Integrated |
| **Maritime Limits & MPAs** | `/api/maritime/limits` | `GET` | ✅ Integrated |
| **ERDDAP Ocean Datasets** | `/api/erddap/dataset` | `GET` | ✅ Integrated |

---

## 4. Unused Backend Endpoints (Available for Future Expansion)
The following backend endpoints are fully implemented and verified on the server side, should additional screens or features be developed:
- `GET /api/languages` — Returns 22 scheduled Indian languages registry
- `POST /api/orca/interpret` — Standalone text intent interpreter
- `GET /api/gateway/normalized` — Canonical single-record ocean normalization
- `GET /api/pfz/candidates` — Standalone candidate PFZ query
- `GET /api/geofence/restricted-zones` — Standalone geofence polygon query
- `GET /api/orchestrate` — Multi-agent orchestration gateway
- `GET /api/ocean-currents`, `/api/ocean-currents/point`, `/api/ocean-currents/all` — Raw NetCDF4 current vector datasets
- `GET /api/coastal-summary`, `/api/coastal-latest` — Sentinel-1 SAR coastal products
- `GET /api/risk/point`, `/api/risk-zones` — Multi-factor risk engine calculations
- `GET /api/cyclone-track`, `/api/cyclone/impact` — RSMC cyclone trajectory GeoJSON
- `GET /api/imd/fishing-zones` — IMD regional fishing advisory bulletins
- `GET /api/copernicus/status`, `/api/copernicus/ocean-data` — Copernicus CMEMS products
- `POST /api/advisory`, `GET /api/advisory/quick` — Direct Gemini AI safety advisory generator
- `POST /api/send-alert`, `POST /api/send-bulk-alert`, `/api/message-status/{sid}` — Twilio SMS/WhatsApp alert dispatch
- `GET /api/tide/stations` — All available INCOIS tide gauge station list
- `GET /api/vessel/sva` — Single vessel class query

---

## 5. Running Frontend & Backend Together

```bash
# Terminal 1 — Start Backend Server
cd backend
.\venv\Scripts\activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 — Start Frontend Server
cd frontend
python -m http.server 3000
```
Open `http://localhost:3000` in your web browser.
