# GridLock Command Center

GridLock is an event-driven congestion pipeline for the Bengaluru Traffic Police. It ingests historical and hypothetical traffic events, processes them through a multi-stage machine learning pipeline (closure triage, duration prediction, spatial conflict detection, and network routing), and surfaces actionable advisories via a React/Vite dashboard.

This repository is divided into two primary standalone systems:

1. **`backend/`** — A FastAPI REST API containing the ML models, spatial logic, and Pydantic schemas.
2. **`frontend/`** — A React 18 Single Page Application (SPA) built with Vite and TypeScript, employing a custom dark mode UI.

## Getting Started

A convenience script `run.sh` is provided in the root directory to boot both the frontend and backend servers concurrently.

### Prerequisites

You must have the following installed in your WSL (Ubuntu) environment:
- Python 3.12+
- Node.js (v18+) & NPM

### Setup & Run

1. **Activate Environment & Install Dependencies (First time only):**
   ```bash
   # Backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r backend/requirements.txt

   # Frontend
   cd frontend
   npm install
   cd ..
   ```

2. **Run the Application:**
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

   This will start:
   - **Backend API:** `http://localhost:8000` (Access the Swagger UI at `/docs`)
   - **Frontend UI:** `http://localhost:5173`

> **Note:** The backend loads ~18MB of ML artifacts and spatial graphs into memory on boot. It may take 10-25 seconds before the endpoints become responsive.

## Architecture & Agent Context

If you are an AI agent or a developer looking to understand the core contracts and folder structure, please refer to:
👉 **[`docs/model_context.md`](docs/model_context.md)**
