from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from services.prediction import PredictionService
from services.history import HistoryService
from services.conflict import ConflictService

app = FastAPI(title="GridLock Command Center API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EventInput(BaseModel):
    event_type: str
    location: str
    zone: str
    time: str
    description: str

# Initialize Services
prediction_svc = PredictionService()
history_svc = HistoryService()
conflict_svc = ConflictService()

@app.get("/")
async def root():
    return {"status": "online", "message": "GridLock Command Center API is active"}

@app.post("/api/generate-report")
async def generate_report(event: EventInput):
    # Convert Pydantic model to dict for services
    event_dict = event.dict()
    
    # Generate the operational intelligence report using the dynamic engine
    return {
        "triage": prediction_svc.generate_triage(event.event_type),
        "duration": prediction_svc.generate_duration(event.event_type),
        "spatial_impact": prediction_svc.generate_spatial(event_dict),
        "resources": prediction_svc.generate_resources(event.event_type),
        "similar_events": history_svc.get_similar_events(event.event_type),
        "conflict_check": conflict_svc.check_conflicts(event_dict)
    }
