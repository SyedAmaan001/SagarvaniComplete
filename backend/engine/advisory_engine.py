"""
Gemini AI Advisory Engine
Generates fisherman-friendly safety advisories using Google Gemini.
Uses 3-key rotation to avoid per-key rate limits.
"""

import os
from typing import Any, Dict, Optional
from datetime import datetime, timezone

try:
    from google import genai as _genai_module
    GENAI_OK = True
except ImportError:
    GENAI_OK = False

from utils.key_rotation import get_next_gemini_key
from utils.geo_utils import risk_level


# Gemini model to use
GEMINI_MODEL = "gemini-1.5-flash"  # fast + cheap for advisory generation
GEMINI_PRO_MODEL = "gemini-1.5-pro"  # use for detailed reports


import concurrent.futures


def _get_gemini_client() -> Any:
    """Return a configured google.genai Client using the next key in rotation.
    Returns None if GENAI_OK is False (import failed).
    """
    if not GENAI_OK:
        return None
    key = get_next_gemini_key()
    return _genai_module.Client(api_key=key)


def _call_gemini_with_timeout(client, model: str, prompt: str, timeout_s: float = 5.0) -> str:
    """Call Gemini generate_content with a hard timeout.
    Returns the response text, or raises TimeoutError / Exception on failure.
    The hard timeout ensures a dead/slow Gemini endpoint never blocks a request.
    """
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        lambda: client.models.generate_content(model=model, contents=prompt).text
    )
    try:
        return future.result(timeout=timeout_s)
    finally:
        try:
            executor.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            executor.shutdown(wait=False)



def generate_fishing_advisory(
    lat: float,
    lon: float,
    risk_score: float,
    risk_data: Dict[str, Any],
    language: str = "english",
) -> Dict[str, Any]:
    """
    Generate a fisherman-friendly safety advisory using Gemini.

    Args:
        lat: Location latitude
        lon: Location longitude
        risk_score: 0–100 risk score from risk engine
        risk_data: Full breakdown from risk_engine.compute_risk_score()
        language: 'english', 'hindi', or 'both'

    Returns:
        Dict with advisory text, recommendations, and metadata
    """
    level_info = risk_level(risk_score)

    # Extract key data for the prompt
    wave_h = risk_data.get("breakdown", {}).get("wave_height", {})
    wind = risk_data.get("breakdown", {}).get("wind_speed", {})
    current = risk_data.get("breakdown", {}).get("ocean_current", {})
    cyclone = risk_data.get("breakdown", {}).get("cyclone_proximity", {})

    prompt = f"""
You are ORCA — a maritime safety AI assistant for Indian fishermen.
Generate a clear, practical safety advisory based on the following ocean conditions.

## Location
- Latitude: {lat}°N, Longitude: {lon}°E
- Date/Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

## Current Sea Conditions
- Risk Score: {risk_score}/100 → {level_info['level']} {level_info['emoji']}
- Wave Height: {wave_h.get('value_m', 'N/A')} meters (Sea state: {wave_h.get('sea_state', 'Unknown')})
- Wind Speed: {wind.get('value_kmh', 'N/A')} km/h ({wind.get('value_ms', 'N/A')} m/s)
- Ocean Current: {current.get('value_ms', 'N/A')} m/s
- Cyclone Threat: {cyclone.get('nearest_cyclone', 'None') or 'No active cyclone nearby'}
  {f"- Nearest cyclone distance: {cyclone.get('nearest_cyclone', {}).get('distance_km', 'N/A') if isinstance(cyclone.get('nearest_cyclone'), dict) else 'N/A'} km" if cyclone.get('nearest_cyclone') else ''}

## Advisory Requirements
Write a safety advisory for Indian fishermen that:
1. Starts with the risk level clearly (SAFE / CAUTION / WARNING / DANGER)
2. Explains the current sea conditions in simple language (2–3 sentences)
3. Gives specific actionable recommendations (bullet points)
4. Mentions if they should stay ashore or can fish safely
5. Includes one traditional/local weather wisdom if applicable
6. Ends with the next check-in time recommendation

{"Write in ENGLISH only." if language == 'english' else
 "Write in HINDI only (Devanagari script)." if language == 'hindi' else
 "Write in BOTH English AND Hindi (Devanagari script). Clearly label each section."}

Keep it under 200 words total. Use simple language that fishermen can understand.
"""

    if not GENAI_OK:
        return {
            "lat": lat, "lon": lon,
            "risk_score": risk_score,
            "risk_level": level_info["level"],
            "risk_emoji": level_info["emoji"],
            "advisory_text": _fallback_advisory(risk_score, level_info, wave_h, wind),
            "language": "english",
            "model_used": "rule-based-fallback",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "error": "google.genai not installed",
        }

    try:
        client = _get_gemini_client()
        advisory_text = _call_gemini_with_timeout(client, GEMINI_MODEL, prompt, timeout_s=5.0)

        return {
            "lat": lat,
            "lon": lon,
            "risk_score": risk_score,
            "risk_level": level_info["level"],
            "risk_emoji": level_info["emoji"],
            "advisory_text": advisory_text,
            "language": language,
            "model_used": GEMINI_MODEL,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }
    except Exception as e:
        # Try fallback with next key
        try:
            client2 = _get_gemini_client()
            advisory_text2 = _call_gemini_with_timeout(client2, GEMINI_MODEL, prompt, timeout_s=5.0)
            return {
                "lat": lat,
                "lon": lon,
                "risk_score": risk_score,
                "risk_level": level_info["level"],
                "risk_emoji": level_info["emoji"],
                "advisory_text": advisory_text2,
                "language": language,
                "model_used": f"{GEMINI_MODEL} (key2)",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "error": None,
            }
        except Exception as e2:
            # Final fallback: rule-based advisory
            return {
                "lat": lat,
                "lon": lon,
                "risk_score": risk_score,
                "risk_level": level_info["level"],
                "risk_emoji": level_info["emoji"],
                "advisory_text": _fallback_advisory(risk_score, level_info, wave_h, wind),
                "language": "english",
                "model_used": "rule-based-fallback",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "error": f"Gemini unavailable: {str(e2)}",
            }


