"""
Marine Data Gateway (ORCA Core Architecture - Page 1 & 5)
Normalizes marine / weather feeds into one schema:
    parameter | value | unit | latitude | longitude | valid_time | source | mode | quality

What is LIVE today (fetched on request, cached ~10 min, see processors/live_data.py):
    - Open-Meteo Marine API : wave height, sea-surface temperature, ocean current, sea level
    - Open-Meteo Weather API: 10 m wind speed and gusts

What is NOT connected yet (the gateway reports these as unavailable instead of inventing values):
    - Chlorophyll-a / ocean colour (needs Copernicus or an ERDDAP dataset)
    - Lightning flash density, IMD warnings, live cyclone positions
    - Official INCOIS Potential Fishing Zones (candidate zones are derived from SST fronts)

What is STATIC:
    - RESTRICTED_MARINE_ZONES and VESSEL_PROFILES below. These are curated in code as circles
      and thresholds. Verify them against official notifications before real-world use.
"""

from typing import Dict, Any, List, Optional

from processors import live_data
from utils.geo_utils import haversine_km

# ─── Reference Indian Marine Protected Areas & Restricted Geofences (STATIC) ───
RESTRICTED_MARINE_ZONES = [
    {
        "id": "MPA_NETRANI",
        "name": "Netrani Island Coral Sanctuary & Defense Firing Zone",
        "state": "Karnataka",
        "type": "DEFENSE_AND_ECOLOGICAL_SANCTUARY",
        "center_lat": 14.0189,
        "center_lon": 74.3297,
        "radius_km": 8.0,
        "restriction_level": "STRICT_PROHIBITED",
        "authority": "Indian Navy & Karnataka Forest Dept",
        "legal_basis": "Wildlife Protection Act 1972 & Naval Defense Geofence"
    },
    {
        "id": "MPA_MALVAN",
        "name": "Malvan Marine Sanctuary",
        "state": "Maharashtra",
        "type": "MARINE_NATIONAL_PARK",
        "center_lat": 16.0500,
        "center_lon": 73.4667,
        "radius_km": 12.0,
        "restriction_level": "NO_COMMERCIAL_FISHING",
        "authority": "Maharashtra Wildlife Wing",
        "legal_basis": "Eco-Sensitive Marine Zone"
    },
    {
        "id": "IMBL_LAKSHADWEEP_INTL",
        "name": "High Seas International Boundary Border Buffer",
        "state": "Offshore",
        "type": "IMBL_SECURITY_BUFFER",
        "center_lat": 10.0000,
        "center_lon": 71.0000,
        "radius_km": 25.0,
        "restriction_level": "REGULATED_SECURITY_ZONE",
        "authority": "Indian Coast Guard (ICG)",
        "legal_basis": "Maritime Zones of India Act"
    },
    {
        "id": "MPA_GULF_OF_MANNAR",
        "name": "Gulf of Mannar Marine National Park",
        "state": "Tamil Nadu",
        "type": "BIOSPHERE_RESERVE",
        "center_lat": 9.1500,
        "center_lon": 79.1000,
        "radius_km": 20.0,
        "restriction_level": "NO_TRAWLING_ZONE",
        "authority": "Gulf of Mannar Biosphere Authority",
        "legal_basis": "Biosphere Conservation Act"
    }
]

# ─── Vessel Profiles & Physical Sea-Keeping Constraints (STATIC) ───────────────
VESSEL_PROFILES = {
    "artisanal_canoe": {
        "name": "Traditional Non-Motorized / Small FRP Canoe (4–7 m)",
        "max_safe_wave_height_m": 1.25,
        "max_safe_wind_speed_kmh": 25.0,
        "max_operating_distance_km": 15.0, # 8 Nautical Miles
        "requires_daylight": True
    },
    "motorized_craft": {
        "name": "Motorized OBM Fishing Craft (8–10 m)",
        "max_safe_wave_height_m": 1.80,
        "max_safe_wind_speed_kmh": 35.0,
        "max_operating_distance_km": 35.0, # 20 Nautical Miles
        "requires_daylight": False
    },
    "mechanized_trawler": {
        "name": "Mechanized Multi-Day Trawler / Purse Seiner (>12 m)",
        "max_safe_wave_height_m": 3.00,
        "max_safe_wind_speed_kmh": 50.0,
        "max_operating_distance_km": 120.0, # 65 Nautical Miles
        "requires_daylight": False
    }
}

# Parameters this gateway cannot supply live yet.
UNAVAILABLE_FEEDS = [
    {"parameter": "CHLOROPHYLL_A_CONCENTRATION", "needs": "Copernicus Marine / ERDDAP ocean-colour dataset"},
    {"parameter": "LIGHTNING_FLASH_DENSITY", "needs": "IMD lightning feed"},
    {"parameter": "ACTIVE_CYCLONES", "needs": "IMD RSMC machine-readable cyclone feed"},
    {"parameter": "OFFICIAL_PFZ", "needs": "INCOIS PFZ advisory access"},
]

CRITICAL_PARAMETERS = ("SIGNIFICANT_WAVE_HEIGHT", "WIND_SPEED_10M")


