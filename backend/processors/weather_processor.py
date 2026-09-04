"""
Open-Meteo Weather & Marine Processor
FREE — no API key required.
Fetches real-time weather + marine forecasts for any lat/lon.
"""

import requests
from typing import Any, Dict, Optional
from datetime import datetime, timezone


WEATHER_BASE = "https://api.open-meteo.com/v1/forecast"
MARINE_BASE = "https://marine-api.open-meteo.com/v1/marine"


def get_weather_forecast(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch real-time weather forecast from Open-Meteo.
    Returns current + 7-day forecast for the given location.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "precipitation",
            "weather_code",
            "cloud_cover",
            "visibility",
        ],
        "hourly": [
            "temperature_2m",
            "precipitation_probability",
            "wind_speed_10m",
            "wind_gusts_10m",
        ],
        "forecast_days": 3,
        "timezone": "Asia/Kolkata",
    }

    try:
        resp = requests.get(WEATHER_BASE, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})

        return {
            "lat": lat,
            "lon": lon,
            "source": "Open-Meteo Weather API",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "current": {
                "temperature_c": current.get("temperature_2m"),
                "wind_speed_kmh": _ms_to_kmh(current.get("wind_speed_10m")),
                "wind_speed_ms": current.get("wind_speed_10m"),
                "wind_direction_deg": current.get("wind_direction_10m"),
                "wind_gusts_kmh": _ms_to_kmh(current.get("wind_gusts_10m")),
                "precipitation_mm": current.get("precipitation"),
                "weather_code": current.get("weather_code"),
                "weather_description": _wmo_code_to_text(current.get("weather_code")),
                "cloud_cover_pct": current.get("cloud_cover"),
                "visibility_m": current.get("visibility"),
            },
            "hourly_forecast": _build_hourly(data.get("hourly", {})),
        }
    except requests.RequestException as e:
        return {"error": f"Weather API request failed: {str(e)}", "lat": lat, "lon": lon}


def get_marine_forecast(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch marine forecast from Open-Meteo Marine API.
    Returns wave height, wave period, swell data.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "wave_height",
            "wave_direction",
            "wave_period",
            "wind_wave_height",
            "swell_wave_height",
            "swell_wave_period",
            "swell_wave_direction",
            "ocean_current_velocity",
            "ocean_current_direction",
        ],
        "hourly": [
            "wave_height",
            "wave_period",
            "swell_wave_height",
            "wind_wave_height",
        ],
        "forecast_days": 3,
        "timezone": "Asia/Kolkata",
    }

    try:
        resp = requests.get(MARINE_BASE, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})

        wh = current.get("wave_height", 0) or 0
        swh = current.get("swell_wave_height", 0) or 0

        return {
            "lat": lat,
            "lon": lon,
            "source": "Open-Meteo Marine API",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "current": {
                "wave_height_m": wh,
                "wave_direction_deg": current.get("wave_direction"),
                "wave_period_s": current.get("wave_period"),
                "wind_wave_height_m": current.get("wind_wave_height"),
                "swell_wave_height_m": swh,
                "swell_wave_period_s": current.get("swell_wave_period"),
                "swell_wave_direction_deg": current.get("swell_wave_direction"),
                "ocean_current_velocity_ms": current.get("ocean_current_velocity"),
                "ocean_current_direction_deg": current.get("ocean_current_direction"),
                "sea_state": _sea_state(wh),
            },
            "hourly_forecast": _build_marine_hourly(data.get("hourly", {})),
        }
    except requests.RequestException as e:
        return {"error": f"Marine API request failed: {str(e)}", "lat": lat, "lon": lon}


def get_combined_forecast(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch both weather and marine forecasts and merge into a single response.
    """
    weather = get_weather_forecast(lat, lon)
    marine = get_marine_forecast(lat, lon)
    return {
        "lat": lat,
        "lon": lon,
        "weather": weather.get("current", {}),
        "marine": marine.get("current", {}),
        "weather_hourly": weather.get("hourly_forecast", []),
        "marine_hourly": marine.get("hourly_forecast", []),
        "weather_error": weather.get("error"),
        "marine_error": marine.get("error"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


# ─── Internal Helpers ──────────────────────────────────────────────────────────

def _ms_to_kmh(val: Optional[float]) -> Optional[float]:
    return round(val * 3.6, 2) if val is not None else None


def _sea_state(wave_height_m: float) -> str:
    """Beaufort/Douglas sea state description from wave height."""
    if wave_height_m < 0.1:
        return "Glassy / Calm"
    elif wave_height_m < 0.5:
        return "Rippled"
    elif wave_height_m < 1.25:
        return "Slight"
    elif wave_height_m < 2.5:
        return "Moderate"
    elif wave_height_m < 4.0:
        return "Rough"
    elif wave_height_m < 6.0:
        return "Very Rough"
    elif wave_height_m < 9.0:
        return "High"
    else:
        return "Very High / Phenomenal"


def _wmo_code_to_text(code: Optional[int]) -> str:
    """Convert WMO weather interpretation code to human-readable text."""
    if code is None:
        return "Unknown"
    wmo = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
        95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
    }
    return wmo.get(code, f"WMO code {code}")


def _build_hourly(hourly: Dict[str, Any]) -> list:
    """Build a clean hourly list from raw Open-Meteo hourly dict."""
    times = hourly.get("time", [])
    ws = hourly.get("wind_speed_10m", [])
    precip = hourly.get("precipitation_probability", [])
    temp = hourly.get("temperature_2m", [])
    gusts = hourly.get("wind_gusts_10m", [])
    result = []
    for i, t in enumerate(times[:24]):  # next 24 hours
        result.append({
            "time": t,
            "temp_c": temp[i] if i < len(temp) else None,
            "wind_speed_kmh": _ms_to_kmh(ws[i]) if i < len(ws) else None,
            "wind_gusts_kmh": _ms_to_kmh(gusts[i]) if i < len(gusts) else None,
            "precipitation_prob_pct": precip[i] if i < len(precip) else None,
        })
    return result


def _build_marine_hourly(hourly: Dict[str, Any]) -> list:
    times = hourly.get("time", [])
    wh = hourly.get("wave_height", [])
    wp = hourly.get("wave_period", [])
    swh = hourly.get("swell_wave_height", [])
    wwh = hourly.get("wind_wave_height", [])
    result = []
    for i, t in enumerate(times[:24]):
        result.append({
            "time": t,
            "wave_height_m": wh[i] if i < len(wh) else None,
            "wave_period_s": wp[i] if i < len(wp) else None,
            "swell_wave_height_m": swh[i] if i < len(swh) else None,
            "wind_wave_height_m": wwh[i] if i < len(wwh) else None,
        })
    return result
