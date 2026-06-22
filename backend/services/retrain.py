"""
services/retrain.py — Self-retraining loop for all four triage/duration
models (closure, priority, duration-fast, duration-slow).

Trigger: every time RETRAIN_BATCH_SIZE (see core/config.py) new outcomes
accumulate -- counted via the active OutcomesRepository, so this works
whether outcomes live in outcomes_log.csv (dev) or the Supabase `outcomes`
table (prod) -- all four models retrain in the background. See
api/outcomes.py for the trigger check that fires this after every
POST /api/outcomes.

Every retrain is a FULL refit on (historical parquet rows + every
outcome-labeled live row collected so far), not an incremental update --
same pattern the original closure-only version used. Each model has its
own ground-truth label and is skipped independently if there isn't enough
labeled data yet for it; one model having no data never blocks the others.

Where the labeled data comes from: every POST /api/predict persists the
full feature row it computed for that event, keyed by a generated event_id
(see inference.py::_persist_pending_event). When an officer later logs the
real outcome for that event, the outcome row carries that same id as
source_event_id. Joining the two on that id reconstructs a fully-featured,
correctly-labeled training row.

Artifacts are written to backend/models/ as before; if Supabase is
configured, the whole folder is also pushed to Storage as the next
incrementing version and promoted to active (see model_manager.py), so the
next process start pulls the freshly retrained models instead of whatever
was baked into the image.
"""

import logging
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

from backend.core.config import (
    ENRICHED_PATH, PENDING_EVENTS_PATH, RETRAIN_LOG_PATH, RETRAIN_BATCH_SIZE,
    MODELS_DIR, USE_SUPABASE,
    CLOSURE_MODEL_PATH, CLOSURE_CALIBRATED_PATH,
    PRIORITY_MODEL_PATH, PRIORITY_CALIBRATED_PATH,
    DURATION_FAST_Q_PATHS, DURATION_SLOW_WEIBULL_PATH,
)
from backend.core.context import get_context
from backend.services.db.outcomes_repo import flatten_outcome_row
from backend.services.pipeline import (
    TRIAGE_CAT_FEATURES, TRIAGE_NUM_FEATURES, DURATION_NUM_FEATURES_EXTRA,
    manual_oof_predict_proba, fit_isotonic_calibrator, LabelEncoder,
)

logger = logging.getLogger("gridlock")

ALL_FEATURES = TRIAGE_CAT_FEATURES + TRIAGE_NUM_FEATURES
AFT_CAT_FEATURES = ["event_cause", "holiday_type"]
AFT_NUM_FEATURES = [
    "hour_ist", "month", "is_weekend", "is_peak", "junction_centrality",
    "rainfall_mm", "is_election_campaign_period", "is_public_holiday",
    "has_kannada", "desc_slow_signal", "cascade_count", "hotspot_score",
    "is_heavy_vehicle", "closure_probability",
]


def _append_retrain_log(record: dict) -> None:
    """Schema-safe append -- a failed run logs {retrained_at, status, error}
    while a completed run logs a different key set (per-model statuses), so
    a plain to_csv(mode='a') would misalign columns the moment the two
    shapes interleave. Widen the file's header instead of letting that
    happen (same fix as CsvOutcomesRepository.insert_outcome)."""
    file_exists = RETRAIN_LOG_PATH.exists() and RETRAIN_LOG_PATH.stat().st_size >= 10
    if not file_exists:
        pd.DataFrame([record]).to_csv(RETRAIN_LOG_PATH, mode="w", header=True, index=False)
        return

    existing_columns = pd.read_csv(RETRAIN_LOG_PATH, nrows=0).columns.tolist()
    new_columns = [c for c in record.keys() if c not in existing_columns]
    if new_columns:
        full_df = pd.read_csv(RETRAIN_LOG_PATH)
        for c in new_columns:
            full_df[c] = None
        full_df.to_csv(RETRAIN_LOG_PATH, mode="w", header=True, index=False)
        existing_columns = existing_columns + new_columns

    row_df = pd.DataFrame([record]).reindex(columns=existing_columns)
    row_df.to_csv(RETRAIN_LOG_PATH, mode="a", header=False, index=False)


