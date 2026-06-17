import random
from typing import List, Dict, Any

class ConflictService:
    """
    Simple logic to detect resource contention.
    """
    def check_conflicts(self, current_event: Dict[str, Any]) -> Dict[str, Any]:
        # Mock active events in the system
        active_events = [
            {"type": "VIP Movement", "priority": "HIGH", "zone": "Central Zone 1"},
            {"type": "Infrastructure Work", "priority": "MEDIUM", "zone": "East Zone"}
        ]
        
        conflicts = [e for e in active_events if e["zone"] == current_event.get("zone")]
        
        if conflicts:
            return {
                "has_conflict": True,
                "message": f"Resource contention detected: {len(conflicts)} other high-priority events active in {current_event.get('zone')}."
            }
        
        return {
            "has_conflict": False,
            "message": "No simultaneous high-priority events detected in this zone."
        }
