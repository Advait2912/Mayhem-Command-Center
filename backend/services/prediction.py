import random
from typing import List, Dict, Any

class PredictionService:
    """
    Dynamic Mock Engine: Maps event types to plausible operational metrics.
    This replaces the static JSON response with a rule-based simulation.
    """
    
    EVENT_PROFILES = {
        "Mass Gathering": {
            "priority": "CRITICAL",
            "cascade_risk_range": (8.5, 10.0),
            "closure_prob_range": (0.6, 0.9),
            "duration_range": (4.0, 12.0),
            "officers_range": (15, 40),
            "impact_radius": 2.5
        },
        "VIP Movement": {
            "priority": "HIGH",
            "cascade_risk_range": (6.0, 8.0),
            "closure_prob_range": (0.4, 0.7),
            "duration_range": (1.0, 3.0),
            "officers_range": (10, 20),
            "impact_radius": 1.2
        },
        "vehicle_breakdown": {
            "priority": "MEDIUM",
            "cascade_risk_range": (2.0, 5.0),
            "closure_prob_range": (0.1, 0.3),
            "duration_range": (0.5, 2.0),
            "officers_range": (2, 5),
            "impact_radius": 0.5
        },
        "Flood/Waterlogging": {
            "priority": "HIGH",
            "cascade_risk_range": (7.0, 9.0),
            "closure_prob_range": (0.3, 0.6),
            "duration_range": (3.0, 24.0),
            "officers_range": (8, 15),
            "impact_radius": 3.0
        },
        "Infrastructure Work": {
            "priority": "MEDIUM",
            "cascade_risk_range": (4.0, 7.0),
            "closure_prob_range": (0.7, 1.0),
            "duration_range": (6.0, 12.0),
            "officers_range": (5, 10),
            "impact_radius": 0.8
        }
    }

    def generate_triage(self, event_type: str):
        profile = self.EVENT_PROFILES.get(event_type, self.EVENT_PROFILES["vehicle_breakdown"])
        return {
            "closure_probability": random.uniform(*profile["closure_prob_range"]),
            "priority": profile["priority"],
            "cascade_risk": round(random.uniform(*profile["cascade_risk_range"]), 1)
        }

    def generate_duration(self, event_type: str):
        profile = self.EVENT_PROFILES.get(event_type, self.EVENT_PROFILES["vehicle_breakdown"])
        base = random.uniform(*profile["duration_range"])
        return {
            "expected_hours": round(base, 1),
            "p10": round(base * 0.6, 1),
            "p50": round(base, 1),
            "p90": round(base * 1.5, 1)
        }

    def generate_spatial(self, event: Dict[str, Any]):
        profile = self.EVENT_PROFILES.get(event["event_type"], self.EVENT_PROFILES["vehicle_breakdown"])
        return {
            "affected_junctions": ["Main Junction", "Diversion Point A", "Cross-road B"],
            "radius_km": profile["impact_radius"],
            "estimated_delay_minutes": random.randint(10, 60),
            "alternate_route": "Suggested via Ring Road"
        }

    def generate_resources(self, event_type: str):
        profile = self.EVENT_PROFILES.get(event_type, self.EVENT_PROFILES["vehicle_breakdown"])
        return {
            "officers_needed": random.randint(*profile["officers_range"]),
            "barricade_points": ["Primary Entry", "Secondary Exit"],
            "diversion_advisory": "Redirect all heavy vehicles via Outer Ring Road"
        }