def _all_outcomes() -> list[dict]:
    """Pages through every outcome via the active repository -- CSV or
    Supabase -- and flattens each to a common shape."""
    ctx = get_context()
    rows, offset, page = [], 0, 1000
    while True:
        batch = ctx.outcomes_repo.list_outcomes(limit=page, offset=offset)
        if not batch:
            break
        rows.extend(flatten_outcome_row(r) for r in batch)
        if len(batch) < page:
            break
        offset += page
    return rows


def _load_labeled_rows() -> pd.DataFrame:
    """Joins every outcome back to its original feature row in
    pending_events.csv -- the one place full features are always persisted
    locally, regardless of which OutcomesRepository is active. Returns one
    row per outcome that could be matched, carrying both the outcome's
    actual_* labels and the original feature columns."""
    outcomes = pd.DataFrame(_all_outcomes())
    if outcomes.empty:
        return pd.DataFrame()
    outcomes = outcomes[
        outcomes["source_event_id"].astype(str).str.strip().replace("nan", "") != ""
    ]
    if outcomes.empty or not PENDING_EVENTS_PATH.exists():
        return pd.DataFrame()

    pending = pd.read_csv(PENDING_EVENTS_PATH, dtype=str)
    merged = outcomes.merge(
        pending, left_on="source_event_id", right_on="event_id",
        how="inner", suffixes=("_outcome", ""),
    )
    return merged


def _filled_outcomes_count() -> int:
    return len(_all_outcomes())


def maybe_trigger_retrain() -> None:
    """Called as a FastAPI BackgroundTask after every outcome submission.
    Fires a retrain only on the exact request that crosses a new multiple
    of RETRAIN_BATCH_SIZE, so it doesn't refire on every subsequent call."""
    count = _filled_outcomes_count()
    if count > 0 and count % RETRAIN_BATCH_SIZE == 0:
        retrain_all_models()


# ════════════════════════════════════════════════════════════════════════════
# Closure model
# ════════════════════════════════════════════════════════════════════════════

def retrain_closure_model(merged: pd.DataFrame) -> dict:
    """Refits the closure classifier on historical rows + every live
    outcome with a usable actual_required_closure label."""
    from catboost import CatBoostClassifier

    if merged.empty:
        return {"status": "skipped", "reason": "no outcomes logged yet"}

    rows = merged[
        merged["actual_required_closure"].astype(str).str.strip().str.lower().isin(["true", "false"])
    ].copy()
    if rows.empty:
        return {"status": "skipped", "reason": "no closure outcomes logged yet"}

    for c in TRIAGE_NUM_FEATURES:
        rows[c] = pd.to_numeric(rows[c], errors="coerce")
    rows["requires_road_closure"] = (
        rows["actual_required_closure"].astype(str).str.strip().str.lower() == "true"
    ).astype(int)
    new_rows = rows[ALL_FEATURES + ["requires_road_closure"]].copy()

    hist = pd.read_parquet(ENRICHED_PATH)
    hist_rows = hist[ALL_FEATURES + ["requires_road_closure"]].copy()

    model_df = pd.concat([hist_rows, new_rows], ignore_index=True)
    for c in TRIAGE_CAT_FEATURES:
        model_df[c] = (
            model_df[c].astype(str).fillna("MISSING")
            .replace("None", "MISSING").replace("nan", "MISSING")
        )

    y = model_df["requires_road_closure"].astype(int)
    X = model_df[ALL_FEATURES]
    pos_rate = y.mean()
    scale_pos_weight = (1 - pos_rate) / pos_rate
    cat_idx = [X.columns.get_loc(c) for c in TRIAGE_CAT_FEATURES]
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    def make_estimator():
        return CatBoostClassifier(
            iterations=800, learning_rate=0.05, depth=7, loss_function="Logloss",
            eval_metric="AUC", scale_pos_weight=scale_pos_weight, cat_features=cat_idx,
            random_seed=42, verbose=False,
        )

    oof_proba = manual_oof_predict_proba(make_estimator, X, y, skf)
    oof_auc = float(roc_auc_score(y, oof_proba))

    calibrator = fit_isotonic_calibrator(oof_proba, y.values)
    import pickle
    with open(CLOSURE_CALIBRATED_PATH, "wb") as f:
        pickle.dump(
            {"calibrator": calibrator, "features": ALL_FEATURES, "cat_features": TRIAGE_CAT_FEATURES},
            f,
        )

    final_model = make_estimator()
    final_model.fit(X, y)
    final_model.save_model(str(CLOSURE_MODEL_PATH))

    return {
        "status": "retrained",
        "n_new_outcomes": int(len(new_rows)),
        "n_total_training_rows": int(len(model_df)),
        "oof_auc": round(oof_auc, 4),
    }


