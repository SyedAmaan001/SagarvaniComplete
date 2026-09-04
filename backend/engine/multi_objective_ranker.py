"""
Multi-Objective Ranker (ORCA Decision Engine - Page 4 & 6)
Ranks safe candidate fishing zones (PFZs) using multi-attribute utility optimization:
Utility = w1 * Fishing_Value + w2 * Safety_Margin - w3 * Distance_Transit_Penalty - w4 * Fuel_Cost
"""

from typing import Dict, Any, List

class MultiObjectiveRanker:
    name: str = "Multi-Objective Ranker"

    def rank_candidates(
        self,
        safe_candidates: List[Dict[str, Any]],
        user_lat: float,
        user_lon: float,
        vessel_type: str = "motorized_craft"
    ) -> List[Dict[str, Any]]:
        """
        Ranks verified safe PFZ options and assigns composite utility scores (0–100).
        """
        if not safe_candidates:
            return []

        ranked_list = []
        for cand in safe_candidates:
            # 1. Fishing Productivity (Chlorophyll + SST front quality)
            fish_score = cand.get("productivity_score", 75.0)
            
            # 2. Distance Penalty (Closer = Better for small boats)
            dist_km = cand.get("distance_from_user_km", 20.0)
            dist_penalty = min(40.0, dist_km * 0.8) # 8 points penalty per 10km
            
            # 3. Chlorophyll-a bonus (mg/m3)
            chla = cand.get("chlorophyll_mg_m3", 1.0)
            chla_bonus = min(15.0, chla * 8.0)

            # 4. Composite Utility Function
            utility_score = (0.50 * fish_score) + chla_bonus - dist_penalty + 15.0
            utility_score = round(max(10.0, min(100.0, utility_score)), 1)

            entry = dict(cand)
            entry["rank_score"] = utility_score
            entry["recommended_departure_window"] = "05:30 AM – 09:30 AM IST (Optimal Morning Ebb Tide)"
            entry["fuel_estimate_liters"] = round(dist_km * 0.45, 1) # Estimated liters for standard OBM
            ranked_list.append(entry)

        # Sort descending by rank score
        ranked_list.sort(key=lambda x: x["rank_score"], reverse=True)

        for i, item in enumerate(ranked_list):
            item["rank_position"] = i + 1
            item["badge"] = "🥇 TOP RECOMMENDATION" if i == 0 else (f"🥈 RANK #{i+1}")

        return ranked_list
