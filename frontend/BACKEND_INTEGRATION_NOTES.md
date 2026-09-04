# Sagarvani Next.js Frontend — Backend Integration Documentation

## Architecture & Overview
- **Repository Source**: [https://github.com/SyedAmaan001/Sagarvani-2.0.git](https://github.com/SyedAmaan001/Sagarvani-2.0.git)
- **Framework**: Next.js 16.3.4 (App Router) + React 19.2.8 + Tailwind CSS v4 + TypeScript 5
- **Visuals**: WebGL Liquid shader (`ogl`), GSAP / Anime.js / Framer Motion, Leaflet.js
- **Backend API URL**: `http://localhost:8000` (FastAPI ORCA Decision Engine)
- **Frontend URL**: `http://localhost:3000`

---

## Changes Made & Integration Points

1. **API Service Layer (`src/lib/api/orca.ts`)**:
   - Updated `queryOrca(query, sessionId, language)`:
     - Directly calls backend `POST /api/orca/chat` with `{ query, session_id, language_override, execute_pipeline: true }`.
     - Maps the authoritative 10-step `pipeline_result` (including `decision_package`, `conditions`, `evidence_trail`, `cartography`, and `multilingual_advisory`) into the dashboard types (`AgentStatus[]`, `ConversationTurn`, `Readout[]`, `Alert[]`).
   - Updated `checkHealth()`:
     - Directly checks `GET /api/status`.
   - Added helper functions:
     - `fetchMarineWeather(lat, lon)` -> `GET /api/weather/marine/{lat}/{lon}`
     - `fetchSatelliteComposite(lat, lon)` -> `GET /api/satellite/composite`
     - `fetchTidePrediction(station, hours)` -> `GET /api/tide/predict`

2. **Dashboard Query Handler (`src/components/dashboard/DashboardClient.tsx`)**:
   - Wired `handleCustomAsk` to update agent rails, live telemetry readouts, validation traces, and alert panels with real-time backend responses.

3. **Preserved Codebase & Designs**:
   - Retained 100% of all homepage components (`Hero.tsx`, `WebGLLiquid.tsx`, `TheAgents.tsx`, `SplitCardSection.tsx`, `WavesSection.tsx`, `ThreeSteps.tsx`, `Reliability.tsx`, `CaseStudyFlipStack.tsx`, `Impact.tsx`, `FAQ.tsx`, `AccessEverywhere.tsx`, `FinalCTA.tsx`, `Nav.tsx`, `Footer.tsx`).
   - Retained all dashboard layout components (`AgentStatusRail.tsx`, `AlertsPanel.tsx`, `ConversationRail.tsx`, `MapCanvas.tsx`, `ReadoutStrip.tsx`, `ReasoningPanel.tsx`, `VoiceModal.tsx`).

---

## Commands to Run Together

**Backend:**
```bash
cd backend
.\venv\Scripts\activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm run dev -- -p 3000
```
- Homepage: `http://localhost:3000`
- Dashboard Console: `http://localhost:3000/dashboard`
