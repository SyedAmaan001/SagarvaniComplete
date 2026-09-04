"""
Stage 2: Planner (Task Planner)
Role: Analyzes incoming maritime queries, interprets operational goals,
and generates a structured execution plan across the 6 specialized domain agents.
"""

from typing import Dict, Any, List

class TaskPlanner:
    name: str = "Planner (Task Planner)"
    role: str = "Query Decomposition & Multi-Agent Execution Graph Generator"

    def create_plan(self, lat: float, lon: float, query_type: str = "safety_assessment") -> Dict[str, Any]:
        """
        Creates an ordered task schedule with input/output dependencies.
        """
        tasks = [
            {
                "task_id": 1,
                "target_agent": "Marine Data Agent",
                "action": "FETCH_HYDRODYNAMICS",
                "parameters": {"lat": lat, "lon": lon, "sources": ["MOSDAC", "CMEMS", "Open-Meteo Marine"]},
                "depends_on": []
            },
            {
                "task_id": 2,
                "target_agent": "Weather Agent",
                "action": "FETCH_ATMOSPHERIC_FORECAST",
                "parameters": {"lat": lat, "lon": lon, "sources": ["Open-Meteo", "IMD"]},
                "depends_on": []
            },
            {
                "task_id": 3,
                "target_agent": "GIS Agent",
                "action": "ANALYZE_COASTAL_LULC_AND_PORTS",
                "parameters": {"lat": lat, "lon": lon, "sources": ["Bhuvan NRSC LULC"]},
                "depends_on": []
            },
            {
                "task_id": 4,
                "target_agent": "Ocean Analytics Agent",
                "action": "ANALYZE_ANOMALIES_AND_WAVE_POWER",
                "parameters": {"lat": lat, "lon": lon},
                "depends_on": [1, 2]
            },
            {
                "task_id": 5,
                "target_agent": "Risk Agent",
                "action": "EVALUATE_COMPOSITE_HAZARD_INDEX",
                "parameters": {"lat": lat, "lon": lon},
                "depends_on": [1, 2, 3]
            },
            {
                "task_id": 6,
                "target_agent": "Spatial Reasoning Agent",
                "action": "COMPUTE_ESCAPE_CORRIDORS_AND_GEOFENCES",
                "parameters": {"lat": lat, "lon": lon},
                "depends_on": [3, 5]
            },
            {
                "task_id": 7,
                "target_agent": "Reasoning & Validation Agent",
                "action": "CROSS_VERIFY_AND_RECONCILE",
                "parameters": {},
                "depends_on": [1, 2, 3, 4, 5, 6]
            },
            {
                "task_id": 8,
                "target_agent": "Visualizer Agent",
                "action": "SYNTHESIZE_CARTOGRAPHIC_AND_CHART_ARTIFACTS",
                "parameters": {"lat": lat, "lon": lon},
                "depends_on": [7]
            }
        ]

        return {
            "planner": self.name,
            "query_type": query_type,
            "target_coordinates": {"lat": lat, "lon": lon},
            "execution_steps_count": len(tasks),
            "execution_graph": tasks,
            "status": "PLAN_READY"
        }
