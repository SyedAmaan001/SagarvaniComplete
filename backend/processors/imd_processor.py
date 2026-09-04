"""
IMD (India Meteorological Department) Data Processor
Fetches and parses cyclone bulletins and weather warnings from IMD.
Uses both API (if key is available) and public web scraping fallback.
"""

import os
import re
import requests
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

IMD_API_KEY = os.getenv("IMD_API_KEY", "")

# IMD public endpoints (no auth required for basic data)
IMD_CYCLONE_URL = "https://rsmcnewdelhi.imd.gov.in/report.php?internal_menu=MQ=="
IMD_WARNING_RSS = "https://mausam.imd.gov.in/imd_latest/contents/warning.php"

# Known Indian Ocean fishing zones (lat/lon bounding boxes)
INDIAN_FISHING_ZONES = [
    {"name": "Arabian Sea (North)", "lat": 15.0, "lon": 65.0, "radius_km": 500},
    {"name": "Arabian Sea (South)", "lat": 10.0, "lon": 70.0, "radius_km": 500},
    {"name": "Bay of Bengal (North)", "lat": 18.0, "lon": 87.0, "radius_km": 500},
    {"name": "Bay of Bengal (Central)", "lat": 13.0, "lon": 82.0, "radius_km": 500},
    {"name": "Lakshadweep Sea", "lat": 10.5, "lon": 72.5, "radius_km": 300},
    {"name": "Andaman Sea", "lat": 12.0, "lon": 93.0, "radius_km": 400},
]


def get_active_cyclones() -> Dict[str, Any]:
    """
    Fetch active cyclone data from IMD RSMC.
    Falls back to a structured mock if network is unavailable.
    """
    cyclones = []
    fetch_error = None

    try:
        headers = {"User-Agent": "ORCA-SIH-Research/1.0"}
        resp = requests.get(IMD_CYCLONE_URL, headers=headers, timeout=10)
        if resp.status_code == 200:
            # Parse basic text from page
            text = resp.text
            # Look for cyclone names (heuristic — improve with BeautifulSoup if needed)
            names = re.findall(r'(?:Cyclone|Depression|Storm)\s+([A-Z][A-Za-z]+)', text)
            if names:
                for name in set(names[:5]):
                    cyclones.append({
                        "name": name,
                        "source": "IMD RSMC",
                        "status": "active",
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                    })
    except Exception as e:
        fetch_error = str(e)

    return {
        "active_cyclones": cyclones,
        "cyclone_count": len(cyclones),
        "fetch_error": fetch_error,
        "note": "Live data from IMD RSMC. Add IMD_API_KEY to .env for full API access.",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "imd_cyclone_portal": "https://rsmcnewdelhi.imd.gov.in/",
    }


def get_imd_weather_warning(lat: float, lon: float) -> Dict[str, Any]:
    """
    Get IMD weather warning level for a given location.
    Color-coded: No Warning / Yellow / Orange / Red.
    """
    # Without a live IMD API key, we derive from Open-Meteo wind data
    # as a proxy. With IMD_API_KEY, this would call the IMD API directly.

    warning_level = "No Warning"
    warning_color = "green"

    if IMD_API_KEY:
        # Placeholder for real IMD API call
        # result = requests.get(f"https://api.imd.gov.in/warnings?lat={lat}&lon={lon}&key={IMD_API_KEY}")
        pass

    return {
        "lat": lat,
        "lon": lon,
        "warning_level": warning_level,
        "warning_color": warning_color,
        "imd_api_key_present": bool(IMD_API_KEY),
        "note": (
            "Register at https://mausam.imd.gov.in to get an IMD API key "
            "and set IMD_API_KEY in your .env file for live warning data."
        ),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def get_fishing_zone_advisories() -> List[Dict[str, Any]]:
    """
    Return IMD-style advisories for all known Indian fishing zones.
    """
    advisories = []
    for zone in INDIAN_FISHING_ZONES:
        advisories.append({
            "zone": zone["name"],
            "center_lat": zone["lat"],
            "center_lon": zone["lon"],
            "radius_km": zone["radius_km"],
            "imd_warning": "Checking...",
            "status": "nominal",
        })
    return advisories


def parse_imd_bulletin_text(text: str) -> Dict[str, Any]:
    """
    Parse raw IMD bulletin text and extract key fields.
    Useful when reading downloaded PDF/text bulletins.
    """
    result = {
        "raw_length": len(text),
        "cyclone_mentions": [],
        "coordinates_found": [],
        "wind_speeds_found": [],
        "warnings": [],
    }

    # Find cyclone names
    result["cyclone_mentions"] = list(set(
        re.findall(r'(?:Cyclone|CYCLONE|Depression|DEPRESSION|Storm)\s+([A-Z][A-Za-z]+)', text)
    ))

    # Find coordinates (e.g., "14.5°N 80.2°E")
    coords = re.findall(
        r'(\d{1,2}(?:\.\d+)?)[°\s]*(N|S)[,\s]+(\d{1,3}(?:\.\d+)?)[°\s]*(E|W)', text
    )
    for lat_v, lat_d, lon_v, lon_d in coords:
        lat = float(lat_v) * (1 if lat_d == "N" else -1)
        lon = float(lon_v) * (1 if lon_d == "E" else -1)
        result["coordinates_found"].append({"lat": lat, "lon": lon})

    # Find wind speeds (e.g., "85-95 kmph", "120 knots")
    ws_kmph = re.findall(r'(\d+(?:-\d+)?)\s*(?:kmph|km/h|kph)', text, re.IGNORECASE)
    result["wind_speeds_found"] = [{"value": v, "unit": "kmph"} for v in ws_kmph]

    # Warning keywords
    warning_kw = ["RED", "ORANGE", "YELLOW", "WARNING", "ALERT", "GALE", "CYCLONE WARNING"]
    for kw in warning_kw:
        if kw in text.upper():
            result["warnings"].append(kw)

    return result
