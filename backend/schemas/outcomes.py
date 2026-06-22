"""
schemas/outcomes.py — Pydantic models for outcome logging.
Source of truth: migration/API_CONTRACT.md → GET /api/outcomes + POST /api/outcomes.
"""

from __future__ import annotations
from typing import Any, List, Optional
from pydantic import BaseModel


class OutcomeRecord(BaseModel):
    logged_at: str
    source_event_id: Optional[str] = None
    event_cause: str
    zone: str
    predicted_officers: Optional[float] = None
    predicted_closure_probability: Optional[float] = None
    predicted_cascade_risk_score: Optional[float] = None
    actual_officers_used: Optional[float] = None
    actual_duration_hrs: Optional[float] = None
    actual_required_closure: Optional[str] = None  # "true" | "false" | null
    actual_priority: Optional[str] = None  # "HIGH" | "LOW" | null
    notes: Optional[str] = ""
    used_for_training: Optional[bool] = None


class OutcomeListResponse(BaseModel):
    count: int
    outcomes: List[OutcomeRecord]


class OutcomeCreateRequest(BaseModel):
    """
    Required: event_cause, zone, predicted_officers, predicted_closure_probability.
    All other fields are optional per API_CONTRACT.md.
    """
    source_event_id: Optional[Any] = None
    event_cause: str
    zone: str
    predicted_officers: float
    predicted_closure_probability: float
    predicted_cascade_risk_score: Optional[float] = None
    actual_officers_used: Optional[float] = None
    actual_duration_hrs: Optional[float] = None
    actual_required_closure: Optional[str] = None
    actual_priority: Optional[str] = None  # "HIGH" | "LOW"
    notes: Optional[str] = ""


class OutcomeCreateResponse(BaseModel):
    status: str
    record: OutcomeRecord
