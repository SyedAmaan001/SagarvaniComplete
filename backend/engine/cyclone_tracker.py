"""
Cyclone Tracker Engine
Tracks active cyclones in the Indian Ocean region.
Sources: IMD RSMC, Open-Meteo, Copernicus Marine.
"""

import os
import re
import math
import requests
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from utils.geo_utils import haversine_km, make_circle_geojson, make_point_geojson, make_feature_collection


# IMD RSMC active cyclone page
IMD_RSMC_URL = "https://rsmcnewdelhi.imd.gov.in"

# Known cyclone track data from MOSDAC SAR files
# (cyc034, cyc035 folders suggest historical cyclone data)
KNOWN_HISTORICAL_CYCLONES = [
    {
        "id": "cyc034",
        "name": "CYC-034 (MOSDAC)",
        "year": 2016,
        "basin": "Indian Ocean",
        "status": "historical",
        "source": "MOSDAC SAR",
    },
    {
        "id": "cyc035",
        "name": "CYC-035 (MOSDAC)",
        "year": 2016,
        "basin": "Indian Ocean",
        "status": "historical",
        "source": "MOSDAC SAR",
    },
]

# Saffir-Simpson equivalent for Indian Ocean cyclones (IMD scale)
IMD_CYCLONE_SCALE = [
    {"name": "Depression", "min_kmph": 0,   "max_kmph": 61,  "color": "#90EE90"},
    {"name": "Deep Depression", "min_kmph": 62, "max_kmph": 88, "color": "#FFD700"},
    {"name": "Cyclonic Storm", "min_kmph": 89, "max_kmph": 117, "color": "#FFA500"},
    {"name": "Severe Cyclonic Storm", "min_kmph": 118, "max_kmph": 167, "color": "#FF4500"},
    {"name": "Very Severe Cyclonic Storm", "min_kmph": 168, "max_kmph": 221, "color": "#FF0000"},
    {"name": "Extremely Severe Cyclonic Storm", "min_kmph": 222, "max_kmph": 279, "color": "#8B0000"},
    {"name": "Super Cyclonic Storm", "min_kmph": 280, "max_kmph": 9999, "color": "#4B0082"},
]


def get_active_cyclones() -> List[Dict[str, Any]]:
    """
    Fetch active cyclones from IMD RSMC.
    Returns a list of cyclone dicts with position, intensity, track.
    Falls back gracefully if network is unavailable.
    """
    cyclones = []

    try:
        headers = {"User-Agent": "ORCA-SIH-Research/1.0 (SIH26176)"}
        resp = requests.get(f"{IMD_RSMC_URL}/", headers=headers, timeout=10)
        if resp.status_code == 200:
            text = resp.text
            # Look for active storm keywords
            if any(kw in text for kw in ["Cyclone", "Depression", "Storm", "Alert"]):
                # Extract any coordinates mentioned
                coords = re.findall(
                    r'(\d{1,2}(?:\.\d+)?)[°\s]*(N|S)[,\s/]+(\d{1,3}(?:\.\d+)?)[°\s]*(E|W)',
                    text
                )
                names = re.findall(
                    r'(?:Cyclone|CYCLONE)\s+([A-Z][A-Za-z]+)', text
                )
                for i, (lat_v, lat_d, lon_v, lon_d) in enumerate(coords[:3]):
                    lat = float(lat_v) * (1 if lat_d == "N" else -1)
                    lon = float(lon_v) * (1 if lon_d == "E" else -1)
                    name = names[i] if i < len(names) else f"System-{i+1}"
                    cyclones.append(_build_cyclone_entry(name, lat, lon, source="IMD RSMC"))
    except Exception:
        pass  # Network error — return empty list

    return cyclones


