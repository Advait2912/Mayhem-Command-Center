"""
api/events.py — GET /api/events + GET /api/events/{id}/advisory
Source of truth: migration/API_CONTRACT.md → Endpoints 2 and 3.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from backend.core.context import get_context
from backend.schemas.events import EventListItem, EventListResponse
from backend.services.inference import build_advisory_for_existing_event

router = APIRouter()


@router.get("/events", response_model=EventListResponse)
def api_events(
    search: Optional[str] = Query(default=""),
    cause: Optional[str] = Query(default=""),
    zone: Optional[str] = Query(default=""),
    track: Optional[str] = Query(default=""),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    ctx = get_context()
    df = ctx.df_hist.copy()

    # ── Filtering (mirrors app.py:107-130) ────────────────────────────────
    if search:
        search_lower = search.lower()
        mask = (
            df["event_cause"].fillna("").str.lower().str.contains(search_lower, regex=False) |
            df["zone_filled"].fillna("").str.lower().str.contains(search_lower, regex=False) |
            df.get("description", df["event_cause"]).fillna("").str.lower().str.contains(search_lower, regex=False)
        )
        df = df[mask]
    if cause:
        df = df[df["event_cause"] == cause]
    if zone:
        df = df[df["zone_filled"] == zone]
    if track:
        df = df[df["model_track"] == track]

    # Sort by start time descending (most recent first)
    if "start_ist" in df.columns:
        df = df.sort_values("start_ist", ascending=False, na_position="last")

    total = int(len(df))

    # Clamp offset
    offset = max(0, offset)
    page_df = df.iloc[offset: offset + limit]

    events = []
    for idx, row in page_df.iterrows():
        start_ist = None
        if "start_ist" in row and row["start_ist"] is not None:
            try:
                ts = row["start_ist"]
                import pandas as pd
                if not pd.isna(ts):
                    start_ist = ts.isoformat()
            except Exception:
                pass

        closure_prob = None
        if "closure_probability" in row:
            try:
                v = float(row["closure_probability"])
                import math
                if not math.isnan(v):
                    closure_prob = round(v, 3)
            except Exception:
                pass

        desc = None
        if "description" in row and row["description"] is not None:
            try:
                import pandas as pd
                if not pd.isna(row["description"]):
                    desc = str(row["description"])
            except Exception:
                pass

        requires_closure = bool(int(row.get("requires_road_closure", 0) or 0))

        events.append(EventListItem(
            id=int(idx),
            event_cause=str(row["event_cause"]),
            zone_filled=str(row["zone_filled"]),
            start_ist=start_ist,
            model_track=str(row.get("model_track", "slow")),
            closure_probability=closure_prob,
            requires_road_closure=requires_closure,
            description=desc,
        ))

    return EventListResponse(total=total, events=events)


@router.get("/events/{idx}/advisory")
def api_event_advisory(idx: int):
    ctx = get_context()
    if idx not in ctx.df_hist.index:
        raise HTTPException(status_code=404, detail=f"event id {idx} not found")
    try:
        advisory = build_advisory_for_existing_event(idx, ctx)
        return advisory
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
