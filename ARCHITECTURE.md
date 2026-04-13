# 🏛️ Praeventix — Technical Architecture

> Deep technical documentation for the Pre-Delinquency Intervention Engine.

---

## System Overview

Praeventix is a **4-layer AI pipeline** that processes 2,000 customer profiles across 52 weeks of behavioral data, trains a multi-model ensemble, and delivers risk intelligence through a premium dashboard.

```
Raw Transactions (380K+)
        │
        ▼
┌─────────────────────┐
│  Feature Engineering │  12 behavioral signals per customer-week
│  (104,000 rows)     │  Converts raw txns → weekly features
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  ML Risk Scoring    │  LightGBM + GRU + Ensemble + IsoForest
│  (5-fold CV)        │  AUC-optimized, SHAP-explainable
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Agentic Decisions  │  LangGraph agent with policy rules
│  (LLM + Rules)      │  Compliance-checked interventions
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  FastAPI REST API    │  JWT auth, rate limiting, CORS
│  (9 endpoints)      │  Serves dashboard + external systems
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  React Dashboard    │  4-tab premium UI
│  (Vite + Recharts)  │  Glassmorphic dark theme
└─────────────────────┘
```

---

## Layer 1: Data & Feature Engineering

### Datasets

| File | Rows | Columns | Description |
|------|------|---------|-------------|
| `customers.csv` | 2,000 | 13 | Demographics, financials, product info |
| `transactions.csv` | ~380,000 | 8 | Raw transaction events (12 months) |
| `weekly_behavioral_features.csv` | 104,000 | 19 | 12 features × 52 weeks × 2,000 customers |
| `intervention_log.csv` | ~8,700 | 8 | Historical intervention outcomes |

### Feature Engineering Pipeline

The `pipeline/feature_engineering.py` module computes **12 behavioral signals** from raw transactions with zero data leakage (uses only transactions *before* each week).

**Computation Flow:**
```
Per customer, per week:
  1. Filter transactions to 7-day window
  2. Compute salary delay (days after expected)
  3. Compute savings delta (week-over-week %)
  4. Count ATM withdrawals + lending app txns
  5. Detect failed auto-debits
  6. Calculate credit utilization ratio
  7. Aggregate discretionary + gambling spend
  8. Compute net cashflow
```

### Risk Score Formula

The composite risk score is a weighted sum of 10 normalized signal components:

```python
risk_components = [
    salary_delay / 20          × 0.15,  # Salary timing
    abs(savings_delta) / 30    × 0.12,  # Savings erosion
    atm_count / 8              × 0.08,  # Cash-out behavior
    lending_count / 5          × 0.12,  # Borrowing pressure
    failed_autodebit / 2       × 0.15,  # Payment failures
    utility_delay / 15         × 0.08,  # Bill delays
    gambling / 2000            × 0.05,  # Gambling exposure
    credit_utilization         × 0.10,  # Credit stress
    cashflow_stress            × 0.10,  # Negative cashflow
    discretionary_drop         × 0.05,  # Spending austerity
]
risk_score = clip(sum(components) + noise, 0, 1)
```

---

## Layer 2: ML Risk Scoring

### Model 1 — LightGBM (Primary)

**Purpose:** Tabular feature-based risk classification.

| Parameter | Value |
|-----------|-------|
| Objective | binary |
| Metric | AUC |
| Num Leaves | 63 |
| Max Depth | 7 |
| Learning Rate | 0.05 |
| N Estimators | 1,000 |
| Class Imbalance | `is_unbalance=True` |

**Training:** 5-fold stratified CV with out-of-fold (OOF) prediction storage for ensemble stacking.

**Explainability:** SHAP TreeExplainer provides per-feature attribution values for every prediction.

### Model 2 — GRU (Temporal)

**Purpose:** Captures 8-week behavioral degradation sequences.

| Parameter | Value |
|-----------|-------|
| Architecture | GRU → Linear(64→32) → Linear(32→1) |
| Input Shape | (batch, 8, 12) |
| Dropout | 0.3 |
| Loss | BCEWithLogitsLoss (pos_weight=4.0) |
| Optimizer | AdamW (lr=0.001, weight_decay=0.0001) |
| Epochs | 50 |

**Key Insight:** While LightGBM captures point-in-time risk, the GRU detects *gradual deterioration patterns* — e.g., a customer whose salary delay increases from 2→5→8→12 days over consecutive weeks.

### Model 3 — Ensemble Meta-Learner

**Purpose:** Learns optimal combination of LightGBM + GRU predictions.

