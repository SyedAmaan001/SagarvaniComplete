"""
ORCA – Ocean Risk & Coastal Advisory System
FastAPI Backend — Main Application
SIH 2026 | Problem Statement: SIH26176

Endpoints:
  GET  /                          → Health check + system status
  GET  /api/status                → Full system status
  GET  /api/ocean-currents        → Latest MOSDAC ocean current data
  GET  /api/ocean-currents/point  → Ocean current at specific lat/lon
  GET  /api/weather/{lat}/{lon}   → Weather + marine forecast
  GET  /api/risk-zones            → Full risk map GeoJSON
  GET  /api/risk/point            → Risk score for specific lat/lon
  GET  /api/cyclone-track         → Active cyclone data + GeoJSON
  GET  /api/advisory              → Gemini AI advisory for lat/lon
  GET  /api/coastal-summary       → MOSDAC SAR coastal product summary
  POST /api/send-alert            → Trigger Twilio SMS/WhatsApp alert
  GET  /api/message-status/{sid}  → Check Twilio message delivery status
"""

import os
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# ─── App Initialisation ────────────────────────────────────────────────────────
app = FastAPI(
    title="ORCA – Ocean Risk & Coastal Advisory System",
    description=(
        "Backend API for the ORCA maritime safety platform. "
        "Provides real-time ocean risk scoring, Gemini AI advisories, "
        "cyclone tracking, and fisherman alert services. "
        "SIH 2026 | Problem Statement: SIH26176"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS (allow frontend to call this API) ───────────────────────────────────
cors_origins_env = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Import modules (lazy to avoid startup errors if packages missing) ─────────
def _import_modules():
    global nc_parser, sar_parser, weather_processor, imd_processor
    global copernicus_processor, risk_engine, advisory_engine
    global cyclone_tracker, alert_service, orchestrator_instance, orca_pipeline_instance
    global marine_products_mod, conversation_agent_instance, INDIAN_LANGUAGES
    global interpreter_instance

    from parsers import nc_parser, sar_parser
    from processors import weather_processor, imd_processor, copernicus_processor
    from processors import marine_products as marine_products_mod
    from engine import risk_engine, advisory_engine, cyclone_tracker
    from services import alert_service
    from agents.orchestrator import MainOrchestrator
    from engine.orca_pipeline import OrcaPipeline
    from agents.conversation_agent import ConversationAgent, INDIAN_LANGUAGES
    from agents.interpreter_agent import InterpreterModule
    
    orchestrator_instance = MainOrchestrator()
    orca_pipeline_instance = OrcaPipeline()
    conversation_agent_instance = ConversationAgent()
    interpreter_instance = InterpreterModule()

try:
    _import_modules()
    MODULES_OK = True
    MODULES_ERROR = None
except Exception as e:
    MODULES_OK = False
    MODULES_ERROR = str(e)


# ─── Pydantic Request/Response Models ─────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str = Field(
        ...,
        description="Natural language question from fisherman",
        example="I have a 5 m boat. Can I leave Malpe at 5 AM tomorrow and fish within 30 km?"
    )
    session_id: Optional[str] = Field(default="default_session", description="Conversation session ID for multi-turn memory")
    language_override: Optional[str] = Field(default="auto", description="Language override code: auto, en, kn, hi, ta, te, ml, etc.")
    execute_pipeline: Optional[bool] = Field(default=True, description="Whether to execute the full 10-step pipeline")


class AlertRequest(BaseModel):
    to_number: str = Field(
        default="+919035195941",
        description="Recipient phone number with country code",
        example="+919035195941",
    )
    message: str = Field(
        ...,
        description="Alert message text",
        example="Cyclone warning: Stay ashore. High waves expected.",
    )
    risk_level: Optional[str] = Field(
        default="WARNING",
        description="Risk level: SAFE | CAUTION | WARNING | DANGER",
        example="DANGER",
    )
    channel: str = Field(
        default="whatsapp",
        description="Delivery channel: 'sms' or 'whatsapp'",
        example="whatsapp",
    )
    lat: Optional[float] = Field(default=None, description="Location latitude")
    lon: Optional[float] = Field(default=None, description="Location longitude")


class BulkAlertRequest(BaseModel):
    phone_numbers: List[str] = Field(
        ...,
        description="List of recipient phone numbers",
    )
    message: str = Field(..., description="Alert message")
    risk_level: str = Field(default="WARNING")
    channel: str = Field(default="sms")
    lat: Optional[float] = None
    lon: Optional[float] = None


class AdvisoryRequest(BaseModel):
    lat: float = Field(..., description="Latitude", example=15.0)
    lon: float = Field(..., description="Longitude", example=72.0)
    language: str = Field(
        default="both",
        description="Advisory language: 'english', 'hindi', or 'both'",
    )
    auto_alert: bool = Field(
        default=False,
        description="Auto-send WhatsApp alert if risk score > 75",
    )


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", tags=["System"])
async def root():
    """Health check and system overview."""
    return {
        "system": "ORCA – Ocean Risk & Coastal Advisory System",
        "version": "1.0.0",
        "status": "online",
        "sih_problem": "SIH26176",
        "modules_loaded": MODULES_OK,
        "modules_error": MODULES_ERROR,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoints": {
            "docs": "/docs",
            "health": "/api/status",
            "ocean_currents": "/api/ocean-currents",
            "weather": "/api/weather/{lat}/{lon}",
            "risk_zones": "/api/risk-zones",
            "risk_point": "/api/risk/point?lat=15.0&lon=72.0",
            "cyclone_track": "/api/cyclone-track",
            "advisory": "/api/advisory",
            "coastal_summary": "/api/coastal-summary",
            "send_alert": "POST /api/send-alert",
        },
    }


