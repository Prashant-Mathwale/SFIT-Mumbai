"""
Generate all 4 CSV datasets for the Pre-Delinquency Intervention Engine.
Run this once to create:
  data/customers.csv
  data/transactions.csv
  data/weekly_behavioral_features.csv
  data/intervention_log.csv
"""

import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

random.seed(42)
np.random.seed(42)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ─────────────────────────────────────────────────
# FILE 1: customers.csv  (2,000 rows)
# ─────────────────────────────────────────────────

CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata",
          "Ahmedabad", "Jaipur", "Lucknow", "Nagpur", "Indore", "Bhopal", "Coimbatore",
          "Kochi", "Surat", "Vadodara", "Chandigarh", "Noida", "Gurgaon"]

OCCUPATIONS = ["Salaried", "Self-Employed", "Business Owner", "Freelancer",
               "Government Employee", "Teacher", "Healthcare Worker", "IT Professional",
               "Sales Executive", "Retired"]

PRODUCT_TYPES = ["Personal Loan", "Home Loan", "Auto Loan", "Credit Card",
                 "Business Loan", "Education Loan"]

FIRST_NAMES = ["Rajesh", "Priya", "Amit", "Sunita", "Vikram", "Anita", "Suresh", "Kavita",
               "Manoj", "Neha", "Arun", "Deepa", "Rahul", "Meena", "Sanjay", "Pooja",
               "Ravi", "Lakshmi", "Krishna", "Divya", "Ajay", "Swati", "Ramesh", "Geeta",
               "Nitin", "Asha", "Mohan", "Rekha", "Vinod", "Shanti", "Prakash", "Usha",
               "Sunil", "Sarita", "Ashok", "Kamla", "Dinesh", "Padma", "Gopal", "Nirmala"]

LAST_NAMES = ["Sharma", "Patel", "Kumar", "Singh", "Verma", "Gupta", "Reddy", "Nair",
              "Desai", "Mehta", "Joshi", "Rao", "Das", "Mishra", "Iyer", "Pillai",
              "Agarwal", "Choudhury", "Bhat", "Menon", "Saxena", "Tiwari", "Pandey",
              "Kapoor", "Banerjee", "Mukherjee", "Sinha", "Yadav", "Malhotra", "Thakur"]

customers = []
for i in range(2000):
    cid = f"CUS-{10001 + i}"
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    age = random.randint(22, 65)
    city = random.choice(CITIES)
    occupation = random.choice(OCCUPATIONS)
    monthly_salary = int(np.random.lognormal(mean=10.5, sigma=0.5)) // 1000 * 1000
    monthly_salary = max(15000, min(monthly_salary, 300000))
    credit_score = int(np.clip(np.random.normal(700, 80), 300, 900))
    loan_amount = random.choice([0] * 2 + [int(monthly_salary * random.uniform(12, 60))] * 8)
    emi_amount = int(loan_amount / random.uniform(12, 48)) if loan_amount > 0 else 0
    credit_limit = int(monthly_salary * random.uniform(1.5, 4))
    savings_balance_initial = int(monthly_salary * random.uniform(0.5, 6))
    product_type = random.choice(PRODUCT_TYPES)
    account_open_days = random.randint(90, 2000)
    customers.append([cid, name, age, city, occupation, monthly_salary, credit_score,
                      loan_amount, emi_amount, credit_limit, savings_balance_initial,
                      product_type, account_open_days])

customers_df = pd.DataFrame(customers, columns=[
    "customer_id", "name", "age", "city", "occupation", "monthly_salary",
    "credit_score", "loan_amount", "emi_amount", "credit_limit",
    "savings_balance_initial", "product_type", "account_open_days"
])
customers_df.to_csv(f"{DATA_DIR}/customers.csv", index=False)
print(f"✅ customers.csv: {len(customers_df)} rows")

# ─────────────────────────────────────────────────
# FILE 2: transactions.csv  (~187,000 rows)
# ─────────────────────────────────────────────────

