# Praeventix Architecture

This document describes the implemented architecture in the current repository state.

## High-Level System

Praeventix is a full-stack risk operations system with four major runtime layers:

1. Data + cache layer (`backend/data`, SQLite cache in API process)
2. ML inference layer (`backend/inference`)
3. Intervention decision layer (`backend/agent`)
4. API + dashboard layer (`backend/api`, `frontend/src`)

Core path:

```text
Weekly/customer behavioral data + scored JSON
  -> FastAPI data/cache layer
  -> model inference and explainability
  -> policy + LLM intervention decision
  -> REST APIs
  -> React operator dashboard
```

## Repository Architecture

```text
backend/
  api/                 # FastAPI app, auth, schemas, endpoints
  agent/               # intervention orchestration, policy, LLM, PII masking
  config/              # thresholds, model params, llm mode, rules
  data/                # csv/json/sqlite runtime datasets
  inference/           # predictor, SHAP, explanation, batch scoring
  pipeline/            # feature engineering module
  training/            # train scripts for all model stages
  tests/               # API/agent/feature/model smoke tests
  models/              # persisted model artifacts
frontend/
  src/
    api/               # axios API client
    components/        # dashboard modules + UI widgets
```

## Backend Runtime Design

### FastAPI app (`backend/api/main.py`)

The API process is the central orchestrator and performs:

- Initial data loading from CSV/JSON
- File mtime snapshotting and refresh (`ensure_data_fresh`)
- SQLite cache rebuild (`rebuild_sql_cache`) for large-table query speed
- Lazy loading of model predictor and intervention agent instances
- CORS middleware setup and auth route handling

Important runtime choices:

- Transactions are moved to SQLite (`transactions_cache`) for timeline queries
- In-memory + SQLite hybrid is used for responsiveness
- The rate limiter class exists, but there is no active middleware hook currently enforcing it globally

### Data files and cache behavior

Main files referenced by API:

- `customers.csv`
- `weekly_behavioral_features.csv`
- `intervention_log.csv`
- `scored_customers.json`
- `transactions.csv`
- `praeventix_cache.db` (materialized query cache)

Cache lifecycle:

- API starts -> loads data -> builds cache
- File timestamp changes detected -> reload + cache rebuild

## ML Architecture

### Inference service (`backend/inference/predict.py`)

`RiskPredictor` loads:

- LightGBM model (`lgbm_model.pkl`)
- GRU model (`gru_model.pt`) and scaler (`gru_scaler.pkl`)
- Ensemble model (`ensemble_meta.pkl`)
- Isolation Forest (`isolation_forest.pkl`)

Prediction modes:

- `predict_from_features`: direct API scoring from feature payload
- `predict_single`: customer-id/week lookup against behavioral dataset
- `batch_predict`: iterate customer predictions

Risk classification thresholds come from `backend/config/thresholds.yaml`.

### Explainability

Explainability stack:

- SHAP TreeExplainer for LightGBM contributions
- Confidence estimate via variance across model probabilities
- Explanation text generation in `inference/ai_explain.py`
  - Gemini API when `GEMINI_API_KEY` exists
  - fallback template narrative otherwise

### Training pipeline

Training scripts (modular):

- `train_lightgbm.py`
- `train_gru.py`
- `train_ensemble.py`
- `train_isolation_forest.py`
- `train_all.py` orchestrator

Also present:

- `train_real_data.py` (combined real + synthetic alternative workflow)
- `generate_scored_customers.py` (offline bulk scoring artifact generation)

## Intervention Agent Architecture

### Components

- `intervention_agent.py`: orchestrates stateful decision pipeline
- `policy_rules.py`: deterministic eligibility checks
- `pii_masking.py`: profile masking and message redaction
- `llm_client.py`: backend abstraction (`mock`, `anthropic`, `openai`)

### Decision flow

1. Risk gate (`MONITOR_ONLY` short-circuit below threshold)
2. Policy eligibility + cooldown checks
3. LLM decision planner (JSON contract)
4. Compliance filter:
   - allowed intervention set
   - max message length
   - aggressive-word blocklist
   - customer-name redaction
5. Dispatch/log append

Fallback behavior:

- On LLM parse/transport failures, rules engine picks intervention.
- On repeated compliance failure, SMS fallback message is forced.

## API Surface (Implemented)

### Core

- `GET /health`
- `POST /auth/token`

### Prediction

- `POST /api/predict`
- `POST /api/predict/batch`
- `GET /api/model-info`

### Customer intelligence

- `GET /api/customers/at-risk`
- `GET /api/customers/{customer_id}`
- `GET /api/customers/{customer_id}/history`
- `GET /api/customers/{customer_id}/explain`
- `GET /api/customers/{customer_id}/timeline`
- `GET /api/customers/{customer_id}/ability-willingness`

### Intervention + metrics + rules

- `POST /api/interventions/trigger`
- `POST /api/interventions/record`
- `GET /api/interventions/log`
- `GET /api/metrics/overview`
- `GET /api/metrics/landing`
- `POST /api/rules/impact`
- `POST /api/rules/save`

## Frontend Architecture

### App shell (`frontend/src/App.jsx`)

Tabbed dashboard with lazy-loaded modules:

- `Overview`
- `ModelPredict`
- `LiveFlagging`
- `RulesShap`
- `OutreachPanel`

Landing mode uses:

- `LandingHero`
- `TextRevealCard`
- Canvas-based neural animation background

### API integration

`frontend/src/api/client.js` provides Axios wrappers for all backend routes.

Notes:

- Uses static API base `http://localhost:8000`
- Automatically stores bearer token after `/auth/token`
- Login defaults to demo creds unless overridden

### UI characteristics

- Monolithic design system in `frontend/src/index.css`
- Animated KPI cards, tickers, modal workflows
- PDF export support from prediction and SHAP modules via `html2pdf.js`

## Configuration Architecture

- `config/model_config.yaml`: model hyperparameters + feature lists
- `config/thresholds.yaml`: risk thresholding, intervention policy, compliance
- `config/llm_config.yaml`: LLM backend mode and retry controls
- `config/rules.json`: UI-editable rule set persisted via API

## Deployment Notes

### Local dev topology

- Backend: Uvicorn on `8000`
- Frontend: Vite configured for `3000`
- Vite proxies `/api`, `/auth`, `/health` to backend

### Optional BentoML service

`backend/service.py` exposes Bento APIs around `RiskPredictor`, but standard app flow uses FastAPI directly.

## Testing Architecture

Current test suite under `backend/tests` is mostly smoke/contract-level:

- API import/auth/schema checks
- Feature engineering smoke checks
- GRU sequence shape/build checks
- LightGBM config/artifact checks
- Agent and PII/compliance behavior checks

## Architectural Risks / Technical Debt

- Mixed data lineage assumptions exist (behavioral-banking vs Lending Club style comments in some modules).
- Demo credentials and permissive CORS are not production-grade defaults.
- Some runtime behaviors (like global rate limiting) are partially implemented but not fully wired.
- Frontend and script port defaults are inconsistent (`3000` vs displayed `5173` in launcher messaging).

## Reference Files

- Runtime API: `backend/api/main.py`
- Inference: `backend/inference/predict.py`
- Agent flow: `backend/agent/intervention_agent.py`
- Frontend entry: `frontend/src/App.jsx`
