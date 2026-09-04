# Sagarvani Backend — Frontend API Documentation

## Base URL
`http://localhost:8000` (Default local development port)

---

## Overview & Architecture
The Sagarvani (ORCA) backend is a FastAPI microservice platform providing real-time ocean intelligence, risk assessments, coastal advisories, weather/marine forecasts, and multi-lingual AI conversation for Indian coastal fishermen.

- **Framework**: FastAPI (Python 3.10+)
- **Data Stores & Sources**: MOSDAC (ISRO), INCOIS, IMD, Open-Meteo, Copernicus Marine, JSON cache stores, NetCDF4 parsers.
- **AI & ML**: Gemini API key rotator, multi-agent AI pipeline (Orchestrator, Interpreter, Planner, Risk, Weather, GIS, Advisory).
- **Communication**: Twilio SMS & WhatsApp alerts, Sarvam AI STT & Translation.

---

## Authentication & Authorization
Currently, endpoints are public or protected by standard client session identifiers (`session_id`).
Optional integrations with external API keys (Twilio, Sarvam, Gemini) are managed via backend `.env` configuration.

---

## API Inventory & Endpoint Specifications

### 1. System & Health
#### `GET /`
- **Purpose**: System health check & endpoint index.
- **Auth**: None
- **Response**:
  ```json
  {
    "system": "ORCA – Ocean Risk & Coastal Advisory System",
    "version": "1.0.0",
    "status": "online",
    "sih_problem": "SIH26176",
    "modules_loaded": true,
    "modules_error": null
  }
  ```

#### `GET /api/status`
- **Purpose**: Detailed system diagnosis (API keys loaded, module status).
- **Response**:
  ```json
  {
    "status": "healthy",
    "modules_loaded": true,
    "key_coverage": "10/10 keys set"
  }
  ```

#### `GET /api/languages`
- **Purpose**: Retrieve supported 22 Scheduled Indian languages.
- **Response**: List of supported language codes and metadata.

---

### 2. Multi-Agent Conversation & Interpretation (ORCA Engine)

#### `POST /api/orca/interpret`
- **Purpose**: Translates regional language queries to English and extracts structured marine intent schema.
- **Request Body**:
  ```json
  {
    "query": "I have a 5m boat. Can I leave Malpe tomorrow at 5 AM?",
    "session_id": "default_session",
    "language_override": "auto"
  }
  ```
- **Response**: Structured intent object containing location, vessel parameters, intent category.

#### `POST /api/orca/query` / `POST /api/orca/chat`
- **Purpose**: Execute multi-agent intelligence pipeline to answer fisherman queries with real-time risk scores and actionable advisories.
- **Request Body**:
  ```json
  {
    "query": "Is it safe to fish 15 km off Mangalore coast today?",
    "session_id": "session_123"
  }
  ```

#### `POST /api/orchestrate`
- **Purpose**: Execute end-to-end multi-agent orchestration for complex multi-part queries.

---

### 3. Marine Weather & Data Services

#### `GET /api/weather/{lat}/{lon}`
- **Purpose**: Get real-time weather and marine forecast (wave height, wind speed, visibility).
- **Parameters**: `lat` (float), `lon` (float)

#### `GET /api/weather/marine/{lat}/{lon}`
- **Purpose**: Marine specific wave spectrum and swell forecast.

#### `GET /api/ocean-currents`
- **Purpose**: Fetch latest MOSDAC ocean current grid data.

#### `GET /api/ocean-currents/point`
- **Purpose**: Get ocean current vector (u, v velocity) for exact lat/lon coordinate.

---

### 4. Risk Assessment & Cyclone Tracking

#### `GET /api/risk/point`
- **Purpose**: Returns instant numerical risk score (0-100), risk status (`SAFE`, `CAUTION`, `WARNING`, `DANGER`), and safety gates.
- **Query Params**: `lat=13.35&lon=74.70`

#### `GET /api/risk-zones`
- **Purpose**: Returns GeoJSON representation of coastal risk zones for mapping components.

#### `GET /api/cyclone-track`
- **Purpose**: Returns active cyclone trajectory and forecast cone.

#### `GET /api/cyclone/impact`
- **Purpose**: Evaluates cyclone threat level for a specific coordinate.

---

### 5. Advisories & Alerts

#### `GET /api/advisory`
- **Purpose**: Generate multi-lingual Gemini AI synthesized safety advisory.
- **Query Params**: `lat=13.35&lon=74.70&language=both`

#### `POST /api/send-alert`
- **Purpose**: Trigger SMS or WhatsApp alert via Twilio to target fisherman.
- **Request Body**:
  ```json
  {
    "to_number": "+919035195941",
    "message": "High Wave Alert: Stay ashore today.",
    "risk_level": "WARNING",
    "channel": "whatsapp"
  }
  ```

---

### 6. Specialized Ocean Products

- `GET /api/pfz/candidates`: Potential Fishing Zones (PFZ) coordinate candidates.
- `GET /api/tide/predict`: Astronomical tide height predictions.
- `GET /api/vessel/sva`: Vessel safety vulnerability assessment based on vessel dimensions.
- `GET /api/geofence/restricted-zones`: Maritime security boundaries and prohibited zones.
- `GET /api/maritime/limits`: Maritime boundaries (EEZ, Territorial waters).
