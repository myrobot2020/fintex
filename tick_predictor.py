"""
Level 3 Architecture: The Next-Tick Scalper
Trains locally on 1-minute data to predict the EXACT next price.
Uses an Online Learning pattern with XGBoost.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error
from google.cloud import aiplatform
from datetime import datetime

# CONFIG
PROJECT_ID = "finance-502004"
aiplatform.init(project=PROJECT_ID, location="us-central1", experiment="gold-forecast-experiment")

def train_next_tick_model():
    print("📡 Fetching 1-minute historical ticks...")
    # yfinance provides 1m data for the last 7 days
    df = yf.download("GC=F", period="7d", interval="1m")
    df = df.reset_index()

    # Standardize column names (handle multi-index if present)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[['Datetime', 'Close']].rename(columns={'Datetime': 'time', 'Close': 'price'})

    print(f"✅ Data loaded: {len(df)} ticks.")

    # 1. Feature Engineering for "The Next Second"
    # We use a sliding window of the last 10 minutes to predict the 11th minute
    WINDOW_SIZE = 10
    for i in range(1, WINDOW_SIZE + 1):
        df[f'tick_lag_{i}'] = df['price'].shift(i)

    # Add micro-volatility (rolling std dev of last 5 ticks)
    df['micro_vol'] = df['price'].rolling(5).std()

    df = df.dropna()

    # 2. Train/Test Split (Last 2 hours for validation)
    train = df.iloc[:-120]
    test = df.iloc[-120:]

    features = [f'tick_lag_{i}' for i in range(1, WINDOW_SIZE + 1)] + ['micro_vol']
    X_train, y_train = train[features], train['price']
    X_test, y_test = test[features], test['price']

    # 3. Train the "Scalper" (XGBoost tuned for low-latency)
    print("🧠 Training Next-Tick Scalper...")
    model = XGBRegressor(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=5,
        n_jobs=-1 # Use all local cores
    )
    model.fit(X_train, y_train)

    # 4. Evaluate
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)

    print(f"📊 Next-Tick MAE: {mae:.4f} USD")
    print(f"🎯 Current Price: {y_test.iloc[-1]:.2f} | Predicted Next: {preds[-1]:.2f}")

    # 5. Log to Vertex AI Experiment (Level 3 Run)
    run_name = f"tick-scalper-{datetime.now().strftime('%H%M%S')}"
    with aiplatform.start_run(run_name):
        aiplatform.log_params({
            "model": "xgboost-fast",
            "horizon": "1-minute-tick",
            "window_size": WINDOW_SIZE,
            "features": "lags + micro-vol"
        })
        aiplatform.log_metrics({"mae": float(mae)})

    print(f"✅ Level 3 Metrics logged to Vertex: {run_name}")
    return model

if __name__ == "__main__":
    train_next_tick_model()
