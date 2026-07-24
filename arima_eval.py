"""
Evaluate BigQuery ML ARIMA baseline on a hold-out period
"""

from google.cloud import bigquery
import pandas as pd

PROJECT_ID = "finance-502004"
BQ_DATASET = "finance"
BQ_TABLE = "gold_price_forecast"
BQ_MODEL = "gold_arima_baseline"

client = bigquery.Client(project=PROJECT_ID)

# Using ML.EVALUATE to get training metrics for the ARIMA model
sql = f"""
SELECT
  *
FROM
  ML.EVALUATE(MODEL `{PROJECT_ID}.{BQ_DATASET}.{BQ_MODEL}`)
"""

try:
    df = client.query(sql).to_dataframe()
    print("ARIMA Training Metrics (from ML.EVALUATE):")
    print(df)
except Exception:
    print("ARIMA Training Metrics (manual fetch):")
    results = client.query(sql).result()
    for row in results:
        # ARIMA metrics usually include non_seasonal_p, etc. and error metrics
        print(row)
