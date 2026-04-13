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

## 🚀 Recent UI/UX Enhancements (Hackathon Updates)

To deliver a truly completely modern and seamless feeling interface, we heavily overhauled the dashboard UI:

1. **Lightweight Canvas 2D Neural Background:** Replaced the heavy, lag-inducing Three.js landing hero with a highly optimized, custom Canvas 2D neural network particle simulation. This ensures **butter-smooth 60FPS animations** without taxing the browser.
2. **Aceternity UI Text Reveal Card:** Integrated a premium hover-reveal typography component onto the landing page. The card features a hidden message ("We intervene 15 days before.") that smoothly tracks the user's cursor with a cyan spotlight effect.
3. **Global Responsive Fixes:** Swept the entire React dashboard (`LiveFlagging`, `Overview`, `ModelPredict`) to remove rigidly hardcoded pixel paddings. Replaced them with compliant `max-width: 100%` rules and responsive padding, eliminating horizontal scroll/overflow bugs on smaller laptop displays.
4. **Cinematic Dark Glassmorphism:** Maintained our high-fidelity, financial surveillance aesthetic (`#0a0a0f` background, indigo/cyan accent typography).

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
git clone https://github.com/Atharv-coder16/SFIT-Mumbai.git
cd SFIT-Mumbai
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
*(Or depending on Vite config, [http://localhost:3000](http://localhost:3000))*

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

## 🎨 Dashboard & UI Architecture

The premium glassmorphic dashboard has **4 tabs**, alongside the highly optimized Landing Page:

| Section | Description |
|-----|----------|
| **Landing Hero** | Custom-built `TextRevealCard` showcasing project foresight, surrounded by a lightweight `Canvas 2D Neural Background`. |
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
│   │   ├── components/        # LandingHero, TextRevealCard, Overview...
│   │   ├── App.jsx            # Main app with tab navigation
│   │   └── index.css          # Premium dark glassmorphic design & global responsive layout
│   ├── index.html
│   └── package.json
│
├── backend/                   # FastAPI + ML Engine
│   ├── api/                   # REST API
│   ├── agent/                 # LangGraph intervention agent
│   ├── inference/             # ML prediction + SHAP
│   ├── models/                # Trained model artifacts
│   └── requirements.txt       
│
├── README.md
└── start.ps1                  # One-click demo launcher
```

---

<div align="center">

*Built with ❤️ using LightGBM · PyTorch · FastAPI · LangGraph · SHAP · React · Recharts*

</div>