CATEGORIES = {
    "SALARY":           ("CREDIT", (0.95, 1.05)),
    "EMI_PAYMENT":      ("DEBIT",  (0.98, 1.02)),
    "ATM_WITHDRAWAL":   ("DEBIT",  (0.3, 0.8)),
    "DINING":           ("DEBIT",  (0.05, 0.15)),
    "UPI_LENDING_APP":  ("DEBIT",  (0.1, 0.4)),
    "GAMBLING_LOTTERY":  ("DEBIT",  (0.02, 0.1)),
    "ELECTRICITY":      ("DEBIT",  (0.03, 0.08)),
    "WATER":            ("DEBIT",  (0.01, 0.03)),
    "GAS":              ("DEBIT",  (0.01, 0.03)),
    "BROADBAND":        ("DEBIT",  (0.02, 0.04)),
    "SHOPPING":         ("DEBIT",  (0.05, 0.2)),
    "ENTERTAINMENT":    ("DEBIT",  (0.03, 0.1)),
    "TRAVEL":           ("DEBIT",  (0.05, 0.15)),
}

CHANNELS = ["UPI", "NEFT", "IMPS", "ATM", "POS", "NET_BANKING", "AUTO_DEBIT"]

transactions = []
txn_counter = 0
base_date = datetime(2025, 1, 1)

for _, cust in customers_df.iterrows():
    cid = cust["customer_id"]
    salary = cust["monthly_salary"]
    emi = cust["emi_amount"]
    is_stressed = random.random() < 0.25  # 25% of customers show stress

    for month in range(1, 13):
        month_start = base_date + timedelta(days=(month - 1) * 30)

        # Salary credit
        salary_day = random.randint(1, 5) if not is_stressed else random.randint(5, 20)
        txn_counter += 1
        txn_date = month_start + timedelta(days=salary_day)
        transactions.append([f"TXN-{txn_counter:07d}", cid, txn_date.strftime("%Y-%m-%d"),
                             "CREDIT", "SALARY", int(salary * random.uniform(0.95, 1.05)),
                             "NEFT", month])

        # EMI payment
        if emi > 0:
            txn_counter += 1
            emi_day = random.randint(1, 5)
            failed = is_stressed and random.random() < 0.3
            txn_date = month_start + timedelta(days=emi_day)
            transactions.append([f"TXN-{txn_counter:07d}", cid, txn_date.strftime("%Y-%m-%d"),
                                 "FAILED" if failed else "DEBIT", "EMI_PAYMENT",
                                 emi, "AUTO_DEBIT", month])

        # Generate multiple transactions per category per month
        num_atm = random.randint(0, 3) if not is_stressed else random.randint(3, 8)
        for _ in range(num_atm):
            txn_counter += 1
            txn_date = month_start + timedelta(days=random.randint(0, 29))
            transactions.append([f"TXN-{txn_counter:07d}", cid, txn_date.strftime("%Y-%m-%d"),
                                 "DEBIT", "ATM_WITHDRAWAL",
                                 int(salary * random.uniform(0.02, 0.08)),
                                 "ATM", month])

        # Dining
        for _ in range(random.randint(1, 5)):
            txn_counter += 1
            txn_date = month_start + timedelta(days=random.randint(0, 29))
            transactions.append([f"TXN-{txn_counter:07d}", cid, txn_date.strftime("%Y-%m-%d"),
                                 "DEBIT", "DINING",
                                 int(salary * random.uniform(0.01, 0.04)),
                                 random.choice(["UPI", "POS"]), month])

        # UPI Lending App (stressed customers)
        if is_stressed:
            for _ in range(random.randint(1, 4)):
                txn_counter += 1
                txn_date = month_start + timedelta(days=random.randint(0, 29))
                transactions.append([f"TXN-{txn_counter:07d}", cid, txn_date.strftime("%Y-%m-%d"),
                                     "DEBIT", "UPI_LENDING_APP",
                                     int(salary * random.uniform(0.05, 0.2)),
                                     "UPI", month])

        # Gambling (some stressed)
        if is_stressed and random.random() < 0.4:
            for _ in range(random.randint(1, 3)):
                txn_counter += 1
                txn_date = month_start + timedelta(days=random.randint(0, 29))
                transactions.append([f"TXN-{txn_counter:07d}", cid, txn_date.strftime("%Y-%m-%d"),
                                     "DEBIT", "GAMBLING_LOTTERY",
                                     int(random.uniform(100, 2000)),
                                     "UPI", month])

        # Utility bills
        for cat in ["ELECTRICITY", "WATER", "GAS", "BROADBAND"]:
            txn_counter += 1
            util_day = random.randint(5, 15) if not is_stressed else random.randint(15, 28)
            txn_date = month_start + timedelta(days=util_day)
            lo, hi = CATEGORIES[cat][1]
            transactions.append([f"TXN-{txn_counter:07d}", cid, txn_date.strftime("%Y-%m-%d"),
                                 "DEBIT", cat,
                                 int(salary * random.uniform(lo, hi)),
                                 random.choice(["AUTO_DEBIT", "NET_BANKING", "UPI"]), month])

        # Shopping & Entertainment
        for cat in ["SHOPPING", "ENTERTAINMENT", "TRAVEL"]:
            n = random.randint(0, 3) if not is_stressed else random.randint(0, 1)
            for _ in range(n):
                txn_counter += 1
                txn_date = month_start + timedelta(days=random.randint(0, 29))
                lo, hi = CATEGORIES[cat][1]
                transactions.append([f"TXN-{txn_counter:07d}", cid, txn_date.strftime("%Y-%m-%d"),
                                     "DEBIT", cat,
                                     int(salary * random.uniform(lo, hi)),
                                     random.choice(["UPI", "POS", "NET_BANKING"]), month])