@app.get("/api/status", tags=["System"])
async def system_status():
    """Full system status: API keys, datasets, module health."""
    env_check = {
        "GEMINI_API_KEY_1": bool(os.getenv("GEMINI_API_KEY_1")),
        "GEMINI_API_KEY_2": bool(os.getenv("GEMINI_API_KEY_2")),
        "GEMINI_API_KEY_3": bool(os.getenv("GEMINI_API_KEY_3")),
        "COPERNICUS_USERNAME": bool(os.getenv("COPERNICUS_USERNAME")),
        "COPERNICUS_PASSWORD": bool(os.getenv("COPERNICUS_PASSWORD")),
        "TWILIO_ACCOUNT_SID": bool(os.getenv("TWILIO_ACCOUNT_SID")),
        "TWILIO_AUTH_TOKEN": bool(os.getenv("TWILIO_AUTH_TOKEN")),
        "TWILIO_PHONE_NUMBER": bool(os.getenv("TWILIO_PHONE_NUMBER")),
        "IMD_API_KEY": bool(os.getenv("IMD_API_KEY")),
        "MOSDAC_API_TOKEN": bool(os.getenv("MOSDAC_API_TOKEN")),
    }

    missing = [k for k, v in env_check.items() if not v]

    return {
        "status": "healthy" if MODULES_OK else "degraded",
        "modules_loaded": MODULES_OK,
        "modules_error": MODULES_ERROR,
        "api_keys": env_check,
        "missing_keys": missing,
        "key_coverage": f"{len(env_check) - len(missing)}/{len(env_check)} keys set",
        "python_version": sys.version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── ORCA Marine Intelligence & Gateway Endpoints (SIH 26176) ────────────────

@app.get("/api/languages", tags=["Multilingual Architecture"])
async def get_supported_languages():
    """Returns the 22 Scheduled Indian Languages + English registry."""
    return {
        "languages": INDIAN_LANGUAGES,
        "coastal_primary": ["en", "kn", "hi", "ta", "te", "ml", "mr", "gu", "bn", "or"],
        "total_count": len(INDIAN_LANGUAGES),
        "architecture": "Indian-Language-Capable Extensible Architecture (ISO-639-3 standard)"
    }


@app.post("/api/orca/interpret", tags=["Step 2: Interpreter"])
async def interpret_query_endpoint(req: ChatRequest):
    """
    Step 2: Interpreter Endpoint (integrated from friend's Interpreter module):
    - Translates regional-language user query to English using Sarvam AI.
    - Extracts structured MarineIntentSchema (intent_type, location, date, vessel_type).
    - Returns standardized interpretation payload for Step 3 (Plan).
    """
    if not MODULES_OK or interpreter_instance is None:
        raise HTTPException(500, detail=f"Interpreter module not loaded: {MODULES_ERROR}")
    try:
        interpretation = interpreter_instance.interpret(
            query=req.query,
            language=req.language_override
        )
        return interpretation
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/api/orca/stt", tags=["Step 2: Voice STT"])
async def voice_stt_endpoint(file: UploadFile = File(...)):
    """
    Step 2: Voice Speech-to-Text & Translate Endpoint:
    - Accepts microphone audio recorded in any Indian regional language.
    - Translates and transcribes using Sarvam AI saaras:v3 model.
    - Extracts MarineIntentSchema and returns complete interpretation.
    """
    if not MODULES_OK or interpreter_instance is None:
        raise HTTPException(500, detail=f"Interpreter module not loaded: {MODULES_ERROR}")
    try:
        audio_bytes = await file.read()
        res = interpreter_instance.process_voice_audio(
            audio_bytes=audio_bytes,
            filename=file.filename or "recording.wav"
        )
        return res
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/api/orca/chat", tags=["Conversational ORCA & Pipeline"])
async def conversational_orca(req: ChatRequest):
    """
    Conversational ORCA Agent Endpoint (Steps 1-10):
    - Step 1: User Query (Text or Voice Transcription)
    - Step 2: Interpreter (Sarvam AI translation + MarineIntentSchema extraction)
    - Step 3-10: Complete Safe Decision Loop (Plan -> Retrieve -> Normalize -> Reason -> Constrain -> Rank -> Verify -> Respond)
    """
    if not MODULES_OK or orca_pipeline_instance is None or conversation_agent_instance is None:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        # Step 2: Run query through the Interpreter module
        interpretation = None
        if interpreter_instance is not None:
            try:
                interpretation = interpreter_instance.interpret(
                    query=req.query,
                    language=req.language_override
                )
            except Exception:
                pass

        # Parse query & extract understanding chips
        parse_result = conversation_agent_instance.parse_query(
            query=req.query,
            session_id=req.session_id or "default_session",
            language_override=req.language_override
        )
        ctx = parse_result["active_context"]

        # Merge Interpreter structured findings if present
        if interpretation:
            if interpretation.get("mapped_intent"):
                parse_result["intent"] = interpretation["mapped_intent"]
            if interpretation.get("location_name") and interpretation["location_name"] != "Malpe":
                ctx["location_name"] = interpretation["location_name"]
                ctx["lat"] = interpretation["lat"]
                ctx["lon"] = interpretation["lon"]
            if interpretation.get("vessel_type"):
                ctx["vessel_type"] = interpretation["vessel_type"]
            if interpretation.get("departure_time") and interpretation["departure_time"] != "Tomorrow 05:00 AM":
                ctx["departure_time"] = interpretation["departure_time"]

        # Step 3-10: Execute pipeline if requested
        pipeline_output = None
        if req.execute_pipeline:
            pipeline_output = orca_pipeline_instance.run(
                lat=ctx["lat"],
                lon=ctx["lon"],
                vessel_type=ctx["vessel_type"],
                language=parse_result["target_language"],
                user_intent=parse_result["intent"],
                departure_time=ctx["departure_time"],
                max_range_km=ctx["range_km"]
            )

        return {
            "session_id": parse_result["session_id"],
            "query": parse_result["query"],
            "english_query": interpretation.get("english_query") if interpretation else parse_result["query"],
            "detected_language": parse_result["detected_language"],
            "target_language": parse_result["target_language"],
            "intent": parse_result["intent"],
            "intent_schema": interpretation.get("intent_schema") if interpretation else None,
            "understanding_chips": parse_result["understanding_chips"],
            "active_context": ctx,
            "pipeline_result": pipeline_output
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/orca/query", tags=["ORCA 10-Step Pipeline"])
async def run_orca_pipeline(
    lat: float = Query(default=13.35, description="Latitude (Default: Malpe Harbor)", example=13.35),
    lon: float = Query(default=74.70, description="Longitude", example=74.70),
    vessel: str = Query(default="motorized_craft", description="Vessel: 'artisanal_canoe', 'motorized_craft', 'mechanized_trawler'"),
    language: str = Query(default="both", description="Language: 'en', 'kn', 'hi', 'ta', 'te', 'ml', 'both'"),
    intent: str = Query(default="safe_fishing_advisory", description="Query Intent"),
    departure_time: str = Query(default="Tomorrow 05:00 AM", description="Planned departure window"),
    max_range_km: float = Query(default=50.0, description="Operating radius limit in km")
):
    """
    Executes the Complete 10-Step ORCA Marine Intelligence Decision Loop (Page 3 & 4 of PDF):
    1. User Query & Context
    2. Intent & Vessel Parsing
    3. Minimal Task Graph Planning
    4. Authoritative Data Retrieval (INCOIS, MOSDAC EOS-06, IMD, ERDDAP)
    5. Common Schema Normalization
    6. Multidisciplinary Fusion (Hydrodynamic & Swell anomaly detection)
    7. Hard Safety & Geofence Gate (Deterministic exclusion of MPAs and unsafe sea-states)
    8. Multi-Objective PFZ Ranking (Chlorophyll, SST, distance penalty, fuel)
    9. Evidence & Source Freshness Audit
    10. Actionable Response & Cartographic GeoJSON Visualization
    """
    if not MODULES_OK or orca_pipeline_instance is None:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return orca_pipeline_instance.run(
            lat=lat,
            lon=lon,
            vessel_type=vessel,
            language=language,
            user_intent=intent,
            departure_time=departure_time,
            max_range_km=max_range_km
        )
    except Exception as e:
        raise HTTPException(500, detail=str(e))



@app.get("/api/gateway/normalized", tags=["Marine Data Gateway"])
async def get_normalized_gateway_record(
    lat: float = Query(default=13.35, example=13.35),
    lon: float = Query(default=74.70, example=74.70)
):
    """Returns authoritative normalized records according to the canonical schema (Page 5)."""
    if not MODULES_OK or orca_pipeline_instance is None:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return orca_pipeline_instance.gateway.fetch_normalized_marine_record(lat, lon)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/pfz/candidates", tags=["Marine Data Gateway"])
async def get_pfz_candidates(
    lat: float = Query(default=13.35, example=13.35),
    lon: float = Query(default=74.70, example=74.70)
):
    """Returns active INCOIS / MOSDAC Potential Fishing Zones with Chlorophyll & SST."""
    if not MODULES_OK or orca_pipeline_instance is None:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return {"candidate_pfzs": orca_pipeline_instance.gateway.get_candidate_pfz_zones(lat, lon)}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/geofence/restricted-zones", tags=["Marine Data Gateway"])
async def get_restricted_geofences():
    """Returns authoritative marine limits, restricted defense zones, and marine national parks."""
    if not MODULES_OK or orca_pipeline_instance is None:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return {"restricted_marine_zones": orca_pipeline_instance.gateway.get_restricted_marine_geofences()}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/orchestrate", tags=["Multi-Agent Orchestrator"])
async def run_orchestrator(
    lat: float = Query(default=15.0, description="Latitude", example=15.0),
    lon: float = Query(default=72.0, description="Longitude", example=72.0),
    language: str = Query(default="both", description="Advisory language: 'english', 'hindi', or 'both'")
):
    """
    Executes the Complete ORCA Multi-Agent Architecture (Stages 2 -> 3 -> 4):
    - Stage 2: Main Orchestrator + Task Planner
    - Stage 3: 6 Specialized Domain Agents (Marine, Weather, GIS, Analytics, Risk, Spatial)
    - Stage 3: Reasoning & Validation Agent (Self-correction feedback loop)
    - Stage 3: Visualizer Agent (GeoJSON, Route Corridors, Radar Charts)
    - Stage 4: Executive Decision & Gemini Advisory Delivery
    """
    if not MODULES_OK or orchestrator_instance is None:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return orchestrator_instance.process_query(lat, lon, language)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/ocean-currents", tags=["Ocean Data"])
async def get_ocean_currents():
    """
    Return latest MOSDAC Global Ocean Surface Current data.
    Parses the most recent .nc file from your downloaded MOSDAC dataset.
    """
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        data = nc_parser.get_latest_ocean_current()
        return data
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/ocean-currents/point", tags=["Ocean Data"])
async def get_ocean_current_at_point(
    lat: float = Query(..., description="Latitude", example=15.0),
    lon: float = Query(..., description="Longitude", example=72.0),
):
    """Get ocean current speed and direction at a specific lat/lon."""
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return nc_parser.get_point_ocean_current(lat, lon)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/ocean-currents/all", tags=["Ocean Data"])
async def get_all_ocean_current_summaries():
    """Return summary statistics from all downloaded MOSDAC ocean current files."""
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return {"summaries": nc_parser.get_all_ocean_current_summaries()}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── Coastal SAR Data ─────────────────────────────────────────────────────────

@app.get("/api/coastal-summary", tags=["Ocean Data"])
async def get_coastal_summary():
    """
    Summarise MOSDAC Indian Mainland Coastal SAR product data.
    Returns wave heights, track info from all downloaded .nc files.
    """
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return sar_parser.get_coastal_summary()
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/coastal-latest", tags=["Ocean Data"])
async def get_latest_coastal_pass():
    """Parse and return the most recent SAR coastal pass file."""
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return sar_parser.get_latest_coastal_pass()
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── Weather & Marine ─────────────────────────────────────────────────────────

@app.get("/api/weather/{lat}/{lon}", tags=["Weather"])
async def get_weather(lat: float, lon: float):
    """
    Fetch combined weather + marine forecast for a location.
    Uses Open-Meteo (FREE — no API key needed).
    """
    try:
        return weather_processor.get_combined_forecast(lat, lon)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/weather/marine/{lat}/{lon}", tags=["Weather"])
async def get_marine_only(lat: float, lon: float):
    """Marine-only forecast: wave height, swell, ocean currents from Open-Meteo."""
    try:
        return weather_processor.get_marine_forecast(lat, lon)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── Risk Engine ──────────────────────────────────────────────────────────────

@app.get("/api/risk/point", tags=["Risk Engine"])
async def get_risk_at_point(
    lat: float = Query(..., description="Latitude", example=15.0),
    lon: float = Query(..., description="Longitude", example=72.0),
    region: str = Query(default="open_sea", description="Coastal region for LULC lookup"),
):
    """
    Compute multi-factor risk score (0–100) for a specific fishing location.
    
    Risk = 30% Wave Height + 25% Wind Speed + 20% Ocean Current 
           + 15% Cyclone Proximity + 10% LULC Vulnerability
    """
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        # Get active cyclones for proximity factor
        cyclones = cyclone_tracker.get_active_cyclones()
        result = risk_engine.compute_risk_score(lat, lon, cyclones, region)
        return result
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/risk-zones", tags=["Risk Engine"])
async def get_risk_zones():
    """
    Compute risk scores for all predefined Indian Ocean fishing zones.
    Returns GeoJSON FeatureCollection for map rendering.
    
    Covers: Arabian Sea, Bay of Bengal, Lakshadweep, Andaman, all coastal zones.
    """
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        cyclones = cyclone_tracker.get_active_cyclones()
        result = risk_engine.build_risk_map(cyclones)
        return result
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── Cyclone Tracker ──────────────────────────────────────────────────────────

@app.get("/api/cyclone-track", tags=["Cyclone"])
async def get_cyclone_track():
    """
    Fetch active cyclone data from IMD RSMC and return GeoJSON with danger zones.
    Includes eye position, eye-wall radius, and gale force wind radius.
    """
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return cyclone_tracker.build_cyclone_geojson()
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/cyclone/impact", tags=["Cyclone"])
async def get_cyclone_impact(
    lat: float = Query(..., example=15.0),
    lon: float = Query(..., example=82.0),
):
    """Check cyclone threat level for a specific fishing location."""
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        cyclones = cyclone_tracker.get_active_cyclones()
        return cyclone_tracker.get_cyclone_impact_on_zone(lat, lon, cyclones)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── IMD Data ─────────────────────────────────────────────────────────────────

@app.get("/api/imd/cyclones", tags=["IMD"])
async def get_imd_cyclones():
    """Fetch active cyclone data from IMD RSMC portal."""
    try:
        return imd_processor.get_active_cyclones()
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/imd/warning", tags=["IMD"])
async def get_imd_warning(
    lat: float = Query(default=13.35, description="Latitude (default: Malpe)", example=15.0),
    lon: float = Query(default=74.70, description="Longitude (default: Malpe)", example=82.0),
):
    """Get IMD weather warning level for a location."""
    try:
        return imd_processor.get_imd_weather_warning(lat, lon)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/imd/fishing-zones", tags=["IMD"])
async def get_fishing_zone_advisories():
    """Get IMD advisories for all known Indian fishing zones."""
    try:
        return {"fishing_zones": imd_processor.get_fishing_zone_advisories()}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── Copernicus Marine ────────────────────────────────────────────────────────

@app.get("/api/copernicus/status", tags=["Copernicus CMEMS"])
async def get_copernicus_status():
    """Check Copernicus Marine credentials and available products."""
    try:
        return copernicus_processor.get_available_products()
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/copernicus/ocean-data", tags=["Copernicus CMEMS"])
async def get_copernicus_ocean_data(
    lat: float = Query(..., example=15.0),
    lon: float = Query(..., example=72.0),
):
    """Fetch live ocean data from Copernicus CMEMS for a location."""
    try:
        return copernicus_processor.get_live_ocean_data(lat, lon)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── AI Advisory ──────────────────────────────────────────────────────────────

@app.post("/api/advisory", tags=["AI Advisory"])
async def generate_advisory(request: AdvisoryRequest):
    """
    Generate a Gemini AI fishing safety advisory for a location.
    Optionally auto-send WhatsApp alert if risk is DANGER.
    """
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        # Get risk score first
        cyclones = cyclone_tracker.get_active_cyclones()
        risk_data = risk_engine.compute_risk_score(request.lat, request.lon, cyclones)

        # Generate Gemini advisory
        advisory = advisory_engine.generate_fishing_advisory(
            lat=request.lat,
            lon=request.lon,
            risk_score=risk_data["risk_score"],
            risk_data=risk_data,
            language=request.language,
        )
        advisory["risk_data"] = risk_data

        # Auto-alert if requested and danger level
        if request.auto_alert and risk_data["risk_score"] > 75:
            alert_result = alert_service.send_danger_alert(
                risk_score=risk_data["risk_score"],
                risk_level_str=risk_data["risk_level"],
                advisory_text=advisory["advisory_text"],
                lat=request.lat,
                lon=request.lon,
            )
            advisory["auto_alert_sent"] = alert_result

        return advisory
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/advisory/quick", tags=["AI Advisory"])
async def quick_advisory(
    lat: float = Query(..., example=15.0),
    lon: float = Query(..., example=72.0),
    language: str = Query(default="english"),
):
    """Quick GET version of the advisory endpoint for easy browser testing."""
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        cyclones = cyclone_tracker.get_active_cyclones()
        risk_data = risk_engine.compute_risk_score(lat, lon, cyclones)
        advisory = advisory_engine.generate_fishing_advisory(
            lat=lat, lon=lon,
            risk_score=risk_data["risk_score"],
            risk_data=risk_data,
            language=language,
        )
        advisory["risk_data"] = risk_data
        return advisory
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── Alert Service ────────────────────────────────────────────────────────────

@app.post("/api/send-alert", tags=["Alerts"])
async def send_alert(request: AlertRequest):
    """
    Send SMS or WhatsApp alert via Twilio.
    Use channel='whatsapp' for WhatsApp, 'sms' for SMS.
    """
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        location = {"lat": request.lat, "lon": request.lon} if request.lat and request.lon else None
        if request.channel == "whatsapp":
            result = alert_service.send_whatsapp_alert(
                to_number=request.to_number,
                message=request.message,
                risk_level=request.risk_level,
                location=location,
            )
        else:
            result = alert_service.send_sms_alert(
                to_number=request.to_number,
                message=request.message,
                risk_level=request.risk_level,
            )
        return result
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/api/send-bulk-alert", tags=["Alerts"])
async def send_bulk_alert(request: BulkAlertRequest):
    """Send alerts to multiple recipients at once."""
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        location = {"lat": request.lat, "lon": request.lon} if request.lat and request.lon else None
        result = alert_service.send_bulk_alert(
            phone_numbers=request.phone_numbers,
            message=request.message,
            risk_level=request.risk_level,
            channel=request.channel,
            location=location,
        )
        return result
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/message-status/{sid}", tags=["Alerts"])
async def get_message_status(sid: str):
    """Check the delivery status of a sent Twilio message by SID."""
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return alert_service.get_message_status(sid)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── Tide Prediction (INCOIS Harmonic Tidal System) ──────────────────────────

@app.get("/api/tide/predict", tags=["Tide & Ocean State"])
async def tide_prediction(
    station: str = Query(default="Malpe", description="Station name: Malpe, Mangalore, Karwar, Kochi, Chennai"),
    hours: int = Query(default=24, ge=1, le=120, description="Forecast horizon in hours")
):
    """INCOIS harmonic tidal prediction for Indian coastal stations."""
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return marine_products_mod.predict_tide(station, hours)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/tide/stations", tags=["Tide & Ocean State"])
async def list_tide_stations():
    """List all available INCOIS tidal prediction stations with geographic coordinates."""
    stations_data = {}
    for name, data in marine_products_mod.TIDE_STATIONS.items():
        stations_data[name] = {
            "name": name,
            "lat": data["lat"],
            "lon": data["lon"],
            "M2_amp": data["M2_amp"],
            "S2_amp": data["S2_amp"],
            "K1_amp": data["K1_amp"],
            "O1_amp": data["O1_amp"],
        }
    return {
        "stations": list(marine_products_mod.TIDE_STATIONS.keys()),
        "stations_detail": stations_data,
        "network": "INCOIS National Tidal Prediction System",
        "model": "Harmonic Analysis (M2, S2, K1, O1 constituents)"
    }


# ─── Small Vessel Advisory (SVA) ─────────────────────────────────────────────

@app.get("/api/vessel/sva", tags=["Vessel Safety Advisory"])
async def vessel_sva(
    vessel_type: str = Query(
        default="motorized_craft",
        description="Vessel class: artisanal_canoe | motorized_craft | mechanized_trawler"
    ),
    wave_m: float = Query(default=1.5, description="Current significant wave height in metres"),
    wind_kmh: float = Query(default=28.0, description="Current wind speed in km/h")
):
    """Small Vessel Advisory (SVA): go/no-go recommendation by vessel class with safety limits."""
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return marine_products_mod.get_vessel_sva(vessel_type, wave_m, wind_kmh)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/vessel/sva/all", tags=["Vessel Safety Advisory"])
async def vessel_sva_all(
    wave_m: float = Query(default=1.5, description="Current significant wave height in metres"),
    wind_kmh: float = Query(default=28.0, description="Current wind speed in km/h")
):
    """SVA status for all vessel classes simultaneously."""
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return {
            "conditions": {"wave_m": wave_m, "wind_kmh": wind_kmh},
            "advisories": [
                marine_products_mod.get_vessel_sva(v["vessel_class"], wave_m, wind_kmh)
                for v in marine_products_mod.VESSEL_SVA_MATRIX
            ],
            "authority": "IMD / INCOIS Small Vessel Advisory System",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── Satellite Products (SST + Ocean Colour / Chlorophyll-a) ─────────────────

@app.get("/api/satellite/composite", tags=["Satellite Products"])
async def satellite_composite(
    lat: float = Query(default=13.5, description="Latitude"),
    lon: float = Query(default=74.5, description="Longitude")
):
    """ISRO EOS-06 (Oceansat-3) satellite composite: SST, Chlorophyll-a, thermal fronts, SLA."""
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return marine_products_mod.get_satellite_composite(lat, lon)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── ERDDAP Machine-Readable Ocean Datasets ───────────────────────────────────

@app.get("/api/erddap/dataset", tags=["ERDDAP Datasets"])
async def erddap_dataset(
    lat: float = Query(default=13.5, description="Centre latitude for dataset bounding box"),
    lon: float = Query(default=74.5, description="Centre longitude for dataset bounding box")
):
    """Machine-readable ERDDAP-compatible ocean dataset schema (OPeNDAP/WMS/WFS)."""
    if not MODULES_OK:
        raise HTTPException(500, detail=f"Modules not loaded: {MODULES_ERROR}")
    try:
        return marine_products_mod.get_erddap_machine_readable(lat, lon)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── Maritime Limits & Restricted/Protected Areas ────────────────────────────

@app.get("/api/maritime/limits", tags=["Maritime Boundaries"])
async def maritime_limits():
    """Maritime boundary zones: Territorial Sea, Contiguous Zone, EEZ, MPAs for Indian coast."""
    return {
        "maritime_zones": [
            {
                "zone": "Territorial Sea",
                "limit_nm": 12,
                "legal_basis": "UNCLOS Article 3 | Indian Territorial Waters Act 1976",
                "access": "Indian-flagged vessels free; foreign vessels require innocent passage",
                "color_hex": "#1e40af"
            },
            {
                "zone": "Contiguous Zone",
                "limit_nm": 24,
                "legal_basis": "UNCLOS Article 33",
                "access": "India exercises customs, fiscal, immigration control",
                "color_hex": "#2563eb"
            },
            {
                "zone": "Exclusive Economic Zone (EEZ)",
                "limit_nm": 200,
                "legal_basis": "UNCLOS Article 55-75 | India EEZ Act 1976",
                "access": "India has sovereign rights over fisheries and marine resources",
                "color_hex": "#3b82f6"
            }
        ],
        "restricted_areas": [
            {
                "name": "Gulf of Mannar Marine National Park (MPA)",
                "type": "Marine Protected Area",
                "coordinates": {"lat_center": 9.0, "lon_center": 79.1, "radius_km": 25},
                "restriction": "NO FISHING — Protected biodiversity zone under Wildlife Protection Act 1972",
                "color_hex": "#dc2626"
            },
            {
                "name": "Lakshadweep MPA Corridor",
                "type": "Marine Protected Area",
                "coordinates": {"lat_center": 10.5, "lon_center": 72.6, "radius_km": 40},
                "restriction": "NO TRAWLING — Reef ecosystem conservation zone",
                "color_hex": "#dc2626"
            },
            {
                "name": "Andaman & Nicobar Tribal Reserve Buffer",
                "type": "Restricted Zone",
                "coordinates": {"lat_center": 12.5, "lon_center": 92.9, "radius_km": 60},
                "restriction": "APPROACH PROHIBITED — Tribal protection and biosecurity zone",
                "color_hex": "#7c3aed"
            },
            {
                "name": "Indian Navy Exercise Zone (Arabian Sea)",
                "type": "Temporary Restricted Area",
                "coordinates": {"lat_center": 16.0, "lon_center": 71.0, "radius_km": 30},
                "restriction": "NOTAM ACTIVE — Vessels to maintain 30 NM clearance during exercises",
                "color_hex": "#b45309"
            }
        ],
        "data_authority": "MoES / National Institute of Ocean Technology (NIOT) / Survey of India",
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "geojson_wms_endpoint": "https://www.incois.gov.in/portal/maps/maritime-limits.wms"
    }


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("Starting ORCA Backend Server...")
    print("API Docs: http://localhost:8000/docs")
    print("System Status: http://localhost:8000/api/status")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
