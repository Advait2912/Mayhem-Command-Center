# GridLock Command Center

GridLock is an event‑driven congestion pipeline for the Bengaluru Traffic Police. It ingests historical and hypothetical traffic events, processes them through a multi‑stage machine‑learning pipeline (closure triage, duration prediction, spatial conflict detection, and network routing), and surfaces actionable advisories via a React/Vite dashboard.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Quick start (local development)](#quick-start-local-development)
- [Environment variables](#environment-variables)

- [Model loading & inference](#model-loading--inference)
- [Self‑retraining](#self-retraining)
- [Deployment modes (CSV vs Supabase)](#deployment-modes-csv-vs-supabase)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [How to start the demo](#how-to-start-the-demo)

## Overview
The repository is split into two independent parts:

* **backend/** – FastAPI server that loads all ML artefacts, provides a set of REST endpoints, and handles outcome logging & automatic model retraining.
* **frontend/** – React 18 SPA built with Vite and TypeScript, offering a dark‑mode UI for operators to view events, request predictions and log real outcomes.

## Architecture
```mermaid
graph LR
    UI[React Frontend] -->|REST| API[FastAPI Backend]
    API -->|load_artifacts| Ctxt[InferenceContext (singleton)]
    Ctxt -->|graph & models| Pipeline[Inference / Pipeline]
    API -->|POST /predict| Feat[Featurisation]
    Feat --> Score[Scoring (CatBoost, XGBoost, Weibull)]
    Score --> AdvBuilder[Advisory Assembly]
    AdvBuilder -->|JSON| UI
    API -->|GET /events| DB[Historical Events (Parquet)]
    API -->|GET/POST /outcomes| OutcomesRepo[(CSV / Supabase)]
    OutcomesRepo --> Retrain[Self‑retraining (BackgroundTasks)]
    Retrain --> ModelMgr[Model Manager (Upload / Promote)]
```

## Quick start (local development)

### Prerequisites
- **Python** 3.12+
- **Node.js** v18+ and **npm**
- **Git** (to clone the repo)

### Setup
```bash
# Clone the repo (if you haven't already)
git clone <repo‑url>
cd gridlock_web

# Python environment
python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate
pip install -r requirements.txt

# Front‑end dependencies
cd frontend
npm install
cd ..
```

### Initial data download
The first start‑up will automatically download the required model artefacts into `$MODEL_CACHE_DIR` (default `/tmp/model_cache`). No manual step is required.

## Environment variables
| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL. If unset → CSV mode. | – |
| `SUPABASE_SERVICE_KEY` | Supabase service‑role key. | – |
| `RAILWAY_ENVIRONMENT` | Set in production to enable strict DB health checks. | – |
| `MODEL_CACHE_DIR` | Directory used to store downloaded model versions. | `/tmp/model_cache` |
| `TAVILY_API_KEY` | Optional API key for live‑event enrichment. | – |
| `CORS_ORIGINS` | Comma‑separated list of allowed origins (used by FastAPI CORS middleware). | `*` |
| `RETRAIN_BATCH_SIZE` | Number of new outcomes required to trigger a retraining run. | `100` |

## How to start the demo

1. **Install dependencies**
   *Linux / macOS*:
   ```bash
   chmod +x setup.sh
   ./setup.sh    # creates a virtual‑env, installs Python & Node dependencies
   ```
   *Windows*:
   ```cmd
   setup.bat     # creates a virtual‑env, installs Python & Node dependencies
   ```

2. **Run the application**
   *Linux / macOS*:
   ```bash
   ./run.sh      # starts the FastAPI backend first, then the React frontend
   ```
   *Windows*:
   ```cmd
   run.bat       # starts the backend, waits for it, then launches the frontend
   ```

3. Open a browser:
   - UI: <http://localhost:5173>
   - API docs: <http://localhost:8000/docs>

> **Note (CSV mode only):** After a retraining run the backend must be restarted to load the newly‑written model artefacts. The console prints a log line reminding you to do so.

## Model loading & inference
At startup FastAPI’s `lifespan` hook calls `load_artifacts()` which:
1. Reads the enriched events parquet (`ENRICHED_PATH`).
2. Loads the OSM road graph and centrality cache.
3. Instantiates CatBoost classifiers, XGBoost quantile regressors and a Weibull AFT model.
4. Stores everything in a global `InferenceContext` singleton.

All prediction requests (`POST /api/predict`) use this in‑memory context, so there is **no I/O latency** after the initial warm‑up.

## Self‑retraining
* `POST /api/outcomes` stores officer‑logged outcomes.
* A FastAPI `BackgroundTask` calls `maybe_trigger_retrain()`.
* When `RETRAIN_BATCH_SIZE` outcomes have accumulated, the training pipeline:
  - Merges the new outcomes with the pending‑event feature rows.
  - Retrains the closure, priority, fast‑track duration and slow‑track duration models.
  - Overwrites the versioned artefacts on disk.
  - **In CSV mode** the process **does not** reload the models automatically – a log line tells the operator to restart the backend.
  - **In Supabase mode** the new artefacts are uploaded, a candidate version is inserted into the `models` table and promoted automatically via the `promote_model` RPC.

## Deployment modes (CSV vs Supabase)
| Mode | Selection | Persistence | Retraining behaviour |
|------|-----------|-------------|----------------------|
| **CSV (local development)** | `SUPABASE_URL` **or** `SUPABASE_SERVICE_KEY` **unset** | Outcomes → `backend/data/outcomes_log.csv`<br>Pending events → `backend/data/pending_events.csv` | After `RETRAIN_BATCH_SIZE` outcomes the model files under `backend/models/versioned/` are overwritten. The running process keeps the old models in memory; **restart the backend** to load the new ones. The console prints a clear log message informing the operator to restart. |
| **Supabase (production / cloud)** | Both `SUPABASE_URL` **and** `SUPABASE_SERVICE_KEY` defined. | Outcomes stored in a Supabase Postgres table (`outcomes`). Model artefacts are uploaded to a Supabase storage bucket (`models/`). | When the batch threshold is reached, the new artefacts are uploaded, a candidate version is inserted into the `models` table and promoted via the `promote_model` RPC. The backend continues serving with the previous in‑memory models; the next start‑up will load the freshly‑promoted version. |

> The CSV mode is intended for hackathon demos where the judges can manually restart the backend after a retraining run. Supabase mode is the production‑ready workflow that handles version promotion automatically.

## Troubleshooting
- **Model files missing** – Ensure `backend/models/versioned/` contains the required `.cbm`, `.pkl` and `.json` files. Run `python -c "from backend.services.inference import load_artifacts; load_artifacts()"` to see any missing‑file errors.
- **Supabase connectivity** – Verify both `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are exported. The startup log will show `[DB] Health check passed` or fall back to CSV mode.
- **Stale models after retraining (CSV mode)** – Look for the log line `"[Retrain] CSV mode – new model artefacts written. Restart the backend to load the updated models."` and restart the backend (`Ctrl‑C` then `./run.sh`).
- **CORS errors** – Adjust `CORS_ORIGINS` in the environment to restrict origins for production.
- **High memory usage on start‑up** – The artefacts (~18 MiB) plus the full enriched dataframe (~hundreds of MB) are kept in RAM. Consider running on a machine with at least 2 GiB of free memory.


## License
This project is licensed under the **MIT License** – see the `LICENSE` file for details.


GridLock is an event-driven congestion pipeline for the Bengaluru Traffic Police. It ingests historical and hypothetical traffic events, processes them through a multi-stage machine learning pipeline (closure triage, duration prediction, spatial conflict detection, and network routing), and surfaces actionable advisories via a React/Vite dashboard.

This repository is divided into two primary standalone systems:

1. **`backend/`** — A FastAPI REST API containing the ML models, spatial logic, and Pydantic schemas.
2. **`frontend/`** — A React 18 Single Page Application (SPA) built with Vite and TypeScript, employing a custom dark mode UI.

