"""
Local Explainable AI (XAI)
Calculates feature importance for our local tick-level models.
Logs the results to Vertex AI Experiments.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from xgboost import XGBRegressor
from google.cloud import aiplatform
from datetime import datetime

# CONFIG
PROJECT_ID = "finance-502004"
FEATURE_FILE = "C:/Users/ADMIN/Desktop/cl/finance/gold_final_features.csv"
EXPERIMENT_NAME = "gold-forecast-experiment"

def run_local_xai():
    # 1. Load data
    df = pd.read_csv(FEATURE_FILE, index_col='timestamp', parse_dates=True)
    features = [c for c in df.columns if 'lag_' in c or 'rolling_' in c or c == 'returns']
    X, y = df[features], df['target']

    # 2. Train XGBoost Model
    print("🏃 Training XGBoost for XAI analysis...")
    model = XGBRegressor(n_estimators=100)
    model.fit(X, y)

    # 3. Extract Feature Importance (The 'XAI' part)
    # This is built-in importance based on weight/gain
    importances = model.feature_importances_
    feature_importance_df = pd.DataFrame({
        'feature': features,
        'importance': importances
    }).sort_values(by='importance', ascending=False)

    print("\n📊 --- LOCAL XAI: FEATURE IMPORTANCE ---")
    print(feature_importance_df)

    # 4. Log to Vertex AI Experiments
    aiplatform.init(project=PROJECT_ID, location="us-central1", experiment=EXPERIMENT_NAME)
    run_name = f"local-xai-{datetime.now().strftime('%H%M%S')}"

    with aiplatform.start_run(run_name):
        # Log the importance of the top 3 features as metrics
        top_3 = feature_importance_df.head(3)
        metrics = {}
        for _, row in top_3.iterrows():
            metrics[f"importance_{row['feature']}"] = float(row['importance'])

        aiplatform.log_metrics(metrics)
        aiplatform.log_params({"model_type": "xgboost", "xai_method": "native-feature-importance"})

    print(f"\n✅ Top feature importance logged to Vertex: {run_name}")

    # Interpretation for the user
    top_f = feature_importance_df.iloc[0]['feature']
    print(f"💡 INSIGHT: Your model relies most on '{top_f}'.")
    if 'lag_1' in top_f:
        print("   This means the model is behaving like a 'Momentum' strategy.")

if __name__ == "__main__":
    run_local_xai()
