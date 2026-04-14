"""
Generate all 4 CSV datasets for the Praeventix Bank-Grade EWS.
============================================================
Implements:
1. 🌾 Farmer (Climate/Harvest Seasonality)
2. 🎓 Student (Allowance Logic)
3. 🎨 Freelancer (Project-based irregular income)
4. 💊 Medical Shock (One-time anomaly detection)
5. 🎉 Festival Spike (Seasonal spending normalization)
6. 💵 Cash User (Alternative digital footprint)
7. 🚜 Decision Intelligence (Context-aware risk signals)
"""

import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Reproducibility
random.seed(42)
np.random.seed(42)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ── DOMAIN CONSTANTS & MAPPING ──
SEGMENT_MAP = {
    "salaried": 0,
    "self-employed": 1,
    "farmer": 2,
    "freelancer": 3,
    "student": 4,
    "other": 5
}

CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow"]
OCCUPATIONS = ["Salaried", "Self-Employed", "Business Owner", "Freelancer", "Farmer", "Student",
               "Government Employee", "Teacher", "Healthcare Worker", "IT Professional",
               "Sales Executive", "Retired"]
PRODUCT_TYPES = ["Personal Loan", "Home Loan", "Auto Loan", "Credit Card", "Business Loan", "Education Loan"]

FIRST_NAMES = ["Rajesh", "Priya", "Amit", "Sunita", "Vikram", "Anita", "Suresh", "Kavita", "Manoj", "Neha",
               "Arun", "Deepa", "Rahul", "Meena", "Sanjay", "Pooja", "Ravi", "Lakshmi", "Krishna", "Divya"]
LAST_NAMES = ["Sharma", "Patel", "Kumar", "Singh", "Verma", "Gupta", "Reddy", "Nair", "Desai", "Mehta",
              "Joshi", "Rao", "Das", "Mishra", "Iyer", "Pillai", "Agarwal", "Choudhury", "Bhat", "Menon"]

# ─────────────────────────────────────────────────
# PHASE 1: Generate Customers (5,000)
# ─────────────────────────────────────────────────
customers = []
for i in range(5000):
    cid = f"CUS-{10001 + i}"
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    age = random.randint(18, 70)
    city = random.choice(CITIES)
    occupation = random.choice(OCCUPATIONS)
    
    # ── Segment Assignment ──
    if occupation in ["Salaried", "Government Employee", "IT Professional", "Sales Executive", "Teacher", "Healthcare Worker"]:
        segment = "salaried"
    elif occupation in ["Self-Employed", "Business Owner"]:
        segment = "self-employed"
    elif occupation == "Farmer":
        segment = "farmer"
    elif occupation == "Freelancer":
        segment = "freelancer"
    elif occupation == "Student":
        segment = "student"
    else:
        segment = "other"

    # ── Income Modeling ──
    base_income = int(np.random.lognormal(mean=10.6, sigma=0.45)) // 1000 * 1000
    if segment == "student":
        base_income = random.randint(8000, 25000) # Allowance
    elif segment == "farmer":
        base_income = random.randint(15000, 60000) # Seasonal avg
    
    base_income = max(8000, min(base_income, 450000))
    
    # Income Segments
    if base_income < 35000:
        income_tier = "low"
    elif base_income > 120000:
        income_tier = "high"
    else:
        income_tier = "medium"
    
    # Credit Score (Student/Freelancer bias)
    cs_mean = 720 if segment == "salaried" else 680
    credit_score = int(np.clip(np.random.normal(cs_mean, 80), 300, 900))
    if segment == "student": credit_score = random.randint(600, 740)
    
    # Loan & EMI Logic
    has_loan = random.random() < 0.8
    loan_amt = int(base_income * random.uniform(5, 50)) if has_loan else 0
    emi_amt = min(int(loan_amt / random.uniform(12, 60)), int(base_income * 0.7)) if has_loan else 0
    
    customers.append([cid, name, age, city, occupation, segment, income_tier, base_income, credit_score,
                      loan_amt, emi_amt, random.randint(50000, 500000), # Credit Limit
                      int(base_income * random.uniform(0.5, 10)), # Init Savings
                      random.choice(PRODUCT_TYPES), random.randint(60, 3000)])

customers_df = pd.DataFrame(customers, columns=[
    "customer_id", "name", "age", "city", "occupation", "customer_segment", "income_segment", "monthly_salary",
    "credit_score", "loan_amount", "emi_amount", "credit_limit",
    "savings_balance_initial", "product_type", "account_open_days"
])
customers_df.to_csv(f"{DATA_DIR}/customers.csv", index=False)
print(f"✅ customers.csv: {len(customers_df)} rows generated.")

# ─────────────────────────────────────────────────
# PHASE 2: Generate Transactions (~200k)
# ─────────────────────────────────────────────────

# Special User Tagging
medical_shock_ids = random.sample(customers_df["customer_id"].tolist(), 150) # 3%
cash_only_ids = random.sample(customers_df["customer_id"].tolist(), 300) # 6%

