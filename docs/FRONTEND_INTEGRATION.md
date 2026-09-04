# Sagarvani Frontend Integration Guide

This guide provides everything needed for a React, Next.js, Vite, or mobile developer to connect to the Sagarvani backend.

---

## 1. Quick Start / Running the Backend

### Prerequisites
- Python 3.10+ installed
- Virtual environment (`venv`) setup

### Startup Commands
```bash
# Navigate to backend directory
cd backend

# Create & activate virtual environment (Windows)
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Backend OpenAPI interactive docs will be available at:
`http://localhost:8000/docs`

---

## 2. CORS Configuration

The backend supports configurable origins via the `.env` file:
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080
```
Ensure your frontend development server URL is listed in `CORS_ORIGINS`.

---

## 3. Standard Request & Response Patterns

Most JSON response payloads follow standard schemas.

### Example Success Response (`GET /api/risk/point?lat=13.35&lon=74.70`)
```json
{
  "lat": 13.35,
  "lon": 74.70,
  "risk_score": 42.5,
  "risk_level": "CAUTION",
  "factors": {
    "wave_height": 2.1,
    "wind_speed": 18.4,
    "current_speed": 0.8
  },
  "timestamp": "2026-09-04T17:18:00Z"
}
```

### Example Validation Error (`422 Unprocessable Entity`)
```json
{
  "detail": [
    {
      "loc": ["query", "lat"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 4. Example Code Snippets for Frontend Integrations

### JavaScript / TypeScript Fetch Example

```typescript
// Fetching weather and marine risk for Malpe Harbor
async function getMarineRisk(lat: number, lon: number) {
  try {
    const response = await fetch(`http://localhost:8000/api/risk/point?lat=${lat}&lon=${lon}`);
    if (!response.ok) {
      throw new Error(`HTTP Error ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Failed to fetch marine risk:", error);
  }
}
```

### Multi-turn AI Assistant Integration

```typescript
async function askOrcaAssistant(userQuery: string, sessionId: string = "user_session_1") {
  const response = await fetch('http://localhost:8000/api/orca/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: userQuery,
      session_id: sessionId,
      language_override: 'auto'
    })
  });
  return await response.json();
}
```

---

## 5. File & Voice Audio Handling

For the Voice Assistant endpoint (`POST /api/orca/stt`), send audio recorded from the microphone using standard `FormData`:

```typescript
async function sendVoiceQuery(audioBlob: Blob) {
  const formData = new FormData();
  formData.append('file', audioBlob, 'query.wav');

  const response = await fetch('http://localhost:8000/api/orca/stt', {
    method: 'POST',
    body: formData,
  });

  return await response.json();
}
```