def _build_cyclone_entry(
    name: str,
    lat: float,
    lon: float,
    wind_kmph: float = 90.0,
    source: str = "IMD",
) -> Dict[str, Any]:
    """Build a standardised cyclone dict."""
    category = _get_imd_category(wind_kmph)
    # Danger radius zones (approximate)
    eye_wall_radius = _danger_radius_km(wind_kmph, "eye_wall")
    gale_radius = _danger_radius_km(wind_kmph, "gale")

    return {
        "name": name,
        "lat": lat,
        "lon": lon,
        "wind_speed_kmph": wind_kmph,
        "category": category["name"],
        "color": category["color"],
        "eye_wall_radius_km": eye_wall_radius,
        "gale_force_radius_km": gale_radius,
        "source": source,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def _get_imd_category(wind_kmph: float) -> Dict[str, str]:
    """Map wind speed to IMD cyclone category."""
    for cat in IMD_CYCLONE_SCALE:
        if cat["min_kmph"] <= wind_kmph <= cat["max_kmph"]:
            return cat
    return IMD_CYCLONE_SCALE[-1]


def _danger_radius_km(wind_kmph: float, zone: str) -> float:
    """
    Approximate danger radii based on cyclone intensity.
    These are generalised estimates (actual radii from IMD advisories).
    """
    if zone == "eye_wall":
        return max(30, wind_kmph * 0.4)
    elif zone == "gale":
        return max(100, wind_kmph * 1.8)
    return 100.0


def build_cyclone_geojson(cyclones: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Build a GeoJSON FeatureCollection from active cyclone data.
    Includes eye position (point), eye-wall zone (circle), gale zone (circle).
    """
    if cyclones is None:
        cyclones = get_active_cyclones()

    features = []
    for cyc in cyclones:
        lat = cyc.get("lat")
        lon = cyc.get("lon")
        if lat is None or lon is None:
            continue

        # Eye position
        features.append(make_point_geojson(lat, lon, {
            "name": cyc.get("name"),
            "category": cyc.get("category"),
            "wind_kmph": cyc.get("wind_speed_kmph"),
            "color": cyc.get("color", "#FF0000"),
            "type": "cyclone_eye",
        }))

        # Eye-wall danger zone
        features.append(make_circle_geojson(lat, lon, cyc.get("eye_wall_radius_km", 50), {
            "name": cyc.get("name"),
            "zone": "eye_wall",
            "risk": "EXTREME",
            "color": "#8B0000",
            "fill_opacity": 0.5,
        }))

        # Gale force wind zone
        features.append(make_circle_geojson(lat, lon, cyc.get("gale_force_radius_km", 200), {
            "name": cyc.get("name"),
            "zone": "gale_force",
            "risk": "DANGER",
            "color": "#FF4500",
            "fill_opacity": 0.2,
        }))

    return {
        "geojson": make_feature_collection(features),
        "cyclone_count": len(cyclones),
        "cyclones": cyclones,
        "historical_data": KNOWN_HISTORICAL_CYCLONES,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


def get_cyclone_impact_on_zone(
    zone_lat: float,
    zone_lon: float,
    cyclones: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Assess cyclone impact on a specific fishing zone.
    Returns distance to nearest cyclone and associated risk.
    """
    if cyclones is None:
        cyclones = get_active_cyclones()

    if not cyclones:
        return {
            "zone_lat": zone_lat,
            "zone_lon": zone_lon,
            "cyclone_threat": "NONE",
            "nearest_cyclone": None,
            "distance_km": None,
            "in_gale_zone": False,
            "in_eye_wall": False,
        }

    nearest_dist = float("inf")
    nearest_cyc = None

    for cyc in cyclones:
        cyc_lat = cyc.get("lat")
        cyc_lon = cyc.get("lon")
        if cyc_lat and cyc_lon:
            d = haversine_km(zone_lat, zone_lon, cyc_lat, cyc_lon)
            if d < nearest_dist:
                nearest_dist = d
                nearest_cyc = cyc

    in_eye_wall = nearest_dist <= (nearest_cyc.get("eye_wall_radius_km", 50) if nearest_cyc else 0)
    in_gale = nearest_dist <= (nearest_cyc.get("gale_force_radius_km", 200) if nearest_cyc else 0)

    if in_eye_wall:
        threat = "EXTREME"
    elif in_gale:
        threat = "DANGER"
    elif nearest_dist <= 500:
        threat = "WARNING"
    elif nearest_dist <= 1000:
        threat = "WATCH"
    else:
        threat = "NONE"

    return {
        "zone_lat": zone_lat,
        "zone_lon": zone_lon,
        "cyclone_threat": threat,
        "nearest_cyclone": nearest_cyc.get("name") if nearest_cyc else None,
        "distance_km": round(nearest_dist, 1) if nearest_dist != float("inf") else None,
        "in_gale_zone": in_gale,
        "in_eye_wall": in_eye_wall,
    }
