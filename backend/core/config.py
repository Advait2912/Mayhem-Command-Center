"""
core/config.py — All path constants for the backend.
All paths are absolute, computed from this file's location.
No relative paths anywhere in the backend.
"""
from pathlib import Path
import os

# Root directories
BACKEND_DIR = Path(__file__).parent.parent
MODELS_DIR = BACKEND_DIR / "models"
DATA_DIR = BACKEND_DIR / "data"

# ── Data files ────────────────────────────────────────────────────────────────
ENRICHED_PATH = DATA_DIR / "events_enriched.parquet"
CENTRALITY_CACHE = DATA_DIR / "node_centrality.parquet"
RAINFALL_CACHE = DATA_DIR / "rainfall_cache.parquet"
GRAPH_PATH = DATA_DIR / "bengaluru_major_roads.graphml"
OUTCOMES_LOG_PATH = DATA_DIR / "outcomes_log.csv"
PENDING_EVENTS_PATH = DATA_DIR / "pending_events.csv"
RETRAIN_LOG_PATH = DATA_DIR / "retrain_log.csv"

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)
IS_PRODUCTION = bool(os.getenv("RAILWAY_ENVIRONMENT"))
MODEL_CACHE_DIR = Path(os.getenv("MODEL_CACHE_DIR", "/tmp/model_cache"))

# Self-retraining loop: every time this many *new* outcome rows with a
# filled-in actual_required_closure accumulate, the triage closure model
# retrains automatically in the background. No human approval gate -- see
# services/retrain.py for the full loop.
RETRAIN_BATCH_SIZE = 100

# ── Model files ───────────────────────────────────────────────────────────────
CBR_INDEX_PATH = MODELS_DIR / "cbr_index.pkl"
BASELINE_CACHE = MODELS_DIR / "baseline_table.pkl"
TARGET_ENCODING_PATH = MODELS_DIR / "target_encoding_maps.json"
CASCADE_SCALER_PATH = MODELS_DIR / "cascade_risk_scaler.json"
PRIORITY_THRESHOLD_PATH = MODELS_DIR / "priority_threshold.json"
CLOSURE_CALIBRATED_PATH = MODELS_DIR / "triage_model_closure_calibrated.pkl"
PRIORITY_CALIBRATED_PATH = MODELS_DIR / "triage_model_priority_calibrated.pkl"
CLOSURE_MODEL_PATH = MODELS_DIR / "triage_model_closure.cbm"
PRIORITY_MODEL_PATH = MODELS_DIR / "triage_model_priority.cbm"
DURATION_SLOW_WEIBULL_PATH = MODELS_DIR / "duration_model_slow_weibull.pkl"

DURATION_FAST_Q_PATHS = {
    0.1: MODELS_DIR / "duration_model_fast_q10.json",
    0.5: MODELS_DIR / "duration_model_fast_q50.json",
    0.9: MODELS_DIR / "duration_model_fast_q90.json",
}

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ORIGINS = ["*"]  # Restrict in production
