# Voice conversation, mock mode and deployment

## Flow
mic (MediaRecorder) -> `POST /api/orca/stt` -> transcript shown & editable -> `POST /api/orca/chat` -> answer shown -> `POST /api/orca/tts` -> audio (provider) or browser speech.

| Endpoint | Purpose |
|---|---|
| `GET /health`, `GET /ready` | liveness / readiness (`/ready` is 503 until modules + engine load; Redis down only degrades) |
| `GET /api/status` | modes + which keys are configured (booleans only, never values) |
| `POST /api/orca/stt` | multipart `file`; returns `text`, `mode` (`real`/`mock`), `is_mock`, `warning` |
| `POST /api/orca/chat` | `{query, session_id?}` -> `ChatResponse` (see `backend/schemas.py`) |
| `POST /api/orca/tts` | `{text, language}` -> `mode` `provider` (base64 audio) or `browser` (client speaks) |

Every response carries `request_id` (also `X-Request-ID` header). Errors: `{"detail", "code", "request_id"}`.

## Honest data policy
* Wave/wind come from Open-Meteo (model **forecast**, not observation). If either is missing, the pipeline answers *cannot assess* - it never substitutes values.
* PFZ registry, SST, chlorophyll, lightning and tide values are **static reference data**; answers that use them set `uses_mock_data=true` and list `mock_components`.
* `DATA_MODE=mock` gives deterministic labelled demo numbers and never a go/no-go.
* `STT_MODE=mock` (or no `SARVAM_API_KEY`) returns a labelled demo transcript - it does **not** recognise speech.

## Environment variables
Backend (Railway): `SARVAM_API_KEY` (STT + TTS; https://dashboard.sarvam.ai), optional `GEMINI_API_KEY_1`, `CORS_ORIGINS`, `REDIS_URL`, `STT_MODE`, `TTS_MODE`, `DATA_MODE`. See `backend/.env.example`.
Frontend (Railway, set **before build**): `NEXT_PUBLIC_BACKEND_URL=https://sagarvanicomplete-production.up.railway.app`.

Backend start command: `uvicorn main:app --host 0.0.0.0 --port $PORT` (or `python main.py`, which reads `PORT`).
CORS already allows the deployed frontend `https://sagarvani-frontend-production.up.railway.app` and localhost; `CORS_ORIGINS` adds more.

## Tests
```
cd backend
venv\Scripts\python -m pip install -r requirements-dev.txt
venv\Scripts\python -m pytest
```
Tests use fakes: no network, no keys.

## Manual microphone test
1. Open the dashboard over HTTPS (or localhost), click the mic, allow permission.
2. Speak, press **Stop & Transcribe**; check the transcript badge says "Speech transcribed" (real) and not "Demo transcription".
3. Submit; read the answer; confirm you hear it (header shows "AI voice" or "Browser voice"); use the header button to stop/mute.