- **Algorithm:** LogisticRegression (C=1.0)
- **Features:** OOF predictions from LightGBM + GRU + contextual features
- **Insight:** Automatically learns when to trust which model — GRU dominates for high-risk escalations, LightGBM excels for medium-risk classification.

### Model 4 — Isolation Forest

**Purpose:** Anomaly detection for extreme behavioral outliers.

- **Algorithm:** IsolationForest (n_estimators=200, contamination=5%)
- **Use Case:** Flags sudden behavioral anomalies (e.g., 10x ATM withdrawals in one week) that models might not capture in standard risk scoring.
- **Action:** Anomalous + high-risk customers get escalated intervention priority.

---

## Layer 3: Agentic Decision Engine

### LangGraph Intervention Agent

The `agent/intervention_agent.py` implements a multi-step decision workflow:

```
Input: customer_id, risk_score, SHAP explanations
        │
        ▼
┌─────────────────────┐
│  Policy Rules Check │  Cooldown periods, intervention limits
│  (policy_rules.py)  │  Salary-based channel routing
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  PII Masking        │  Removes Aadhaar, PAN, phone from LLM input
│  (pii_masking.py)   │  Regex + validation patterns
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  LLM Client         │  Generates empathetic outreach messages
│  (llm_client.py)    │  Supports: mock / Anthropic / OpenAI
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Compliance Check   │  Scans for aggressive language
│  (thresholds.yaml)  │  Character limits (SMS: 160, Email: 500)
└────────┬────────────┘
         │
         ▼
Output: intervention_type, channel, message, compliance_status
```

### Intervention Types

| Type | Trigger Condition | Channel |
|------|------------------|---------|
| `MONITOR_ONLY` | Risk 0.40–0.55 | — |
| `SMS_OUTREACH` | Risk 0.55+ | SMS |
| `FINANCIAL_COUNSELING` | Risk 0.55+ | APP / EMAIL |
| `RM_CALL` | Risk 0.70+ & Salary ≥ ₹30K | CALL |
| `RESTRUCTURING_OFFER` | Risk 0.70+ | EMAIL |
| `PAYMENT_HOLIDAY` | Risk 0.70+ | EMAIL / CALL |

---

## Layer 4: Frontend Dashboard

### Technology Stack
- **React 18** with Hooks
- **Vite** for fast HMR development
- **Recharts** for data visualization
- **Axios** for API communication
- **CSS** with glassmorphic dark theme

### 4-Tab Layout

| Tab | Components | Key Features |
|-----|-----------|-------------|
| Overview | KPI cards, risk distribution, weekly trends | Real-time metrics, animated counters |
| Live Flagging | Customer risk table, SHAP modal | Sort by risk, click-to-explain |
| Rules & SHAP | Rule editor, SHAP visualization | Configure thresholds, view feature impact |
| Outreach | Intervention panel, message preview | Trigger interventions, compliance review |

---

## API Architecture

```
FastAPI App (api/main.py)
├── Middleware: CORS (allow all origins)
├── Auth: JWT tokens (python-jose)
├── Rate Limiting: Custom middleware
├── Data: Pandas DataFrames loaded at startup
├── Models: Lazy-loaded on first request
│
├── GET  /health                    → HealthResponse
├── POST /auth/token                → TokenResponse
├── GET  /api/customers/at-risk     → List[CustomerRiskSummary]
├── GET  /api/customers/{id}        → CustomerDetailResponse
├── GET  /api/customers/{id}/history → List[WeeklyRecord]
├── GET  /api/customers/{id}/explain → SHAP explanation
├── POST /api/interventions/trigger  → InterventionResponse
├── GET  /api/interventions/log      → List[InterventionLogEntry]
└── GET  /api/metrics/overview       → OverviewMetrics
```

---

## Risk Thresholds

```yaml
risk_thresholds:
  monitor_only: 0.40        # Flag for monitoring
  low_intervention: 0.55    # Trigger outreach
  high_risk: 0.70           # Escalated intervention
```

---

## Innovation Highlights

1. **Pre-emptive Detection:** 2–4 week advance warning vs. post-default detection
2. **Multi-Model Ensemble:** Tabular + temporal + anomaly models for robust scoring
3. **SHAP Explainability:** Every risk score comes with human-readable reasons
4. **Empathetic Interventions:** LLM-generated messages that help, not threaten
5. **PII Protection:** Automatic masking before any LLM processing
6. **Compliance-First:** Auto-scans for aggressive language, enforces character limits
7. **12 Behavioral Signals:** Deep feature engineering from raw transaction data
