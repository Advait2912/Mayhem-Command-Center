"""
services/retrain.py — Self-retraining loop for the triage closure model.

Trigger: every time RETRAIN_BATCH_SIZE (see core/config.py) new
officer-submitted outcomes with a filled-in actual_required_closure
accumulate, the closure classifier retrains automatically in the
background -- no human approval gate. See api/outcomes.py for the trigger
check that fires this after every POST /api/outcomes.

Retraining only overwrites the model artifacts on disk. The running server
keeps serving whichever model it loaded at startup (services/inference.py
load_artifacts() caches it in a singleton) until its next restart -- the
new artifacts just sit on disk ready for then.

Where the labeled data comes from: every POST /api/predict persists the
full feature row it computed for that event, keyed by a generated event_id
(see inference.py::_persist_pending_event). When an officer later logs the
real outcome for that event, the outcome row carries that same id as
source_event_id. Joining the two on that id reconstructs a fully-featured,
correctly-labeled training row -- the same row stage5_triage would have
seen as a historical event, just freshly observed.
"""

import pickle
from datetime import datetime, timezone

import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

from backend.core.config import (
    ENRICHED_PATH, OUTCOMES_LOG_PATH, PENDING_EVENTS_PATH,
    CLOSURE_MODEL_PATH, CLOSURE_CALIBRATED_PATH, RETRAIN_LOG_PATH,
    RETRAIN_BATCH_SIZE,
)
from backend.services.pipeline import (
    TRIAGE_CAT_FEATURES, TRIAGE_NUM_FEATURES,
    manual_oof_predict_proba, fit_isotonic_calibrator,
)

ALL_FEATURES = TRIAGE_CAT_FEATURES + TRIAGE_NUM_FEATURES


def _filled_outcomes_count() -> int:
    """Counts outcome rows that have a usable ground-truth label."""
    if not OUTCOMES_LOG_PATH.exists():
        return 0
    df = pd.read_csv(OUTCOMES_LOG_PATH, dtype=str)
    if "actual_required_closure" not in df.columns:
        return 0
    vals = df["actual_required_closure"].astype(str).str.strip().str.lower()
    return int(vals.isin(["true", "false"]).sum())


def _append_retrain_log(record: dict) -> None:
    out_df = pd.DataFrame([record])
    write_header = not RETRAIN_LOG_PATH.exists()
    out_df.to_csv(RETRAIN_LOG_PATH, mode="a", header=write_header, index=False)


def maybe_trigger_retrain() -> None:
    """Called as a FastAPI BackgroundTask after every outcome submission.
    Fires a retrain only on the exact request that crosses a new multiple
    of RETRAIN_BATCH_SIZE, so it doesn't refire on every subsequent call."""
    count = _filled_outcomes_count()
    if count > 0 and count % RETRAIN_BATCH_SIZE == 0:
        retrain_triage_closure_model()


def retrain_triage_closure_model() -> dict:
    """Joins officer-confirmed outcomes back to their original feature
    rows, appends them to the historical training set, and retrains the
    closure classifier using the same manual-OOF + isotonic-calibration
    procedure as services/pipeline.py::stage5_triage. Overwrites
    triage_model_closure.cbm + triage_model_closure_calibrated.pkl."""
    from catboost import CatBoostClassifier

    try:
        if not PENDING_EVENTS_PATH.exists() or not OUTCOMES_LOG_PATH.exists():
            result = {"status": "skipped", "reason": "no pending events or outcomes logged yet"}
            _append_retrain_log({"retrained_at": datetime.now(timezone.utc).isoformat(), **result})
            return result

        pending = pd.read_csv(PENDING_EVENTS_PATH, dtype=str)
        outcomes = pd.read_csv(OUTCOMES_LOG_PATH, dtype=str)

        outcomes = outcomes[
            outcomes["actual_required_closure"].astype(str).str.strip().str.lower().isin(["true", "false"])
        ]
        outcomes = outcomes[outcomes["source_event_id"].astype(str).str.strip().replace("nan", "") != ""]

        # suffixes=("_outcome", "") keeps the *pending* (feature) side's
        # column names bare, since those are the real feature values --
        # the outcomes side only contributes source_event_id + the label.
        merged = outcomes.merge(
            pending, left_on="source_event_id", right_on="event_id",
            how="inner", suffixes=("_outcome", ""),
        )
        if merged.empty:
            result = {"status": "skipped", "reason": "no outcomes could be matched back to a feature row"}
            _append_retrain_log({"retrained_at": datetime.now(timezone.utc).isoformat(), **result})
            return result

        for c in TRIAGE_NUM_FEATURES:
            merged[c] = pd.to_numeric(merged[c], errors="coerce")
        merged["requires_road_closure"] = (
            merged["actual_required_closure"].astype(str).str.strip().str.lower() == "true"
        ).astype(int)

        new_rows = merged[ALL_FEATURES + ["requires_road_closure"]].copy()

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
        with open(CLOSURE_CALIBRATED_PATH, "wb") as f:
            pickle.dump(
                {"calibrator": calibrator, "features": ALL_FEATURES, "cat_features": TRIAGE_CAT_FEATURES},
                f,
            )

        final_model = make_estimator()
        final_model.fit(X, y)
        final_model.save_model(str(CLOSURE_MODEL_PATH))

        result = {
            "status": "retrained",
            "n_new_outcomes": int(len(new_rows)),
            "n_total_training_rows": int(len(model_df)),
            "oof_auc": round(oof_auc, 4),
        }
        _append_retrain_log({"retrained_at": datetime.now(timezone.utc).isoformat(), **result})
        return result

    except Exception as e:
        result = {"status": "failed", "error": str(e)}
        _append_retrain_log({"retrained_at": datetime.now(timezone.utc).isoformat(), **result})
        return result
