"""
schemas/events.py — Pydantic models for event listing.
Source of truth: migration/API_CONTRACT.md → GET /api/events response.
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class EventListItem(BaseModel):
    id: int
    event_cause: str
    zone_filled: str
    start_ist: Optional[str] = None
    model_track: str
    closure_probability: Optional[float] = None
    requires_road_closure: bool
    description: Optional[str] = None


class EventListResponse(BaseModel):
    total: int
    events: List[EventListItem]
