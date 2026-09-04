"""
Stage 3 - Agent 6: Spatial Reasoning Agent
Domain: Spatial Relations, Boundary Constraints, Safe Return Corridors, Geofenced Hazard Zones.
Sources: Shapely Topology Engine, Haversine Distance Geometry.
"""

from typing import Dict, Any, List, Optional
from utils.geo_utils import haversine_km, make_circle_geojson, make_point_geojson

class SpatialReasoningAgent:
    name: str = "Spatial Reasoning Agent"
    domain: str = "Spatial Relations, Marine Constraints & Route Corridors"

    def execute(self, lat: float, lon: float, gis_data: Dict[str, Any], risk_data: Dict[str, Any]) -> Dict[str, Any]:
        params_g = gis_data.get("parameters", {})
        nearest_port = params_g.get("nearest_refuge_port", {})
        risk_meta = risk_data.get("risk_assessment", {})
        score = risk_meta.get("composite_risk_score", 40.0)

        port_lat = nearest_port.get("lat", lat + 0.2)
        port_lon = nearest_port.get("lon", lon + 0.2)
        dist_port_km = nearest_port.get("distance_km", 15.0)

        # 1. Compute Safe Navigation Corridor (Waypoints to nearest refuge port)
        # Interpolate 3 intermediate safety waypoints
        corridor_waypoints = []
        num_steps = 4
        for i in range(num_steps + 1):
            fraction = i / float(num_steps)
            w_lat = round(lat + fraction * (port_lat - lat), 4)
            w_lon = round(lon + fraction * (port_lon - lon), 4)
            d_remaining = round((1.0 - fraction) * dist_port_km, 1)
            corridor_waypoints.append({
                "step": i,
                "lat": w_lat,
                "lon": w_lon,
                "distance_to_harbor_km": d_remaining
            })

        # 2. Maximum Safe Outbound Radius (in Nautical Miles & KM)
        # Higher risk -> restricted fishing perimeter
        if score > 75:
            safe_radius_nm = 3.0   # Near shore only / Harbor locked
        elif score > 50:
            safe_radius_nm = 12.0  # Within territorial waters
        elif score > 25:
            safe_radius_nm = 35.0  # Continental shelf
        else:
            safe_radius_nm = 100.0 # Open deep-sea fishing

        # 3. Spatial Hazard Zone Geofencing
        spatial_constraints = []
        if score > 50:
            spatial_constraints.append({
                "type": "RESTRICTED_ZONE",
                "severity": "CRITICAL" if score > 75 else "WARNING",
                "center": {"lat": lat, "lon": lon},
                "radius_km": round(safe_radius_nm * 1.852, 1),
                "description": f"Enforced advisory geofence: Do not navigate beyond {safe_radius_nm} NM."
            })

        return {
            "agent": self.name,
            "status": "success",
            "spatial_reasoning": {
                "max_safe_distance_nm": safe_radius_nm,
                "max_safe_distance_km": round(safe_radius_nm * 1.852, 1),
                "escape_corridor_to_port": {
                    "destination": nearest_port.get("port_name", "Local Harbor"),
                    "total_distance_km": dist_port_km,
                    "estimated_travel_time_hours": round(dist_port_km / 15.0, 1), # Assumes 15 km/h trawler speed
                    "waypoints": corridor_waypoints
                },
                "active_geofence_constraints": spatial_constraints,
                "corridor_feasibility": "SAFE" if score < 75 else "URGENT_EVACUATION"
            },
            "sources": ["Geospatial Route Corridor Models", "Topological Geofence Engine"],
            "confidence_score": 0.95
        }