# ════════════════════════════════════════════════════════════════════════════
# Priority model
# ════════════════════════════════════════════════════════════════════════════

def retrain_priority_model(merged: pd.DataFrame) -> dict:
    """Refits the priority classifier on historical rows + every live
    outcome with a usable actual_priority label (HIGH/LOW)."""
    from catboost import CatBoostClassifier

    if merged.empty or "actual_priority" not in merged.columns:
        return {"status": "skipped", "reason": "no outcomes logged yet"}

    rows = merged[
        merged["actual_priority"].astype(str).str.strip().str.upper().isin(["HIGH", "LOW"])
    ].copy()
    if rows.empty:
        return {"status": "skipped", "reason": "no priority outcomes logged yet"}

    cat_features_pri = [c for c in TRIAGE_CAT_FEATURES if c != "corridor"]
    all_features_pri = cat_features_pri + TRIAGE_NUM_FEATURES

    for c in TRIAGE_NUM_FEATURES:
        rows[c] = pd.to_numeric(rows[c], errors="coerce")
    rows["priority_label"] = (rows["actual_priority"].astype(str).str.strip().str.upper() == "HIGH").astype(int)
    new_rows = rows[all_features_pri + ["priority_label"]].copy()

    hist = pd.read_parquet(ENRICHED_PATH)
    hist_pri = hist[hist["priority"].notna()].copy()
    hist_pri["priority_label"] = (hist_pri["priority"] == "High").astype(int)
    hist_rows = hist_pri[all_features_pri + ["priority_label"]].copy()

    model_df = pd.concat([hist_rows, new_rows], ignore_index=True)
    for c in cat_features_pri:
        model_df[c] = (
            model_df[c].astype(str).fillna("MISSING")
            .replace("None", "MISSING").replace("nan", "MISSING")
        )

    y = model_df["priority_label"].astype(int)
    X = model_df[all_features_pri]
    cat_idx = [X.columns.get_loc(c) for c in cat_features_pri]
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    def make_estimator():
        return CatBoostClassifier(
            iterations=600, learning_rate=0.05, depth=6, loss_function="Logloss",
            eval_metric="AUC", cat_features=cat_idx, random_seed=42, verbose=False,
        )

    oof_proba = manual_oof_predict_proba(make_estimator, X, y, skf)
    oof_auc = float(roc_auc_score(y, oof_proba))

    calibrator = fit_isotonic_calibrator(oof_proba, y.values)
    import pickle
    with open(PRIORITY_CALIBRATED_PATH, "wb") as f:
        pickle.dump(
            {"calibrator": calibrator, "features": all_features_pri, "cat_features": cat_features_pri},
            f,
        )

    final_model = make_estimator()
    final_model.fit(X, y)
    final_model.save_model(str(PRIORITY_MODEL_PATH))

    return {
        "status": "retrained",
        "n_new_outcomes": int(len(new_rows)),
        "n_total_training_rows": int(len(model_df)),
        "oof_auc": round(oof_auc, 4),
    }


# ════════════════════════════════════════════════════════════════════════════
# Duration models -- fast track (XGBoost quantile regressors)
# ════════════════════════════════════════════════════════════════════════════

