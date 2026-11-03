"""
Live map builder: turns the live data snapshot into GeoJSON layers the dashboard can draw.

Every feature carries the provider's own valid_time. Layers the backend cannot back with a
real feed are reported as NOT_CONNECTED instead of being drawn with placeholder shapes.
"""

import math
from datetime import datetime, timezone
from typing import Any, Dict, List

from gateway.marine_data_gateway import RESTRICTED_MARINE_ZONES, VESSEL_PROFILES
from processors import live_data
from utils.geo_utils import make_circle_geojson, make_feature_collection

# Wave thresholds reuse the vessel limits so the map and the safety gate agree.
CAUTION_WAVE_M = VESSEL_PROFILES["artisanal_canoe"]["max_safe_wave_height_m"]      # 1.25
HIGH_WAVE_M = VESSEL_PROFILES["motorized_craft"]["max_safe_wave_height_m"]          # 1.8
DANGER_WAVE_M = VESSEL_PROFILES["mechanized_trawler"]["max_safe_wave_height_m"]     # 3.0


def _wave_level(h: float) -> str:
    if h > DANGER_WAVE_M:
        return "DANGER"
    if h > HIGH_WAVE_M:
        return "HIGH"
    if h > CAUTION_WAVE_M:
        return "CAUTION"
    return "NORMAL"


def _point(p: Dict[str, Any], props: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": "Feature",
            "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
            "properties": props}


def _arrow(p: Dict[str, Any]) -> Dict[str, Any]:
    """Current vector as a short line. Direction is assumed to be the direction the water flows TOWARDS."""
    speed, direction = p["current_ms"], p["current_dir_deg"]
    length_deg = min(0.08, max(0.02, speed * 0.08))
    theta = math.radians(direction)
    end_lat = p["lat"] + length_deg * math.cos(theta)
    end_lon = p["lon"] + length_deg * math.sin(theta) / max(0.2, math.cos(math.radians(p["lat"])))
    return {"type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[p["lon"], p["lat"]], [round(end_lon, 4), round(end_lat, 4)]]},
            "properties": {"type": "CURRENT_VECTOR", "speed_ms": speed, "direction_deg": direction,
                           "valid_time": p["marine_valid_time"]}}


def build_live_map(lat: float, lon: float, radius_km: float = 60.0) -> Dict[str, Any]:
    snap = live_data.get_snapshot(lat, lon, radius_km)
    ocean = [p for p in snap["points"] if p["is_ocean"]]
    now = datetime.now(timezone.utc)

    waves, sst, currents, warnings = [], [], [], []
    for p in ocean:
        if p["wave_height_m"] is not None:
            level = _wave_level(p["wave_height_m"])
            props = {"type": "WAVE_POINT", "wave_height_m": p["wave_height_m"],
                     "wave_period_s": p["wave_period_s"],
                     "wind_kmh": p["wind_kmh"], "gust_kmh": p["gust_kmh"], "level": level,
                     "valid_time": p["marine_valid_time"]}
            waves.append(_point(p, props))
            if level != "NORMAL":
                warnings.append(_point(p, dict(props, type="HIGH_WAVE_WARNING")))
        if p["sst_c"] is not None:
            sst.append(_point(p, {"type": "SST_POINT", "sst_c": p["sst_c"], "valid_time": p["marine_valid_time"]}))
        if p["current_ms"] is not None and p["current_dir_deg"] is not None:
            currents.append(_arrow(p))

    fronts = live_data.detect_sst_fronts(snap["points"])
    pfz = [_point(z, {"type": "SST_FRONT_CANDIDATE", "name": z["name"], "sst_c": z["sst_c"],
                      "sst_gradient_c_per_km": z["sst_gradient_c_per_km"], "score": z["productivity_score"],
                      "score_basis": z["score_basis"], "source": z["source"], "valid_time": z["valid_time"]})
           for z in fronts]

    restricted = [make_circle_geojson(z["center_lat"], z["center_lon"], z["radius_km"], {
        "type": "RESTRICTED_ZONE", "name": z["name"], "restriction_level": z["restriction_level"],
        "authority": z["authority"], "legal_basis": z["legal_basis"]}) for z in RESTRICTED_MARINE_ZONES]

    # Conditions at the map centre (nearest ocean cell) for the readout strip
    centre_pt, centre_dist = live_data.nearest_ocean_point(snap, lat, lon)
    conditions = None
    if centre_pt:
        conditions = {
            "wave_height_m": centre_pt["wave_height_m"], "wind_kmh": centre_pt["wind_kmh"],
            "sst_c": centre_pt["sst_c"], "current_ms": centre_pt["current_ms"],
            "valid_time": centre_pt["marine_valid_time"], "distance_from_centre_km": centre_dist,
        }

    age_min = None
    if snap["data_valid_time"]:
        age_min = round(max(0.0, (now - datetime.fromisoformat(snap["data_valid_time"])).total_seconds() / 60.0), 1)

    return {
        "generated_at": now.isoformat(),
        "center": {"lat": lat, "lon": lon},
        "radius_km": snap["radius_km"],
        "live": bool(ocean),
        "data_valid_time": snap["data_valid_time"],
        "data_age_minutes": age_min,
        "fetched_at": snap["fetched_at"],
        "refresh_seconds": live_data.CACHE_TTL_S,
        "ocean_point_count": len(ocean),
        "conditions": conditions,
        "sources": snap["sources"],
        "errors": snap["errors"],
        "layers": {
            "waves": make_feature_collection(waves),
            "sst": make_feature_collection(sst),
            "currents": make_feature_collection(currents),
            "wave_warnings": make_feature_collection(warnings),
            "pfz": make_feature_collection(pfz),
            "restricted": make_feature_collection(restricted),
        },
        "not_connected": [
            {"layer": "Cyclone", "needs": "IMD RSMC machine-readable cyclone feed"},
            {"layer": "Chlorophyll / official PFZ", "needs": "Copernicus Marine or INCOIS access"},
        ],
        "legend": {
            "wave_levels_m": {"CAUTION": f">{CAUTION_WAVE_M}", "HIGH": f">{HIGH_WAVE_M}", "DANGER": f">{DANGER_WAVE_M}"},
            "pfz_note": "SST thermal-front candidates derived from model data; not official INCOIS PFZ advisories.",
        },
    }
