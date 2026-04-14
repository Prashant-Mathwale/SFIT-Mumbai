"""
Risk Predictor Module — Real Data Models
Combines LightGBM + GRU + Ensemble + Isolation Forest
trained on the Lending Club dataset (train_real_data.py).
"""

import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import joblib
import yaml
import os
import sys
import json
from inference.ai_explain import generate_ai_explanation

random.seed(42)
np.random.seed(42)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


# ── GRU Model Architecture ─────────────────────────────────
# Must exactly match the architecture in train_real_data.py
class GRUModel(nn.Module):
    """GRU model matching train_gru.py architecture."""

    def __init__(self, input_size, hidden1=64, hidden2=32, dropout=0.3):
        super().__init__()
        self.gru1 = nn.GRU(input_size=input_size, hidden_size=hidden1,
                           batch_first=True)
        self.gru2 = nn.GRU(input_size=hidden1, hidden_size=hidden2,
                           batch_first=True)
        self.fc1 = nn.Linear(hidden2, 16)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(16, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        out, _ = self.gru1(x)
        out, _ = self.gru2(out)
        out = out[:, -1, :]
        out = self.fc1(out)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        out = self.sigmoid(out)
        return out


class RiskPredictor:
    """Combined risk prediction using all 4 trained models."""

    FEATURE_COLS = [
        "salary_delay_days", "savings_wow_delta_pct", "atm_withdrawal_count_7d",
        "atm_withdrawal_amount_7d", "discretionary_spend_7d", "lending_upi_count_7d",
        "lending_upi_amount_7d", "failed_autodebit_count", "utility_payment_delay_days",
        "gambling_spend_7d", "credit_utilization", "net_cashflow_7d"
    ]

    FEATURE_DESCRIPTIONS = {
        "salary_delay_days": "salary delayed by {value:.0f} days",
        "savings_wow_delta_pct": "savings changed {value:.1f}% week-over-week",
        "atm_withdrawal_count_7d": "{value:.0f} ATM withdrawals in 7 days",
        "atm_withdrawal_amount_7d": "ATM withdrawal amount: ₹{value:.0f}",
        "discretionary_spend_7d": "discretionary spending: ₹{value:.0f}",
        "lending_upi_count_7d": "{value:.0f} UPI transfers to lending apps",
        "lending_upi_amount_7d": "lending app UPI amount: ₹{value:.0f}",
        "failed_autodebit_count": "{value:.0f} failed auto-debits",
        "utility_payment_delay_days": "utility payments delayed {value:.0f} days",
        "gambling_spend_7d": "gambling spend: ₹{value:.0f}",
        "credit_utilization": "credit utilization: {value:.1%}",
        "net_cashflow_7d": "net cashflow: ₹{value:.0f}",
    }

    def __init__(self):
        with open(os.path.join(ROOT, "config", "model_config.yaml"), "r") as f:
            self.config = yaml.safe_load(f)
        with open(os.path.join(ROOT, "config", "thresholds.yaml"), "r") as f:
            self.thresholds = yaml.safe_load(f)

        self.features = self.config["features"]["tabular"]
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        models_dir = os.path.join(ROOT, "models")

        # Load tabular models
        self.lgbm = joblib.load(os.path.join(models_dir, "lgbm_model.pkl"))
        self.iso_forest = joblib.load(os.path.join(models_dir, "isolation_forest.pkl"))
        self.ensemble_meta = joblib.load(os.path.join(models_dir, "ensemble_meta.pkl"))
        self.gru_scaler = joblib.load(os.path.join(models_dir, "gru_scaler.pkl"))

        # Load GRU model (architecture from train_real_data.py)
        gru_cfg = self.config["gru"]
        self.gru = GRUModel(
            input_size=len(self.features),
            hidden1=gru_cfg["hidden1"],
            hidden2=gru_cfg["hidden2"],
            dropout=gru_cfg["dropout"]
        ).to(self.device)
        self.gru.load_state_dict(
            torch.load(os.path.join(models_dir, "gru_model.pt"),
                        weights_only=True, map_location=self.device))
        self.gru.eval()

        # SHAP explainer (lazy-loaded)
        self._shap_explainer = None

        # Load behavioral data (for customer-based lookups)
        try:
            self.weekly_df = pd.read_csv(
                os.path.join(ROOT, "data", "weekly_behavioral_features.csv"))
            self.customers_df = pd.read_csv(
                os.path.join(ROOT, "data", "customers.csv"))
        except Exception:
            self.weekly_df = pd.DataFrame()
            self.customers_df = pd.DataFrame()

        # Thresholds
        rt = self.thresholds["risk_thresholds"]
        self.th_low = rt["monitor_only"]
        self.th_med = rt["low_intervention"]
        self.th_high = rt["high_risk"]

        print(f"[OK] RiskPredictor loaded - {len(self.features)} features, device={self.device}")

    @property
    def shap_explainer(self):
        if self._shap_explainer is None:
            import shap
            self._shap_explainer = shap.TreeExplainer(self.lgbm)
        return self._shap_explainer

    # ── Direct prediction from raw features ──────────────────

    def predict_from_features(self, feature_values: dict):
        """Predict risk from raw Lending Club feature values.

        Args:
            feature_values: dict with feature names as keys
                e.g. {"total_rec_prncp": 5000, "total_rec_int": 1200, ...}

        Returns:
            Full prediction dict with all model outputs
        """
        x = np.array([[feature_values.get(f, 0.0) for f in self.features]],
                      dtype=np.float32)

        # ── LightGBM ──
        lgbm_prob = float(self.lgbm.predict(x)[0])

        # ── GRU (simulate sequence by repeating the feature vector) ──
        seq_len = self.config["gru"]["seq_len"]
        x_seq = np.tile(x, (seq_len, 1))  # (seq_len, n_features)
        x_scaled = self.gru_scaler.transform(x_seq).reshape(1, seq_len, len(self.features))
        with torch.no_grad():
            seq_tensor = torch.FloatTensor(x_scaled).to(self.device)
            gru_prob = float(self.gru(seq_tensor).cpu().numpy().flatten()[0])

        # ── Isolation Forest (uses 5 specific features) ──
        iso_features = ["atm_withdrawal_amount_7d", "lending_upi_amount_7d",
                        "net_cashflow_7d", "credit_utilization", "failed_autodebit_count"]
        iso_indices = [self.features.index(f) for f in iso_features]
        x_iso = x[:, iso_indices]
        anomaly_flag = bool(self.iso_forest.predict(x_iso)[0] == -1)

        # ── Ensemble (5 meta-features) ──
        c_util_idx = self.features.index("credit_utilization")
        credit_utilization = x[0, c_util_idx]
        # Assume latest week (52) and default/medium stress level (1) if single prediction
        meta_x = np.array([[lgbm_prob, gru_prob, 52.0/52.0, 1.0/2.0, credit_utilization]])
        ensemble_prob = float(self.ensemble_meta.predict_proba(meta_x)[:, 1][0])

        # Anomaly escalation
        if anomaly_flag and ensemble_prob >= 0.50:
            ensemble_prob = max(ensemble_prob, self.th_high)

        # Risk level
        if ensemble_prob >= self.th_high:
            risk_level = "HIGH"
        elif ensemble_prob >= self.th_low:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # SHAP explanation — pass real model outputs for AI-powered narrative
        shap_result = self._compute_shap(
            x, lgbm_prob=lgbm_prob, gru_prob=gru_prob,
            ensemble_prob=ensemble_prob, anomaly_flag=anomaly_flag,
            risk_level=risk_level
        )

        return {
            "lgbm_prob": round(lgbm_prob, 4),
            "gru_prob": round(gru_prob, 4),
            "ensemble_prob": round(ensemble_prob, 4),
            "anomaly_flag": anomaly_flag,
            "risk_level": risk_level,
            "shap_top3": shap_result["top_drivers"],
            "all_shap": shap_result["all_drivers"],
            "shap_values": shap_result["shap_values"],
            "human_explanation": shap_result["human_explanation"],
            "confidence": shap_result["confidence"]
        }

    def _compute_shap(self, x, lgbm_prob=0.0, gru_prob=0.0, ensemble_prob=0.0, anomaly_flag=False, risk_level="LOW"):
        """Compute SHAP values for a single sample."""
        try:
            raw_shap = self.shap_explainer.shap_values(x)
            # CRITICAL: SHAP BUG FIX
            if isinstance(raw_shap, list):
                shap_vals = raw_shap[1] if len(raw_shap) > 1 else raw_shap[0]
            else:
                shap_vals = raw_shap
            shap_vals = shap_vals.flatten()
        except Exception as e:
            print(f"SHAP error: {e}")
            shap_vals = np.zeros(len(self.features))

        # Confidence Calculation
        confidence = 1.0 - np.var([lgbm_prob, gru_prob, ensemble_prob])
        confidence = round(np.clip(confidence, 0.4, 0.99), 2)

        feature_contribs = []
        for i, fname in enumerate(self.features):
            feature_contribs.append({
                "feature": fname,
                "contribution": round(float(shap_vals[i]), 4),
                "direction": "INCREASES_RISK" if shap_vals[i] > 0 else "DECREASES_RISK",
                "abs_contribution": abs(float(shap_vals[i]))
            })
        feature_contribs.sort(key=lambda c: c["abs_contribution"], reverse=True)

        top_drivers = [{
            "feature": fc["feature"],
            "contribution": fc["contribution"],
            "direction": fc["direction"]
        } for fc in feature_contribs[:3]]

        # Build feature values dict for the explainer
        fv = {f: float(x.flatten()[i]) for i, f in enumerate(self.features)}

        # Generate AI-powered explanation using real model data
        explanation = generate_ai_explanation(
            shap_drivers=feature_contribs,
            feature_values=fv,
            ensemble_prob=ensemble_prob,
            lgbm_prob=lgbm_prob,
            gru_prob=gru_prob,
            anomaly_flag=anomaly_flag,
            risk_level=risk_level,
        )

        return {
            "shap_values": {f: round(float(v), 4) for f, v in zip(self.features, shap_vals)},
            "top_drivers": top_drivers,
            "all_drivers": feature_contribs,
            "human_explanation": explanation,
            "confidence": confidence
        }

    # _generate_explanation is now handled by inference.ai_explain module
    # which provides both Gemini-powered and improved template-based explanations

    # ── Customer-based prediction (uses behavioral CSVs) ──────

    def predict_single(self, customer_id, week_number=None):
        """Predict risk for a customer from behavioral data.

        Falls back to CSV-based risk scores if models can't match features.
        """
        if self.weekly_df.empty:
            return {"error": "No behavioral data loaded"}

        cust_data = self.weekly_df[self.weekly_df["customer_id"] == customer_id]
        if len(cust_data) == 0:
            return {"error": f"Customer {customer_id} not found"}

        if week_number is None:
            week_number = int(cust_data["week_number"].max())

        latest = cust_data[cust_data["week_number"] == week_number]
        if len(latest) == 0:
            latest = cust_data[cust_data["week_number"] == cust_data["week_number"].max()]
        latest_row = latest.iloc[0]

        # The behavioral CSV has different features than the trained models.
        # Use the raw risk_score from the CSV and run SHAP on available features.
        risk_score = float(latest_row.get("risk_score", 0.5))

        # Map behavioral features to model features where possible
        feature_map = {}
        for f in self.features:
            if f in latest_row.index:
                feature_map[f] = float(latest_row[f])
            else:
                feature_map[f] = 0.0

        # Check if we have enough real features to run the model
        available = sum(1 for f in self.features if f in latest_row.index)

        if available >= 6:
            # Enough features overlap — run full model
            pred = self.predict_from_features(feature_map)
        else:
            # Not enough overlap — use CSV risk_score with synthetic model outputs
            pred = {
                "lgbm_prob": risk_score,
                "gru_prob": risk_score,
                "ensemble_prob": risk_score,
                "anomaly_flag": risk_score >= 0.70,
                "risk_level": "HIGH" if risk_score >= self.th_high
                              else "MEDIUM" if risk_score >= self.th_low
                              else "LOW",
                "shap_top3": [],
                "all_shap": [],
                "shap_values": {},
                "human_explanation": f"Risk score from behavioral data: {risk_score:.4f}",
            }

        # Add customer profile
        cust_profile = self.customers_df[
            self.customers_df["customer_id"] == customer_id]
        profile_dict = cust_profile.iloc[0].to_dict() if len(cust_profile) > 0 else {}

        return {
            "customer_id": customer_id,
            "week_number": int(week_number),
            **pred,
            "customer_profile": profile_dict,
        }

    def batch_predict(self, week_number=52):
        """Run predict_single for all customers."""
        if self.customers_df.empty:
            return pd.DataFrame()

        customer_ids = self.customers_df["customer_id"].unique()
        results = []
        for i, cid in enumerate(customer_ids):
            if (i + 1) % 200 == 0:
                print(f"  Predicting {i+1}/{len(customer_ids)}...")
            try:
                result = self.predict_single(cid, week_number)
                results.append(result)
            except Exception as e:
                results.append({
                    "customer_id": cid,
                    "ensemble_prob": 0.0,
                    "risk_level": "LOW",
                    "error": str(e)
                })

        results_df = pd.DataFrame(results)
        if "ensemble_prob" in results_df.columns:
            results_df = results_df.sort_values("ensemble_prob", ascending=False)
        return results_df


if __name__ == "__main__":
    predictor = RiskPredictor()

    # Demo: predict from raw features
    sample = {
        "total_rec_late_fee": 0.0,
        "recoveries": 0.0,
        "last_pymnt_amnt": 357.48,
        "loan_amnt_div_instlmnt": 36.1,
        "debt_settlement_flag": 0,
        "loan_age": 36,
        "total_rec_int": 2214.92,
        "out_prncp": 0.0,
        "time_since_last_credit_pull": 1,
        "time_since_last_payment": 1,
        "int_rate%": 13.56,
        "total_rec_prncp": 10000.0,
    }
    result = predictor.predict_from_features(sample)
    print("\n🔍 Prediction from raw features:")
    print(json.dumps(result, indent=2, default=str))

    # Demo: customer-based prediction (if CSV data exists)
    if not predictor.weekly_df.empty:
        cid = predictor.customers_df["customer_id"].iloc[0]
        result = predictor.predict_single(cid)
        print(f"\n🔍 Customer prediction for {cid}:")
        print(json.dumps({k: v for k, v in result.items()
                          if k != "customer_profile"}, indent=2, default=str))