def retrain_duration_fast_model(merged: pd.DataFrame) -> dict:
    """Refits the fast-track quantile regressors on historical fast-track
    rows + live outcomes with a usable actual_duration_hrs, for events that
    were triaged to the fast track (model_track == 'fast').

    Encoders: inference.py reconstructs fast_encoders deterministically by
    re-fitting LabelEncoder on backend.df_hist's fast-track rows alone (see
    the GAP FILL comment in inference.load_artifacts) -- it does not know
    about this retrain. To stay compatible with that reconstruction, the
    encoders here are fit the same way (historical fast-track rows only);
    any live row whose categorical value isn't in that historical
    vocabulary is dropped rather than crashing the encoder."""
    import xgboost as xgb

    all_features = ALL_FEATURES + DURATION_NUM_FEATURES_EXTRA
    hist = pd.read_parquet(ENRICHED_PATH)
    hist_fast = hist[(hist["model_track"] == "fast") & (hist["duration_valid"])].copy()
    if hist_fast.empty:
        return {"status": "skipped", "reason": "no historical fast-track rows"}
    hist_fast["log_duration"] = np.log1p(hist_fast["duration_hrs"])

    encoders = {}
    for c in TRIAGE_CAT_FEATURES:
        le = LabelEncoder()
        le.fit(hist_fast[c].astype(str).fillna("MISSING"))
        encoders[c] = le

    new_rows = pd.DataFrame()
    n_dropped_unseen = 0
    if not merged.empty and "model_track" in merged.columns:
        live = merged[merged["model_track"] == "fast"].copy()
        live["actual_duration_hrs"] = pd.to_numeric(live.get("actual_duration_hrs"), errors="coerce")
        live = live[live["actual_duration_hrs"].notna() & (live["actual_duration_hrs"] > 0)]
        for c in all_features:
            if c in TRIAGE_NUM_FEATURES or c in DURATION_NUM_FEATURES_EXTRA:
                live[c] = pd.to_numeric(live[c], errors="coerce")
        for c in TRIAGE_CAT_FEATURES:
            known = set(encoders[c].classes_)
            unseen_mask = ~live[c].astype(str).fillna("MISSING").isin(known)
            n_dropped_unseen += int(unseen_mask.sum())
            live = live[~unseen_mask]
        if not live.empty:
            live["log_duration"] = np.log1p(live["actual_duration_hrs"])
            new_rows = live[all_features + ["log_duration"]].copy()

    if new_rows.empty:
        return {"status": "skipped", "reason": "no fast-track outcomes logged yet"}

    model_df = pd.concat([hist_fast[all_features + ["log_duration"]], new_rows], ignore_index=True)
    X = model_df[all_features].copy()
    for c in TRIAGE_CAT_FEATURES:
        X[c] = encoders[c].transform(X[c].astype(str).fillna("MISSING"))
    y = model_df["log_duration"].values

    for q in [0.1, 0.5, 0.9]:
        model = xgb.XGBRegressor(
            objective="reg:quantileerror", quantile_alpha=q, n_estimators=400,
            max_depth=6, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8,
            min_child_weight=10, random_state=42,
        )
        model.fit(X, y)
        model.save_model(str(DURATION_FAST_Q_PATHS[q]))

    return {
        "status": "retrained",
        "n_new_outcomes": int(len(new_rows)),
        "n_total_training_rows": int(len(model_df)),
        "n_dropped_unseen_category": n_dropped_unseen,
    }


# ════════════════════════════════════════════════════════════════════════════
# Duration models -- slow track (Weibull AFT survival model)
# ════════════════════════════════════════════════════════════════════════════