stress_map = {}
for _, c in customers_df.iterrows():
    stress_map[c["customer_id"]] = {
        "is_stressed": random.random() < 0.23,
        "stress_level": random.uniform(0.4, 0.98)
    }

transactions = []
txn_counter = 0
start_date = datetime(2025, 1, 1)

for _, cust in customers_df.iterrows():
    cid = cust["customer_id"]
    seg = cust["customer_segment"]
    income = cust["monthly_salary"]
    emi = cust["emi_amount"]
    is_stressed = stress_map[cid]["is_stressed"]

    for month in range(1, 13):
        m_start = start_date + timedelta(days=(month - 1) * 30)
        
        # 1. INCOME SIGNALS (Winning Edge Cases)
        i_date = m_start + timedelta(days=random.randint(1, 7))
        if seg == "farmer":
            if month in [4, 10]: # Harvest Months
                amt = income * random.uniform(6, 12)
                transactions.append([f"TXN-{txn_counter:07d}", cid, i_date.strftime("%Y-%m-%d"), "CREDIT", "HARVEST_PAYMENT", int(amt), "NEFT", month])
            else:
                if random.random() < 0.25: # Side income
                    transactions.append([f"TXN-{txn_counter:07d}", cid, i_date.strftime("%Y-%m-%d"), "CREDIT", "OFF_SEASON_INCOME", int(income * 0.4), "CASH", month])
        elif seg == "student":
            transactions.append([f"TXN-{txn_counter:07d}", cid, i_date.strftime("%Y-%m-%d"), "CREDIT", "ALLOWANCE", int(income), "UPI", month])
        elif seg == "freelancer":
            for _ in range(random.randint(1, 3)):
                txn_counter += 1
                transactions.append([f"TXN-{txn_counter:07d}", cid, (m_start + timedelta(days=random.randint(1, 28))).strftime("%Y-%m-%d"), "CREDIT", "PROJECT_PAY", int(income * random.uniform(0.3, 0.8)), "IMPS", month])
        else: # Salaried
            s_day = random.randint(1, 5) if not is_stressed else random.randint(5, 18)
            transactions.append([f"TXN-{txn_counter:07d}", cid, (m_start + timedelta(days=s_day)).strftime("%Y-%m-%d"), "CREDIT", "SALARY", int(income), "NEFT", month])

        # 2. ANOMALY SHOCKS (Medical)
        if cid in medical_shock_ids and month == 8:
            txn_counter += 1
            transactions.append([f"TXN-{txn_counter:07d}", cid, (m_start + timedelta(days=14)).strftime("%Y-%m-%d"), "DEBIT", "MEDICAL_EMERGENCY", int(income * random.uniform(2.5, 5.0)), "IMPS", month])

        # 3. SPENDING SPIKES (Festival/Diwali)
        is_diwali = (month == 10)
        mult = 2.5 if is_diwali else 1.0

        # 4. DEBITS
        if emi > 0:
            txn_counter += 1
            is_failed = is_stressed and random.random() < 0.3
            transactions.append([f"TXN-{txn_counter:07d}", cid, (m_start + timedelta(days=5)).strftime("%Y-%m-%d"), "FAILED" if is_failed else "DEBIT", "EMI_PAYMENT", emi, "AUTO_DEBIT", month])

        for _ in range(random.randint(5, 15)):
            txn_counter += 1
            cat = random.choice(["SHOPPING", "DINING", "GROCERTIES", "ATM"])
            amt = int(income * random.uniform(0.01, 0.1) * mult)
            chan = "ATM" if (cid in cash_only_ids or cat == "ATM") else random.choice(["UPI", "POS"])
            transactions.append([f"TXN-{txn_counter:07d}", cid, (m_start + timedelta(days=random.randint(1, 28))).strftime("%Y-%m-%d"), "DEBIT", cat, amt, chan, month])

        if is_stressed:
            txn_counter += 1
            transactions.append([f"TXN-{txn_counter:07d}", cid, (m_start + timedelta(days=22)).strftime("%Y-%m-%d"), "DEBIT", "LENDING_APP_REPAY", int(income * 0.25), "UPI", month])

df_txns = pd.DataFrame(transactions, columns=["txn_id", "customer_id", "date", "txn_type", "category", "amount", "channel", "month"])
df_txns.to_csv(f"{DATA_DIR}/transactions.csv", index=False)
print(f"✅ transactions.csv: {len(df_txns)} rows.")

# ─────────────────────────────────────────────────
# PHASE 3: Generate Weekly Behavioral Features (260k)
# ─────────────────────────────────────────────────

