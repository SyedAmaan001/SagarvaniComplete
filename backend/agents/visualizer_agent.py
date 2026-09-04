"""
Stage 2 & 3: Visualizer Agent
Role: Generates high-fidelity visual payloads including:
- Interactive GeoJSON feature collections (Risk pins, Escape Corridor Polyline, Geofences, Port markers)
- Chart dataset payloads (Wave height, Wind gusts, Risk breakdown radar)
- Dynamic CSS themes / color-coded alert badges.
"""

from typing import Dict, Any, List
from utils.geo_utils import make_point_geojson, make_circle_geojson, make_feature_collection

class VisualizerAgent:
    name: str = "Visualizer Agent"
    role: str = "Visual Payload, Cartographic Engine & Chart Generator"

    def generate_visual_output(
        self,
        lat: float,
        lon: float,
        marine_res: Dict[str, Any],
        weather_res: Dict[str, Any],
        gis_res: Dict[str, Any],
        analytics_res: Dict[str, Any],
        risk_res: Dict[str, Any],
        spatial_res: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesizes all domain intelligence into rich GeoJSON and Chart visualization artifacts.
        """
        features = []

        risk_meta = risk_res.get("risk_assessment", {})
        score = risk_meta.get("composite_risk_score", 35.0)
        risk_color = risk_meta.get("risk_color", "#22c55e")
        risk_level = risk_meta.get("risk_level", "SAFE")
        risk_emoji = risk_meta.get("risk_emoji", "🟢")

        # 1. Primary Query Location Marker
        features.append(make_point_geojson(lat, lon, {
            "type": "USER_VESSEL_LOCATION",
            "title": f"Target Position ({lat}°N, {lon}°E)",
            "risk_score": score,
            "risk_level": risk_level,
            "risk_color": risk_color,
            "risk_emoji": risk_emoji,
            "wave_m": marine_res.get("parameters", {}).get("wave_height_m"),
            "wind_kmh": weather_res.get("parameters", {}).get("wind_speed_kmh"),
            "capsize_hazard": risk_meta.get("capsize_hazard_index")
        }))

        # 2. Nearest Safe Refuge Port Marker
        nearest_port = gis_res.get("parameters", {}).get("nearest_refuge_port", {})
        if nearest_port:
            features.append(make_point_geojson(nearest_port["lat"], nearest_port["lon"], {
                "type": "SAFE_REFUGE_PORT",
                "title": f"⚓ {nearest_port.get('port_name')}",
                "state": nearest_port.get("state"),
                "distance_km": nearest_port.get("distance_km"),
                "shelter_rating": nearest_port.get("shelter_rating"),
                "marker_color": "#00b4ff"
            }))

        # 3. Escape Corridor Route Polyline (GeoJSON LineString)
        corridor = spatial_res.get("spatial_reasoning", {}).get("escape_corridor_to_port", {})
        waypoints = corridor.get("waypoints", [])
        if waypoints:
            line_coords = [[wp["lon"], wp["lat"]] for wp in waypoints]
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": line_coords
                },
                "properties": {
                    "type": "SAFE_CORRIDOR_ROUTE",
                    "title": f"Recommended Course to {corridor.get('destination')}",
                    "eta_hours": corridor.get("estimated_travel_time_hours"),
                    "stroke_color": "#00e5ff",
                    "stroke_style": "dashed" if score > 75 else "solid"
                }
            })

        # 4. Geofenced Max Safe Perimeter Circle
        safe_radius_km = spatial_res.get("spatial_reasoning", {}).get("max_safe_distance_km", 50.0)
        features.append(make_circle_geojson(lat, lon, safe_radius_km, {
            "type": "SAFE_OPERATING_PERIMETER",
            "title": f"Maximum Advisory Perimeter ({safe_radius_km} km)",
            "risk_color": risk_color,
            "fill_opacity": 0.12
        }))

        # 5. Chart.js Series Data
        chart_payload = {
            "radar_risk_breakdown": {
                "labels": ["Waves", "Wind", "Currents", "Cyclone Proximity", "Coastal Sensitivity"],
                "datasets": [{
                    "label": "Risk Factor Scores (0–100)",
                    "data": [
                        risk_meta.get("sub_scores", {}).get("wave_score", 30),
                        risk_meta.get("sub_scores", {}).get("wind_score", 30),
                        risk_meta.get("sub_scores", {}).get("current_score", 20),
                        risk_meta.get("sub_scores", {}).get("cyclone_score", 0),
                        risk_meta.get("sub_scores", {}).get("coastal_vulnerability_score", 50),
                    ],
                    "backgroundColor": f"{risk_color}33",
                    "borderColor": risk_color,
                    "borderWidth": 2
                }]
            },
            "hydrodynamic_metrics": {
                "wave_energy_kw_m": analytics_res.get("analytics", {}).get("wave_energy_flux_kw_m"),
                "drift_speed_knots": analytics_res.get("analytics", {}).get("drift_rate_knots"),
                "trend": analytics_res.get("analytics", {}).get("trend_24h")
            }
        }

        return {
            "agent": self.name,
            "status": "success",
            "visual_artifacts": {
                "geojson": make_feature_collection(features),
                "charts": chart_payload,
                "map_view_bounds": {
                    "center": [lat, lon],
                    "zoom": 7 if safe_radius_km < 50 else 6
                }
            }
        }
