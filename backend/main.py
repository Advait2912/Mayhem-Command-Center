"""
main.py — FastAPI application entry point.

Run with:
    uvicorn backend.main:app --reload --port 8000

Startup lifecycle (via lifespan):
  1. load_artifacts() — blocks until all models + data are loaded (~10-25s)
  2. set_context(ctx) — stores singleton for all request handlers
  3. Server ready

No business logic lives here. All routing is delegated to backend/api/*.py.
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import events, meta, outcomes, predict
from backend.core.config import CORS_ORIGINS, USE_SUPABASE, IS_PRODUCTION, OUTCOMES_LOG_PATH
from backend.core.context import set_context
from backend.core.supabase_client import get_supabase_client
from backend.services.inference import load_artifacts
from backend.services.db.outcomes_repo import CsvOutcomesRepository, SupabaseOutcomesRepository
from backend.services.db.retraining_repo import NoopRetrainingRepository

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gridlock")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: load all artifacts once at startup."""
    print("[GridLock] Loading artifacts — this takes ~10-25 seconds on first start...")
    ctx = load_artifacts()
    
    # ── Repository Wiring ──────────────────────────────────────────────────────
    if USE_SUPABASE:
        logger.info("[DB] Mode: Supabase")
        try:
            client = get_supabase_client()
            # Mandatory Health Check: verify connectivity and schema
            client.table("models").select("id").limit(1).execute()
            logger.info("[DB] Health check passed")
            
            ctx.outcomes_repo = SupabaseOutcomesRepository(client)
            ctx.retraining_repo = NoopRetrainingRepository() 
        except Exception as e:
            logger.error(f"[DB] Health check failed: {e}")
            if IS_PRODUCTION:
                # Fail fast in production
                raise RuntimeError(f"CRITICAL: Supabase connectivity failed in production: {e}")
            else:
                # In local dev, we fall back if Supabase was configured but is unreachable
                logger.warning("[DB] Falling back to CSV due to Supabase failure in local mode.")
                ctx.outcomes_repo = CsvOutcomesRepository(OUTCOMES_LOG_PATH)
                ctx.retraining_repo = NoopRetrainingRepository()
    else:
        logger.info("[DB] Mode: CSV")
        ctx.outcomes_repo = CsvOutcomesRepository(OUTCOMES_LOG_PATH)
        ctx.retraining_repo = NoopRetrainingRepository()

    set_context(ctx)
    print(f"[GridLock] Ready. {len(ctx.df_hist)} events loaded, "
          f"{len(ctx.G_main.nodes)} road nodes available.")
    yield
    # Shutdown: nothing to clean up (all state is in-memory)
    print("[GridLock] Shutting down.")


app = FastAPI(
    title="GridLock Command Center",
    description="Event-driven traffic advisory system for Bengaluru — FastAPI backend.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta.router,     prefix="/api", tags=["Meta"])
app.include_router(events.router,   prefix="/api", tags=["Events"])
app.include_router(predict.router,  prefix="/api", tags=["Predict"])
app.include_router(outcomes.router, prefix="/api", tags=["Outcomes"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "GridLock Command Center API"}
