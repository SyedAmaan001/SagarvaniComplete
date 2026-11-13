# 🌊 Sagarvani — ORCA Marine Intelligence Platform

> **Conversational marine decision intelligence for safer and smarter coastal operations**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-Frontend-black.svg)](https://nextjs.org/)
[![Tests](https://img.shields.io/badge/Backend%20tests-62%20passing-brightgreen.svg)](#-testing)
[![Status](https://img.shields.io/badge/Status-Active%20Development-orange.svg)]()

Sagarvani lets a fisherman or maritime operator **speak or type a question** — *"Is it safe to go fishing from Malpe today?"* — and get a spoken, explainable answer built from marine, weather and geospatial data with deterministic safety rules.

**Smart India Hackathon 2026 · SIH26176 · Team Helios Luna · Dayananda Sagar University**

---

## 📑 Contents
[Overview](#-overview) · [Voice conversation](#-voice-conversation) · [Honest data policy](#-honest-data-policy) · [Architecture](#-architecture) · [Repository structure](#-repository-structure) · [Local development](#-local-development) · [Configuration](#-configuration) · [API](#-api) · [Testing](#-testing) · [Deployment](#-deployment-railway) · [Known limitations](#-known-limitations) · [Roadmap](#-roadmap) · [Project](#-project)

---

## 🌊 Overview

ORCA sits above fragmented marine, meteorological and geospatial sources and turns them into one decision loop:

```text
Interpret → Plan → Retrieve → Normalize → Reason → Constrain (safety gate) → Rank → Verify → Respond
```

Core principle: **AI plans and explains; deterministic systems enforce safety.** Unsafe or restricted options are removed *before* productive ones are ranked.

It is designed for questions such as: *Can I safely go fishing tomorrow morning? What are the sea conditions near me? Where is the nearest useful fishing zone? Which areas should I avoid?*

---

## 🎙️ Voice conversation

```text
mic (MediaRecorder) → POST /api/orca/stt → transcript (editable)
   → POST /api/orca/chat → answer → POST /api/orca/tts → spoken reply
```

- **Speech-to-text:** Sarvam AI (`SARVAM_API_KEY`). The response states `mode: "real"` or `mode: "mock"`. Mock mode returns a clearly labelled demo sentence — it does **not** recognise speech — and the UI shows a "Demo transcription" warning.
- **Conversation engine:** intent-aware (greeting, capabilities, weather, sea conditions, hazards, fishing decision, follow-ups) with per-conversation memory. It never assumes a location; it asks for one.
- **Text-to-speech:** Sarvam audio when a key is configured, otherwise the browser's `speechSynthesis`. The header shows which is playing ("AI voice" / "Browser voice"), with stop and mute controls and a *Listen* button on every answer.
- Works without any paid API: STT falls back to labelled mock, TTS to browser speech.

---

## 🛡️ Honest data policy

- Wave height and wind come from **Open-Meteo model forecasts** (not observations). If either feed is unavailable the system answers **"cannot assess"** — it never substitutes values.
- Potential Fishing Zones, SST, chlorophyll, lightning and tide values are **static reference data**, not live INCOIS/IMD/ISRO feeds. Answers using them set `uses_mock_data: true` and list `mock_components`.
- Cyclone/hazard questions point to the official IMD and INCOIS bulletins; no verified live alert feed is integrated yet.
- `DATA_MODE=mock` returns deterministic, labelled demo numbers and never a go/no-go recommendation.
- Every safety answer ends with a reminder to confirm with the official IMD/INCOIS bulletin or harbour authority.

---

## 🏗️ Architecture

```text
Next.js dashboard ──HTTP──▶ FastAPI (backend/main.py)
                                │
        ┌───────────────────────┼─────────────────────────┐
        ▼                       ▼                         ▼
 ConversationEngine      STT / TTS services        Sessions (Redis or memory)
        │ (decision intents, location known)
        ▼
 Interpreter → ConversationAgent → OrcaPipeline (10 steps)
                                      │
              MarineDataGateway · HardSafetyGate · Ranker · EvidenceEngine
```

- **Pipeline:** `backend/engine/orca_pipeline.py` runs retrieval, normalisation, the hard safety/geofence gate, multi-objective ranking, evidence audit and the decision package. It fails closed when live sea-state data is missing.
- **Agents:** planner, marine, weather, GIS, ocean analytics, risk, spatial reasoning, validator and visualizer agents behind `/api/orchestrate`.
- **Sessions:** Redis when `REDIS_URL` is set and reachable; otherwise in-memory. Redis failures degrade gracefully and are reported by `/ready`.

---

## 📁 Repository structure

```text
backend/
  main.py                 FastAPI app, middleware, endpoints
  schemas.py              ChatResponse / STT / TTS models
  agents/                 planner, orchestrator, domain agents, interpreter, conversation agent
  engine/                 orca_pipeline, safety_gate, ranker, evidence, risk, cyclone, advisory
  gateway/                MarineDataGateway (normalisation + provenance)
  services/               conversation_engine, stt_service, tts_service, session_store, alert_service
  processors/ parsers/    Open-Meteo, IMD, Copernicus, MOSDAC NetCDF / SAR parsing
  utils/                  config (settings, key pools), geo utils, Gemini helper
  tests/                  pytest suite (no network, no keys needed)
frontend/
  src/app/                pages (home, dashboard, ...)
  src/components/         dashboard (ConversationRail, VoiceModal, MapCanvas, ...) and landing UI
  src/lib/                api clients (orca, voice), speech manager, config
docs/                     API reference, frontend integration, VOICE_AND_DEPLOYMENT.md
MOSDAC/ IMD/ ...          reference datasets and documents
```

---

## 🚀 Local development

**Backend**
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Linux/macOS: source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env           # then add keys (all optional)
python main.py                 # http://localhost:8000  (docs at /docs)
```

**Frontend**
```bash
cd frontend
npm install
npm run dev                    # http://localhost:3000 (use -p 3001 if 3000 is busy)
```
Locally the frontend defaults to `http://localhost:8000`. Use HTTPS or `localhost` for microphone access.

---

## ⚙️ Configuration

Backend (`backend/.env`, see `.env.example`):

| Variable | Purpose |
|---|---|
| `SARVAM_API_KEY` | Real STT and TTS ([dashboard.sarvam.ai](https://dashboard.sarvam.ai)). Without it: labelled mock STT + browser speech |
| `GEMINI_API_KEY_1…` | Optional LLM-assisted extraction/advisory |
| `STT_MODE` / `TTS_MODE` | `auto` (default) · `real`/`mock` · `provider`/`browser` |
| `DATA_MODE` | `live` (default) or `mock` |
| `CORS_ORIGINS` | Extra allowed origins (added to localhost + defaults); `*` allows any |
| `REDIS_URL` | Optional durable sessions |
| `MAX_AUDIO_BYTES`, `LOG_LEVEL` | Limits and logging |

Frontend: `NEXT_PUBLIC_BACKEND_URL` — backend base URL, no trailing slash. It is inlined at **build time**, so set it before building.

Never commit `.env`, keys or tokens (`.env` is git-ignored).

---

## 🔌 API

| Endpoint | Purpose |
|---|---|
| `GET /health`, `GET /ready` | Liveness / readiness |
| `GET /api/status` | Modes and which keys are configured (booleans only) |
| `POST /api/orca/stt` | Multipart audio → transcript (`mode`, `is_mock`, `warning`) |
| `POST /api/orca/chat` | `{query, session_id?}` → answer, intent, status, `uses_mock_data`, `data_sources`, errors |
| `POST /api/orca/tts` | `{text, language}` → provider audio or "use browser speech" |
| `GET /api/orca/query` | Run the full 10-step pipeline for a location |
| `GET /api/risk-zones`, `/api/weather/{lat}/{lon}`, `/api/pfz/candidates`, … | Data and risk endpoints |

Every response carries `request_id` (also the `X-Request-ID` header); errors are `{detail, code, request_id}`. Interactive docs: `/docs`. More detail in [`docs/`](docs/).

---

## 🧪 Testing

```bash
cd backend
python -m pytest        # 62 tests, no network or API keys required
```

Covers startup, health/readiness, CORS, config validation, conversation intents and follow-ups, mock and real-provider STT/TTS paths, audio validation, provider failures, Redis unavailability, pipeline fail-closed behaviour and the full mock voice flow. `python test_all.py` smoke-tests the data endpoints against a running server.

Not automated: real microphone hardware and audible playback — see the manual steps in [`docs/VOICE_AND_DEPLOYMENT.md`](docs/VOICE_AND_DEPLOYMENT.md).

---

## ☁️ Deployment (Railway)

- **Backend start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT` (or `python main.py`, which reads `PORT`). Set `SARVAM_API_KEY` and any extra `CORS_ORIGINS`.
- **Frontend:** set `NEXT_PUBLIC_BACKEND_URL` to the backend's public URL **before** building.
- Verify with `GET /health` and `GET /ready` on the deployed backend.

Details: [`docs/VOICE_AND_DEPLOYMENT.md`](docs/VOICE_AND_DEPLOYMENT.md).

---

## ⚠️ Known limitations

- PFZ, SST, chlorophyll, lightning, tide and geofence data are static reference data; no live INCOIS/IMD/MOSDAC integration yet.
- Chat answers are in English (speech input in Indian languages is translated to English).
- Fishing-decision answers cover current conditions only, not a specific future time.
- `/api/orchestrate` and the older domain agents still default to a 1.2 m wave / 22 km/h wind when feeds fail.
- No verified live cyclone/alert feed in chat.

## 🔮 Roadmap

- Live INCOIS PFZ / IMD warning / MOSDAC integrations through the Marine Data Gateway
- Time-specific forecast answers and regional-language responses
- Durable task execution and observability for production
- Wider coastal coverage beyond the Karnataka pilot

---

## 🏆 Project

| | |
|---|---|
| Event | Smart India Hackathon 2026 |
| Problem Statement | SIH26176 — ORCA Marine Ecosystem Reasoning with Collaborative Agents |
| Theme / Category | Disaster Management / Software |
| Team | Team Helios Luna |
| Institution | Dayananda Sagar University |

Data sources referenced by the concept: INCOIS (incl. ERDDAP), MOSDAC/ISRO, IMD, Bhuvan/NRSC and government GIS datasets. API availability, authentication and usage permissions must be validated before production integration.

## 🤝 Contributing

Create a feature branch, make your changes with tests, and open a Pull Request.

## 📄 License

Released under the [MIT License](LICENSE).
