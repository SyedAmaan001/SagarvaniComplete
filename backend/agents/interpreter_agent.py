"""
ORCA Step 2: Access & Understanding Layer (Interpreter Module)
Integrated from friend's completed implementation in /Interpreter/app.py

Pipeline:
    User Query - TEXT (any Indian language)
        -> Sarvam AI Text Translation (-> English)
        -> Structured Extraction (-> MarineIntentSchema)

    User Query - VOICE (any Indian regional language, via microphone)
        -> Sarvam AI Speech-to-Text-Translate (-> English transcript)
        -> Structured Extraction (-> MarineIntentSchema)

Both paths converge on MarineIntentSchema, which is handed off to Step 3 (Plan) -> Steps 4-10.
"""

import io
import os
import re
import wave
from typing import Optional, Dict, Any, Tuple
import requests
from pydantic import BaseModel, Field

# --------------------------------------------------------------------------
# 1. CONFIGURATION & MODEL REGISTRY
# --------------------------------------------------------------------------

SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_TRANSLATE_MODEL = "mayura:v1"
SARVAM_STT_MODEL = "saaras:v3"

SARVAM_API_KEY_RAW = os.environ.get("SARVAM_API_KEY", "")
GOOGLE_API_KEY_RAW = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY_1", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")


class KeyRotator:
    """
    Tracks a pool of API keys (parsed from a comma-separated string)
    and rotates to the next one when the active key hits rate-limits or quota errors.
    """
    def __init__(self, keys_csv: str):
        self.keys = [k.strip() for k in keys_csv.split(",") if k.strip()]
        self.index = 0

    @property
    def current_key(self) -> str:
        if not self.keys:
            return ""
        return self.keys[self.index]

    def rotate(self) -> bool:
        """Advance to the next key. Returns False once every key is exhausted."""
        if not self.keys or self.index + 1 >= len(self.keys):
            return False
        self.index += 1
        return True


sarvam_key_rotator = KeyRotator(SARVAM_API_KEY_RAW)
google_key_rotator = KeyRotator(GOOGLE_API_KEY_RAW)


# --------------------------------------------------------------------------
# 2. PYDANTIC SCHEMA - the contract handed off to Step 3 (Plan)
# --------------------------------------------------------------------------

class MarineIntentSchema(BaseModel):
    """Structured representation of a fisherman/user's marine query intent."""
    intent_type: str = Field(
        default="general_query",
        description=(
            "The core intent of the query. Must be one of: "
            "find_pfz, weather_alert, safe_route, geofence_check, general_query."
        )
    )
    location: Optional[str] = Field(
        default=None,
        description="Named location, coordinates, or region mentioned in the query, if any."
    )
    date: Optional[str] = Field(
        default=None,
        description="Date or time reference mentioned in the query (e.g., 'today', 'tomorrow', '15 Aug'), if any."
    )
    vessel_type: Optional[str] = Field(
        default=None,
        description="Type of vessel mentioned, e.g., trawler, gillnetter, canoe, motorized, if any."
    )


# --------------------------------------------------------------------------
# 3. SARVAM AI - TEXT TRANSLATION (for regional language text queries)
# --------------------------------------------------------------------------

def translate_to_english(text: str) -> Tuple[str, dict]:
    """
    Translate a user query from any supported Indian language into
    English using the Sarvam AI Translate API (model: mayura:v1).
    Supports automatic fallback rotation across available Sarvam API keys.
    """
    char_count = len(text)
    if not sarvam_key_rotator.current_key:
        return text, {"model": SARVAM_TRANSLATE_MODEL, "chars": char_count, "status": "skipped_no_key"}

    for _ in range(max(1, len(sarvam_key_rotator.keys))):
        headers = {
            "api-subscription-key": sarvam_key_rotator.current_key,
            "Content-Type": "application/json",
        }
        payload = {
            "input": text,
            "source_language_code": "auto",
            "target_language_code": "en-IN",
            "mode": "formal",
            "model": SARVAM_TRANSLATE_MODEL,
        }
        try:
            response = requests.post(SARVAM_TRANSLATE_URL, headers=headers, json=payload, timeout=12)
            if response.status_code in (429, 403, 500, 502, 503) and sarvam_key_rotator.rotate():
                continue

            response.raise_for_status()
            data = response.json()
            translated = data.get("translated_text", text)
            return translated, {"model": SARVAM_TRANSLATE_MODEL, "chars": char_count, "status": "success"}
        except Exception as e:
            if sarvam_key_rotator.rotate():
                continue
            return text, {"model": SARVAM_TRANSLATE_MODEL, "chars": char_count, "status": f"failed: {e}"}

    return text, {"model": SARVAM_TRANSLATE_MODEL, "chars": char_count, "status": "exhausted_keys"}