transactions_df = pd.DataFrame(transactions, columns=[
    "txn_id", "customer_id", "date", "txn_type", "category", "amount", "channel", "month"
])
transactions_df.to_csv(f"{DATA_DIR}/transactions.csv", index=False)
print(f"✅ transactions.csv: {len(transactions_df)} rows")

# ─────────────────────────────────────────────────
# FILE 3: weekly_behavioral_features.csv  (104,000 rows)
# ─────────────────────────────────────────────────

weekly_features = []
for _, cust in customers_df.iterrows():
    cid = cust["customer_id"]
    salary = cust["monthly_salary"]
    credit_limit = cust["credit_limit"]
    credit_score = cust["credit_score"]
    savings = cust["savings_balance_initial"]
    is_stressed = random.random() < 0.25
    stress_progression = random.uniform(0.3, 0.9) if is_stressed else 0.0

    for week in range(1, 53):
        t = week / 52  # time progression

        if is_stressed:
            # Gradually worsening features
            stress_factor = stress_progression * t
            salary_delay = int(np.clip(np.random.normal(5 + 10 * stress_factor, 3), 0, 25))
            savings_delta = np.random.normal(-5 - 15 * stress_factor, 5)
            atm_count = int(np.clip(np.random.poisson(2 + 4 * stress_factor), 0, 15))
            atm_amount = int(atm_count * salary * random.uniform(0.02, 0.06))
            discretionary = int(salary * random.uniform(0.05, 0.15) * (1 - 0.5 * stress_factor))
            lending_count = int(np.clip(np.random.poisson(1 + 3 * stress_factor), 0, 8))
            lending_amount = int(lending_count * salary * random.uniform(0.05, 0.15))
            failed_autodebit = int(np.clip(np.random.poisson(0.5 * stress_factor), 0, 3))
            utility_delay = int(np.clip(np.random.normal(5 + 10 * stress_factor, 3), 0, 25))
            gambling = int(np.clip(np.random.exponential(300 * stress_factor), 0, 5000))
            credit_util = np.clip(random.uniform(0.3, 0.5) + 0.4 * stress_factor, 0, 1)
            net_cash = int(salary * random.uniform(-0.3, 0.1) * (1 - stress_factor))
        else:
            salary_delay = int(np.clip(np.random.normal(2, 2), 0, 8))
            savings_delta = np.random.normal(2, 3)
            atm_count = int(np.clip(np.random.poisson(1.5), 0, 6))
            atm_amount = int(atm_count * salary * random.uniform(0.01, 0.04))
            discretionary = int(salary * random.uniform(0.1, 0.25))
            lending_count = 0
            lending_amount = 0
            failed_autodebit = 0
            utility_delay = int(np.clip(np.random.normal(3, 2), 0, 10))
            gambling = 0
            credit_util = np.clip(random.uniform(0.1, 0.4), 0, 1)
            net_cash = int(salary * random.uniform(0.05, 0.3))

        savings = max(0, savings * (1 + savings_delta / 100))

        # Risk score: composite of all signals
        risk_components = [
            min(salary_delay / 20, 1) * 0.15,
            min(abs(min(savings_delta, 0)) / 30, 1) * 0.12,
            min(atm_count / 8, 1) * 0.08,
            min(lending_count / 5, 1) * 0.12,
            min(failed_autodebit / 2, 1) * 0.15,
            min(utility_delay / 15, 1) * 0.08,
            min(gambling / 2000, 1) * 0.05,
            min(credit_util, 1) * 0.10,
            max(0, 1 - net_cash / (salary * 0.2)) * 0.10 if salary > 0 else 0,
            max(0, 1 - discretionary / (salary * 0.15)) * 0.05,
        ]
        risk_score = np.clip(sum(risk_components) + np.random.normal(0, 0.05), 0, 1)

        # Stress level: 0, 1, 2
        if risk_score < 0.35:
            stress_level = 0
        elif risk_score < 0.60:
            stress_level = 1
        else:
            stress_level = 2

        # Will default: based on risk_score with noise
        default_prob = 1 / (1 + np.exp(-8 * (risk_score - 0.55)))
        will_default = 1 if random.random() < default_prob else 0

        weekly_features.append([
            cid, week, 2025, stress_level, salary_delay, round(savings, 2),
            round(savings_delta, 2), atm_count, atm_amount, discretionary,
            lending_count, lending_amount, failed_autodebit, utility_delay,
            gambling, round(credit_util, 4), net_cash, round(risk_score, 4),
            will_default
        ])

