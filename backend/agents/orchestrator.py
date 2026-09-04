"""
Stage 2 & Stage 4: Main Orchestrator (Decision Maker)
Coordinates the complete ORCA Technical Architecture:
1. Stage 2 Orchestration: Dispatches Task Planner.
2. Stage 3 Intelligence: Executes the 6 Domain Specialized Agents (Marine, Weather, GIS, Analytics, Risk, Spatial).
3. Stage 3 Validation: Triggers Reasoning & Validation Agent (self-correction loop).
4. Stage 3 Visualization: Invokes Visualizer Agent for GeoJSON & charts.
5. Stage 4 Delivery: Synthesizes final decision via Gemini AI and delivers unified response to user.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone

from agents.planner import TaskPlanner
from agents.marine_agent import MarineDataAgent
from agents.weather_agent import WeatherAgent
from agents.gis_agent import GISAgent
from agents.ocean_analytics_agent import OceanAnalyticsAgent
from agents.risk_agent import RiskAgent
from agents.spatial_reasoning_agent import SpatialReasoningAgent
from agents.validator import ReasoningValidationAgent
from agents.visualizer_agent import VisualizerAgent
from engine.advisory_engine import generate_fishing_advisory

class MainOrchestrator:
    name: str = "Main Orchestrator (Decision Maker)"
    role: str = "Central Autonomous Coordination, Multidisciplinary Reasoning & Final Decision Delivery"

    def __init__(self):
        self.planner = TaskPlanner()
        self.marine_agent = MarineDataAgent()
        self.weather_agent = WeatherAgent()
        self.gis_agent = GISAgent()
        self.analytics_agent = OceanAnalyticsAgent()
        self.risk_agent = RiskAgent()
        self.spatial_agent = SpatialReasoningAgent()
        self.validator = ReasoningValidationAgent()
        self.visualizer = VisualizerAgent()

    def process_query(self, lat: float, lon: float, language: str = "both") -> Dict[str, Any]:
        """
        Executes the end-to-end ORCA pipeline:
        Understand -> Orchestrate -> Plan -> Retrieve -> Analyze -> Validate -> Visualize -> Decide -> Deliver
        """
        start_time = datetime.now(timezone.utc)

        # STAGE 2: Plan Generation
        plan = self.planner.create_plan(lat, lon)

        # STAGE 3: Specialized Intelligence Domain Agents Execution
        # Step 1: Base Observation Agents
        marine_res = self.marine_agent.execute(lat, lon)
        weather_res = self.weather_agent.execute(lat, lon)
        gis_res = self.gis_agent.execute(lat, lon)

        # Step 2: Higher-Order Analytics & Risk Agents
        analytics_res = self.analytics_agent.execute(lat, lon, marine_res, weather_res)
        risk_res = self.risk_agent.execute(lat, lon, marine_res, weather_res, gis_res)
        spatial_res = self.spatial_agent.execute(lat, lon, gis_res, risk_res)

        # Step 3: Reasoning & Validation (Stage 3 Feedback / Contradiction Loop)
        validation_res = self.validator.validate(
            marine_res, weather_res, gis_res, analytics_res, risk_res, spatial_res
        )

        # Step 4: Visualizer Agent (Stage 2/3 Cartographic Synthesis)
        visualizer_res = self.visualizer.generate_visual_output(
            lat, lon, marine_res, weather_res, gis_res, analytics_res, risk_res, spatial_res
        )

        # STAGE 4: Executive Decision & User Delivery
        risk_meta = risk_res.get("risk_assessment", {})
        score = risk_meta.get("composite_risk_score", 35.0)

        # Format risk data packet for Gemini AI Advisory
        synthetic_risk_packet = {
            "breakdown": {
                "wave_height": {
                    "value_m": marine_res["parameters"]["wave_height_m"],
                    "sea_state": marine_res["parameters"]["sea_state"]
                },
                "wind_speed": {
                    "value_kmh": weather_res["parameters"]["wind_speed_kmh"],
                    "value_ms": weather_res["parameters"]["wind_speed_ms"]
                },
                "ocean_current": {
                    "value_ms": marine_res["parameters"]["current_speed_ms"]
                },
                "cyclone_proximity": {
                    "nearest_cyclone": {
                        "name": risk_meta.get("nearest_cyclone", "None"),
                        "distance_km": risk_meta.get("cyclone_dist_km", "N/A")
                    } if risk_meta.get("nearest_cyclone") else None
                }
            }
        }

        # Generate Gemini Decision & Advisory
        advisory_res = generate_fishing_advisory(
            lat=lat,
            lon=lon,
            risk_score=score,
            risk_data=synthetic_risk_packet,
            language=language
        )

        elapsed_ms = round((datetime.now(timezone.utc) - start_time).total_seconds() * 1000, 1)

        return {
            "pipeline_status": "COMPLETED",
            "execution_time_ms": elapsed_ms,
            "stage_1_interface": {
                "user_channel": "Web / Mobile Portal",
                "intent_interpreted": "Maritime Navigation & Fishery Safety Advisory",
                "coordinates": {"lat": lat, "lon": lon},
                "language_requested": language
            },
            "stage_2_orchestration": {
                "orchestrator": self.name,
                "planner": plan,
                "execution_mode": "Autonomous Multi-Agent Consensus"
            },
            "stage_3_intelligence_layer": {
                "marine_data_agent": marine_res,
                "weather_agent": weather_res,
                "gis_agent": gis_res,
                "ocean_analytics_agent": analytics_res,
                "risk_agent": risk_res,
                "spatial_reasoning_agent": spatial_res,
                "reasoning_and_validation": validation_res
            },
            "stage_3_visualizer": visualizer_res,
            "stage_4_delivery": {
                "final_decision": {
                    "verdict": risk_meta.get("risk_level"),
                    "composite_risk_score": score,
                    "capsize_hazard_level": risk_meta.get("capsize_hazard_index"),
                    "max_safe_distance_nm": spatial_res["spatial_reasoning"]["max_safe_distance_nm"],
                    "nearest_shelter_port": gis_res["parameters"]["nearest_refuge_port"]["port_name"]
                },
                "actionable_recommendation": advisory_res.get("advisory_text"),
                "advisory_metadata": {
                    "language": language,
                    "model": advisory_res.get("model_used"),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        }
