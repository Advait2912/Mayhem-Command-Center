"""
schemas/meta.py — Pydantic models for the metadata endpoint.
Source of truth: migration/API_CONTRACT.md → GET /api/meta response.
"""

from __future__ import annotations
from typing import Dict, List
from pydantic import BaseModel


class ZoneCentroid(BaseModel):
    latitude: float
    longitude: float


class MetaResponse(BaseModel):
    causes: List[str]
    zones: List[str]
    veh_types: List[str]
    event_count: int
    zone_centroids: Dict[str, ZoneCentroid]
