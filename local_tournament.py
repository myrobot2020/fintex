"""
Local Tournament Engine
Trains multiple models locally and compares them.
Integrates with Vertex AI Experiments for tracking.
"""
import pandas as pd
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from google.cloud import aiplatform
from datetime import datetime
import os

# CONFIG
PROJECT_ID = "finance-502004"
EXPERIMENT_NAME = "gold-forecast-experiment"
FEATURE_FILE = "C:/Users/ADMIN/Desktop/cl/finance/gold_final_features.csv"

def run_tournament():
    # 1. Load data
    df = pd.read_csv(FEATURE_FILE, index_col='timestamp', parse_dates=True)

    # 2. Split
    train_size = int(len(df) * 0.8)
    train, test = df.iloc[:train_size], df.iloc[train_size:]

    features = [c for c in df.columns if 'lag_' in c or 'rolling_' in c or c == 'returns']
    X_train, y_train = train[features], train['target']
    X_test, y_test = test[features], test['target']

    # 3. Models to test
    models = {
        "XGBoost_Local": XGBRegressor(n_estimators=100, learning_rate=0.05),
        "RF_Local": RandomForestRegressor(n_estimators=100),
        "Ridge_Local": Ridge(alpha=1.0)
    }

    # 4. INIT Vertex (for logging only)
    aiplatform.init(project=PROJECT_ID, location="us-central1", experiment=EXPERIMENT_NAME)

    print(f"🏁 Starting Tournament on {len(X_train)} training rows...")

    leaderboard = []

    for name, model in models.items():
        print(f"🏃 Training {name}...")
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)

        # Log to Vertex - Removing invalid characters from ID
        safe_name = name.lower().replace("_", "-")
        with aiplatform.start_run(f"local-{safe_name}-{datetime.now().strftime('%H%M%S')}"):
            aiplatform.log_params({"model_class": name, "n_features": len(features)})
            aiplatform.log_metrics({"mae": float(mae)})

        leaderboard.append({"Model": name, "MAE": mae})
        print(f"✅ {name} MAE: {mae:.4f}")

    # 5. Summary
    lb_df = pd.DataFrame(leaderboard).sort_values("MAE")
    print("\n🏆 LOCAL TOURNAMENT LEADERBOARD:")
    print(lb_df)

    winner_name = lb_df.iloc[0]["Model"]
    print(f"\n🥇 RECOMMENDED FOR INFERENCE: {winner_name}")

    # 6. Save Winner Model
    import pickle
    winner_model = models[winner_name]
    with open("C:/Users/ADMIN/Desktop/cl/finance/local_winner.pkl", "wb") as f:
        pickle.dump(winner_model, f)

    return winner_name

if __name__ == "__main__":
    run_tournament()