# --------------------------------------------------------------------------
# 4. SARVAM AI - SPEECH-TO-TEXT-TRANSLATE (for microphone voice input)
# --------------------------------------------------------------------------

def transcribe_and_translate_audio(audio_bytes: bytes, filename: str = "recording.wav") -> Tuple[Optional[str], dict]:
    """
    Send recorded audio in any Indian regional language to Sarvam AI's
    speech-to-text-translate endpoint (model: saaras:v3).
    Returns tuple: (english_transcript, stats_dict).
    """
    byte_len = len(audio_bytes)
    duration_sec = round(byte_len / 32000.0, 1)

    if not sarvam_key_rotator.current_key:
        return None, {"model": SARVAM_STT_MODEL, "duration_sec": duration_sec, "bytes": byte_len, "status": "skipped_no_key"}

    for _ in range(max(1, len(sarvam_key_rotator.keys))):
        headers = {
            "api-subscription-key": sarvam_key_rotator.current_key,
        }
        files = {
            "file": (filename, audio_bytes, "audio/wav"),
        }
        data = {
            "model": SARVAM_STT_MODEL,
        }
        try:
            response = requests.post(
                SARVAM_STT_TRANSLATE_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=25,
            )
            if response.status_code in (429, 403, 500, 502, 503) and sarvam_key_rotator.rotate():
                continue

            response.raise_for_status()
            result = response.json()
            transcript = result.get("transcript", "")
            return transcript, {"model": SARVAM_STT_MODEL, "duration_sec": duration_sec, "bytes": byte_len, "status": "success"}
        except Exception as e:
            if sarvam_key_rotator.rotate():
                continue
            return None, {"model": SARVAM_STT_MODEL, "duration_sec": duration_sec, "bytes": byte_len, "status": f"failed: {e}"}

    return None, {"model": SARVAM_STT_MODEL, "duration_sec": duration_sec, "bytes": byte_len, "status": "exhausted_keys"}


# --------------------------------------------------------------------------
# 5. INTENT EXTRACTION ENGINE (LangChain / Gemini + Deterministic fallback)
# --------------------------------------------------------------------------

def _rule_based_extract(english_text: str) -> MarineIntentSchema:
    """Fast, reliable deterministic fallback parser for standard marine queries."""
    q = english_text.lower()
    
    # 1. Intent Type
    if any(w in q for w in ["route", "safest route", "path", "course", "navigate", "direction"]):
        intent = "safe_route"
    elif any(w in q for w in ["pfz", "fishing zone", "productive", "potential fishing", "catch", "fish"]):
        if any(w in q for w in ["restricted", "sanctuary", "geofence", "safe area"]):
            intent = "geofence_check"
        else:
            intent = "find_pfz"
    elif any(w in q for w in ["weather", "wave", "wind", "cyclone", "storm", "lightning", "sea condition", "sea state"]):
        intent = "weather_alert"
    elif any(w in q for w in ["geofence", "restricted", "boundary", "prohibited", "mpa", "naval"]):
        intent = "geofence_check"
    else:
        intent = "general_query"

    # 2. Location
    location = None
    known_ports = ["malpe", "mangalore", "mangaluru", "karwar", "bhatkal", "honnavar", "goa", "kochi", "cochin", "mumbai", "chennai", "visakhapatnam", "vizag"]
    for p in known_ports:
        if p in q:
            location = p.capitalize()
            break

    # 3. Date / Time
    date_val = None
    if "tomorrow" in q:
        if "morning" in q or "5 am" in q or "05:00" in q:
            date_val = "Tomorrow 05:00 AM"
        elif "9 am" in q or "09:00" in q:
            date_val = "Tomorrow 09:00 AM"
        elif "afternoon" in q or "2 pm" in q:
            date_val = "Tomorrow 02:00 PM"
        else:
            date_val = "Tomorrow"
    elif "today" in q or "now" in q:
        date_val = "Today Immediate Departure"

    # 4. Vessel Type
    vessel_val = None
    if any(w in q for w in ["canoe", "traditional", "kattumaram", "5 m", "5m", "small boat"]):
        vessel_val = "artisanal_canoe"
    elif any(w in q for w in ["motorized", "obm", "ibm", "fiberglass", "8 m", "10 m", "8m", "10m"]):
        vessel_val = "motorized_craft"
    elif any(w in q for w in ["trawler", "mechanized", "multiday", "12 m", "15 m", "12m", "15m"]):
        vessel_val = "mechanized_trawler"

    return MarineIntentSchema(
        intent_type=intent,
        location=location,
        date=date_val,
        vessel_type=vessel_val
    )


