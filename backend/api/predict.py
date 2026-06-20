"""
api/predict.py — POST /api/predict
Source of truth: migration/API_CONTRACT.md → Endpoint 4.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.context import get_context
from backend.services.inference import build_advisory_for_new_event

router = APIRouter()


class PredictRequest(BaseModel):
    """
    Request body for POST /api/predict.
    Required: event_cause, zone_filled, latitude, longitude, start_datetime.
    All other fields are optional per API_CONTRACT.md.
    """
    event_cause: str
    zone_filled: str
    latitude: float
    longitude: float
    start_datetime: str
    description: Optional[str] = ""
    veh_type: Optional[str] = "MISSING"
    corridor: Optional[str] = "MISSING"
    gba_identifier: Optional[str] = "MISSING"
    endlatitude: Optional[float] = None
    endlongitude: Optional[float] = None


@router.post("/predict")
def api_predict(body: PredictRequest):
    ctx = get_context()
    raw = body.model_dump()
    try:
        advisory = build_advisory_for_new_event(raw, ctx)
        return advisory
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
