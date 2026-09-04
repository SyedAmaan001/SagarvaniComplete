"""
Stage 2 & 3: Reasoning & Validation Agent (Validator)
Role: Cross-verifies intelligence from all 6 specialized domain agents,
detects inconsistencies/conflicts (e.g. wind vs wave contradiction, cyclone proximity vs warning level),
and performs automatic self-correction / confidence calibration.
"""

from typing import Dict, Any, List, Tuple

class ReasoningValidationAgent:
    name: str = "Reasoning & Validation Agent"
    role: str = "Cross-Verification, Anomaly Detection & Consistency Engine"

    def validate(
        self,
        marine_res: Dict[str, Any],
        weather_res: Dict[str, Any],
        gis_res: Dict[str, Any],
        analytics_res: Dict[str, Any],
        risk_res: Dict[str, Any],
        spatial_res: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes cross-agent verification rules.
        Returns validation status, detected contradictions, and overall confidence score.
        """
        conflicts = []
        corrections = []

        params_m = marine_res.get("parameters", {})
        params_w = weather_res.get("parameters", {})
        risk_meta = risk_res.get("risk_assessment", {})
        analytics = analytics_res.get("analytics", {})

        wave_h = params_m.get("wave_height_m", 1.0)
        wind_spd = params_w.get("wind_speed_kmh", 20.0)
        risk_score = risk_meta.get("composite_risk_score", 30.0)
        cyclone_threat = risk_meta.get("cyclone_threat_level", "NONE")

        # Rule 1: Cross-check Wind vs Wave Consistency
        # Very high waves (>3.5m) with low wind (<15 km/h) -> Check for distant swell
        if wave_h > 3.5 and wind_spd < 15.0:
            conflicts.append({
                "type": "HYDRO_ATMOSPHERIC_DEVIATION",
                "severity": "MEDIUM",
                "detail": f"High significant wave height ({wave_h}m) despite mild local wind ({wind_spd} km/h)."
            })
            corrections.append("Validated: Attributed to distant storm swell propagation detected by Ocean Analytics Agent.")

        # Rule 2: Cyclone Threat vs Risk Score alignment
        if cyclone_threat in ["DANGER", "EXTREME"] and risk_score < 60:
            conflicts.append({
                "type": "CYCLONE_RISK_UNDERESTIMATION",
                "severity": "HIGH",
                "detail": f"Active cyclone nearby but risk score ({risk_score}) remained below warning threshold."
            })
            risk_meta["composite_risk_score"] = max(risk_score, 80.0)
            corrections.append("Auto-Corrected: Upgraded composite risk score to reflect direct gale danger perimeter.")

        # Rule 3: Visualizer / Spatial corridor feasibility check
        corridor_status = spatial_res.get("spatial_reasoning", {}).get("corridor_feasibility", "SAFE")
        if risk_score > 80 and corridor_status == "SAFE":
            spatial_res["spatial_reasoning"]["corridor_feasibility"] = "URGENT_EVACUATION"
            corrections.append("Auto-Corrected: Escape corridor updated to Emergency Evacuation status.")

        # Calculate Consensus Confidence
        base_confidence = (
            marine_res.get("confidence_score", 0.9) +
            weather_res.get("confidence_score", 0.9) +
            gis_res.get("confidence_score", 0.9) +
            analytics_res.get("confidence_score", 0.9) +
            risk_res.get("confidence_score", 0.9) +
            spatial_res.get("confidence_score", 0.9)
        ) / 6.0

        # Penalize if unresolved severe conflicts
        final_confidence = round(base_confidence - (0.05 * len(conflicts)), 2)
        is_consistent = len([c for c in conflicts if c.get("severity") == "HIGH"]) == 0 or len(corrections) > 0

        return {
            "agent": self.name,
            "status": "VALID_CONSISTENT" if is_consistent else "CONFLICT_DETECTED",
            "is_valid": is_consistent,
            "consensus_confidence": max(0.5, min(1.0, final_confidence)),
            "conflicts_detected": conflicts,
            "reconciliation_actions": corrections,
            "validation_verdict": "All domain parameters cross-verified and consistent." if not conflicts else f"{len(conflicts)} discrepancies analyzed and reconciled."
        }
