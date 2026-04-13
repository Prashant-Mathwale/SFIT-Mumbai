"""
FastAPI Application — Pre-Delinquency Intervention Engine API
All routes for the Praeventix dashboard backend.

Now supports both:
  - Direct model prediction via /api/predict (Lending Club features)
  - Customer-based lookups via /api/customers/* (behavioral CSVs)
"""

import os
import sys
import pandas as pd
import numpy as np
import yaml
import json
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from api.schemas import (
    HealthResponse, TokenRequest, TokenResponse, CustomerRiskSummary,
    CustomerDetailResponse, WeeklyRecord, InterventionTriggerRequest,
    InterventionResponse, InterventionLogEntry, OverviewMetrics
)
from api.auth import authenticate_user, create_access_token, get_current_user
from api.rate_limiter import rate_limiter

app = FastAPI(
    title="Praeventix — Pre-Delinquency Intervention Engine",
    description="AI-powered early warning system for banking risk management",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load Data at startup ──
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(ROOT, "data"))


def load_data():
    """Load CSV data files."""
    data = {}
    try:
        data["customers"] = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"))
        data["weekly"] = pd.read_csv(os.path.join(DATA_DIR, "weekly_behavioral_features.csv"))
        data["interventions"] = pd.read_csv(os.path.join(DATA_DIR, "intervention_log.csv"))
        try:
            with open(os.path.join(DATA_DIR, "scored_customers.json"), "r") as f:
                data["scored"] = json.load(f)
        except Exception:
            data["scored"] = []
        data["transactions"] = None  # Loaded on demand (large file)
    except Exception as e:
        print(f"Warning: Could not load data: {e}")
        data = {"customers": pd.DataFrame(), "weekly": pd.DataFrame(),
                "interventions": pd.DataFrame(), "transactions": None, "scored": []}
    return data


def load_thresholds():
    try:
        with open(os.path.join(ROOT, "config", "thresholds.yaml"), "r") as f:
            return yaml.safe_load(f)
    except:
        return {"risk_thresholds": {"monitor_only": 0.40, "low_intervention": 0.55, "high_risk": 0.70}}


data = load_data()
thresholds_config = load_thresholds()

# ── Lazy model loading ──
_predictor = None
_agent = None


def get_predictor():
    global _predictor
    if _predictor is None:
        try:
            from inference.predict import RiskPredictor
            _predictor = RiskPredictor()
        except Exception as e:
            print(f"Could not load predictor: {e}")
            import traceback
            traceback.print_exc()
    return _predictor


def get_agent():
    global _agent
    if _agent is None:
        try:
            from agent.intervention_agent import InterventionAgent
            _agent = InterventionAgent()
        except Exception as e:
            print(f"Could not load agent: {e}")
    return _agent


def models_available():
    """Check if trained models are available."""
    models_dir = os.path.join(ROOT, "models")
    required = ["lgbm_model.pkl", "gru_model.pt", "gru_scaler.pkl",
                "ensemble_meta.pkl", "isolation_forest.pkl"]
    return all(os.path.exists(os.path.join(models_dir, f)) for f in required)


# ═══════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS FOR NEW ENDPOINTS
# ═══════════════════════════════════════════════════════════════

class PredictRequest(BaseModel):
    """Direct prediction request using raw Lending Club features."""
    total_rec_late_fee: float = 0.0
    recoveries: float = 0.0
    last_pymnt_amnt: float = 0.0
    loan_amnt_div_instlmnt: float = 0.0
    debt_settlement_flag: float = 0.0
    loan_age: float = 0.0
    total_rec_int: float = 0.0
    out_prncp: float = 0.0
    time_since_last_credit_pull: float = 0.0
    time_since_last_payment: float = 0.0
    int_rate_pct: float = 0.0  # maps to "int_rate%"
    total_rec_prncp: float = 0.0


class PredictResponse(BaseModel):
    lgbm_prob: float
    gru_prob: float
    ensemble_prob: float
    anomaly_flag: bool
    risk_level: str
    shap_top3: List[Dict[str, Any]] = []
    all_shap: List[Dict[str, Any]] = []
    shap_values: Dict[str, float] = {}
    human_explanation: str = ""


class ModelInfoResponse(BaseModel):
    models_loaded: bool
    model_files: List[str]
    feature_columns: List[str]
    training_source: str


# ═══════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", models_loaded=models_available())