def generate_weather_report(
    forecast_data: Dict[str, Any],
    zone_name: str = "Indian Waters",
) -> Dict[str, Any]:
    """
    Generate a detailed weather report for a fishing zone using Gemini Pro.
    """
    weather = forecast_data.get("weather", {})
    marine = forecast_data.get("marine", {})

    prompt = f"""
You are ORCA, a maritime weather analyst.
Generate a professional 5-day weather outlook report for Indian fishermen in {zone_name}.

## Current Conditions
- Temperature: {weather.get('temperature_c', 'N/A')}°C
- Wind: {weather.get('wind_speed_kmh', 'N/A')} km/h from {weather.get('wind_direction_deg', 'N/A')}°
- Gusts: {weather.get('wind_gusts_kmh', 'N/A')} km/h
- Precipitation: {weather.get('precipitation_mm', 'N/A')} mm
- Weather: {weather.get('weather_description', 'N/A')}
- Wave Height: {marine.get('wave_height_m', 'N/A')} m
- Sea State: {marine.get('sea_state', 'N/A')}
- Swell: {marine.get('swell_wave_height_m', 'N/A')} m

## Report Requirements
Write a weather outlook that includes:
1. Current conditions summary (2 sentences)
2. Fishing safety assessment for today
3. Tomorrow's outlook
4. Any warnings or advisories
5. Recommended fishing windows (if safe)

Format as a professional marine weather bulletin. Keep under 300 words.
"""

    if not GENAI_OK:
        return {
            "zone": zone_name,
            "report_text": "Weather report generation unavailable (google.genai not installed).",
            "model_used": "error",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "error": "google.genai not installed",
        }

    try:
        client = _get_gemini_client()
        report_text = _call_gemini_with_timeout(client, GEMINI_PRO_MODEL, prompt, timeout_s=5.0)
        return {
            "zone": zone_name,
            "report_text": report_text,
            "model_used": GEMINI_PRO_MODEL,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }
    except Exception as e:
        return {
            "zone": zone_name,
            "report_text": f"Weather report generation failed: {str(e)}",
            "model_used": "error",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }


def _fallback_advisory(
    risk_score: float,
    level_info: Dict,
    wave_h: Dict,
    wind: Dict,
) -> str:
    """Rule-based advisory fallback when Gemini is unavailable."""
    level = level_info["level"]
    emoji = level_info["emoji"]

    if level == "SAFE":
        return (
            f"{emoji} SAFE FISHING CONDITIONS\n\n"
            f"Sea conditions are favorable. Wave height: {wave_h.get('value_m', 'N/A')}m, "
            f"Wind: {wind.get('value_kmh', 'N/A')} km/h.\n\n"
            "✅ Safe to venture into sea. Carry life jackets and communication device.\n"
            "✅ Stay within 12 nautical miles of shore.\n"
            "⏰ Check conditions again in 6 hours."
        )
    elif level == "CAUTION":
        return (
            f"{emoji} CAUTION — MODERATE CONDITIONS\n\n"
            f"Moderate sea conditions. Wave height: {wave_h.get('value_m', 'N/A')}m, "
            f"Wind: {wind.get('value_kmh', 'N/A')} km/h.\n\n"
            "⚠️ Experienced fishermen only. Stay within 6 nautical miles.\n"
            "⚠️ Avoid night fishing. Return before sunset.\n"
            "⏰ Check conditions again in 3 hours."
        )
    elif level == "WARNING":
        return (
            f"{emoji} WARNING — ROUGH CONDITIONS\n\n"
            f"Rough sea conditions. Wave height: {wave_h.get('value_m', 'N/A')}m, "
            f"Wind: {wind.get('value_kmh', 'N/A')} km/h.\n\n"
            "🚫 Avoid deep-sea fishing.\n"
            "🚫 Small boats should stay ashore.\n"
            "⏰ Check conditions again in 2 hours."
        )
    else:  # DANGER
        return (
            f"{emoji} DANGER — EXTREME CONDITIONS — STAY ASHORE\n\n"
            f"Extremely dangerous sea conditions. Wave height: {wave_h.get('value_m', 'N/A')}m, "
            f"Wind: {wind.get('value_kmh', 'N/A')} km/h.\n\n"
            "🚨 DO NOT VENTURE INTO SEA.\n"
            "🚨 All fishing boats must return to port immediately.\n"
            "🚨 Contact coast guard if you are at sea: 1554\n"
            "⏰ Monitor updates every hour."
        )
