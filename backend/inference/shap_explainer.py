"""
SHAP Explainability Engine — Real Data Models
Provides human-readable explanations for risk scores using SHAP.
Works with LightGBM trained on Lending Club features.
"""

import numpy as np
import pandas as pd
import shap
import joblib
import yaml
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

FEATURE_DESCRIPTIONS = {
    "total_rec_late_fee": "late fees totaling ${value:.2f}",
    "recoveries": "recovery amount of ${value:.2f}",
    "last_pymnt_amnt": "last payment was ${value:.2f}",
    "loan_amnt_div_instlmnt": "loan-to-installment ratio of {value:.1f}",
    "debt_settlement_flag": "debt settlement flag is {value:.0f}",
    "loan_age": "loan is {value:.0f} months old",
    "total_rec_int": "total interest received: ${value:.2f}",
    "out_prncp": "outstanding principal: ${value:.2f}",
    "time_since_last_credit_pull": "last credit pull {value:.0f} months ago",
    "time_since_last_payment": "last payment {value:.0f} months ago",
    "int_rate%": "interest rate at {value:.1f}%",
    "total_rec_prncp": "total principal received: ${value:.2f}",
}


class SHAPExplainer:
    """SHAP-based explainability for LightGBM risk predictions."""

    def __init__(self):
        with open(os.path.join(ROOT, "config", "model_config.yaml"), "r") as f:
            config = yaml.safe_load(f)
        self.features = config["features"]["tabular"]
        model_path = os.path.join(ROOT, "models", "lgbm_model.pkl")
        self.model = joblib.load(model_path)
        self.explainer = shap.TreeExplainer(self.model)

    def explain(self, feature_values):
        """Compute SHAP values for a single sample.

        Args:
            feature_values: dict, Series, or array with feature values

        Returns:
            dict with shap_values, top_drivers, human_explanation
        """
        if isinstance(feature_values, dict):
            x = np.array([[feature_values.get(f, 0) for f in self.features]])
        elif isinstance(feature_values, pd.Series):
            available = [f for f in self.features if f in feature_values.index]
            if len(available) == len(self.features):
                x = feature_values[self.features].values.reshape(1, -1)
            else:
                x = np.array([[feature_values.get(f, 0) for f in self.features]])
        else:
            x = np.array(feature_values).reshape(1, -1)

        x = x.astype(float)

        shap_vals = self.explainer.shap_values(x)
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[1] if len(shap_vals) > 1 else shap_vals[0]
        shap_vals = shap_vals.flatten()

        # Get top drivers sorted by absolute contribution
        feature_contribs = []
        for i, fname in enumerate(self.features):
            feature_contribs.append({
                "feature": fname,
                "contribution": round(float(shap_vals[i]), 4),
                "direction": "INCREASES_RISK" if shap_vals[i] > 0 else "DECREASES_RISK",
                "abs_contribution": abs(float(shap_vals[i]))
            })
        feature_contribs.sort(key=lambda x: x["abs_contribution"], reverse=True)

        top_drivers = []
        for fc in feature_contribs[:3]:
            top_drivers.append({
                "feature": fc["feature"],
                "contribution": fc["contribution"],
                "direction": fc["direction"]
            })

        # Generate human explanation
        explanation = self._generate_explanation(top_drivers, x[0])

        return {
            "shap_values": {f: round(float(v), 4) for f, v in zip(self.features, shap_vals)},
            "top_drivers": top_drivers,
            "all_drivers": feature_contribs,
            "human_explanation": explanation
        }

    def _generate_explanation(self, top_drivers, feature_values):
        """Generate a human-readable explanation string from SHAP values."""
        parts = []
        for driver in top_drivers:
            fname = driver["feature"]
            idx = self.features.index(fname) if fname in self.features else -1
            val = feature_values[idx] if idx >= 0 else 0

            if fname == "total_rec_prncp":
                parts.append(f"total principal received is ${val:,.2f}")
            elif fname == "total_rec_int":
                parts.append(f"total interest received is ${val:,.2f}")
            elif fname == "last_pymnt_amnt":
                parts.append(f"last payment amount was ${val:,.2f}")
            elif fname == "out_prncp":
                if val > 0:
                    parts.append(f"outstanding principal of ${val:,.2f}")
                else:
                    parts.append(f"no outstanding principal remaining")
            elif fname == "loan_age":
                parts.append(f"loan is {int(val)} months old")
            elif fname == "time_since_last_payment":
                parts.append(f"last payment was {int(val)} months ago")
            elif fname == "time_since_last_credit_pull":
                parts.append(f"last credit pull was {int(val)} months ago")
            elif fname == "int_rate%":
                parts.append(f"interest rate is {val:.1f}%")
            elif fname == "total_rec_late_fee":
                if val > 0:
                    parts.append(f"${val:,.2f} in late fees")
                else:
                    parts.append(f"no late fees recorded")
            elif fname == "recoveries":
                if val > 0:
                    parts.append(f"${val:,.2f} in post-default recoveries")
                else:
                    parts.append(f"no recovery amounts")
            elif fname == "debt_settlement_flag":
                if val > 0:
                    parts.append(f"debt settlement is active")
                else:
                    parts.append(f"no debt settlement flag")
            elif fname == "loan_amnt_div_instlmnt":
                parts.append(f"loan-to-installment ratio is {val:.1f}")
            else:
                parts.append(f"{fname} value is {val:.2f}")

        if not parts:
            return "No significant risk drivers identified for this loan."

        explanation = "This loan is flagged primarily because "
        if len(parts) == 1:
            explanation += parts[0] + "."
        elif len(parts) == 2:
            explanation += parts[0] + " and " + parts[1] + "."
        else:
            explanation += ", ".join(parts[:-1]) + ", and " + parts[-1] + "."

        return explanation


if __name__ == "__main__":
    explainer = SHAPExplainer()
    sample = {
        "total_rec_late_fee": 25.0,
        "recoveries": 0.0,
        "last_pymnt_amnt": 0.0,
        "loan_amnt_div_instlmnt": 36.1,
        "debt_settlement_flag": 0,
        "loan_age": 12,
        "total_rec_int": 800.0,
        "out_prncp": 8500.0,
        "time_since_last_credit_pull": 2,
        "time_since_last_payment": 5,
        "int_rate%": 18.5,
        "total_rec_prncp": 1500.0,
    }
    result = explainer.explain(sample)
    import json
    print(json.dumps(result, indent=2))
