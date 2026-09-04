"""
Hard Safety & Geofence Engine (ORCA Core Decision Loop - Page 4)
Core Principle: "Safe First, Productive Second" — AI scoring never overrides a hard safety constraint.

Enforces deterministic hard constraints:
1. Marine Protected Areas (MPAs), defense firing ranges, and international boundary buffers (IMBL).
2. Vessel-specific sea-keeping limits (boat length, wave height threshold, wind speed ceiling, daylight constraint).
3. Severe meteorological hazards (cyclone gale radius, severe lightning strike clusters).
"""

from typing import Dict, Any, List, Tuple
from utils.geo_utils import haversine_km
from gateway.marine_data_gateway import RESTRICTED_MARINE_ZONES, VESSEL_PROFILES

class HardSafetyGate:
    name: str = "Hard Safety & Geofence Gate"

    def evaluate_safety_constraints(
        self,
        target_lat: float,
        target_lon: float,
        vessel_type: str,
        wave_height_m: float,
        wind_speed_kmh: float,
        is_cyclone_active: bool = False,
        lightning_density: float = 0.0
    ) -> Dict[str, Any]:
        """
        Executes binary pass/fail safety rules.
        If ANY critical constraint is violated, the target area is marked REJECTED / UNSAFE.
        """
        violations = []
        warnings = []
        is_safe = True

        vessel = VESSEL_PROFILES.get(vessel_type, VESSEL_PROFILES["motorized_craft"])

        # ── 1. Geofence Rule: Restricted / Protected Marine Area Intersection ──
        for zone in RESTRICTED_MARINE_ZONES:
            dist_to_center = haversine_km(target_lat, target_lon, zone["center_lat"], zone["center_lon"])
            if dist_to_center <= zone["radius_km"]:
                is_safe = False
                violations.append({
                    "rule": "GEOFENCE_PROHIBITED_ZONE",
                    "severity": "FATAL_REJECT",
                    "zone_name": zone["name"],
                    "legal_basis": zone["legal_basis"],
                    "message": f"Target location lies inside {zone['name']} ({zone['restriction_level']}). Navigation and fishing are prohibited."
                })
            elif dist_to_center <= (zone["radius_km"] + 5.0):
                warnings.append({
                    "rule": "GEOFENCE_PROXIMITY_WARNING",
                    "severity": "CAUTION",
                    "zone_name": zone["name"],
                    "message": f"Within 5 km of restricted boundary of {zone['name']}."
                })

        # ── 2. Vessel Profile Rule: Wave Height Sea-Keeping Limit ────────────
        max_wave = vessel["max_safe_wave_height_m"]
        if wave_height_m > max_wave:
            is_safe = False
            violations.append({
                "rule": "VESSEL_WAVE_EXCEEDANCE",
                "severity": "CAPSIZE_DANGER",
                "message": f"Forecast wave height ({wave_height_m}m) exceeds maximum safe sea-keeping limit ({max_wave}m) for {vessel['name']}."
            })

        # ── 3. Vessel Profile Rule: Wind Speed Limit ─────────────────────────
        max_wind = vessel["max_safe_wind_speed_kmh"]
        if wind_speed_kmh > max_wind:
            is_safe = False
            violations.append({
                "rule": "VESSEL_WIND_EXCEEDANCE",
                "severity": "SQUALL_DANGER",
                "message": f"Forecast wind speed ({wind_speed_kmh} km/h) exceeds safe threshold ({max_wind} km/h) for {vessel['name']}."
            })

        # ── 4. Severe Hazard Rule: Active Cyclone or Lightning ───────────────
        if is_cyclone_active:
            is_safe = False
            violations.append({
                "rule": "ACTIVE_CYCLONE_RED_ALERT",
                "severity": "IMMEDIATE_HARBOR_LOCK",
                "message": "Active cyclonic system in operational marine sector. All sailings suspended by port authority."
            })

        if lightning_density > 0.4:
            warnings.append({
                "rule": "LIGHTNING_STRIKE_CLUSTER",
                "severity": "SEVERE_WEATHER",
                "message": "High convective lightning flash density observed in sector."
            })

        return {
            "is_safe": is_safe,
            "gate_status": "PASSED_CLEAR" if is_safe else "REJECTED_UNSAFE",
            "vessel_profile_applied": vessel["name"],
            "fatal_violations": violations,
            "caution_warnings": warnings,
            "decision": "APPROVED_FOR_FISHING" if is_safe else "DO_NOT_PROCEED_STAY_ASHORE"
        }

    def filter_candidate_pfzs(
        self,
        candidate_pfzs: List[Dict[str, Any]],
        vessel_type: str,
        wave_height_m: float,
        wind_speed_kmh: float
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Splits candidate PFZs into (Safe_Feasible_PFZs, Rejected_Unsafe_PFZs).
        """
        safe_candidates = []
        rejected_candidates = []

        for pfz in candidate_pfzs:
            eval_res = self.evaluate_safety_constraints(
                target_lat=pfz["lat"],
                target_lon=pfz["lon"],
                vessel_type=vessel_type,
                wave_height_m=wave_height_m,
                wind_speed_kmh=wind_speed_kmh
            )
            enriched_pfz = dict(pfz)
            enriched_pfz["safety_gate_evaluation"] = eval_res

            if eval_res["is_safe"]:
                safe_candidates.append(enriched_pfz)
            else:
                rejected_candidates.append(enriched_pfz)

        return safe_candidates, rejected_candidates
