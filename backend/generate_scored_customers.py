"""
Generate 600 Pre-Scored Customers using BOTH trained models
============================================================
Takes 600 real Lending Club rows, runs all 4 AI models
(LightGBM, GRU, Ensemble, Isolation Forest), computes SHAP,
and saves a comprehensive JSON file for the dashboard.
"""

import os
import sys
import json
import random
import numpy as np
import pandas as pd
import joblib
import torch
import torch.nn as nn
import yaml

from inference.ai_explain import generate_ai_explanation

random.seed(42)
np.random.seed(42)

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

ARCHIVE_PATH = os.path.join(os.path.dirname(ROOT), "archive (4)", "df_2014-18_selected.csv")
MODELS_DIR = os.path.join(ROOT, "models")
OUTPUT_PATH = os.path.join(ROOT, "data", "scored_customers.json")

FEATURE_COLS = [
    "total_rec_late_fee", "recoveries", "last_pymnt_amnt",
    "loan_amnt_div_instlmnt", "debt_settlement_flag", "loan_age",
    "total_rec_int", "out_prncp", "time_since_last_credit_pull",
    "time_since_last_payment", "int_rate%", "total_rec_prncp"
]

# ── Indian-style customer profiles ──
FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
    "Ananya", "Diya", "Myra", "Sara", "Aadhya", "Isha", "Anika", "Anvi", "Priya", "Kavya",
    "Rohan", "Rahul", "Amit", "Vikram", "Suresh", "Rajesh", "Karan", "Nikhil", "Manish", "Deepak",
    "Pooja", "Neha", "Swati", "Meera", "Anjali", "Sneha", "Ritu", "Divya", "Nisha", "Preeti",
    "Arnav", "Dev", "Harsh", "Yash", "Pranav", "Kunal", "Sahil", "Tushar", "Gaurav", "Varun",
    "Shreya", "Tanvi", "Ritika", "Aishwarya", "Sakshi", "Kriti", "Palak", "Simran", "Megha", "Tanya"
]
LAST_NAMES = [
    "Sharma", "Patel", "Kumar", "Singh", "Reddy", "Iyer", "Nair", "Gupta", "Joshi", "Verma",
    "Agarwal", "Mishra", "Mehta", "Shah", "Das", "Rao", "Pillai", "Desai", "Kulkarni", "Bose",
    "Mukherjee", "Banerjee", "Sinha", "Chandra", "Tiwari", "Yadav", "Kapoor", "Malhotra", "Khanna", "Dutta"
]
CITIES = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow", "Chandigarh", "Indore", "Nagpur", "Kochi", "Vishakhapatnam"]
OCCUPATIONS = ["Salaried", "Self-Employed", "Freelancer", "Business Owner", "Government", "IT Professional", "Doctor", "Engineer", "Teacher", "Accountant"]
PRODUCT_TYPES = ["Personal Loan", "Home Loan", "Auto Loan", "Business Loan", "Education Loan", "Credit Card"]


