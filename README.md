# GridLock — Traffic Intelligence Command Center

GridLock is a high-ops tactical decision-support system designed for Bengaluru's traffic police. Unlike a generic analytics dashboard, GridLock focuses on an **Operational Intelligence Pipeline**: transforming a raw traffic event into an actionable deployment report.

## System Architecture

The project is built with a strict separation of concerns and isolated environments to prevent global system corruption.

###  Backend (Python/FastAPI)
- **Location**: `/backend`
- **Isolation**: Managed via a local virtual environment (`venv`).
- **Core Engine**: FastAPI providing a high-performance asynchronous API.
- **Operational Pipeline**: 
  - `POST /api/generate-report`: The primary entry point. It accepts event details and returns the canonical Operational Intelligence Report.
- **Current State**: Implemented with a **Dynamic Mock Engine**. It uses rule-based profiles to generate plausible, event-specific intelligence (Triage, Duration, Resources) rather than static responses.

###  Frontend (React/Vite)
- **Location**: `/frontend`
- **Styling**: Custom "High-Ops" dark theme using CSS variables for consistent tactical aesthetics.
- **Layout**: 3-Panel Grid Architecture:
    1. **Control Panel**: Event input and Scenario Quick-Select.
    2. **Tactical Map**: Interactive Leaflet map focused on Bengaluru, featuring dynamic centering and spatial impact visualization.
    3. **Intelligence Report**: Modular feed of data cards (Triage, Duration, Spatial, Resources, Similarities, Conflicts).
- **Current State**: Fully functional Command Center UI with integrated API layer and scenario-driven demo mode.

---

##  Getting Started

### Quick Start
To launch the entire system (Backend & Frontend) in one go:<br>
for linux setup after cloning(remeber to make both files *executable* by chmod +x <filename>(for linux only))
``` bash
./setup.sh
```
```bash
./run.sh
```
for windows setup after cloning
``` bash
./setup.bat
```
to run in windows
```
./run.bat
```

### Manual Setup
**Backend Setup**
```bash
cd backend
source venv/bin/activate  # Linux/macOS
# or .\venv\Scripts\activate # Windows
pip install -r requirements.txt # (or install fastapi uvicorn pydantic manually)
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

##  Current Feature Set

### 1. Event Simulation Pipeline
Users can manually enter event details or use the **Scenario Quick-Select** to instantly trigger reports for common Bengaluru traffic crises:
- **RCB Match** (Mass Gathering)
- **VIP Movement** (High Security)
- **Bus Breakdown** (Obstruction)
- **Water Logging** (Environmental)
- **Metro Construction** (Infrastructure)

### 2. Tactical Mapping
- **Dynamic Centering**: The map automatically pans to the event location when a scenario is selected.
- **Spatial Impact**: Renders a red impact radius based on the `radius_km` provided by the prediction pipeline.

### 3. Intelligence Reporting
The report is broken down into operational modules:
- **Triage**: Priority level and Cascade Risk score.
- **Duration**: Expected resolution time (P50/P90).
- **Spatial**: Affected junctions and alternate routing.
- **Resources**: Personnel requirements and diversion advisories.
- **Historical Context**: Similar past events for case-based reasoning.
- **Conflict Analysis**: Detection of resource contention with other active events.

---

## 📋 Data Contract (Canonical)

### Input
```json
{
  "event_type": "string",
  "location": "string",
  "zone": "string",
  "time": "string",
  "description": "string"
}
```

### Output
The backend returns a comprehensive report containing:
- `triage`: `{ closure_probability, priority, cascade_risk }`
- `duration`: `{ expected_hours, p10, p50, p90 }`
- `spatial_impact`: `{ affected_junctions, radius_km, estimated_delay_minutes, alternate_route }`
- `resources`: `{ officers_needed, barricade_points, diversion_advisory }`
- `similar_events`: `Array<{ summary, avg_resolution_hours, officers_used, closure_required }>`
- `conflict_check`: `{ has_conflict, message }`

---

## 🗺️ Roadmap Status
- [x] **Day 1: Shell & Map** (Complete)
- [x] **Day 2: The Prediction Pipeline** (Complete)
- [ ] **Day 3: Intelligence Report UI** (Pending)
- [ ] **Day 4: Spatial Impact Visualizations** (Pending)
- [ ] **Day 5: Ops Intelligence** (Pending)
- [ ] **Day 6: Polish & Demo Mode** (Pending)