weekly_data = []
for _, cust in customers_df.iterrows():
    cid = cust["customer_id"]
    income = cust["monthly_salary"]
    seg = cust["customer_segment"]
    is_stressed = stress_map[cid]["is_stressed"]
    stress_prog = stress_map[cid]["stress_level"]
    
    prev_util = 0.15
    prev_net = 0
    history_cashflow = []

    for week in range(1, 53):
        t = week / 52
        month = (week - 1) // 4 + 1
        is_harvest = (seg == "farmer" and month in [4, 10])
        is_festival = (month == 10)
        
        # ── Behavioral Degradation Logic ──
        if is_stressed:
            sf = stress_prog * t # Stress Factor
            salary_delay = int(np.clip(np.random.normal(6 + 15 * sf, 3), 0, 30))
            if is_harvest: salary_delay = 0 # Buffer during harvest
            
            util = np.clip(0.3 + 0.6 * sf, 0, 1)
            atms = int(np.clip(np.random.poisson(2 + 4 * sf), 0, 10))
            failed = 1 if (random.random() < 0.35 * sf) else 0
            net = int(income * random.uniform(-0.5, 0.05) * (1 - sf))
            
            # Shock Impact
            if cid in medical_shock_ids and week in [30, 31, 32]: # Impact of Month 8 shock
                net -= income * 4
                util = 0.98
        else:
            salary_delay = random.randint(0, 3)
            util = random.uniform(0.1, 0.3)
            atms = random.randint(0, 2)
            failed = 0
            net = int(income * random.uniform(0.1, 0.35))
            if is_festival: util += 0.3 # One-time spending spike

        # ── Decision Intelligence: Score Simulation ──
        # Formula: Base Risk + Behavioral Delta
        raw_risk = (salary_delay / 30 * 0.3) + (util * 0.3) + (failed * 0.3) + (max(0, -net/income) * 0.1)
        
        # Decision Bias Correction (Forced in Data for ML Training)
        adjusted_risk = raw_risk
        if is_festival: adjusted_risk *= 0.8 # Normalize festival spending
        if cid in medical_shock_ids and week in [30, 31, 32]: adjusted_risk *= 0.65 # Medical shock protection
        if seg == "farmer" and not is_harvest: adjusted_risk += 0.05 # Contextual uncertainty
        
        final_score = np.clip(adjusted_risk + np.random.normal(0, 0.05), 0, 1)
        
        stress_lvl = 0 if final_score < 0.35 else 1 if final_score < 0.7 else 2
        will_default = 1 if (final_score > 0.85 and random.random() < 0.7) else 0
        
        # ── Days to Default Estimation ──
        if final_score > 0.9: dtd = random.randint(5, 12)
        elif final_score > 0.7: dtd = random.randint(13, 28)
        else: dtd = random.randint(60, 365)
        
        weekly_data.append([
            cid, week, 2025, stress_lvl, salary_delay, int(income * 3), # savings
            round(random.uniform(-4, 4), 2), atms, atms * 4000, 15000,
            2 if is_stressed else 0, 12000, failed, 0, 0,
            round(util, 4), net, round(final_score, 4),
            seg, random.randint(0, 5) if is_stressed else 0,
            round(random.uniform(0.2, 0.9), 4),
            round((net - prev_net)/10000.0, 4),
            round(util - prev_util, 4), net - prev_net,
            round(final_score * 1.1, 4),
            1 if (is_stressed and t > 0.83 and random.random() < 0.2) else 0, # recovered
            dtd, will_default
        ])
        prev_util = util
        prev_net = net

cols = ["customer_id", "week_number", "year", "stress_level", "salary_delay_days", "savings_balance", "savings_wow_delta_pct", "atm_withdrawal_count_7d", "atm_withdrawal_amount_7d", "discretionary_spend_7d", "lending_upi_count_7d", "lending_upi_amount_7d", "failed_autodebit_count", "utility_payment_delay_days", "gambling_spend_7d", "credit_utilization", "net_cashflow_7d", "risk_score", "customer_segment", "round_number_withdrawal_count_7d", "weekend_spend_ratio", "net_cashflow_trend_slope", "delta_utilization", "delta_cashflow", "stress_score_interaction", "customer_recovered_after_intervention", "days_to_default", "will_default_next_30d"]
df_weekly = pd.DataFrame(weekly_data, columns=cols)
df_weekly.to_csv(f"{DATA_DIR}/weekly_behavioral_features.csv", index=False)
print(f"✅ weekly_behavioral_features.csv: {len(df_weekly)} rows.")

# ─────────────────────────────────────────────────
# PHASE 4: Intervention Log
# ─────────────────────────────────────────────────
logs = []
for _, row in df_weekly[(df_weekly["week_number"] == 52) & (df_weekly["risk_score"] > 0.45)].iterrows():
    logs.append([row["customer_id"], 52, row["risk_score"], "RM_CALL" if row["risk_score"] > 0.7 else "SMS_LINK", "CALL", "SENT", "PENDING", "salary_delay_days"])

pd.DataFrame(logs, columns=["customer_id", "week_number", "risk_score_at_trigger", "intervention_type", "channel", "status", "outcome", "top_signal"]).to_csv(f"{DATA_DIR}/intervention_log.csv", index=False)
print(f"✅ intervention_log.csv: {len(logs)} rows.")
print("\n🎉 BANK-GRADE DATASET READY FOR TRAINING.")
