# Praeventix - Pre-Delinquency Intervention Engine

**Team Code Atlantis · Hackathon**

Praeventix is an AI-assisted early warning and intervention platform for banking collections teams.  
It predicts delinquency risk before missed payments, explains risk drivers, and helps trigger compliant outreach.

## What This Repository Contains

- `backend`: FastAPI services, ML inference/training, SHAP explainability, intervention agent, configs, tests
- `frontend`: React + Vite risk operations dashboard (Overview, AI Predict, Live Flagging, Rules/SHAP, Outreach)
- Root docs and helper scripts (`README.md`, `ARCHITECTURE.md`, `start.ps1`)

## Stack

- Backend: Python, FastAPI, Pandas, NumPy, LightGBM, PyTorch, SHAP, scikit-learn, python-jose
- Agent layer: Policy rules + PII masking + pluggable LLM client (mock/Anthropic/OpenAI)
- Frontend: React 18, Vite 5, Axios, Recharts
- Optional serving: BentoML service (`backend/service.py`)

## Quick Start

### 1) Prerequisites

- Python 3.11+ (project can run on newer Python as well)
- Node.js 18+
- npm

### 2) Backend setup

```powershell
cd backend
pip install -r requirements.txt
```

### 3) Data and model artifacts

Use existing provided data/artifacts or regenerate:

```powershell
# from backend/
python generate_data.py
python training/train_all.py
python generate_scored_customers.py
```

### 4) Start backend API

```powershell
cd backend
uvicorn api.main:app --reload --port 8000
```

### 5) Start frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend is configured for port `3000` in `frontend/vite.config.js`.

### 6) Open app

- Dashboard: <http://localhost:3000>
- API docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

### Optional one-click launch (Windows)

From repo root:

```powershell
.\start.ps1
```

Note: `start.ps1` prints `5173`, but Vite config currently sets `3000`.

## Backend API Overview

### Auth/health

- `GET /health`
- `POST /auth/token`

### Prediction APIs

- `POST /api/predict` (single feature payload)
- `POST /api/predict/batch`
- `GET /api/model-info`

### Customer risk APIs

- `GET /api/customers/at-risk`
- `GET /api/customers/{customer_id}`
- `GET /api/customers/{customer_id}/history`
- `GET /api/customers/{customer_id}/explain`
- `GET /api/customers/{customer_id}/timeline`
- `GET /api/customers/{customer_id}/ability-willingness`

### Intervention and metrics APIs

- `POST /api/interventions/trigger`
- `POST /api/interventions/record`
- `GET /api/interventions/log`
- `GET /api/metrics/overview`
- `GET /api/metrics/landing`
- `POST /api/rules/impact`
- `POST /api/rules/save`

## ML/Scoring Pipeline

- Feature inputs center around weekly behavioral stress signals (salary delay, savings change, credit utilization, failed auto-debits, lending app activity, cashflow, etc.)
- Models:
  - LightGBM classifier
  - GRU temporal model
  - Logistic ensemble meta-learner
  - Isolation Forest anomaly detector
- Explainability:
  - SHAP feature attributions
  - Human explanation text (template or Gemini-backed when key is provided)

## Agentic Intervention Layer

`backend/agent/intervention_agent.py` orchestrates:

- Risk gate and policy eligibility checks
- PII masking before LLM prompts
- LLM-based intervention selection with rule-based fallback
- Compliance filtering (length, banned/aggressive terms)
- Dispatch + intervention log append

LLM mode is controlled by `backend/config/llm_config.yaml` and environment keys.

## Frontend Modules

- `Overview`: KPIs, risk distribution, velocity, portfolio exposure, model status
- `AI Predict`: manual/preset/CSV prediction, SHAP bars, PDF report export
- `Live Flagging`: searchable at-risk table, modal drill-down, timeline, explainability
- `Rules & SHAP`: rule tuning, impact simulation, SHAP explain view, SHAP PDF export
- `Outreach`: intervention queue, channel/message workflow, dispatch logging

## Repository Structure

```text
SFIT-Mumbai/
  backend/
    api/
    agent/
    config/
    data/
    inference/
    models/
    pipeline/
    tests/
    training/
    requirements.txt
    service.py
  frontend/
    src/
    package.json
    vite.config.js
  ARCHITECTURE.md
  README.md
  start.ps1
```

## Running Tests

From `backend`:

```powershell
python -m pytest tests
```

There are targeted test modules for API imports/auth, feature engineering, sequence building, LightGBM config/artifacts, and intervention agent behavior.

## Configuration Notes

- Risk thresholds and compliance controls: `backend/config/thresholds.yaml`
- Model hyperparameters/features: `backend/config/model_config.yaml`
- LLM backend mode: `backend/config/llm_config.yaml`
- Dynamic rule settings: `backend/config/rules.json`

## Known Operational Notes

- Some code paths reference both synthetic behavioral datasets and Lending Club style training conventions; this is intentional in the current hackathon codebase but means naming and comments can look mixed.
- `backend/data/praeventix_cache.db` is tracked via Git LFS (`.gitattributes`) for API-side query caching.
- Auth is demo-oriented by default (`admin` / `admin123`) and should be hardened before production use.

## Extended Documentation

See `ARCHITECTURE.md` for detailed architecture, runtime flow, data/model layers, and deployment considerations.
