"""
Log ARIMA + AutoML metrics into Vertex Experiments for comparison.
Project: finance-502004
"""

from google.cloud import aiplatform, bigquery
from datetime import datetime

PROJECT_ID = "finance-502004"
REGION = "us-central1"
EXPERIMENT = "gold-forecast-experiment"

# Paste AutoML eval metrics from console if needed
AUTOML_METRICS = {
    "r_squared": 0.58,
    # fill if you have them:
    # "mae": None,
    # "rmse": None,
    # "mape": None,
}

aiplatform.init(
    project=PROJECT_ID,
    location=REGION,
    experiment=EXPERIMENT,
)
bq = bigquery.Client(project=PROJECT_ID)

def arima_holdout_metrics(days=14):
    # Reduced to 14 to match the trained horizon of the ARIMA model
    sql = f"""
    WITH actuals AS (
      SELECT date, price AS actual
      FROM `{PROJECT_ID}.finance.gold_price_forecast`
      WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    ),
    forecasts AS (
      SELECT
        DATE(forecast_timestamp) AS date,
        forecast_value AS predicted
      FROM ML.FORECAST(
        MODEL `{PROJECT_ID}.finance.gold_arima_baseline`,
        STRUCT({days} AS horizon, 0.95 AS confidence_level)
      )
    )
    SELECT
      AVG(ABS(actual - predicted)) AS mae,
      SQRT(AVG(POW(actual - predicted, 2))) AS rmse,
      AVG(ABS(actual - predicted) / NULLIF(actual, 0)) * 100 AS mape
    FROM actuals a
    JOIN forecasts f USING (date)
    """
    try:
        row = list(bq.query(sql).result())[0]
        return {
            "mae": float(row["mae"]) if row["mae"] is not None else None,
            "rmse": float(row["rmse"]) if row["rmse"] is not None else None,
            "mape": float(row["mape"]) if row["mape"] is not None else None,
        }
    except Exception as e:
        print(f"Warning: Could not compute holdout metrics: {e}")
        return {}

def log_run(model_type: str, metrics: dict, params: dict):
    run_name = f"{model_type}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    # drop Nones so Vertex doesn't choke
    clean_metrics = {k: v for k, v in metrics.items() if v is not None}
    with aiplatform.start_run(run_name):
        aiplatform.log_params(params)
        if clean_metrics:
            aiplatform.log_metrics(clean_metrics)
    print(f"Logged run: {run_name}")
    print(" metrics:", clean_metrics)

if __name__ == "__main__":
    print("Computing ARIMA holdout metrics...")
    arima_metrics = arima_holdout_metrics(14)
    log_run(
        model_type="arima",
        metrics=arima_metrics,
        params={
            "model_type": "arima",
            "model": "finance.gold_arima_baseline",
            "horizon_days": 14,
            "path": "online",
        },
    )

    print("Logging AutoML metrics from console eval...")
    log_run(
        model_type="automl",
        metrics=AUTOML_METRICS,
        params={
            "model_type": "automl",
            "model_id": "7996651861547417600",
            "path": "batch",
            "r_squared_source": "vertex_evaluation",
        },
    )

    print("Done. Open Experiments → gold-forecast-experiment")
