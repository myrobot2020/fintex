"""
Live Gold Price Ingestion
Fetches latest prices and updates BigQuery + GCS
"""

import yfinance as yf
import pandas as pd
from google.cloud import bigquery, storage
from datetime import datetime, timedelta
import os

# ======================
# CONFIG
# ======================
PROJECT_ID = "finance-502004"
REGION = "us-central1"
BUCKET_NAME = "cloud-ai-platform-5198f7b8-0786-40a1-802e-78049446b994"

BQ_DATASET = "finance"
BQ_TABLE = "gold_price_forecast"
GCS_PATH = "data/gold_price_forecast.csv"

# How many days back to refresh (safe overlap)
LOOKBACK_DAYS = 30

# ======================
# Clients
# ======================
bq_client = bigquery.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)

print("✅ Clients ready")

# ======================
# 1. Fetch live gold prices
# ======================
def fetch_gold_prices(days: int = LOOKBACK_DAYS) -> pd.DataFrame:
    print(f"📡 Fetching last {days} days of gold prices...")

    ticker = yf.Ticker("GC=F")  # Gold Futures
    df = ticker.history(period=f"{days}d", interval="1d")

    if df.empty:
        raise RuntimeError("No data returned from yfinance")

    df = df.reset_index()
    df["date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.date
    df["series_id"] = "GOLD"
    df["price"] = df["Close"].astype(float)

    result = df[["date", "series_id", "price"]].dropna()
    result = result.sort_values("date").drop_duplicates(subset=["date"])

    print(f"✅ Got {len(result)} rows")
    print(result.tail(5))
    return result

# ======================
# 2. Update BigQuery (merge / append latest)
# ======================
def update_bigquery(df: pd.DataFrame):
    table_id = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"

    # Ensure dataset exists
    dataset = bigquery.Dataset(f"{PROJECT_ID}.{BQ_DATASET}")
    dataset.location = REGION
    bq_client.create_dataset(dataset, exists_ok=True)

    # Convert date to string for load
    df_load = df.copy()
    df_load["date"] = df_load["date"].astype(str)

    job = bq_client.load_table_from_dataframe(
        df_load,
        table_id,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",  # full replace for simplicity
            schema=[
                bigquery.SchemaField("date", "DATE"),
                bigquery.SchemaField("series_id", "STRING"),
                bigquery.SchemaField("price", "FLOAT"),
            ],
        ),
    )
    job.result()
    print(f"✅ BigQuery table updated: {table_id}")

# ======================
# 3. Update GCS CSV
# ======================
def update_gcs(df: pd.DataFrame):
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(GCS_PATH)

    csv_data = df.to_csv(index=False)
    blob.upload_from_string(csv_data, content_type="text/csv")
    print(f"✅ GCS updated: gs://{BUCKET_NAME}/{GCS_PATH}")

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    print("\n🚀 Live Gold Price Ingestion\n")

    df = fetch_gold_prices(days=LOOKBACK_DAYS)

    # Optional: if you want full history, change period to "max" once
    # and then switch to daily incremental later.

    update_bigquery(df)
    update_gcs(df)

    print("\n✅ Live prices loaded into BigQuery + GCS")
    print("Next: retrain model or run batch prediction on fresh data")