def retrain_duration_slow_model(merged: pd.DataFrame) -> dict:
    """Refits the slow-track Weibull AFT model on historical slow-track
    rows (some censored) + live outcomes with a usable actual_duration_hrs
    for events triaged to the slow track. Officers only log a final
    actual_duration_hrs after a case is resolved, so every live row counts
    as an observed (non-censored) event -- there is no "still open" status
    being captured to make any of them censored."""
    from lifelines import WeibullAFTFitter

    hist = pd.read_parquet(ENRICHED_PATH)
    hist_slow = hist[hist["model_track"] == "slow"].copy()
    if hist_slow.empty:
        return {"status": "skipped", "reason": "no historical slow-track rows"}

    reference_now = hist["start_datetime"].max()
    hist_slow["survival_time_hrs"] = np.where(
        hist_slow["is_censored"] == 1,
        (reference_now - hist_slow["start_datetime"]).dt.total_seconds() / 3600,
        hist_slow["duration_hrs"]
    )
    hist_slow["event_observed"] = 1 - hist_slow["is_censored"]
    hist_slow = hist_slow[hist_slow["survival_time_hrs"].notna() & (hist_slow["survival_time_hrs"] > 0)]
    hist_slow["survival_time_hrs"] = hist_slow["survival_time_hrs"].clip(upper=2000)

    new_rows = pd.DataFrame()
    if not merged.empty and "model_track" in merged.columns:
        live = merged[merged["model_track"] == "slow"].copy()
        live["actual_duration_hrs"] = pd.to_numeric(live.get("actual_duration_hrs"), errors="coerce")
        live = live[live["actual_duration_hrs"].notna() & (live["actual_duration_hrs"] > 0)]
        if not live.empty:
            for c in AFT_NUM_FEATURES:
                live[c] = pd.to_numeric(live[c], errors="coerce")
            live["survival_time_hrs"] = live["actual_duration_hrs"].clip(upper=2000)
            live["event_observed"] = 1  # always observed -- see docstring
            new_rows = live[AFT_CAT_FEATURES + AFT_NUM_FEATURES + ["survival_time_hrs", "event_observed"]].copy()

    if new_rows.empty:
        return {"status": "skipped", "reason": "no slow-track outcomes logged yet"}

    hist_rows = hist_slow[AFT_CAT_FEATURES + AFT_NUM_FEATURES + ["survival_time_hrs", "event_observed"]].copy()
    aft_df = pd.concat([hist_rows, new_rows], ignore_index=True)
    # A handful of historical rows have NaN hour_ist/month (failed datetime
    # parsing upstream) -- WeibullAFTFitter can't fit through NaN covariates.
    aft_df = aft_df.dropna(subset=AFT_NUM_FEATURES + AFT_CAT_FEATURES)
    aft_df = pd.get_dummies(aft_df, columns=AFT_CAT_FEATURES, drop_first=True)

    aft_final = WeibullAFTFitter(penalizer=0.1)
    aft_final.fit(aft_df, duration_col="survival_time_hrs", event_col="event_observed")

    import pickle
    aft_columns = aft_df.drop(columns=["survival_time_hrs", "event_observed"]).columns.tolist()
    with open(DURATION_SLOW_WEIBULL_PATH, "wb") as f:
        pickle.dump({"model": aft_final, "columns": aft_columns}, f)

    return {
        "status": "retrained",
        "n_new_outcomes": int(len(new_rows)),
        "n_total_training_rows": int(len(aft_df)),
        "concordance": round(float(aft_final.concordance_index_), 4),
    }


# ════════════════════════════════════════════════════════════════════════════
# Orchestrator
# ════════════════════════════════════════════════════════════════════════════

def _push_to_supabase(metrics: dict) -> None:
    """Pushes the freshly retrained backend/models/ folder to Supabase
    Storage as the next version and promotes it. A failed push never
    rolls back the local retrain -- the new artifacts are already correct
    and serving locally; only the cloud sync didn't make it through."""
    if not USE_SUPABASE:
        return
    from backend.core.supabase_client import get_supabase_client
    from backend.services.model_manager import upload_new_version
    try:
        client = get_supabase_client()
        upload_new_version(client, metrics, MODELS_DIR)
    except Exception as e:
        logger.error(f"[ModelManager] Push to Supabase failed (local artifacts still updated): {e}")


def retrain_all_models() -> dict:
    """Retrains closure, priority, and both duration models in one pass,
    each independently skipped if it doesn't have enough labeled data yet.
    Always logs to RETRAIN_LOG_PATH and reports through retraining_repo."""
    started_at = datetime.now(timezone.utc).isoformat()
    ctx = get_context()
    run_id = ctx.retraining_repo.start_run()

    try:
        merged = _load_labeled_rows()

        results = {
            "closure": retrain_closure_model(merged),
            "priority": retrain_priority_model(merged),
            "duration_fast": retrain_duration_fast_model(merged),
            "duration_slow": retrain_duration_slow_model(merged),
        }

        any_retrained = any(r["status"] == "retrained" for r in results.values())
        if any_retrained:
            _push_to_supabase(results)

        record = {"retrained_at": started_at, "status": "completed",
                  **{f"{name}_status": r["status"] for name, r in results.items()}}
        _append_retrain_log(record)
        ctx.retraining_repo.complete_run(
            run_id, model_id="local", metrics=results, rows_used=int(len(merged)),
        )
        return results

    except Exception as e:
        _append_retrain_log({"retrained_at": started_at, "status": "failed", "error": str(e)})
        ctx.retraining_repo.fail_run(run_id, str(e))
        return {"status": "failed", "error": str(e)}


# Backwards-compatible name -- older callers/tests may still reference this.
def retrain_triage_closure_model() -> dict:
    return retrain_closure_model(_load_labeled_rows())
