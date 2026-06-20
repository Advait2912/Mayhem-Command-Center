"""
api/outcomes.py — GET /api/outcomes + POST /api/outcomes
Source of truth: migration/API_CONTRACT.md → Endpoints 5 and 6.
"""

from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, HTTPException

from backend.core.config import OUTCOMES_LOG_PATH
from backend.schemas.outcomes import (
    OutcomeCreateRequest,
    OutcomeCreateResponse,
    OutcomeListResponse,
    OutcomeRecord,
)

router = APIRouter()

# CSV column order — must match what legacy app.py wrote
OUTCOME_COLUMNS = [
    "logged_at",
    "source_event_id",
    "event_cause",
    "zone",
    "predicted_officers",
    "predicted_closure_probability",
    "predicted_cascade_risk_score",
    "actual_officers_used",
    "actual_duration_hrs",
    "actual_required_closure",
    "notes",
]


def _read_outcomes_df() -> pd.DataFrame:
    if not OUTCOMES_LOG_PATH.exists() or OUTCOMES_LOG_PATH.stat().st_size < 10:
        return pd.DataFrame(columns=OUTCOME_COLUMNS)
    df = pd.read_csv(OUTCOMES_LOG_PATH, dtype=str)
    # Ensure all expected columns exist
    for col in OUTCOME_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[OUTCOME_COLUMNS]


def _sanitize_row(d: dict) -> dict:
    """Replace NaN / None / 'nan' with None for JSON safety. Mirrors app.py:102."""
    out = {}
    for k, v in d.items():
        if v is None:
            out[k] = None
        elif isinstance(v, float):
            import math
            out[k] = None if math.isnan(v) else v
        elif isinstance(v, str) and v.lower() in ("nan", "none", ""):
            out[k] = None
        else:
            out[k] = v
    return out


@router.get("/outcomes", response_model=OutcomeListResponse)
def api_list_outcomes():
    df = _read_outcomes_df()
    if len(df) == 0:
        return OutcomeListResponse(count=0, outcomes=[])

    # Sort descending by logged_at, return last 100
    df = df.sort_values("logged_at", ascending=False).head(100)
    outcomes = []
    for _, row in df.iterrows():
        d = _sanitize_row(row.to_dict())
        outcomes.append(OutcomeRecord(**d))
    return OutcomeListResponse(count=len(outcomes), outcomes=outcomes)


@router.post("/outcomes", response_model=OutcomeCreateResponse)
def api_log_outcome(body: OutcomeCreateRequest):
    logged_at = datetime.now(timezone.utc).isoformat()
    record = {
        "logged_at": logged_at,
        "source_event_id": str(body.source_event_id) if body.source_event_id is not None else None,
        "event_cause": body.event_cause,
        "zone": body.zone,
        "predicted_officers": body.predicted_officers,
        "predicted_closure_probability": body.predicted_closure_probability,
        "predicted_cascade_risk_score": body.predicted_cascade_risk_score,
        "actual_officers_used": body.actual_officers_used,
        "actual_duration_hrs": body.actual_duration_hrs,
        "actual_required_closure": body.actual_required_closure,
        "notes": body.notes or "",
    }

    # Append to CSV — create with header if first write
    row_df = pd.DataFrame([record])[OUTCOME_COLUMNS]
    write_header = (not OUTCOMES_LOG_PATH.exists()) or OUTCOMES_LOG_PATH.stat().st_size < 10
    row_df.to_csv(OUTCOMES_LOG_PATH, mode="a", header=write_header, index=False)

    clean = _sanitize_row(record)
    return OutcomeCreateResponse(
        status="logged",
        record=OutcomeRecord(**clean),
    )
