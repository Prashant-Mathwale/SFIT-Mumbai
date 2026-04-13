"""
Pydantic Schemas for API Request/Response Models
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SHAPDriver(BaseModel):
    feature: str
    contribution: float
    direction: str


class CustomerRiskSummary(BaseModel):
    customer_id: str
    risk_score: float
    risk_level: str
    top_signal: str = ""
    recent_signals: List[str] = []
    intervention_eligible: bool = True
    anomaly_flag: bool = False
    name: str = ""
    city: str = ""


class CustomerDetailResponse(BaseModel):
    customer_id: str
    name: str = ""
    age: int = 0
    city: str = ""
    occupation: str = ""
    monthly_salary: int = 0
    credit_score: int = 0
    loan_amount: int = 0
    emi_amount: int = 0
    credit_limit: int = 0
    product_type: str = ""
    risk_score: float = 0.0
    lgbm_prob: float = 0.0
    gru_prob: float = 0.0
    ensemble_prob: float = 0.0
    anomaly_flag: bool = False
    risk_level: str = "LOW"
    shap_top3: List[Dict[str, Any]] = []
    all_shap: List[Dict[str, Any]] = []
    shap_values: Dict[str, float] = {}
    human_explanation: str = ""


class WeeklyRecord(BaseModel):
    week_number: int
    risk_score: float
    salary_delay_days: float = 0
    savings_wow_delta_pct: float = 0
    credit_utilization: float = 0
    failed_autodebit_count: int = 0
    lending_upi_count_7d: int = 0
    stress_level: int = 0


class InterventionTriggerRequest(BaseModel):
    customer_id: str
    week_number: int = 52
    override_intervention: Optional[str] = None


class InterventionResponse(BaseModel):
    customer_id: str
    week_number: int
    risk_score: float
    chosen_intervention: str
    chosen_channel: str
    intervention_reason: str
    outreach_message: str
    compliance_approved: bool
    dispatched: bool


class InterventionLogEntry(BaseModel):
    customer_id: str
    week_number: int
    risk_score_at_trigger: float
    intervention_type: str
    channel: str
    status: str
    outcome: str
    top_signal: str


class OverviewMetrics(BaseModel):
    total_customers: int
    at_risk_count: int
    high_risk_count: int
    interventions_sent_today: int
    recovery_rate: float
    default_rate: float
