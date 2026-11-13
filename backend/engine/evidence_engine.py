"""
Evidence & Provenance Critic Agent (ORCA Architecture - Page 4, 6 & 8)
Role: Generates the "Why this answer?" transparent evidence trail with source timestamps,
freshness verification, sensor provenance, and conflict validation metrics.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone

class EvidenceEngine:
    name: str = "Evidence & Provenance Critic"

    def build_evidence_trail(
        self,
        gateway_data: Dict[str, Any],
        safety_eval: Dict[str, Any],
        ranked_pfz: List[Dict[str, Any]],
        rejected_pfz: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesizes authoritative evidence entries with ISO timestamps, latency, and sensor modes.
        """
        now = datetime.now(timezone.utc)
        integrity = gateway_data.get("data_integrity", {})
        fetched = gateway_data.get("timestamp", now.isoformat())

        def _live(flag: bool, live_text: str):
            return live_text if flag else "UNAVAILABLE (no live data)"

        evidence_items = [
            {
                "source": "Open-Meteo Marine API (model forecast)",
                "timestamp": fetched,
                "status": _live(integrity.get("wave_live", False), "FETCHED THIS REQUEST"),
                "data_point": "Significant wave height",
                "verified": bool(integrity.get("wave_live", False)),
            },
            {
                "source": "Open-Meteo Weather API (model forecast)",
                "timestamp": fetched,
                "status": _live(integrity.get("wind_live", False), "FETCHED THIS REQUEST"),
                "data_point": "10 m wind speed",
                "verified": bool(integrity.get("wind_live", False)),
            },
            {
                "source": "MOSDAC ISRO ocean-current NetCDF (archived file)",
                "timestamp": "archive file - not real-time",
                "status": "ARCHIVE" if integrity.get("current_live") else "UNAVAILABLE",
                "data_point": "Surface current vector",
                "verified": False,
            },
            {
                "source": "Static reference registry (PFZ, SST, chlorophyll, lightning, tide)",
                "timestamp": "n/a",
                "status": "STATIC - NOT LIVE INCOIS/IMD/ISRO DATA",
                "data_point": "Potential fishing zones and ocean-colour values",
                "verified": False,
            },
            {
                "source": "Bhuvan NRSC LULC & Maritime Geofence Layer (reference geofences)",
                "timestamp": "2024-2025 Release",
                "status": "REFERENCE",
                "data_point": "Restricted zones, sanctuaries, territorial baseline",
                "verified": False,
            },
        ]

        # Reason formulation
        reasons = []
        if safety_eval.get("is_safe"):
            reasons.append(f"Marine conditions verified within safe operational limits for {safety_eval.get('vessel_profile_applied')}.")
            if ranked_pfz:
                top = ranked_pfz[0]
                reasons.append(f"Optimal Potential Fishing Zone identified at {top['name']} ({top['distance_from_user_km']} km away) with high Chlorophyll-a ({top['chlorophyll_mg_m3']} mg/m³).")
        else:
            for v in safety_eval.get("fatal_violations", []):
                reasons.append(f"CRITICAL SAFETY GATE ACTIVATED: {v['message']}")

        if rejected_pfz:
            reasons.append(f"{len(rejected_pfz)} high-fish candidate zone(s) excluded due to intersecting restricted sanctuary / hazard geofences (e.g. Netrani MPA).")

        return {
            "evidence_trail": evidence_items,
            "provenance_summary": {
                "live_sea_state": bool(integrity.get("conditions_live", False)),
                "uses_static_reference_data": True,
                "overall_data_confidence": 0.6 if integrity.get("conditions_live") else 0.0
            },
            "why_this_answer": reasons,
            "generated_at": now.isoformat()
        }
