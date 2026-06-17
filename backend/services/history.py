import random
import re
from typing import List, Dict, Any

class HistoryService:
    """
    Generates plausible historical similarities.
    In a real scenario, this would query the SQLite database for events with similar types/zones.
    """
    
    SIMILAR_TEMPLATES = {
        "Mass Gathering": [
            "Previous IPL Final: Resolved in 8h, used 35 officers",
            "Republic Day Parade: Resolved in 12h, used 50 officers",
            "Kannada Rajyotsava: Resolved in 6h, used 20 officers"
        ],
        "VIP Movement": [
            "PM Visit (Jan 2024): Resolved in 2h, used 15 officers",
            "Foreign Dignitary Visit: Resolved in 1.5h, used 10 officers"
        ],
        "vehicle_breakdown": [
            "Bus breakdown at Silk Board: Resolved in 1.2h, used 3 officers",
            "Truck stall at Hebbal: Resolved in 0.8h, used 2 officers"
        ],
        "Flood/Waterlogging": [
            "August Monsoon Flash Flood: Resolved in 18h, used 12 officers",
            "KR Puram Underpass Flooding: Resolved in 10h, used 8 officers"
        ],
        "Infrastructure Work": [
            "Metro Pillar 45 Installation: Resolved in 10h, used 6 officers",
            "Flyover Repair (Night): Resolved in 7h, used 4 officers"
        ]
    }

    def get_similar_events(self, event_type: str) -> List[Dict[str, Any]]:
        templates = self.SIMILAR_TEMPLATES.get(event_type, self.SIMILAR_TEMPLATES["vehicle_breakdown"])
        
        # Randomly pick 1-3 similar events
        count = random.randint(1, 3)
        selected = random.sample(templates, min(count, len(templates)))
        
        results = []
        for text in selected:
            # Basic parsing to split text into structured data for the UI
            # In a real app, these would be database records.
            parts = text.split(":")
            summary = parts[0]
            
            # Extract numbers from the second part
            res_hours = 1.0
            off_used = 2
            if len(parts) > 1:
                words = parts[1].split()
                # Find 'h' for hours and 'officers' for officers
                for i, w in enumerate(words):
                    match = re.search(r'(\d+(?:\.\d+)?)h', w)
                    if match:
                        res_hours = float(match.group(1))
                        if 'officers' in w: off_used = int(words[i-1])

            results.append({
                "summary": summary,
                "avg_resolution_hours": res_hours,
                "officers_used": off_used,
                "closure_required": random.choice([True, False])
            })
        return results
