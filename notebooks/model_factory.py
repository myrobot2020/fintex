"""
Model Factory for Gold Price Forecasting
Trains 5 different models and logs their metrics to Vertex AI Experiments.
1. Prophet (Meta)
2. XGBoost (Regression)
3. Random Forest (Ensemble)
4. Ridge Regression (Linear)
5. Simple Moving Average (Baseline)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from google.cloud import aiplatform, bigquery
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from xgboost import XGBRegressor
from prophet import Prophet
import os

# CONFIG
PROJECT_ID = "finance-502004"
REGION = "us-central1"
EXPERIMENT_NAME = "gold-forecast-experiment"

aiplatform.init(project=PROJECT_ID, location=REGION, experiment=EXPERIMENT_NAME)
bq_client = bigquery.Client(project=PROJECT_ID)

def load_data():
    sql = f"SELECT date, price FROM `{PROJECT_ID}.finance.gold_price_forecast` ORDER BY date"
    df = bq_client.query(sql).to_dataframe()
    df['date'] = pd.to_datetime(df['date'])
    return df

def prepare_features(df, lags=7):
    # For ML models, we need lags as features
    for i in range(1, lags + 1):
        df[f'lag_{i}'] = df['price'].shift(i)
    df = df.dropna()

    # Split: Last 30 days for holdout
    train = df[df['date'] < df['date'].max() - timedelta(days=30)]
    test = df[df['date'] >= df['date'].max() - timedelta(days=30)]

    feature_cols = [f'lag_{i}' for i in range(1, lags + 1)]
    return train, test, feature_cols

def log_to_vertex(model_name, metrics, params):
    run_id = f"{model_name}-{datetime.now().strftime('%H%M%S')}"
    with aiplatform.start_run(run_id):
        aiplatform.log_params(params)
        aiplatform.log_metrics(metrics)
    print(f"✅ Logged {model_name} to Experiment")

# --- MODEL 1: PROPHET ---
def run_prophet(df):
    print("🏃 Running Prophet...")
    train = df[df['date'] < df['date'].max() - timedelta(days=30)].copy()
    test = df[df['date'] >= df['date'].max() - timedelta(days=30)].copy()

    m = Prophet(daily_seasonality=True)
    m.fit(train.rename(columns={'date': 'ds', 'price': 'y'}))

    # Predict for the test dates
    future = pd.DataFrame({'ds': test['date']})
    forecast = m.predict(future)

    mae = mean_absolute_error(test['price'], forecast['yhat'])
    log_to_vertex("prophet", {"mae": float(mae)}, {"type": "time-series", "library": "meta-prophet"})

# --- MODEL 2: XGBOOST ---
def run_xgboost(train, test, features):
    print("🏃 Running XGBoost...")
    model = XGBRegressor(n_estimators=100, learning_rate=0.05)
    model.fit(train[features], train['price'])
    pred = model.predict(test[features])
    mae = mean_absolute_error(test['price'], pred)
    log_to_vertex("xgboost", {"mae": float(mae)}, {"n_estimators": 100, "library": "xgboost"})

# --- MODEL 3: RANDOM FOREST ---
def run_rf(train, test, features):
    print("🏃 Running Random Forest...")
    model = RandomForestRegressor(n_estimators=100)
    model.fit(train[features], train['price'])
    pred = model.predict(test[features])
    mae = mean_absolute_error(test['price'], pred)
    log_to_vertex("random-forest", {"mae": float(mae)}, {"n_estimators": 100, "library": "sklearn-rf"})

# --- MODEL 4: RIDGE REGRESSION ---
def run_ridge(train, test, features):
    print("🏃 Running Ridge...")
    model = Ridge(alpha=1.0)
    model.fit(train[features], train['price'])
    pred = model.predict(test[features])
    mae = mean_absolute_error(test['price'], pred)
    log_to_vertex("ridge-regression", {"mae": float(mae)}, {"alpha": 1.0, "library": "sklearn-ridge"})

# --- MODEL 5: MOVING AVERAGE (7d) ---
def run_sma(df):
    print("🏃 Running Moving Average...")
    test = df[df['date'] >= df['date'].max() - timedelta(days=30)].copy()
    # Simple logic: forecast is just the average of the last 7 days from the training end
    last_price = df[df['date'] < df['date'].max() - timedelta(days=30)]['price'].iloc[-1]
    pred = [last_price] * len(test)
    mae = mean_absolute_error(test['price'], pred)
    log_to_vertex("moving-average", {"mae": float(mae)}, {"window": 7, "type": "baseline"})

if __name__ == "__main__":
    data = load_data()
    train, test, features = prepare_features(data.copy())

    run_prophet(data)
    run_xgboost(train, test, features)
    run_rf(train, test, features)
    run_ridge(train, test, features)
    run_sma(data)

    print("\n🏁 All 5 models trained and logged to gold-forecast-experiment!")
