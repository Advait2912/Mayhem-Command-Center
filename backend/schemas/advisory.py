"""
schemas/advisory.py — Pydantic models for the Advisory response and all nested types.
Source of truth: migration/API_CONTRACT.md → Shared Types.
Every field, type, and nullable annotation matches the contract exactly.
"""

from __future__ import annotations
from typing import List, Optional, Union
from pydantic import BaseModel


class DurationQuantile(BaseModel):
    type: str = "quantile"
    p10_hrs: float
    p50_hrs: float
    p90_hrs: float


class DurationBand(BaseModel):
    type: str = "band"
    band: str
    median_hrs_raw: float
    confidence: str


class DurationNone(BaseModel):
    type: str = "none"
    note: str


# Discriminated union -- FastAPI will serialise whichever shape is returned
DurationResult = Union[DurationQuantile, DurationBand, DurationNone]


class PriorityResult(BaseModel):
    probability_high: float
    label: str  # "HIGH" | "LOW"


class RoutingResult(BaseModel):
    footprint_size: int
    baseline_minutes: float
    affected_minutes: Optional[float] = None
    delay_minutes: Optional[float] = None
    alt_route_exists: bool
    blocked_node_count: int
    blocked_nodes: List[int]


class DiversionRoute(BaseModel):
    rank: int
    path_length: int
    distance_km: float
    travel_minutes: float
    via: str
    path_nodes: List[int]


class SimilarEvent(BaseModel):
    event_cause: str
    zone: str
    duration_hrs: Optional[float] = None
    requires_road_closure: bool
    recommended_officers: Optional[float] = None
    similarity: float


class SimilarEventsSummary(BaseModel):
    n: int
    avg_resolution_hrs: Optional[float] = None
    avg_officers: Optional[float] = None
    closure_rate: Optional[float] = None


class ConflictEvent(BaseModel):
    event_cause: str
    closure_probability: float


class ConflictsResult(BaseModel):
    count: int
    events: List[ConflictEvent]


class NetworkResilienceRoute(BaseModel):
    rank: int
    path_length: int
    distance_km: float
    travel_minutes: float
    via: str
    compromised: bool


class NetworkResilienceResult(BaseModel):
    routes_checked: int
    routes_compromised: int
    warning: Optional[str] = None
    route_status: List[NetworkResilienceRoute]


class HikeContext(BaseModel):
    zone: str
    predicted_window: str
    trigger_reason: str
    confidence: float
    suggested_event_cause: str
    source_snippet: Optional[str] = None


class HistoricalPeakWindow(BaseModel):
    window: str
    basis: str


class Advisory(BaseModel):
    """Top-level advisory response. Matches API_CONTRACT.md → Advisory shape exactly."""
    event_cause: str
    zone: str
    closure_probability: float
    recommended_officers: float
    cascade_risk_score: float
    spatial_confidence: bool
    spatial_warning: Optional[str] = None
    recommended_tow_trucks: Optional[float] = None
    signal_timing_suggestion: Optional[str] = None
    historical_peak_window: Optional[HistoricalPeakWindow] = None
    priority: Optional[PriorityResult] = None
    duration: Optional[DurationResult] = None
    predicted_hike_context: Optional[HikeContext] = None
    conflicts: Optional[ConflictsResult] = None
    latitude: float
    longitude: float
    footprint_radius_km: float
    routing: Optional[RoutingResult] = None
    recommended_barricade_node: Optional[int] = None
    barricade_candidates_considered: List[int] = []
    diversion_routes: List[DiversionRoute] = []
    network_resilience: Optional[NetworkResilienceResult] = None
    similar_past_events: List[SimilarEvent] = []
    similar_past_events_summary: Optional[SimilarEventsSummary] = None

    model_config = {"extra": "allow"}