@app.post("/auth/token", response_model=TokenResponse)
async def login(request: TokenRequest):
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(data={"sub": user["username"]})
    return TokenResponse(access_token=token)


# ── NEW: Direct Model Prediction ──────────────────────────────

@app.post("/api/predict", response_model=PredictResponse)
async def predict_risk(request: PredictRequest):
    """Run all 4 models (LightGBM + GRU + Ensemble + Isolation Forest)
    on raw Lending Club features. No authentication required for demo."""
    predictor = get_predictor()
    if predictor is None:
        raise HTTPException(status_code=503, detail="Models not loaded")

    features = {
        "total_rec_late_fee": request.total_rec_late_fee,
        "recoveries": request.recoveries,
        "last_pymnt_amnt": request.last_pymnt_amnt,
        "loan_amnt_div_instlmnt": request.loan_amnt_div_instlmnt,
        "debt_settlement_flag": request.debt_settlement_flag,
        "loan_age": request.loan_age,
        "total_rec_int": request.total_rec_int,
        "out_prncp": request.out_prncp,
        "time_since_last_credit_pull": request.time_since_last_credit_pull,
        "time_since_last_payment": request.time_since_last_payment,
        "int_rate%": request.int_rate_pct,
        "total_rec_prncp": request.total_rec_prncp,
    }

    result = predictor.predict_from_features(features)
    return PredictResponse(**result)


@app.get("/api/model-info", response_model=ModelInfoResponse)
async def get_model_info():
    """Get information about the loaded models."""
    models_dir = os.path.join(ROOT, "models")
    model_files = []
    if os.path.exists(models_dir):
        model_files = sorted(os.listdir(models_dir))

    from inference.predict import RiskPredictor
    return ModelInfoResponse(
        models_loaded=models_available(),
        model_files=model_files,
        feature_columns=RiskPredictor.FEATURE_COLS,
        training_source="Lending Club 2014-2018 (2M+ loans)"
    )


@app.post("/api/predict/batch")
async def predict_batch(loans: List[PredictRequest]):
    """Batch prediction for multiple loans."""
    predictor = get_predictor()
    if predictor is None:
        raise HTTPException(status_code=503, detail="Models not loaded")

    results = []
    for loan in loans:
        features = {
            "total_rec_late_fee": loan.total_rec_late_fee,
            "recoveries": loan.recoveries,
            "last_pymnt_amnt": loan.last_pymnt_amnt,
            "loan_amnt_div_instlmnt": loan.loan_amnt_div_instlmnt,
            "debt_settlement_flag": loan.debt_settlement_flag,
            "loan_age": loan.loan_age,
            "total_rec_int": loan.total_rec_int,
            "out_prncp": loan.out_prncp,
            "time_since_last_credit_pull": loan.time_since_last_credit_pull,
            "time_since_last_payment": loan.time_since_last_payment,
            "int_rate%": loan.int_rate_pct,
            "total_rec_prncp": loan.total_rec_prncp,
        }
        result = predictor.predict_from_features(features)
        results.append(result)

    return {"predictions": results, "count": len(results)}


# ── Existing Customer-Based Routes ────────────────────────────

