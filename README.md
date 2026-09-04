# 🌊 SAGARVANI — ORCA Marine Intelligence & Decision Support System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg?style=flat&logo=streamlit)](https://streamlit.io)
[![Gemini](https://img.shields.io/badge/Google_Gemini-Multi--Key_Rotation-8E75B2.svg)](https://deepmind.google/technologies/gemini/)
[![Sarvam AI](https://img.shields.io/badge/Sarvam_AI-Bilingual_STT_&_Translate-FF6F00.svg)](https://www.sarvam.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ORCA (Ocean Risk & Coastal Analytics)** is an AI-powered, multi-agent marine intelligence and decision-support system developed for **SAGARVANI** (SIH26176). It integrates real-time oceanographic and meteorological telemetry, satellite earth observation datasets (MOSDAC, Copernicus CMEMS, Bhuvan NRSC), and autonomous AI agents to deliver hyper-localized maritime safety scores, navigation routes, potential fishing zone (PFZ) insights, and multi-lingual voice/text advisories for coastal communities, fishermen, and maritime authorities.

---

## 🚀 Key Features

### 1. 🤖 Multi-Agent Orchestration Pipeline
A coordinated multi-agent system built with domain-specialized agents:
- **Planner Agent**: Deconstructs user intents into actionable oceanographic workflows.
- **Weather Agent**: Fetches real-time wind speed, gusts, atmospheric pressure, and precipitation.
- **Marine Agent**: Analyzes wave heights, swell direction, sea surface temperature (SST), and ocean currents.
- **GIS & Spatial Reasoning Agent**: Geofences Marine Protected Areas (MPAs), defense firing ranges, and international maritime boundaries.
- **Ocean Analytics Agent**: Synthesizes INCOIS Potential Fishing Zones (PFZ) using Chlorophyll-a and SST fronts.
- **Risk Engine Agent**: Calculates a composite 0–100 Marine Risk Score using multi-parameter weighted algorithms.
- **Visualizer Agent**: Formats data for GIS maps, GeoJSON layers, and dynamic dashboard charts.
- **Validator Agent**: Applies cross-validation checks and safety gates before advisory dispatch.
- **Conversation & Interpreter Agent**: Generates contextual natural language responses in English and regional languages (Kannada, etc.) powered by Google Gemini and Sarvam AI.

### 2. ⚡ 10-Step Autonomous Decision Pipeline
Executes end-to-end maritime analysis from raw GPS coordinates:
1. Intent Parsing & Geo-coordinate normalization
2. Authoritative Telemetry Ingestion (Gateway layer)
3. Meteorological & Wave Hazard Evaluation
4. Cyclone Threat & Trajectory Impact Modeling
5. INCOIS PFZ & Chlorophyll Target Identification
6. Geofence & Restricted Zone Validation
7. Multi-Objective Safe Route Planning
8. Composite Risk Index Calculation (0–100)
9. Automated High-Risk Alert Gating (SMS / WhatsApp via Twilio)
10. Multilingual Advisory Synthesis & Audio Generation

### 3. 📡 Multi-Source Earth Observation & Ingestion
- **MOSDAC / ISRO**: Altimetry & Scatterometer `.nc` (NetCDF) ocean data parsers.
- **Copernicus Marine Service (CMEMS)**: Global ocean physics analysis and forecasts.
- **IMD (India Meteorological Department)**: RSMC cyclone tracking, sea area bulletins, and coastal storm warnings.
- **Bhuvan NRSC**: Coastal Land Use / Land Cover (LULC) vulnerability layers.
- **Open-Meteo**: High-resolution marine and atmospheric forecasts.

### 4. 🚨 Multi-Channel Alert & Broadcast Engine
- Automated Twilio integration for SMS and WhatsApp broadcasts to registered coastal vessels.
- Emergency triggers for high-risk conditions (Risk Score > 75 or active cyclone vicinity).

### 5. 🛰️ Streamlit Satellite Data Interpreter
- Dedicated interactive exploration dashboard for analyzing coastal NetCDF files, SAR imagery, wind vectors, and oceanographic layers.

---

## 🏛️ System Architecture

```
                                  ┌────────────────────────┐
                                  │   Frontend Dashboard   │
                                  │ (Leaflet GIS / Web UI) │
                                  └───────────┬────────────┘
                                              │ HTTP / JSON
                                              ▼
                                  ┌────────────────────────┐
                                  │   FastAPI Core Engine  │
                                  │       (main.py)        │
                                  └───────────┬────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
         ┌────────────────────────┐                      ┌────────────────────────┐
         │  Multi-Agent Pipeline  │                      │  Marine Data Gateway   │
         │  - Planner             │                      │  - IMD RSMC Cyclones   │
         │  - Weather & Marine    │                      │  - INCOIS PFZ Feed     │
         │  - GIS / Geofencing    │                      │  - Copernicus CMEMS    │
         │  - Risk Engine         │                      │  - MOSDAC NetCDF / SAR │
         │  - Validator & Output  │                      │  - Open-Meteo Marine   │
         └────────────┬───────────┘                      └────────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  AI & Services Layer   │
         │  - Gemini Multi-Key    │
         │  - Sarvam AI (Voice)   │
         │  - Twilio (SMS/WA)     │
         └────────────────────────┘
```

---

## 📁 Repository Structure

```
├── backend/
│   ├── agents/                   # Multi-agent implementations (Orchestrator, Planner, Weather, etc.)
│   ├── engine/                   # Core decision pipeline, Risk Engine, Safety Gate, Cyclone Tracker
│   ├── gateway/                  # Marine Data Gateway & Telemetry Normalization
│   ├── parsers/                  # NetCDF (.nc) and SAR parser modules
│   ├── processors/               # IMD, Copernicus CMEMS, and Weather processors
│   ├── services/                 # Twilio alert and notification services
│   ├── utils/                    # Key rotation, geodesic and geospatial calculations
│   ├── main.py                   # FastAPI application entrypoint & API endpoints
│   ├── requirements.txt          # Python dependencies
│   ├── start.bat                 # Windows start script
│   ├── .env.example              # Environment variable configuration template
│   └── .gitignore
├── frontend/
│   ├── index.html                # Maritime GIS Dashboard UI
│   ├── style.css                 # Custom modern stylesheet
│   └── app.js                    # Leaflet map integration, telemetry streams & API client
├── Interpreter/
│   ├── app.py                    # Streamlit Satellite & NetCDF Visualizer
│   └── .gitignore
├── MOSDAC/                       # Sample MOSDAC Coastal NetCDF datasets
├── Bhuvan  NRSC – LULC 2024–25/  # Land Use / Land Cover documentation & guides
├── docs/
│   └── API_REFERENCE.md          # Comprehensive REST API specifications
├── .gitignore                    # Global repository gitignore
└── README.md                     # Project documentation
```

---

## ⚙️ Installation & Setup

### Prerequisites
- **Python 3.10+**
- **pip** package manager
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/MallikarjunaDM/Sagarvani-backend-.git
cd Sagarvani-backend-
```

### 2. Configure Environment Variables
Copy `.env.example` in the `backend/` directory to `.env`:
```bash
cp backend/.env.example backend/.env
```
Fill in your credentials inside `backend/.env`:
- `GEMINI_API_KEY_1` to `GEMINI_API_KEY_6` or `GOOGLE_API_KEY`
- `SARVAM_API_KEY` (for speech-to-text & translation)
- `COPERNICUS_USERNAME` & `COPERNICUS_PASSWORD` (optional, for CMEMS toolbox)
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` (optional, for alerts)

### 3. Install Backend Dependencies
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Run the FastAPI Backend Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Or run using `start.bat` on Windows.

Interactive API Documentation will be available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 5. Launch the Frontend Dashboard
Simply serve the `frontend/` directory using any local HTTP server (or open `frontend/index.html` in your browser):
```bash
# Using Python built-in HTTP server:
cd frontend
python -m http.server 3000
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 6. Launch the Streamlit Satellite Interpreter (Optional)
```bash
streamlit run Interpreter/app.py
```

---

## 📊 Core API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check & system routing map |
| `GET` | `/api/orca/query?lat=&lon=&vessel=&language=&intent=` | Complete 10-Step Decision Pipeline (English & Kannada) |
| `GET` | `/api/gateway/normalized?lat=&lon=` | Normalized Marine Data Gateway telemetry record |
| `GET` | `/api/pfz/candidates?lat=&lon=` | Active INCOIS Potential Fishing Zones |
| `GET` | `/api/geofence/restricted-zones` | MPAs, Defense firing zones & geofences |
| `GET` | `/api/weather/{lat}/{lon}` | Combined atmospheric & marine forecast |
| `GET` | `/api/risk/point?lat=&lon=` | Multi-parameter composite risk assessment |
| `GET` | `/api/cyclone-track` | Active cyclone trajectories & danger zones |
| `POST`| `/api/advisory` | AI advisory generation with automatic key rotation |
| `POST`| `/api/send-alert` | Dispatch SMS / WhatsApp emergency alerts |

> For complete parameter lists and schemas, refer to [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md).

---

## 🧮 Marine Risk Scoring Model

The composite risk score is evaluated on a normalized scale (0–100):

$$\text{Risk Score} = 0.30 \cdot S_{\text{wave}} + 0.25 \cdot S_{\text{wind}} + 0.20 \cdot S_{\text{current}} + 0.15 \cdot S_{\text{cyclone}} + 0.10 \cdot S_{\text{lulc}}$$

| Score Range | Risk Level | Status Indicator | Action Required |
|---|---|---|---|
| **0 – 25** | 🟢 SAFE | Normal | Safe for artisanal and commercial fishing |
| **26 – 50** | 🟡 CAUTION | Moderate | Exercise caution; monitor weather changes |
| **51 – 75** | 🟠 WARNING | Severe | Avoid deep-sea ventures; stay near coastline |
| **76 – 100** | 🔴 DANGER | Critical | Cease all operations; immediate return to harbor & auto-alert dispatched |

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome!
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
