"""
api/outcomes.py — GET /api/outcomes + POST /api/outcomes
Source of truth: migration/API_CONTRACT.md → Endpoints 5 and 6.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from backend.core.context import get_context
from backend.schemas.outcomes import (
    OutcomeCreateRequest,
    OutcomeCreateResponse,
    OutcomeListResponse,
    OutcomeRecord,
)
from backend.services.db.outcomes_repo import flatten_outcome_row
from backend.services.retrain import maybe_trigger_retrain

router = APIRouter()

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
def api_list_outcomes(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    ctx = get_context()
    # Fetch records using the repository
    records = ctx.outcomes_repo.list_outcomes(limit=limit, offset=offset)
    
    if not records:
        return OutcomeListResponse(count=0, outcomes=[])

    outcomes = []
    for r in records:
        # The record from the repo might be a raw dict from Supabase (nested
        # in event_payload/actual_outcome jsonb) or a flat CSV row --
        # flatten_outcome_row normalizes both to the OutcomeRecord shape.
        clean = _sanitize_row(flatten_outcome_row(r))
        outcomes.append(OutcomeRecord(**clean))

    return OutcomeListResponse(count=len(outcomes), outcomes=outcomes)


@router.post("/outcomes", response_model=OutcomeCreateResponse)
def api_log_outcome(body: OutcomeCreateRequest, background_tasks: BackgroundTasks):
    ctx = get_context()
    
    # Prepare a flat record that both CSV and Supabase repositories can interpret
    # We use the column names from the legacy CSV as the "interchange format"
    record = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "source_event_id": str(body.source_event_id) if body.source_event_id is not None else None,
        "event_cause": body.event_cause,
        "zone": body.zone,
        "predicted_officers": body.predicted_officers,
        "predicted_closure_probability": body.predicted_closure_probability,
        "predicted_cascade_risk_score": body.predicted_cascade_risk_score,
        "actual_officers_used": body.actual_officers_used,
        "actual_duration_hrs": body.actual_duration_hrs,
        "actual_required_closure": body.actual_required_closure,
        "actual_priority": body.actual_priority,
        "notes": body.notes or "",
    }

    try:
        # Store via repository
        ctx.outcomes_repo.insert_outcome(record)
    except Exception as e:
        # Fail loudly as per requirement
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Self-retraining loop: fires automatically
    background_tasks.add_task(maybe_trigger_retrain)

    clean = _sanitize_row(record)
    return OutcomeCreateResponse(
        status="logged",
        record=OutcomeRecord(**clean),
    )