class MarineDataGateway:
    """Normalizes live marine/weather feeds into structured telemetry records."""

    def fetch_normalized_marine_record(self, lat: float, lon: float, radius_km: float = 50.0) -> Dict[str, Any]:
        """
        Live conditions at (lat, lon). Coastal points are often land cells in the model grid,
        so values come from the nearest ocean cell (distance reported in ``data_location``).
        Missing values are omitted from ``normalized_records`` and listed in
        ``unavailable_parameters``; ``critical_missing`` is non-empty when the safety gate
        cannot be evaluated.
        """
        snap = live_data.get_snapshot(lat, lon, radius_km)
        point, dist_km = live_data.nearest_ocean_point(snap, lat, lon)
        fetched_at = snap["fetched_at"]

        records: List[Dict[str, Any]] = []
        unavailable: List[str] = []

        def add(parameter, value, unit, source, mode, valid_time):
            if value is None or point is None:
                unavailable.append(parameter)
                return
            records.append({
                "parameter": parameter,
                "value": value,
                "unit": unit,
                "latitude": point["lat"],
                "longitude": point["lon"],
                "valid_time": valid_time,
                "fetched_at": fetched_at,
                "source": source,
                "mode": mode,
            })

        p = point or {}
        marine_src = "Open-Meteo Marine API"
        weather_src = "Open-Meteo Weather API"
        mt, wt = p.get("marine_valid_time"), p.get("weather_valid_time")
        add("SIGNIFICANT_WAVE_HEIGHT", p.get("wave_height_m"), "meters", marine_src, "MODEL_NOWCAST", mt)
        add("WIND_SPEED_10M", p.get("wind_kmh"), "km/h", weather_src, "MODEL_NOWCAST", wt)
        add("WIND_GUSTS_10M", p.get("gust_kmh"), "km/h", weather_src, "MODEL_NOWCAST", wt)
        add("SURFACE_OCEAN_CURRENT_VELOCITY", p.get("current_ms"), "m/s", marine_src, "MODEL_NOWCAST", mt)
        add("SEA_SURFACE_TEMPERATURE", p.get("sst_c"), "deg_C", marine_src, "MODEL_NOWCAST", mt)
        add("SEA_LEVEL_HEIGHT_MSL", p.get("sea_level_m"), "meters_above_MSL", marine_src, "MODEL_NOWCAST", mt)

        critical_missing = [c for c in CRITICAL_PARAMETERS if c in unavailable]

        have = {r["parameter"] for r in records}
        sources = [
            {
                "source": marine_src,
                "parameters": ["SIGNIFICANT_WAVE_HEIGHT", "SURFACE_OCEAN_CURRENT_VELOCITY",
                               "SEA_SURFACE_TEMPERATURE", "SEA_LEVEL_HEIGHT_MSL"],
                "valid_time": mt, "fetched_at": fetched_at,
                "ok": "SIGNIFICANT_WAVE_HEIGHT" in have,
            },
            {
                "source": weather_src,
                "parameters": ["WIND_SPEED_10M", "WIND_GUSTS_10M"],
                "valid_time": wt, "fetched_at": fetched_at,
                "ok": "WIND_SPEED_10M" in have,
            },
        ]

        return {
            "gateway": "ORCA Marine Data Gateway",
            "timestamp": fetched_at,
            "query_location": {"lat": lat, "lon": lon},
            "data_location": ({"lat": point["lat"], "lon": point["lon"], "distance_from_query_km": dist_km}
                              if point else None),
            "records_count": len(records),
            "normalized_records": records,
            "unavailable_parameters": sorted(set(unavailable)),
            "unavailable_feeds": UNAVAILABLE_FEEDS,
            "critical_missing": critical_missing,
            "sources": sources,
            "provenance": {
                "open_meteo_marine": "OK" if "SIGNIFICANT_WAVE_HEIGHT" in have else "UNAVAILABLE",
                "open_meteo_weather": "OK" if "WIND_SPEED_10M" in have else "UNAVAILABLE",
                "incois": "NOT_CONNECTED",
                "mosdac_live": "NOT_CONNECTED",
                "imd": "NOT_CONNECTED",
                "cyclone_feed": "NOT_CONNECTED",
            },
            "errors": snap.get("errors", []),
        }

    def get_candidate_pfz_zones(self, user_lat: float, user_lon: float, max_range_km: float = 60.0) -> List[Dict[str, Any]]:
        """
        Candidate fishing zones within range, derived live from sea-surface-temperature fronts.
        These are model-derived candidates, not official INCOIS PFZ advisories.
        """
        snap = live_data.get_snapshot(user_lat, user_lon, max_range_km)
        candidates = []
        for zone in live_data.detect_sst_fronts(snap["points"]):
            dist = haversine_km(user_lat, user_lon, zone["lat"], zone["lon"])
            if dist <= max_range_km:
                entry = dict(zone)
                entry["distance_from_user_km"] = round(dist, 1)
                entry["transit_time_hours"] = round(dist / 15.0, 1)  # assumes 15 km/h cruise
                candidates.append(entry)
        return candidates

    def get_hourly_outlook(self, lat: float, lon: float) -> Dict[str, Any]:
        """Hourly wave/wind outlook at the nearest ocean cell, for departure windows."""
        snap = live_data.get_snapshot(lat, lon, 20.0)
        point, _ = live_data.nearest_ocean_point(snap, lat, lon)
        if point is None:
            return {"hours": [], "error": "no ocean data point near location", "fetched_at": snap["fetched_at"]}
        return live_data.get_hourly_outlook(point["lat"], point["lon"])

    def get_restricted_marine_geofences(self) -> List[Dict[str, Any]]:
        """Curated restricted waters / protected areas (static reference data)."""
        return RESTRICTED_MARINE_ZONES

    def get_vessel_profile(self, profile_key: str = "motorized_craft") -> Dict[str, Any]:
        """Returns vessel specifications and wave/wind safety thresholds."""
        return VESSEL_PROFILES.get(profile_key, VESSEL_PROFILES["motorized_craft"])