@app.get("/api/customers/at-risk", response_model=List[CustomerRiskSummary])
async def get_at_risk_customers(
    week_number: Optional[int] = Query(None, description="Week number (default: latest)"),
    threshold: float = Query(0.40, description="Risk score threshold"),
    limit: int = Query(600, description="Max results")
):
    if "scored" in data and data["scored"]:
        # Use the pre-scored customers (Hackathon optimized)
        scored = data["scored"]
        filtered = [c for c in scored if c.get("ensemble_prob", 0) >= threshold]
        
        # Sort by ensemble probability descending
        filtered.sort(key=lambda x: x.get("ensemble_prob", 0), reverse=True)
        
        # Map to expected response format
        results = []
        for c in filtered[:limit]:
            results.append({
                "customer_id": c["customer_id"],
                "name": c["name"],
                "city": c.get("city", "Unknown"),
                "risk_score": c["ensemble_prob"],  # Use ensemble score as main risk score
                "recent_signals": [
                    s["feature"].replace("_", " ").title() 
                    for s in c.get("shap_top3", [])
                ],
                "top_signal": c.get("shap_top3", [{"feature": ""}])[0].get("feature", "").replace("_", " ").title() if c.get("shap_top3") else "",
                "anomaly_flag": c.get("anomaly_flag", False),
                "risk_level": c.get("risk_level", "LOW")
            })
        return results
    weekly = data["weekly"]
    customers = data["customers"]

    if weekly.empty:
        return []

    wk = week_number or int(weekly["week_number"].max())
    week_data = weekly[weekly["week_number"] == wk].copy()
    at_risk = week_data[week_data["risk_score"] >= threshold].copy()
    at_risk = at_risk.sort_values("risk_score", ascending=False).head(limit)

    rt = thresholds_config["risk_thresholds"]
    results = []
    for _, row in at_risk.iterrows():
        cid = row["customer_id"]
        cust = customers[customers["customer_id"] == cid]
        name = cust.iloc[0]["name"] if len(cust) > 0 else ""
        rs = float(row["risk_score"])

        if rs >= rt["high_risk"]:
            level = "HIGH"
        elif rs >= rt["monitor_only"]:
            level = "MEDIUM"
        else:
            level = "LOW"

        # Determine top signal
        signal_cols = ["salary_delay_days", "savings_wow_delta_pct", "credit_utilization",
                       "failed_autodebit_count", "lending_upi_count_7d", "atm_withdrawal_count_7d"]
        signal_vals = {c: abs(float(row.get(c, 0))) for c in signal_cols}
        top_signal = max(signal_vals, key=signal_vals.get) if signal_vals else ""

        results.append(CustomerRiskSummary(
            customer_id=cid,
            risk_score=round(rs, 4),
            risk_level=level,
            top_signal=top_signal,
            intervention_eligible=rs >= rt["monitor_only"],
            name=name
        ))

    return results


@app.get("/api/customers/{customer_id}")
async def get_customer_detail(
    customer_id: str,
):
    if "scored" in data and data["scored"]:
        for c in data["scored"]:
            if c["customer_id"] == customer_id:
                return {
                    "customer_id": c["customer_id"],
                    "account_info": {
                        "name": c["name"],
                        "age": c.get("age", 35),
                        "city": c.get("city", "Unknown"),
                        "occupation": c.get("occupation", "Salaried"),
                        "product_type": c.get("product_type", "Personal Loan")
                    },
                    "financial_profile": {
                        "monthly_salary": float(c.get("monthly_salary", 50000)),
                        "credit_score": c.get("credit_score", 700),
                        "loan_amount": float(c.get("loan_amount", 10000)),
                        "emi_amount": float(c.get("emi_amount", 1000)),
                        "credit_limit": float(c.get("credit_limit", 50000))
                    },
                    "current_behavior": {
                        "week_number": 52,
                        "stress_level": 7 if c.get("risk_level") == "HIGH" else 2,
                        "salary_delay_days": c.get("salary_delay_days", 0),
                        "credit_utilization": c.get("credit_utilization", 0.4),
                        "risk_score": c["ensemble_prob"]
                    },
                    "scored_details": c  # Pass the full AI payload
                }
                
    # Fallback to old behavior
    customers = data["customers"]
    weekly = data["weekly"]

    cust = customers[customers["customer_id"] == customer_id]
    if len(cust) == 0:
        raise HTTPException(status_code=404, detail="Customer not found")

    cust_row = cust.iloc[0]
    cust_weekly = weekly[weekly["customer_id"] == customer_id]
    latest = cust_weekly[cust_weekly["week_number"] == cust_weekly["week_number"].max()]

    risk_score = float(latest.iloc[0]["risk_score"]) if len(latest) > 0 else 0.0

    rt = thresholds_config["risk_thresholds"]
    if risk_score >= rt["high_risk"]:
        risk_level = "HIGH"
    elif risk_score >= rt["monitor_only"]:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Try ML prediction if models available
    lgbm_prob = risk_score
    gru_prob = risk_score
    ensemble_prob = risk_score
    anomaly_flag = False
    shap_top3 = []
    all_shap = []
    shap_values = {}
    explanation = ""

    predictor = get_predictor()
    if predictor:
        try:
            pred = predictor.predict_single(customer_id)
            lgbm_prob = pred.get("lgbm_prob", risk_score)
            gru_prob = pred.get("gru_prob", risk_score)
            ensemble_prob = pred.get("ensemble_prob", risk_score)
            anomaly_flag = pred.get("anomaly_flag", False)
            shap_top3 = pred.get("shap_top3", [])
            all_shap = pred.get("all_shap", [])
            shap_values = pred.get("shap_values", {})
            explanation = pred.get("human_explanation", "")
            risk_level = pred.get("risk_level", risk_level)
        except Exception as e:
            print(f"Prediction error: {e}")

    return CustomerDetailResponse(
        customer_id=customer_id,
        name=str(cust_row.get("name", "")),
        age=int(cust_row.get("age", 0)),
        city=str(cust_row.get("city", "")),
        occupation=str(cust_row.get("occupation", "")),
        monthly_salary=int(cust_row.get("monthly_salary", 0)),
        credit_score=int(cust_row.get("credit_score", 0)),
        loan_amount=int(cust_row.get("loan_amount", 0)),
        emi_amount=int(cust_row.get("emi_amount", 0)),
        credit_limit=int(cust_row.get("credit_limit", 0)),
        product_type=str(cust_row.get("product_type", "")),
        risk_score=round(risk_score, 4),
        lgbm_prob=round(lgbm_prob, 4),
        gru_prob=round(gru_prob, 4),
        ensemble_prob=round(ensemble_prob, 4),
        anomaly_flag=anomaly_flag,
        risk_level=risk_level,
        shap_top3=shap_top3,
        all_shap=all_shap,
        shap_values=shap_values,
        human_explanation=explanation
    )


