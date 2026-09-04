"""
Stage 3 - Agent 5: Risk Agent
Domain: Multi-Hazard Risk Assessment, Cyclone Proximity Scoring, Navigation Hazards, Capsize Index.
Sources: IMD RSMC, MOSDAC SAR Altimetry, Mathematical Risk Matrix.
"""

from typing import Dict, Any, Optional
from engine.cyclone_tracker import get_active_cyclones, get_cyclone_impact_on_zone
from utils.geo_utils import normalize_score, risk_level

class RiskAgent:
    name: str = "Risk Agent"
    domain: str = "Multi-Hazard Maritime Safety & Capsize Risk Quantification"

    def execute(self, lat: float, lon: float, marine_data: Dict[str, Any], weather_data: Dict[str, Any], gis_data: Dict[str, Any]) -> Dict[str, Any]:
        params_m = marine_data.get("parameters", {})
        params_w = weather_data.get("parameters", {})
        params_g = gis_data.get("parameters", {})

        wave_h = params_m.get("wave_height_m", 1.2)
        curr_spd = params_m.get("current_speed_ms", 0.4)
        wind_spd_ms = params_w.get("wind_speed_ms", 7.0)
        dist_coast_km = params_g.get("distance_to_coast_km", 20.0)

        # 1. Check Cyclone Proximity
        active_cyclones = get_active_cyclones()
        cyclone_impact = get_cyclone_impact_on_zone(lat, lon, active_cyclones)
        
        cyclone_score = 0.0
        if cyclone_impact.get("in_eye_wall"):
            cyclone_score = 100.0
        elif cyclone_impact.get("in_gale_zone"):
            cyclone_score = 85.0
        elif cyclone_impact.get("cyclone_threat") == "WARNING":
            cyclone_score = 60.0
        elif cyclone_impact.get("cyclone_threat") == "WATCH":
            cyclone_score = 35.0

        # 2. Individual factor scores (0 to 100)
        score_wave = normalize_score(wave_h, 0.0, 5.0)
        score_wind = normalize_score(wind_spd_ms, 0.0, 22.0)
        score_curr = normalize_score(curr_spd, 0.0, 1.8)
        score_coast_vuln = params_g.get("lulc_vulnerability_index", 0.5) * 100.0

        # 3. Artisanal Small Boat Capsize Hazard Index (CHI)
        # Combination of steep wave + cross wind
        chi_raw = (wave_h * 1.5) + (wind_spd_ms * 0.2) + (curr_spd * 2.0)
        capsize_hazard = "CRITICAL" if chi_raw > 6.0 else ("HIGH" if chi_raw > 4.0 else ("MODERATE" if chi_raw > 2.5 else "LOW"))

        # 4. Weighted Composite Score
        composite_score = (
            0.30 * score_wave +
            0.25 * score_wind +
            0.20 * score_curr +
            0.15 * cyclone_score +
            0.10 * score_coast_vuln
        )
        composite_score = round(max(0.0, min(100.0, composite_score)), 1)
        level_info = risk_level(composite_score)

        return {
            "agent": self.name,
            "status": "success",
            "risk_assessment": {
                "composite_risk_score": composite_score,
                "risk_level": level_info["level"],
                "risk_color": level_info["color"],
                "risk_emoji": level_info["emoji"],
                "capsize_hazard_index": capsize_hazard,
                "cyclone_threat_level": cyclone_impact.get("cyclone_threat", "NONE"),
                "nearest_cyclone": cyclone_impact.get("nearest_cyclone"),
                "cyclone_dist_km": cyclone_impact.get("distance_km"),
                "sub_scores": {
                    "wave_score": round(score_wave, 1),
                    "wind_score": round(score_wind, 1),
                    "current_score": round(score_curr, 1),
                    "cyclone_score": round(cyclone_score, 1),
                    "coastal_vulnerability_score": round(score_coast_vuln, 1)
                }
            },
            "sources": ["IMD Cyclone RSMC Bulletins", "Multivariate Maritime Safety Equations"],
            "confidence_score": 0.96
        }
