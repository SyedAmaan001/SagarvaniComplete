"""
ORCA Complete 10-Step Pipeline Engine (SIH26176 Reference - Page 3 & 4)
Orchestrates:
  Step 1: User Query
  Step 2: Interpret Context (Location, Time, Vessel Profile, Intent)
  Step 3: Plan (Task Graph)
  Step 4: Retrieve (Authoritative feeds via Marine Data Gateway)
  Step 5: Normalize (Canonical data records with provenance)
  Step 6: Reason (Spatial, temporal & hydrodynamic anomaly fusion)
  Step 7: Constrain (Hard Safety Gate — deterministic geofence & vessel rules)
  Step 8: Rank (Multi-Objective utility ranking of feasible PFZs)
  Step 9: Verify (Evidence trail & source freshness audit)
  Step 10: Respond (Explainable answer + GeoJSON map + Kannada/English bilingual decision)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta

from gateway.marine_data_gateway import MarineDataGateway
from engine.safety_gate import HardSafetyGate
from engine.multi_objective_ranker import MultiObjectiveRanker
from engine.evidence_engine import EvidenceEngine
from processors import live_data
from processors.weather_processor import _sea_state
from utils.geo_utils import (
    make_point_geojson, make_circle_geojson, make_feature_collection,
    compute_safe_detour_route, point_to_segment_distance_km
)
from agents.conversation_agent import ConversationAgent

IST = timezone(timedelta(hours=5, minutes=30))


class OrcaPipeline:
    def __init__(self):
        self.gateway = MarineDataGateway()
        self.safety_gate = HardSafetyGate()
        self.ranker = MultiObjectiveRanker()
        self.evidence_engine = EvidenceEngine()
        self.conversation_agent = ConversationAgent()

    def run(
        self,
        lat: float = 13.35,
        lon: float = 74.70, # Default: Malpe / Karnataka Coast
        vessel_type: str = "motorized_craft",
        language: str = "en",
        user_intent: str = "safe_fishing_advisory",
        departure_time: str = "Tomorrow 05:00 AM",
        max_range_km: float = 50.0
    ) -> Dict[str, Any]:
        start_time = datetime.now(timezone.utc)

        # Trace record for 10-step pipeline animation & verification
        steps_trace = [
            {"step": 1, "name": "Query Received", "status": "COMPLETED", "detail": f"Intent: {user_intent} | Pos: {lat}°N, {lon}°E"},
            {"step": 2, "name": "Intent Interpreted", "status": "COMPLETED", "detail": f"Vessel: {vessel_type} | Dep: {departure_time} | Range: {max_range_km}km"},
            {"step": 3, "name": "Plan Generated", "status": "COMPLETED", "detail": "Executing Minimal Task Graph"},
            {"step": 4, "name": "Data Retrieved", "status": "IN_PROGRESS", "detail": "Open-Meteo Marine + Weather (live)"},
        ]

        # ── Step 4 & 5: Retrieve & Normalize via Marine Data Gateway (live) ───
        # One snapshot radius is used for conditions and candidate zones so the
        # provider is only called once (results are cached for ~10 minutes).
        radius_km = max(max_range_km, 40.0)
        gateway_data = self.gateway.fetch_normalized_marine_record(lat, lon, radius_km=radius_km)
        vessel_info = self.gateway.get_vessel_profile(vessel_type)
        restricted_zones = self.gateway.get_restricted_marine_geofences()

        if gateway_data["critical_missing"]:
            steps_trace[3]["status"] = "FAILED"
            steps_trace[3]["detail"] = "Live wave/wind data unavailable: " + ", ".join(gateway_data["critical_missing"])
            return self._data_unavailable_result(
                lat, lon, vessel_info, departure_time, max_range_km, user_intent,
                gateway_data, steps_trace, restricted_zones, language, start_time
            )
        steps_trace[3]["status"] = "COMPLETED"

        raw_pfzs = [
            z for z in self.gateway.get_candidate_pfz_zones(lat, lon, max_range_km=radius_km)
            if z["distance_from_user_km"] <= max_range_km
        ]

        steps_trace.append({"step": 5, "name": "Normalised", "status": "COMPLETED",
                            "detail": f"{len(gateway_data['normalized_records'])} canonical ocean records"})

        records_map = {r["parameter"]: r["value"] for r in gateway_data["normalized_records"]}
        wave_h = records_map["SIGNIFICANT_WAVE_HEIGHT"]
        wind_kmh = records_map["WIND_SPEED_10M"]
        current_spd = records_map.get("SURFACE_OCEAN_CURRENT_VELOCITY")
        sst_c = records_map.get("SEA_SURFACE_TEMPERATURE")

        # ── Step 6: Reason across oceanographic & meteorological state ───────
        cur_txt = f", Current {current_spd}m/s" if current_spd is not None else ""
        steps_trace.append({"step": 6, "name": "Reasoning", "status": "COMPLETED",
                            "detail": f"Wave {wave_h}m, Wind {wind_kmh}km/h{cur_txt}"})

        # ── Step 7: Constrain (Hard Safety Gate) ─────────────────────────────
        # No live cyclone / lightning feed is connected, so those rules are not evaluated.
        # Severe wind and sea state are still caught by the vessel wave/wind limits.
        departure_safety = self.safety_gate.evaluate_safety_constraints(
            target_lat=lat,
            target_lon=lon,
            vessel_type=vessel_type,
            wave_height_m=wave_h,
            wind_speed_kmh=wind_kmh,
            is_cyclone_active=False,
            lightning_density=0.0
        )

        safe_pfzs, rejected_pfzs = self.safety_gate.filter_candidate_pfzs(
            candidate_pfzs=raw_pfzs,
            vessel_type=vessel_type,
            wave_height_m=wave_h,
            wind_speed_kmh=wind_kmh
        )
        steps_trace.append({"step": 7, "name": "Safety Constrained", "status": "COMPLETED", "detail": f"Gate: {departure_safety['gate_status']} | Safe zones: {len(safe_pfzs)} | Rejected: {len(rejected_pfzs)}"})

        # ── Step 8: Rank Feasible Safe Candidates ────────────────────────────
        ranked_pfzs = self.ranker.rank_candidates(
            safe_candidates=safe_pfzs,
            user_lat=lat,
            user_lon=lon,
            vessel_type=vessel_type
        )

        # Departure window from the real hourly forecast (not a fixed time of day)
        outlook = self.gateway.get_hourly_outlook(lat, lon)
        best_window = self._best_window(outlook, vessel_info)
        for z in ranked_pfzs:
            z["recommended_departure_window"] = best_window
        steps_trace.append({"step": 8, "name": "Ranked", "status": "COMPLETED", "detail": f"Top Zone: {ranked_pfzs[0]['name'] if ranked_pfzs else 'None'}"})

        # ── Step 9: Verify (Evidence Trail & Freshness Audit) ─────────────────
        evidence_audit = self.evidence_engine.build_evidence_trail(
            gateway_data=gateway_data,
            safety_eval=departure_safety,
            ranked_pfz=ranked_pfzs,
            rejected_pfz=rejected_pfzs
        )
        confidence = evidence_audit["provenance_summary"]["overall_data_confidence"]
        steps_trace.append({"step": 9, "name": "Verified", "status": "COMPLETED", "detail": f"Freshness and provenance audited (confidence {confidence})"})

        # ── Safest Route Calculation with Obstacle Avoidance ──────────────────
        route_info = None
        top_pfz = ranked_pfzs[0] if ranked_pfzs else None
        if top_pfz:
            route_info = compute_safe_detour_route(
                start_lat=lat,
                start_lon=lon,
                end_lat=top_pfz["lat"],
                end_lon=top_pfz["lon"],
                restricted_zones=restricted_zones,
                safety_buffer_km=3.0
            )
        route_intersections = (
            self._count_route_intersections(route_info["route_coordinates"], restricted_zones) if route_info else 0
        )

        # ── Step 10: Respond (Visual Cartography + Explainable Delivery) ─────
        map_features = []

        map_features.append(make_point_geojson(lat, lon, {
            "type": "USER_BASE_LOCATION",
            "title": f"📍 Departure Point ({lat}°N, {lon}°E)",
            "vessel": vessel_info["name"],
            "safety_status": departure_safety["gate_status"]
        }))

        for pfz in raw_pfzs:
            is_rejected = any(r.get("pfz_id") == pfz.get("pfz_id") for r in rejected_pfzs)
            map_features.append(make_point_geojson(pfz["lat"], pfz["lon"], {
                "type": "PFZ_CANDIDATE",
                "title": f"🐟 {pfz['name']} ({'REJECTED' if is_rejected else 'FEASIBLE'})",
                "productivity_score": pfz.get("productivity_score"),
                "score_basis": pfz.get("score_basis"),
                "chlorophyll": _fmt(pfz.get("chlorophyll_mg_m3"), "mg/m³", "n/a (no live feed)"),
                "sst": _fmt(pfz.get("sst_c"), "°C"),
                "sst_gradient": _fmt(pfz.get("sst_gradient_c_per_km"), "°C/km"),
                "is_rejected": is_rejected,
                "color": "#ef4444" if is_rejected else "#10b981"
            }))

        if top_pfz:
            map_features.append(make_point_geojson(top_pfz["lat"], top_pfz["lon"], {
                "type": "RECOMMENDED_PFZ_ZONE",
                "title": f"🎯 RECOMMENDED: {top_pfz['name']} ({top_pfz['badge']})",
                "productivity_score": top_pfz["productivity_score"],
                "rank_score": top_pfz["rank_score"],
                "chlorophyll": _fmt(top_pfz.get("chlorophyll_mg_m3"), "mg/m³", "n/a (no live feed)"),
                "sst": _fmt(top_pfz.get("sst_c"), "°C"),
                "species": ", ".join(top_pfz.get("species_likely", [])) or "n/a",
                "distance_km": route_info["safe_route_distance_km"] if route_info else top_pfz["distance_from_user_km"],
                "color": "#22c55e"
            }))
            map_features.append(make_circle_geojson(top_pfz["lat"], top_pfz["lon"], 6.0, {
                "type": "PFZ_PERIMETER",
                "title": f"SST Thermal Front ({top_pfz['name']})",
                "color": "#22c55e",
                "fill_opacity": 0.20
            }))

            if route_info:
                map_features.append({
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": route_info["route_coordinates"]},
                    "properties": {
                        "type": "SAFE_NAVIGATION_COURSE",
                        "title": f"Safest Navigation Course ({route_info['safe_route_distance_km']} km)",
                        "stroke_color": "#00f2ff",
                        "stroke_weight": 4,
                        "is_detour": route_info["is_detour_required"],
                        "avoided_zones": [z["zone_name"] for z in route_info["avoided_zones"]],
                        "transit_time_hours": round(route_info["safe_route_distance_km"] / 18.0, 1)
                    }
                })
                if route_info["is_detour_required"]:
                    map_features.append({
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": route_info["direct_coordinates"]},
                        "properties": {
                            "type": "AVOIDED_DIRECT_SEGMENT",
                            "title": "Blocked Direct Course (Crosses Restricted Hazard Geofence)",
                            "stroke_color": "#ef4444",
                            "stroke_dash": "5, 5",
                            "warning": "Restricted sanctuary / firing range intersection avoided"
                        }
                    })

        for r_zone in restricted_zones:
            map_features.append(make_circle_geojson(r_zone["center_lat"], r_zone["center_lon"], r_zone["radius_km"], {
                "type": "RESTRICTED_AVOIDANCE_GEOFENCE",
                "title": f"⛔ RESTRICTED: {r_zone['name']}",
                "restriction_level": r_zone["restriction_level"],
                "legal_basis": r_zone["legal_basis"],
                "color": "#dc2626",
                "fill_opacity": 0.35
            }))
            map_features.append(make_point_geojson(r_zone["center_lat"], r_zone["center_lon"], {
                "type": "RESTRICTED_CENTER_PIN",
                "title": f"⛔ {r_zone['name']}",
                "color": "#dc2626"
            }))

        steps_trace.append({"step": 10, "name": "Advisory Delivered", "status": "COMPLETED", "detail": "Decision package and cartographic layers rendered"})

        # Verdict
        if not departure_safety["is_safe"]:
            verdict = "AVOID"
            verdict_label = "AVOID (STAY ASHORE)"
            why_text = f"Safety Gate Rejection: {departure_safety['fatal_violations'][0]['message'] if departure_safety['fatal_violations'] else 'Unfavorable sea conditions'}"
        elif not ranked_pfzs:
            verdict = "REASSESS"
            verdict_label = "REASSESS (NO SAFE FRONT FOUND)"
            why_text = "Sea state is within limits, but no safe thermal-front candidate was found within your operating range."
        else:
            verdict = "GO"
            verdict_label = "GO (FAVORABLE)"
            why_text = (f"Live waves {wave_h} m and wind {wind_kmh} km/h are within limits. "
                        f"Strongest SST front candidate: {top_pfz['name']} ({top_pfz['distance_from_user_km']} km).")

        safe_route_dist = route_info["safe_route_distance_km"] if route_info else (top_pfz["distance_from_user_km"] if top_pfz else 0.0)
        avoided = [z["zone_name"] for z in route_info["avoided_zones"]] if route_info else []
        conditions = {
            "wave_m": wave_h,
            "wind_kmh": wind_kmh,
            "current_ms": current_spd,
            "current_knots": round(current_spd * 1.94384, 2) if current_spd is not None else None,
            "sst_c": sst_c,
            "sea_state": _sea_state(wave_h),
            "data_location": gateway_data.get("data_location"),
        }
        decision_package = {
            "verdict": verdict,
            "verdict_label": verdict_label,
            "best_zone": top_pfz["name"] if top_pfz else "None",
            "recommended_zone": top_pfz["name"] if top_pfz else "None",
            "best_zone_id": top_pfz.get("pfz_id") if top_pfz else None,
            "best_window": best_window,
            "safety_score": self._safety_score(departure_safety["is_safe"], wave_h, wind_kmh, vessel_info),
            "safety_gate": departure_safety["gate_status"],
            "fishing_value": top_pfz["productivity_score"] if top_pfz else 0,
            "confidence": confidence,
            "route_km": safe_route_dist,
            "transit_time_hours": round(safe_route_dist / 18.0, 1) if safe_route_dist else 0.0,
            "restricted_intersections": route_intersections,
            "route_warning": ("Computed route still intersects a restricted zone - do not follow it."
                              if route_intersections else None),
            "detour_taken": route_info["is_detour_required"] if route_info else False,
            "avoided_zones": avoided,
            "conditions": conditions,
            "why": why_text
        }

        decision_meta_for_translation = {
            "verdict": verdict,
            "best_zone": decision_package["best_zone"],
            "safety_score": decision_package["safety_score"],
            "fishing_score": decision_package["fishing_value"],
            "route_km": decision_package["route_km"],
            "wave_h": wave_h,
            "wind_kmh": wind_kmh,
            "vessel": vessel_info["name"],
            "why": why_text,
            "avoided_zones": avoided,
        }

        target_lang = language.lower()
        if target_lang == "both":
            target_lang = "kn" # Default regional in both mode

        regional_advisory = self.conversation_agent.translate_advisory(decision_meta_for_translation, target_lang)
        english_advisory = self.conversation_agent.translate_advisory(decision_meta_for_translation, "en")

        elapsed_ms = round((datetime.now(timezone.utc) - start_time).total_seconds() * 1000, 1)

        return {
            "pipeline": "ORCA 10-Step Marine Intelligence Engine",
            "execution_status": "SUCCESS",
            "latency_ms": elapsed_ms,
            "context": {
                "location": {"lat": lat, "lon": lon},
                "vessel_profile": vessel_info["name"],
                "departure_time": departure_time,
                "assessed_for": "current live conditions (departure_time is not yet used to pick a forecast hour)",
                "max_range_km": max_range_km,
                "intent": user_intent,
                "timestamp": now_iso()
            },
            "decision_package": decision_package,
            "situation_metrics": {
                "recommendation_verdict": verdict_label,
                "fishing_suitability": "CANDIDATES_FOUND" if ranked_pfzs else "NONE_FOUND",
                "marine_safety": "SAFE" if departure_safety["is_safe"] else "DANGER",
                "restrictions": "RESTRICTED_AREAS_EXCLUDED" if rejected_pfzs else "CLEAR",
                "best_window": best_window,
                "safety_score": decision_package["safety_score"],
                "fishing_value_score": decision_package["fishing_value"],
                "data_confidence": confidence
            },
            "data_status": {
                "live": True,
                "fetched_at": gateway_data["timestamp"],
                "data_location": gateway_data.get("data_location"),
                "unavailable_parameters": gateway_data["unavailable_parameters"],
                "not_connected": [f["parameter"] for f in gateway_data["unavailable_feeds"]],
            },
            "hard_safety_gate": departure_safety,
            "candidate_pfz_count": len(raw_pfzs),
            "safe_ranked_pfzs": ranked_pfzs,
            "rejected_unsafe_pfzs": rejected_pfzs,
            "route_calculation": route_info,
            "evidence_trail": evidence_audit,
            "steps_trace": steps_trace,
            "cartography": {
                "geojson": make_feature_collection(map_features),
                "center": [lat, lon],
                "zoom": 9,
                "distance_km": safe_route_dist,
            },
            "multilingual_advisory": {
                "english": english_advisory["body"],
                "regional": regional_advisory["body"],
                "active_language": target_lang,
                "language_name": regional_advisory.get("lang", target_lang)
            }
        }

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _safety_score(is_safe: bool, wave_h: float, wind_kmh: float, vessel: Dict[str, Any]) -> int:
        """
        0-100 from the margin to the vessel's limits.
        Passing the gate: 40 (at the limit) to 100 (calm). Failing it: at most 39.
        """
        worst = max(wave_h / vessel["max_safe_wave_height_m"], wind_kmh / vessel["max_safe_wind_speed_kmh"])
        if is_safe:
            return round(40 + 60 * max(0.0, 1.0 - worst))
        return max(5, round(39 - 30 * min(1.0, max(0.0, worst - 1.0))))

    @staticmethod
    def _count_route_intersections(route_coords: List[List[float]], zones: List[Dict[str, Any]]) -> int:
        """Number of restricted zones the final route actually passes through."""
        count = 0
        for z in zones:
            for a, b in zip(route_coords, route_coords[1:]):
                d, _, _ = point_to_segment_distance_km(z["center_lat"], z["center_lon"], a[1], a[0], b[1], b[0])
                if d < z["radius_km"]:
                    count += 1
                    break
        return count

    @staticmethod
    def _best_window(outlook: Dict[str, Any], vessel: Dict[str, Any]) -> str:
        if outlook.get("error") or not outlook.get("hours"):
            return "Forecast unavailable"
        windows = live_data.safe_windows(
            outlook["hours"], vessel["max_safe_wave_height_m"], vessel["max_safe_wind_speed_kmh"]
        )
        if not windows:
            return "No safe window in the next 48 h"
        w = windows[0]
        start = datetime.fromisoformat(w["start_utc"]).astimezone(IST)
        end = datetime.fromisoformat(w["end_utc"]).astimezone(IST)
        end_fmt = f"{end:%H:%M}" if end.date() == start.date() else f"{end:%a %d %b %H:%M}"
        return f"{start:%a %d %b %H:%M} – {end_fmt} IST ({w['hours']} h within vessel limits)"

    def _data_unavailable_result(self, lat, lon, vessel_info, departure_time, max_range_km, user_intent,
                                 gateway_data, steps_trace, restricted_zones, language, start_time):
        """Never guess: with no live wave/wind data the only honest answer is 'cannot verify'."""
        evidence = self.evidence_engine.build_evidence_trail(gateway_data, {"is_safe": False}, [], [])
        why = ("Live wave/wind data could not be retrieved, so safety cannot be verified. "
               "Do not rely on this result; check official INCOIS/IMD bulletins before going to sea.")
        map_features = [make_point_geojson(lat, lon, {
            "type": "USER_BASE_LOCATION", "title": f"📍 Departure Point ({lat}°N, {lon}°E)",
            "vessel": vessel_info["name"], "safety_status": "UNVERIFIED"})]
        for r in restricted_zones:
            map_features.append(make_circle_geojson(r["center_lat"], r["center_lon"], r["radius_km"], {
                "type": "RESTRICTED_AVOIDANCE_GEOFENCE", "title": f"⛔ RESTRICTED: {r['name']}",
                "restriction_level": r["restriction_level"], "legal_basis": r["legal_basis"],
                "color": "#dc2626", "fill_opacity": 0.35}))
        target = "en" if language.lower() == "both" else language.lower()
        meta = {"verdict": "REASSESS", "best_zone": "None", "safety_score": 0, "fishing_score": 0,
                "route_km": 0, "wave_h": "n/a", "wind_kmh": "n/a", "vessel": vessel_info["name"],
                "why": why, "avoided_zones": []}
        regional = self.conversation_agent.translate_advisory(meta, target)
        english = self.conversation_agent.translate_advisory(meta, "en")
        return {
            "pipeline": "ORCA 10-Step Marine Intelligence Engine",
            "execution_status": "DATA_UNAVAILABLE",
            "latency_ms": round((datetime.now(timezone.utc) - start_time).total_seconds() * 1000, 1),
            "context": {"location": {"lat": lat, "lon": lon}, "vessel_profile": vessel_info["name"],
                        "departure_time": departure_time, "max_range_km": max_range_km,
                        "intent": user_intent, "timestamp": now_iso()},
            "decision_package": {
                "verdict": "REASSESS", "verdict_label": "REASSESS (LIVE DATA UNAVAILABLE)",
                "best_zone": "None", "recommended_zone": "None", "best_zone_id": None,
                "best_window": "Forecast unavailable", "safety_score": 0, "safety_gate": "UNVERIFIED",
                "fishing_value": 0, "confidence": 0.0, "route_km": 0.0, "transit_time_hours": 0.0,
                "restricted_intersections": 0, "route_warning": None, "detour_taken": False,
                "avoided_zones": [], "conditions": {}, "why": why},
            "data_status": {"live": False, "fetched_at": gateway_data["timestamp"],
                            "critical_missing": gateway_data["critical_missing"],
                            "errors": gateway_data.get("errors", [])},
            "hard_safety_gate": None,
            "candidate_pfz_count": 0, "safe_ranked_pfzs": [], "rejected_unsafe_pfzs": [],
            "route_calculation": None, "evidence_trail": evidence, "steps_trace": steps_trace,
            "cartography": {"geojson": make_feature_collection(map_features), "center": [lat, lon], "zoom": 9,
                            "distance_km": 0},
            "multilingual_advisory": {"english": english["body"], "regional": regional["body"],
                                      "active_language": target, "language_name": regional.get("lang", target)},
        }


def _fmt(value, unit: str = "", missing: str = "n/a") -> str:
    return f"{value} {unit}".strip() if value is not None else missing


def now_iso():
    return datetime.now(timezone.utc).isoformat()