@app.get("/api/customers/{customer_id}/history", response_model=List[WeeklyRecord])
async def get_customer_history(
    customer_id: str,
):
    weekly = data["weekly"]
    cust_data = weekly[weekly["customer_id"] == customer_id].sort_values("week_number")

    if len(cust_data) == 0:
        raise HTTPException(status_code=404, detail="Customer not found")

    records = []
    for _, row in cust_data.iterrows():
        records.append(WeeklyRecord(
            week_number=int(row["week_number"]),
            risk_score=round(float(row["risk_score"]), 4),
            salary_delay_days=float(row.get("salary_delay_days", 0)),
            savings_wow_delta_pct=float(row.get("savings_wow_delta_pct", 0)),
            credit_utilization=float(row.get("credit_utilization", 0)),
            failed_autodebit_count=int(row.get("failed_autodebit_count", 0)),
            lending_upi_count_7d=int(row.get("lending_upi_count_7d", 0)),
            stress_level=int(row.get("stress_level", 0))
        ))
    return records


@app.get("/api/customers/{customer_id}/explain")
async def explain_customer(
    customer_id: str,
):
    if "scored" in data and data["scored"]:
        for c in data["scored"]:
            if c["customer_id"] == customer_id:
                return {
                    "customer_id": customer_id,
                    "risk_score": c["ensemble_prob"],
                    "prediction_date": "2025-W12",
                    "top_drivers": [
                        {
                            "feature": s["feature"],
                            "value": float(c.get("loan_features", {}).get(s["feature"], 0)),
                            "contribution": s["contribution"],
                            "direction": s["direction"]
                        } for s in c.get("shap_top3", [])
                    ],
                    "human_explanation": c.get("human_explanation", "Risk evaluated based on ensemble models.")
                }
                
    predictor = get_predictor()
    if predictor:
        try:
            result = predictor.predict_single(customer_id)
            return {
                "customer_id": customer_id,
                "risk_score": result.get("ensemble_prob", result.get("lgbm_prob", 0)),
                "top_drivers": result.get("shap_top3", []),
                "all_drivers": result.get("all_shap", []),
                "shap_values": result.get("shap_values", {}),
                "human_explanation": result.get("human_explanation", ""),
                "risk_level": result.get("risk_level", "LOW")
            }
        except Exception as e:
            print(f"Explain error: {e}")

    # Fallback: use raw data
    weekly = data["weekly"]
    cust = weekly[weekly["customer_id"] == customer_id]
    if len(cust) == 0:
        raise HTTPException(status_code=404, detail="Customer not found")

    latest = cust[cust["week_number"] == cust["week_number"].max()].iloc[0]
    return {
        "customer_id": customer_id,
        "risk_score": float(latest["risk_score"]),
        "top_drivers": [],
        "all_drivers": [],
        "shap_values": {},
        "human_explanation": "Model not loaded. Raw risk score shown.",
        "risk_level": "HIGH" if latest["risk_score"] >= 0.70 else "MEDIUM" if latest["risk_score"] >= 0.40 else "LOW"
    }