def extract_intent(english_text: str) -> Tuple[MarineIntentSchema, dict]:
    """
    Extract structured MarineIntentSchema from English text.
    Attempts LangChain / Gemini extraction when available, with deterministic fallback.
    """
    # First get deterministic baseline
    baseline = _rule_based_extract(english_text)

    # If LangChain Google GenAI is available, attempt structured extraction
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = google_key_rotator.current_key or os.environ.get("GEMINI_API_KEY_1", "")
        if api_key:
            llm = ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                temperature=0,
                google_api_key=api_key,
                request_timeout=6.0
            )
            structured_llm = llm.with_structured_output(MarineIntentSchema)
            system_instruction = (
                "You are the Access & Understanding module of ORCA, a marine "
                "assistant for Indian fishermen. Extract the structured intent "
                "from the user's query. intent_type must be one of: "
                "find_pfz, weather_alert, safe_route, geofence_check, general_query."
            )
            parsed: MarineIntentSchema = structured_llm.invoke(
                [
                    ("system", system_instruction),
                    ("human", english_text)
                ]
            )
            if parsed:
                # Merge with baseline if any field was missing
                return MarineIntentSchema(
                    intent_type=parsed.intent_type or baseline.intent_type,
                    location=parsed.location or baseline.location,
                    date=parsed.date or baseline.date,
                    vessel_type=parsed.vessel_type or baseline.vessel_type
                ), {"status": "llm_success", "model": GEMINI_MODEL}
    except Exception:
        pass

    return baseline, {"status": "rule_baseline", "model": "rule_engine"}


# --------------------------------------------------------------------------
# 6. UNIFIED INTERPRETER HANDOFF (Step 2 -> Step 3 Plan)
# --------------------------------------------------------------------------

class InterpreterModule:
    """
    Unified Step 2 Interpreter engine:
    Receives raw text (English or Indian regional language) or microphone audio,
    translates if necessary, produces MarineIntentSchema, and outputs standardized context.
    """
    def interpret(self, query: str, language: Optional[str] = None) -> Dict[str, Any]:
        # 1. Translate to English if regional language query
        english_text, translate_stats = translate_to_english(query)
        
        # 2. Extract structured MarineIntentSchema
        intent_schema, extract_stats = extract_intent(english_text)
        
        # 3. Map intent_type to ORCA pipeline standard intent
        intent_map = {
            "find_pfz": "nearest_pfz",
            "weather_alert": "sea_conditions",
            "safe_route": "safest_route",
            "geofence_check": "productive_safe_zones",
            "general_query": "safe_fishing_advisory"
        }
        mapped_intent = intent_map.get(intent_schema.intent_type, "safe_fishing_advisory")

        # 4. Map vessel type to ORCA standard
        vessel_map = {
            "canoe": "artisanal_canoe",
            "artisanal_canoe": "artisanal_canoe",
            "traditional": "artisanal_canoe",
            "motorized": "motorized_craft",
            "motorized_craft": "motorized_craft",
            "trawler": "mechanized_trawler",
            "mechanized_trawler": "mechanized_trawler"
        }
        mapped_vessel = vessel_map.get((intent_schema.vessel_type or "").lower(), "motorized_craft")

        # 5. Extract location coordinates
        port_coords = {
            "malpe": (13.35, 74.70),
            "mangalore": (12.87, 74.84),
            "karwar": (14.80, 74.13),
            "kochi": (9.97, 76.28),
            "chennai": (13.08, 80.27)
        }
        loc_name = intent_schema.location or "Malpe"
        lat, lon = port_coords.get(loc_name.lower(), (13.35, 74.70))

        return {
            "original_query": query,
            "english_query": english_text,
            "intent_schema": intent_schema.model_dump(),
            "mapped_intent": mapped_intent,
            "location_name": loc_name.capitalize(),
            "lat": lat,
            "lon": lon,
            "vessel_type": mapped_vessel,
            "departure_time": intent_schema.date or "Tomorrow 05:00 AM",
            "translate_stats": translate_stats,
            "extract_stats": extract_stats
        }

    def process_voice_audio(self, audio_bytes: bytes, filename: str = "voice.wav") -> Dict[str, Any]:
        """Transcribe and interpret raw microphone audio from user."""
        transcript, stt_stats = transcribe_and_translate_audio(audio_bytes, filename)
        if not transcript:
            transcript = "Can I safely go fishing tomorrow morning from Malpe?"
        interpretation = self.interpret(transcript)
        interpretation["stt_stats"] = stt_stats
        return interpretation
