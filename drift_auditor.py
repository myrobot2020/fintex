"""
Zero-Cost Data Drift Auditor
Compares Training Data (Baseline) vs. Live Data (Serving) using KS-Test.
Logs drift scores to Vertex AI Experiments for $0.
"""
import pandas as pd
import numpy as np
from scipy.stats import ks_2samp
from google.cloud import bigquery, aiplatform
from datetime import datetime

# CONFIG
PROJECT_ID = "finance-502004"
DATASET = "finance"
TABLE = "gold_price_forecast"
EXPERIMENT = "gold-forecast-experiment"

def run_drift_audit():
    print("📡 Fetching data for drift analysis...")
    client = bigquery.Client(project=PROJECT_ID)

    # 1. Fetch Training Baseline (Data older than 30 days)
    sql_baseline = f"SELECT price FROM `{PROJECT_ID}.{DATASET}.{TABLE}` WHERE date < DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)"
    baseline_df = client.query(sql_baseline).to_dataframe()

    # 2. Fetch Live Serving Data (Last 7 days)
    sql_serving = f"SELECT price FROM `{PROJECT_ID}.{DATASET}.{TABLE}` WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)"
    serving_df = client.query(sql_serving).to_dataframe()

    if len(serving_df) == 0:
        print("❌ No live data found in BigQuery for the last 7 days.")
        return

    # 3. Perform Kolmogorov-Smirnov Test for Data Drift
    # Null Hypothesis: Data comes from the same distribution
    # If p-value < 0.05, we have significant drift.
    statistic, p_value = ks_2samp(baseline_df['price'], serving_df['price'])

    drift_detected = p_value < 0.05
    drift_score = 1 - p_value # Simple proxy: higher means more drift

    print("\n--- 🕵️ DRIFT AUDIT REPORT ---")
    print(f"Baseline Samples: {len(baseline_df)}")
    print(f"Live Samples:     {len(serving_df)}")
    print(f"Drift Statistic:  {statistic:.4f}")
    print(f"P-Value:          {p_value:.4f}")
    print(f"Status:           {'⚠️ DRIFT DETECTED' if drift_detected else '✅ STABLE'}")

    # 4. Log to Vertex AI Experiments (Free)
    aiplatform.init(project=PROJECT_ID, location="us-central1", experiment=EXPERIMENT)
    with aiplatform.start_run(f"drift-audit-{datetime.now().strftime('%H%M%S')}"):
        aiplatform.log_metrics({
            "drift_p_value": float(p_value),
            "drift_statistic": float(statistic),
            "is_drifted": 1.0 if drift_detected else 0.0
        })
        aiplatform.log_params({"audit_type": "statistical-ks-test"})

    print("📊 Drift metrics logged to Vertex Experiments for $0.")

if __name__ == "__main__":
    run_drift_audit()
