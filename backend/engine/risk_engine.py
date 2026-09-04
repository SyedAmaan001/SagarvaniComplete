"""
Multi-Factor Risk Scoring Engine
Computes a 0–100 risk score for fishing safety at a given lat/lon.

Risk Score Formula:
  Risk = 0.30 × Wave_Height_Score
       + 0.25 × Wind_Speed_Score
       + 0.20 × Current_Speed_Score
       + 0.15 × Cyclone_Prox_Score
       + 0.10 × LULC_Coastal_Vuln_Score
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from processors.weather_processor import get_combined_forecast
from parsers.nc_parser import get_point_ocean_current
from utils.geo_utils import haversine_km, normalize_score, risk_level, make_feature_collection, make_point_geojson, make_circle_geojson


# ─── Scoring Thresholds ────────────────────────────────────────────────────────

# Wave height: 0m = 0 score, ≥6m = 100 score
WAVE_HEIGHT_MIN = 0.0
WAVE_HEIGHT_MAX = 6.0

# Wind speed: 0 m/s = 0, ≥25 m/s (90 kmh) = 100
WIND_SPEED_MIN = 0.0
WIND_SPEED_MAX = 25.0

# Ocean current speed: 0 m/s = 0, ≥2 m/s = 100
CURRENT_MIN = 0.0
CURRENT_MAX = 2.0

# Cyclone proximity: ≤200km = 100, ≥1000km = 0
CYCLONE_PROX_DANGER_KM = 200.0
CYCLONE_PROX_SAFE_KM = 1000.0

# Indian coastal vulnerability (static lookup by region)
# Values from LULC assessment — coastal areas get higher base vulnerability
COASTAL_VULNERABILITY_ZONES = {
    "andaman": 60,
    "lakshadweep": 65,
    "kerala": 55,
    "karnataka": 45,
    "goa": 45,
    "maharashtra": 50,
    "gujarat": 55,
    "andhra_pradesh": 50,
    "odisha": 60,
    "west_bengal": 65,
    "tamil_nadu": 55,
    "open_sea": 30,
}

# Predefined fishing zones for the risk map
FISHING_GRID_POINTS = [
    # Arabian Sea
    {"lat": 15.0, "lon": 65.0, "zone": "Arabian Sea North"},
    {"lat": 12.0, "lon": 68.0, "zone": "Arabian Sea Central"},
    {"lat": 10.0, "lon": 70.0, "zone": "Arabian Sea South"},
    {"lat": 8.5,  "lon": 72.5, "zone": "Lakshadweep Sea"},
    # Bay of Bengal
    {"lat": 18.0, "lon": 87.0, "zone": "Bay of Bengal North"},
    {"lat": 15.0, "lon": 85.0, "zone": "Bay of Bengal Central"},
    {"lat": 13.0, "lon": 82.0, "zone": "Bay of Bengal South"},
    {"lat": 12.0, "lon": 93.0, "zone": "Andaman Sea"},
    # Indian Coast
    {"lat": 20.0, "lon": 70.5, "zone": "Gujarat Coast"},
    {"lat": 15.5, "lon": 73.5, "zone": "Goa Coast"},
    {"lat": 11.0, "lon": 75.5, "zone": "Kerala Coast"},
    {"lat": 13.0, "lon": 80.3, "zone": "Tamil Nadu Coast"},
]


def compute_risk_score(
    lat: float,
    lon: float,
    active_cyclones: Optional[List[Dict]] = None,
    region: str = "open_sea",
) -> Dict[str, Any]:
    """
    Compute the full multi-factor risk score for a given lat/lon.

    Args:
        lat: Latitude of the fishing location
        lon: Longitude of the fishing location
        active_cyclones: List of active cyclone dicts with 'lat', 'lon' keys
        region: Coastal region name for LULC vulnerability lookup

    Returns:
        Dict with score (0–100), breakdown, level, and advisory
    """
    breakdown = {}
    errors = []

    # ── Factor 1: Wave Height (30%) ──────────────────────────────────────────
    wave_score = 0.0
    wave_height_m = None
    try:
        forecast = get_combined_forecast(lat, lon)
        marine = forecast.get("marine", {})
        wave_height_m = marine.get("wave_height_m") or 0.0
        wind_speed_ms = forecast.get("weather", {}).get("wind_speed_ms") or 0.0
        current_vel = marine.get("ocean_current_velocity_ms") or None

        wave_score = normalize_score(wave_height_m, WAVE_HEIGHT_MIN, WAVE_HEIGHT_MAX)
        breakdown["wave_height"] = {
            "value_m": wave_height_m,
            "score": round(wave_score, 2),
            "weight": 0.30,
            "sea_state": marine.get("sea_state", "Unknown"),
        }

        # ── Factor 2: Wind Speed (25%) ───────────────────────────────────────
        wind_score = normalize_score(wind_speed_ms, WIND_SPEED_MIN, WIND_SPEED_MAX)
        breakdown["wind_speed"] = {
            "value_ms": wind_speed_ms,
            "value_kmh": round(wind_speed_ms * 3.6, 2),
            "score": round(wind_score, 2),
            "weight": 0.25,
        }
    except Exception as e:
        errors.append(f"Weather/Marine fetch: {str(e)}")
        wave_score = 25.0  # assume moderate
        wind_score = 25.0
        breakdown["wave_height"] = {"error": str(e), "score": wave_score, "weight": 0.30}
        breakdown["wind_speed"] = {"error": str(e), "score": wind_score, "weight": 0.25}
        current_vel = None

    # ── Factor 3: Ocean Current Speed (20%) ──────────────────────────────────
    current_score = 0.0
    try:
        current_data = get_point_ocean_current(lat, lon)
        if "error" not in current_data:
            speed = current_data.get("speed_ms", 0.0) or 0.0
            current_score = normalize_score(speed, CURRENT_MIN, CURRENT_MAX)
            breakdown["ocean_current"] = {
                "value_ms": speed,
                "score": round(current_score, 2),
                "weight": 0.20,
                "source": current_data.get("source_file", "MOSDAC"),
            }
        elif current_vel is not None:
            # Fallback to Open-Meteo ocean current
            current_score = normalize_score(current_vel, CURRENT_MIN, CURRENT_MAX)
            breakdown["ocean_current"] = {
                "value_ms": current_vel,
                "score": round(current_score, 2),
                "weight": 0.20,
                "source": "Open-Meteo Marine",
            }
        else:
            breakdown["ocean_current"] = {"note": "No current data", "score": 0.0, "weight": 0.20}
    except Exception as e:
        errors.append(f"Ocean current: {str(e)}")
        breakdown["ocean_current"] = {"error": str(e), "score": 0.0, "weight": 0.20}

    # ── Factor 4: Cyclone Proximity (15%) ────────────────────────────────────
    cyclone_score = 0.0
    nearest_cyclone = None
    if active_cyclones:
        distances = []
        for cyc in active_cyclones:
            cyc_lat = cyc.get("lat")
            cyc_lon = cyc.get("lon")
            if cyc_lat is not None and cyc_lon is not None:
                dist = haversine_km(lat, lon, cyc_lat, cyc_lon)
                distances.append((dist, cyc))
        if distances:
            nearest_dist, nearest_cyc = min(distances, key=lambda x: x[0])
            nearest_cyclone = {"name": nearest_cyc.get("name"), "distance_km": round(nearest_dist, 1)}
            # Invert: closer = higher score
            if nearest_dist <= CYCLONE_PROX_DANGER_KM:
                cyclone_score = 100.0
            elif nearest_dist >= CYCLONE_PROX_SAFE_KM:
                cyclone_score = 0.0
            else:
                cyclone_score = normalize_score(
                    CYCLONE_PROX_SAFE_KM - nearest_dist,
                    0,
                    CYCLONE_PROX_SAFE_KM - CYCLONE_PROX_DANGER_KM,
                )

    breakdown["cyclone_proximity"] = {
        "nearest_cyclone": nearest_cyclone,
        "score": round(cyclone_score, 2),
        "weight": 0.15,
        "note": "0 = no cyclone nearby, 100 = cyclone within 200km",
    }

    # ── Factor 5: LULC Coastal Vulnerability (10%) ───────────────────────────
    vuln_score = COASTAL_VULNERABILITY_ZONES.get(region.lower(), 30)
    breakdown["lulc_vulnerability"] = {
        "region": region,
        "score": vuln_score,
        "weight": 0.10,
        "source": "Bhuvan NRSC LULC 2024-25",
    }

    # ── Final Weighted Score ──────────────────────────────────────────────────
    final_score = (
        0.30 * wave_score
        + 0.25 * (breakdown.get("wind_speed", {}).get("score", 25.0))
        + 0.20 * current_score
        + 0.15 * cyclone_score
        + 0.10 * vuln_score
    )
    final_score = round(min(100.0, max(0.0, final_score)), 2)
    level_info = risk_level(final_score)

    return {
        "lat": lat,
        "lon": lon,
        "risk_score": final_score,
        "risk_level": level_info["level"],
        "risk_color": level_info["color"],
        "risk_emoji": level_info["emoji"],
        "advice": level_info["advice"],
        "breakdown": breakdown,
        "errors": errors if errors else None,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


def build_risk_map(active_cyclones: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Compute risk scores for all predefined fishing zones.
    Returns a GeoJSON FeatureCollection suitable for map rendering.
    """
    features = []
    zone_summaries = []

    for zone in FISHING_GRID_POINTS:
        lat, lon = zone["lat"], zone["lon"]
        zone_name = zone["zone"]

        # Determine region for LULC lookup
        region = _infer_region(lat, lon, zone_name)
        score_data = compute_risk_score(lat, lon, active_cyclones, region)

        # Point feature
        features.append(make_point_geojson(lat, lon, {
            "zone": zone_name,
            "risk_score": score_data["risk_score"],
            "risk_level": score_data["risk_level"],
            "risk_color": score_data["risk_color"],
            "risk_emoji": score_data["risk_emoji"],
            "advice": score_data["advice"],
            "wave_height_m": score_data["breakdown"].get("wave_height", {}).get("value_m"),
            "wind_speed_kmh": score_data["breakdown"].get("wind_speed", {}).get("value_kmh"),
        }))

        # Circle zone feature
        features.append(make_circle_geojson(lat, lon, 150, {
            "zone": zone_name,
            "risk_score": score_data["risk_score"],
            "risk_level": score_data["risk_level"],
            "risk_color": score_data["risk_color"],
            "fill_opacity": 0.3,
        }))

        zone_summaries.append({
            "zone": zone_name,
            "lat": lat,
            "lon": lon,
            "risk_score": score_data["risk_score"],
            "risk_level": score_data["risk_level"],
        })

    overall_max = max(z["risk_score"] for z in zone_summaries)
    overall_avg = round(sum(z["risk_score"] for z in zone_summaries) / len(zone_summaries), 2)

    return {
        "geojson": make_feature_collection(features),
        "zone_summaries": zone_summaries,
        "overall_max_risk": overall_max,
        "overall_avg_risk": overall_avg,
        "zone_count": len(FISHING_GRID_POINTS),
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


def _infer_region(lat: float, lon: float, zone_name: str) -> str:
    """Infer the coastal region name from zone name or coordinates."""
    name_lower = zone_name.lower()
    if "gujarat" in name_lower:
        return "gujarat"
    elif "goa" in name_lower:
        return "goa"
    elif "kerala" in name_lower:
        return "kerala"
    elif "tamil" in name_lower:
        return "tamil_nadu"
    elif "andaman" in name_lower:
        return "andaman"
    elif "lakshadweep" in name_lower:
        return "lakshadweep"
    elif "andhra" in name_lower:
        return "andhra_pradesh"
    elif "odisha" in name_lower:
        return "odisha"
    elif "bengal" in name_lower:
        return "west_bengal"
    else:
        return "open_sea"
