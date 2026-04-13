<div align="center">

# 🛡️ Praeventix — Pre-Delinquency Intervention Engine

### *AI-Powered Early Warning System for Banking Risk Management*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![LightGBM](https://img.shields.io/badge/LightGBM-02569B?style=for-the-badge&logo=microsoft&logoColor=white)](https://lightgbm.readthedocs.io)

> **Team Markoblitz** · Hack-o-Hire 2026

---

*Detects financial distress **2–4 weeks before** a missed payment and triggers empathetic, personalized interventions — reducing bank NPAs while protecting customers.*

</div>

---

## 🎯 Problem Statement

Indian banks lose **₹1.5 lakh crore** annually to loan defaults. Traditional systems detect delinquency *after* the damage — missed EMIs, damaged credit scores, legal recovery costs.

**Praeventix** shifts the paradigm from **reactive collection** to **proactive intervention** by identifying distress signals *before* the first missed payment.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                      PRAEVENTIX PIPELINE                             │
├───────────────┬───────────────┬────────────────┬─────────────────────┤
│   Layer 1     │   Layer 2     │    Layer 3     │      Layer 4        │
│   Data &      │   ML Risk     │   Agentic      │    Frontend         │
│   Features    │   Scoring     │   Decisions    │    Dashboard        │
├───────────────┼───────────────┼────────────────┼─────────────────────┤
│ 12 Behavioral │ LightGBM      │ LangGraph      │ React + Vite        │
│ Signals       │ GRU (PyTorch) │ Policy Engine  │ Recharts            │
│ Feature Eng.  │ Ensemble Meta │ LLM Client     │ 4-Tab Premium UI    │
│ 104K weekly   │ IsoForest     │ SHAP Explain   │ Dark Glassmorphism  │
│ records       │ SHAP          │ PII Masking    │ Real-Time Updates   │
└───────────────┴───────────────┴────────────────┴─────────────────────┘
                            │
                      FastAPI REST API
                    (JWT Auth · Rate Limiting)
```

> See [ARCHITECTURE.md](ARCHITECTURE.md) for deep technical details.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** with pip
- **Node.js 18+** with npm

### 1️⃣ Clone & Setup

```bash
git clone https://github.com/Prashant-Mathwale/HackX.git
cd HackX
```

### 2️⃣ Generate Data

```bash
cd backend
python generate_data.py
```

### 3️⃣ Install Dependencies & Train Models

```bash
# Backend
pip install -r requirements.txt
python training/train_all.py

# Frontend (in new terminal)
cd ../frontend
npm install
```

### 4️⃣ Launch

```bash
# Terminal 1 — Backend API
cd backend
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Frontend Dashboard
cd frontend
npm run dev
```

**Open** → [http://localhost:5173](http://localhost:5173) 🎉

> 💡 **One-click launch (Windows):** Run `.\start.ps1` from the project root.

---

## 🧠 ML Models

| Model | Purpose | Key Features |
|-------|---------|-------------|
| **LightGBM** | Tabular risk scoring | 5-fold CV, SHAP-native, handles 80/20 class imbalance |
| **GRU (PyTorch)** | Temporal degradation patterns | 8-week sliding windows, BCELoss with pos_weight=4.0 |
| **Ensemble Meta-Learner** | Combines LightGBM + GRU | LogisticRegression on OOF predictions |
| **Isolation Forest** | Anomaly detection | Flags sudden behavioral outliers (e.g. ATM spikes) |
| **SHAP Explainer** | Feature attribution | Per-customer human-readable explanations |

### Model Artifacts
```
backend/models/
├── lgbm_model.pkl          # LightGBM classifier
├── gru_model.pt            # GRU PyTorch model
├── gru_scaler.pkl          # StandardScaler for GRU
├── ensemble_meta.pkl       # Meta-learner
└── isolation_forest.pkl    # Anomaly detector
```

---

## 📊 12 Behavioral Signals

| # | Signal | Description |
|---|--------|-------------|
| 1 | `salary_delay_days` | Days salary credited after expected date |
| 2 | `savings_wow_delta_pct` | Week-over-week savings change (%) |
| 3 | `credit_utilization` | Credit card utilization ratio |
| 4 | `failed_autodebit_count` | Failed EMI/bill auto-debits |
| 5 | `lending_upi_count_7d` | UPI lending app transactions (7d) |
| 6 | `lending_upi_amount_7d` | UPI lending app volume (7d) |
| 7 | `atm_withdrawal_count_7d` | ATM withdrawals (7d) |
| 8 | `atm_withdrawal_amount_7d` | ATM withdrawal volume (7d) |
| 9 | `utility_payment_delay_days` | Days utilities paid after due |
| 10 | `gambling_spend_7d` | Gambling/lottery spending (7d) |
| 11 | `discretionary_spend_7d` | Discretionary spending (7d) |
| 12 | `net_cashflow_7d` | Net cash inflow/outflow (7d) |

---

## 🖥️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check + model status |
| `POST` | `/auth/token` | JWT authentication |
| `GET` | `/api/customers/at-risk` | Top at-risk customers |
| `GET` | `/api/customers/{id}` | Full customer profile + ML risk |
| `GET` | `/api/customers/{id}/history` | 52-week risk history |
| `GET` | `/api/customers/{id}/explain` | SHAP explainability |
| `POST` | `/api/interventions/trigger` | Trigger AI intervention |
| `GET` | `/api/interventions/log` | Paginated intervention history |
| `GET` | `/api/metrics/overview` | Dashboard KPI metrics |

---

## 🎨 Dashboard

The premium glassmorphic dashboard has **4 tabs**:

| Tab | Function |
|-----|----------|
| **Overview** | KPI cards, risk distribution, intervention stats |
| **Live Flagging** | Real-time at-risk customer table with SHAP modal |
| **Rules & SHAP** | Behavioral rule configuration + SHAP explanation viewer |
| **Outreach** | AI-generated intervention messages with compliance checks |

---

## 📁 Project Structure

```
Praeventix/
├── frontend/                  # React + Vite Dashboard
│   ├── src/
│   │   ├── api/client.js      # API client
│   │   ├── components/        # Overview, LiveFlagging, RulesShap, Outreach
│   │   ├── App.jsx            # Main app with tab navigation
│   │   └── index.css          # Premium dark glassmorphic design
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── backend/                   # FastAPI + ML Engine
│   ├── api/                   # REST API (FastAPI routes, auth, schemas)
│   ├── agent/                 # LangGraph intervention agent
│   ├── inference/             # ML prediction + SHAP explainability
│   ├── training/              # Model training scripts
│   ├── pipeline/              # Feature engineering
│   ├── config/                # YAML configs (thresholds, model params)
│   ├── data/                  # Generated CSV datasets
│   ├── models/                # Trained model artifacts
│   ├── tests/                 # Pytest test suite
│   ├── generate_data.py       # Dataset generator
│   └── requirements.txt       # Python dependencies
│
├── README.md
├── ARCHITECTURE.md
└── start.ps1                  # One-click demo launcher
```

---

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MODE` | `mock` | LLM backend: `mock` / `anthropic` / `openai` |
| `DATA_DIR` | `./data` | Path to CSV data directory |
| Risk Tiers | `config/thresholds.yaml` | Monitor: 0.40 · Low: 0.55 · High: 0.70 |

---

## 🧪 Testing

```bash
cd backend
python -m pytest tests/ -v
```

---

## 👥 Team Markoblitz

**Hack-o-Hire 2026**

---

<div align="center">

*Built with ❤️ using LightGBM · PyTorch · FastAPI · LangGraph · SHAP · React · Recharts*

</div>