@app.post("/api/interventions/trigger", response_model=InterventionResponse)
async def trigger_intervention(
    request: InterventionTriggerRequest,
):
    # Get risk prediction
    predictor = get_predictor()
    risk_score = 0.5
    shap_explanations = []
    customer_profile = {}

    if predictor:
        try:
            pred = predictor.predict_single(request.customer_id, request.week_number)
            risk_score = pred.get("ensemble_prob", 0.5)
            shap_explanations = pred.get("shap_top3", [])
            customer_profile = pred.get("customer_profile", {})
        except Exception as e:
            print(f"Prediction error: {e}")
            # Fallback to raw data
            weekly = data["weekly"]
            cust = weekly[(weekly["customer_id"] == request.customer_id) &
                          (weekly["week_number"] == request.week_number)]
            if len(cust) > 0:
                risk_score = float(cust.iloc[0]["risk_score"])
    else:
        weekly = data["weekly"]
        cust = weekly[(weekly["customer_id"] == request.customer_id) &
                      (weekly["week_number"] == request.week_number)]
        if len(cust) > 0:
            risk_score = float(cust.iloc[0]["risk_score"])

    # Run agent
    agent = get_agent()
    if agent:
        result = agent.run(
            customer_id=request.customer_id,
            week_number=request.week_number,
            risk_score=risk_score,
            shap_explanations=shap_explanations,
            customer_profile=customer_profile
        )
    else:
        # Fallback
        result = {
            "customer_id": request.customer_id,
            "week_number": request.week_number,
            "risk_score": risk_score,
            "chosen_intervention": request.override_intervention or "SMS_OUTREACH",
            "chosen_channel": "SMS",
            "intervention_reason": "Agent not available - fallback",
            "outreach_message": "We care about your financial wellness. Our team is here to help.",
            "compliance_approved": True,
            "dispatched": True
        }

    return InterventionResponse(
        customer_id=result["customer_id"],
        week_number=result["week_number"],
        risk_score=result["risk_score"],
        chosen_intervention=result["chosen_intervention"],
        chosen_channel=result["chosen_channel"],
        intervention_reason=result.get("intervention_reason", ""),
        outreach_message=result.get("outreach_message", ""),
        compliance_approved=result.get("compliance_approved", False),
        dispatched=result.get("dispatched", False)
    )


@app.get("/api/interventions/log", response_model=List[InterventionLogEntry])
async def get_intervention_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    outcome_filter: Optional[str] = None,
):
    log_df = data["interventions"]

    if log_df.empty:
        return []

    if outcome_filter:
        log_df = log_df[log_df["outcome"] == outcome_filter]

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    page_data = log_df.iloc[start:end]

    results = []
    for _, row in page_data.iterrows():
        results.append(InterventionLogEntry(
            customer_id=str(row["customer_id"]),
            week_number=int(row["week_number"]),
            risk_score_at_trigger=float(row["risk_score_at_trigger"]),
            intervention_type=str(row["intervention_type"]),
            channel=str(row["channel"]),
            status=str(row["status"]),
            outcome=str(row["outcome"]),
            top_signal=str(row["top_signal"])
        ))
    return results


@app.get("/api/metrics/overview", response_model=OverviewMetrics)
async def get_overview_metrics(
):
    customers = data["customers"]
    weekly = data["weekly"]
    interventions = data["interventions"]

    rt = thresholds_config["risk_thresholds"]

    total = len(customers)
    latest_week = int(weekly["week_number"].max()) if not weekly.empty else 52
    latest_data = weekly[weekly["week_number"] == latest_week]

    at_risk = len(latest_data[latest_data["risk_score"] >= rt["monitor_only"]])
    high_risk = len(latest_data[latest_data["risk_score"] >= rt["high_risk"]])

    # Interventions in latest week
    latest_interventions = interventions[interventions["week_number"] == latest_week]
    sent_count = len(latest_interventions[latest_interventions["status"].isin(["SENT", "DELIVERED"])])

    # Recovery rate
    if not interventions.empty:
        total_acted = len(interventions[interventions["outcome"] != ""])
        recovered = len(interventions[interventions["outcome"] == "RECOVERED"])
        recovery_rate = (recovered / total_acted * 100) if total_acted > 0 else 0
    else:
        recovery_rate = 0

    # Default rate
    if not latest_data.empty:
        default_rate = latest_data["will_default_next_30d"].mean() * 100
    else:
        default_rate = 0

    return OverviewMetrics(
        total_customers=total,
        at_risk_count=at_risk,
        high_risk_count=high_risk,
        interventions_sent_today=sent_count,
        recovery_rate=round(recovery_rate, 1),
        default_rate=round(default_rate, 1)
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