weekly_df = pd.DataFrame(weekly_features, columns=[
    "customer_id", "week_number", "year", "stress_level", "salary_delay_days",
    "savings_balance", "savings_wow_delta_pct", "atm_withdrawal_count_7d",
    "atm_withdrawal_amount_7d", "discretionary_spend_7d", "lending_upi_count_7d",
    "lending_upi_amount_7d", "failed_autodebit_count", "utility_payment_delay_days",
    "gambling_spend_7d", "credit_utilization", "net_cashflow_7d", "risk_score",
    "will_default_next_30d"
])
weekly_df.to_csv(f"{DATA_DIR}/weekly_behavioral_features.csv", index=False)
print(f"✅ weekly_behavioral_features.csv: {len(weekly_df)} rows")
print(f"   Default rate: {weekly_df['will_default_next_30d'].mean():.1%}")

# ─────────────────────────────────────────────────
# FILE 4: intervention_log.csv  (~32,000 rows)
# ─────────────────────────────────────────────────

INTERVENTION_TYPES = ["PAYMENT_HOLIDAY", "RESTRUCTURING_OFFER", "FINANCIAL_COUNSELING",
                      "RM_CALL", "SMS_OUTREACH", "MONITOR_ONLY"]
INT_CHANNELS = ["SMS", "EMAIL", "APP", "CALL"]
INT_STATUSES = ["SENT", "DELIVERED", "OPENED", "ACTED_UPON", "IGNORED"]
INT_OUTCOMES = ["RECOVERED", "PENDING", "NO_ACTION"]
TOP_SIGNALS = ["salary_delay_days", "savings_wow_delta_pct", "credit_utilization",
               "failed_autodebit_count", "lending_upi_count_7d", "atm_withdrawal_count_7d",
               "utility_payment_delay_days", "gambling_spend_7d"]

interventions = []
for _, row in weekly_df[weekly_df["risk_score"] >= 0.40].iterrows():
    if random.random() < 0.55:  # Not all flagged get interventions
        risk = row["risk_score"]
        if risk >= 0.70:
            itype = random.choice(["PAYMENT_HOLIDAY", "RM_CALL", "RESTRUCTURING_OFFER"])
        elif risk >= 0.55:
            itype = random.choice(["FINANCIAL_COUNSELING", "SMS_OUTREACH", "RESTRUCTURING_OFFER"])
        else:
            itype = random.choice(["SMS_OUTREACH", "MONITOR_ONLY"])

        status = random.choice(INT_STATUSES)
        if status in ["ACTED_UPON"]:
            outcome = random.choice(["RECOVERED"] * 3 + ["PENDING"])
        elif status == "IGNORED":
            outcome = random.choice(["NO_ACTION"] * 2 + ["PENDING"])
        else:
            outcome = random.choice(INT_OUTCOMES)

        interventions.append([
            row["customer_id"], row["week_number"], round(risk, 4),
            itype, random.choice(INT_CHANNELS), status, outcome,
            random.choice(TOP_SIGNALS)
        ])

intervention_df = pd.DataFrame(interventions, columns=[
    "customer_id", "week_number", "risk_score_at_trigger", "intervention_type",
    "channel", "status", "outcome", "top_signal"
])
intervention_df.to_csv(f"{DATA_DIR}/intervention_log.csv", index=False)
print(f"✅ intervention_log.csv: {len(intervention_df)} rows")
print(f"\n🎉 All 4 CSV files generated in {DATA_DIR}/")