# ── GRU Model Architecture (must match training) ──
class GRUModel(nn.Module):
    def __init__(self, input_size, hidden1=64, hidden2=32, dropout=0.3):
        super().__init__()
        self.gru = nn.GRU(input_size, hidden1, batch_first=True, dropout=dropout, num_layers=2)
        self.fc1 = nn.Linear(hidden1, hidden2)
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden2, 1)
        self.relu = nn.ReLU()

    def forward(self, x):
        _, h = self.gru(x)
        out = self.relu(self.fc1(h[-1]))
        out = self.dropout(out)
        return self.fc2(out).squeeze(-1)


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("\n" + "=" * 60)
    print("  GENERATING 600 PRE-SCORED CUSTOMERS")
    print("  Using all 4 trained models + SHAP")
    print("=" * 60)

    # ── Load config ──
    with open(os.path.join(ROOT, "config", "model_config.yaml"), "r") as f:
        config = yaml.safe_load(f)
    with open(os.path.join(ROOT, "config", "thresholds.yaml"), "r") as f:
        thresholds = yaml.safe_load(f)

    features = config["features"]["tabular"]
    rt = thresholds["risk_thresholds"]

    # ── Load all models ──
    print("\n📦 Loading trained models...")
    lgbm = joblib.load(os.path.join(MODELS_DIR, "lgbm_model.pkl"))
    iso_forest = joblib.load(os.path.join(MODELS_DIR, "isolation_forest.pkl"))
    ensemble_meta = joblib.load(os.path.join(MODELS_DIR, "ensemble_meta.pkl"))
    gru_scaler = joblib.load(os.path.join(MODELS_DIR, "gru_scaler.pkl"))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    gru_cfg = config["gru"]
    gru_model = GRUModel(
        input_size=len(features),
        hidden1=gru_cfg["hidden1"],
        hidden2=gru_cfg["hidden2"],
        dropout=gru_cfg["dropout"]
    ).to(device)
    gru_model.load_state_dict(
        torch.load(os.path.join(MODELS_DIR, "gru_model.pt"),
                    weights_only=True, map_location=device))
    gru_model.eval()
    print("   ✅ All 4 models loaded")

    # ── Load SHAP explainer ──
    print("🔍 Initializing SHAP explainer...")
    import shap
    shap_explainer = shap.TreeExplainer(lgbm)
    print("   ✅ SHAP ready")

    # ── Load 600 diverse rows from Combine Dataset ──
    print(f"\n📂 Loading real loan data from: {ARCHIVE_PATH}")
    df_real = pd.read_csv(ARCHIVE_PATH)
    
    SYNTHETIC_PATH = os.path.join(ROOT, "data", "synthetic_archive.csv")
    print(f"📂 Loading SYNTHETIC data from: {SYNTHETIC_PATH}")
    if os.path.exists(SYNTHETIC_PATH):
        df_synthetic = pd.read_csv(SYNTHETIC_PATH)
        df_synthetic["loan_status_binary"] = df_synthetic["loan_status_binary"]  # retain
    else:
        df_synthetic = pd.DataFrame()
        
    df = pd.concat([df_real, df_synthetic], ignore_index=True)
    print(f"   Combined dataset: {len(df):,} rows")

    # Stratified sampling: get a mix of risk levels
    df["target"] = 1 - df["loan_status_binary"]
    defaults = df[df["target"] == 1].sample(n=min(200, len(df[df["target"] == 1])), random_state=42)
    good = df[df["target"] == 0].sample(n=400, random_state=42)
    sample_df = pd.concat([defaults, good]).sample(frac=1, random_state=42).reset_index(drop=True)
    sample_df = sample_df.head(600)
    print(f"   Sampled: {len(sample_df)} rows (stratified: {len(defaults)} default + {len(good)} good)")

    X = sample_df[FEATURE_COLS].values.astype(np.float32)

    # ── Run LightGBM ──
    print("\n🌳 Running LightGBM predictions...")
    lgbm_probs = lgbm.predict_proba(X)[:, 1]

    # ── Run GRU ──
    print("🧠 Running GRU predictions...")
    seq_len = config["gru"]["seq_len"]
    gru_probs = np.zeros(len(X))
    with torch.no_grad():
        for i in range(len(X)):
            x_seq = np.tile(X[i:i+1], (seq_len, 1))
            x_scaled = gru_scaler.transform(x_seq).reshape(1, seq_len, len(features))
            seq_tensor = torch.FloatTensor(x_scaled).to(device)
            logit = float(gru_model(seq_tensor).cpu().numpy()[0])
            gru_probs[i] = 1.0 / (1.0 + np.exp(-logit))
    print(f"   ✅ GRU: mean={gru_probs.mean():.4f}")

    # ── Run Isolation Forest ──
    print("🔎 Running Isolation Forest...")
    anomaly_flags = iso_forest.predict(X) == -1

    # ── Run Ensemble ──
    print("🔗 Running Ensemble meta-learner...")
    meta_X = np.column_stack([lgbm_probs, gru_probs])
    ensemble_probs = ensemble_meta.predict_proba(meta_X)[:, 1]

    # Anomaly escalation
    for i in range(len(ensemble_probs)):
        if anomaly_flags[i] and ensemble_probs[i] >= 0.50:
            ensemble_probs[i] = max(ensemble_probs[i], rt["high_risk"])

    # ── Compute SHAP for each customer ──
    print("🔍 Computing SHAP explanations (600 customers)...")
    shap_values_all = shap_explainer.shap_values(X)
    if isinstance(shap_values_all, list):
        shap_values_all = shap_values_all[1] if len(shap_values_all) > 1 else shap_values_all[0]

    # ── Build customer records ──
    print("\n👤 Building customer profiles...")
    scored_customers = []

    for i in range(len(sample_df)):
        row = sample_df.iloc[i]
        ep = float(ensemble_probs[i])

        # Risk level
        if ep >= rt["high_risk"]:
            risk_level = "HIGH"
        elif ep >= rt["monitor_only"]:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # SHAP for this customer
        sv = shap_values_all[i]
        feature_contribs = []
        for j, fname in enumerate(features):
            feature_contribs.append({
                "feature": fname,
                "contribution": round(float(sv[j]), 4),
                "direction": "INCREASES_RISK" if sv[j] > 0 else "DECREASES_RISK",
                "abs_contribution": round(abs(float(sv[j])), 4)
            })
        feature_contribs.sort(key=lambda x: x["abs_contribution"], reverse=True)
        top3 = [{"feature": fc["feature"], "contribution": fc["contribution"], "direction": fc["direction"]} for fc in feature_contribs[:3]]

        # Human explanation using the centralized generator
        fv = {f: float(X[i][idx]) for idx, f in enumerate(features)}
        explanation = generate_ai_explanation(
            shap_drivers=feature_contribs,
            feature_values=fv,
            ensemble_prob=ep,
            lgbm_prob=float(lgbm_probs[i]),
            gru_prob=float(gru_probs[i]),
            anomaly_flag=bool(anomaly_flags[i]),
            risk_level=risk_level
        )

        # Generate realistic Indian customer profile
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        age = random.randint(22, 62)
        city = random.choice(CITIES)
        occupation = random.choice(OCCUPATIONS)
        product_type = random.choice(PRODUCT_TYPES)

        # Salary correlated with risk
        base_salary = random.randint(20000, 150000)
        if risk_level == "HIGH":
            base_salary = random.randint(15000, 60000)
        elif risk_level == "MEDIUM":
            base_salary = random.randint(25000, 80000)

        credit_score = random.randint(550, 850)
        if risk_level == "HIGH":
            credit_score = random.randint(500, 650)
        elif risk_level == "MEDIUM":
            credit_score = random.randint(600, 720)

        loan_amount = int(float(row.get("total_rec_prncp", 10000)) + float(row.get("out_prncp", 0)))
        if loan_amount < 1000:
            loan_amount = random.randint(50000, 2000000)
        emi_amount = int(loan_amount / max(float(row.get("loan_amnt_div_instlmnt", 36)), 1))

        customer = {
            "customer_id": f"CUS-{20001 + i}",
            "name": name,
            "age": age,
            "city": city,
            "occupation": occupation,
            "monthly_salary": base_salary,
            "credit_score": credit_score,
            "loan_amount": loan_amount,
            "emi_amount": emi_amount,
            "product_type": product_type,
            "credit_limit": random.randint(50000, 500000),

            # ── Raw Lending Club features ──
            "loan_features": {f: round(float(X[i][j]), 4) for j, f in enumerate(features)},

            # ── Model predictions ──
            "lgbm_prob": round(float(lgbm_probs[i]), 4),
            "gru_prob": round(float(gru_probs[i]), 4),
            "ensemble_prob": round(ep, 4),
            "anomaly_flag": bool(anomaly_flags[i]),
            "risk_level": risk_level,

            # ── SHAP explanation ──
            "shap_top3": top3,
            "all_shap": [{"feature": fc["feature"], "contribution": fc["contribution"], "direction": fc["direction"]} for fc in feature_contribs],
            "shap_values": {f: round(float(sv[j]), 4) for j, f in enumerate(features)},
            "human_explanation": explanation,

            # ── Behavioral signals (simulated) ──
            "salary_delay_days": random.randint(0, 15) if risk_level != "LOW" else 0,
            "savings_delta_pct": round(random.uniform(-30, 10) if risk_level == "HIGH" else random.uniform(-5, 15), 2),
            "failed_autodebit": random.randint(0, 3) if risk_level == "HIGH" else 0,
            "credit_utilization": round(random.uniform(0.5, 0.95) if risk_level == "HIGH" else random.uniform(0.1, 0.5), 3),
        }
        scored_customers.append(customer)

        if (i + 1) % 100 == 0:
            print(f"   Scored {i+1}/600 customers...")

    # ── Save ──
    with open(OUTPUT_PATH, "w") as f:
        json.dump(scored_customers, f, indent=2, default=str)

    # ── Summary ──
    high = sum(1 for c in scored_customers if c["risk_level"] == "HIGH")
    med = sum(1 for c in scored_customers if c["risk_level"] == "MEDIUM")
    low = sum(1 for c in scored_customers if c["risk_level"] == "LOW")
    anomalies = sum(1 for c in scored_customers if c["anomaly_flag"])

    print(f"\n" + "=" * 60)
    print(f"  ✅ SCORED 600 CUSTOMERS SUCCESSFULLY")
    print(f"=" * 60)
    print(f"\n   📁 Output: {OUTPUT_PATH}")
    print(f"   📊 Risk Distribution:")
    print(f"      🔴 HIGH:   {high} ({high/6:.1f}%)")
    print(f"      🟠 MEDIUM: {med} ({med/6:.1f}%)")
    print(f"      🟢 LOW:    {low} ({low/6:.1f}%)")
    print(f"      ⚠ Anomalies: {anomalies}")
    print(f"\n   Models used: LightGBM + GRU + Ensemble + Isolation Forest")
    print(f"   Features: {len(features)} Lending Club features")
    print(f"   SHAP: All 12 feature attributions per customer")
    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"   File size: {size_kb:.0f} KB\n")


if __name__ == "__main__":
    main()
