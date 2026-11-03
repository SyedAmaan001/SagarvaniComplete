"""
Evidence & Provenance Critic (ORCA Architecture - Page 4, 6 & 8)
Builds the "Why this answer?" trail from what was ACTUALLY fetched:
real provider timestamps, computed data age, and a confidence score that is derived
from completeness, freshness and how far the data point is from the requested location.
Nothing here is hardcoded: if a feed was not connected or failed, it is listed as such.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

FRESH_MAX_MIN = 90        # model "current" values are ~15-minutely; older than this is not fresh
STALE_MAX_MIN = 360       # beyond this the data is treated as stale
COASTAL_SNAP_WARN_KM = 10.0


def _age_minutes(valid_time: Optional[str], now: datetime) -> Optional[float]:
    if not valid_time:
        return None
    try:
        return max(0.0, (now - datetime.fromisoformat(valid_time)).total_seconds() / 60.0)
    except ValueError:
        return None


def _status(ok: bool, age_min: Optional[float]) -> str:
    if not ok:
        return "UNAVAILABLE"
    if age_min is None:
        return "UNKNOWN_AGE"
    if age_min <= FRESH_MAX_MIN:
        return f"FRESH (age {age_min:.0f} min)"
    if age_min <= STALE_MAX_MIN:
        return f"AGING (age {age_min / 60:.1f} h)"
    return f"STALE (age {age_min / 60:.1f} h)"


def compute_confidence(gateway_data: Dict[str, Any], now: Optional[datetime] = None) -> float:
    """
    confidence = completeness x freshness x proximity, clipped to [0, 0.95].
      completeness: share of the 6 live parameters that were actually received
      freshness   : 1.0 up to 90 min old, falling linearly to 0.4 at 6 h and beyond
      proximity   : 0.9 if the data cell is >10 km from the requested point (coastal snap)
    Capped below 1.0 because these are model outputs, not in-situ observations.
    """
    now = now or datetime.now(timezone.utc)
    received = gateway_data.get("records_count", 0)
    completeness = min(1.0, received / 6.0)

    ages = [a for a in (_age_minutes(r.get("valid_time"), now)
                        for r in gateway_data.get("normalized_records", [])) if a is not None]
    if not ages:
        freshness = 0.4
    else:
        worst = max(ages)
        if worst <= FRESH_MAX_MIN:
            freshness = 1.0
        elif worst >= STALE_MAX_MIN:
            freshness = 0.4
        else:
            freshness = 1.0 - 0.6 * (worst - FRESH_MAX_MIN) / (STALE_MAX_MIN - FRESH_MAX_MIN)

    loc = gateway_data.get("data_location") or {}
    proximity = 0.9 if loc.get("distance_from_query_km", 0) > COASTAL_SNAP_WARN_KM else 1.0

    return round(min(0.95, completeness * freshness * proximity), 2)


class EvidenceEngine:
    name: str = "Evidence & Provenance Critic"

    def build_evidence_trail(
        self,
        gateway_data: Dict[str, Any],
        safety_eval: Dict[str, Any],
        ranked_pfz: List[Dict[str, Any]],
        rejected_pfz: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)

        evidence_items: List[Dict[str, Any]] = []
        for src in gateway_data.get("sources", []):
            age = _age_minutes(src.get("valid_time"), now)
            evidence_items.append({
                "source": src["source"],
                "timestamp": src.get("valid_time") or src.get("fetched_at"),
                "fetched_at": src.get("fetched_at"),
                "status": _status(src.get("ok", False), age),
                "data_point": ", ".join(p.replace("_", " ").title() for p in src.get("parameters", [])),
                "verified": bool(src.get("ok")),
            })

        evidence_items.append({
            "source": "Static reference geofence layer (curated in code)",
            "timestamp": None,
            "status": "STATIC (verify against official notifications)",
            "data_point": "Restricted areas and protected zones",
            "verified": False,
        })
        for feed in gateway_data.get("unavailable_feeds", []):
            evidence_items.append({
                "source": feed["needs"],
                "timestamp": None,
                "status": "NOT CONNECTED",
                "data_point": feed["parameter"].replace("_", " ").title(),
                "verified": False,
            })

        reasons: List[str] = []
        if gateway_data.get("critical_missing"):
            reasons.append("Live wave/wind data could not be retrieved, so safety could not be verified.")
        elif safety_eval.get("is_safe"):
            reasons.append(f"Live sea state is within limits for {safety_eval.get('vessel_profile_applied')}.")
            if ranked_pfz:
                top = ranked_pfz[0]
                reasons.append(
                    f"Strongest thermal-front candidate: {top['name']} ({top['distance_from_user_km']} km away, "
                    f"SST gradient {top.get('sst_gradient_c_per_km')} °C/km). "
                    "This is model-derived, not an official INCOIS PFZ."
                )
        else:
            for v in safety_eval.get("fatal_violations", []):
                reasons.append(f"SAFETY GATE: {v['message']}")

        if rejected_pfz:
            names = ", ".join(z["name"] for z in rejected_pfz[:3])
            reasons.append(f"{len(rejected_pfz)} candidate zone(s) excluded by the safety gate: {names}.")

        if gateway_data.get("data_location") and \
                gateway_data["data_location"].get("distance_from_query_km", 0) > COASTAL_SNAP_WARN_KM:
            reasons.append(
                f"Conditions are from the nearest ocean cell, "
                f"{gateway_data['data_location']['distance_from_query_km']} km from your position."
            )

        confidence = compute_confidence(gateway_data, now)
        prov = gateway_data.get("provenance", {})
        return {
            "evidence_trail": evidence_items,
            "provenance_summary": {
                "open_meteo_marine": prov.get("open_meteo_marine"),
                "open_meteo_weather": prov.get("open_meteo_weather"),
                "official_incois_pfz": prov.get("incois"),
                "imd": prov.get("imd"),
                "overall_data_confidence": confidence,
                "confidence_basis": "completeness x freshness x proximity (model data, capped at 0.95)",
            },
            "why_this_answer": reasons,
            "generated_at": now.isoformat(),
        }
