"""
Incremental gold price ingestion with MERGE (no full overwrite)
"""

import yfinance as yf
import pandas as pd
from google.cloud import bigquery, storage
from datetime import date
import os

PROJECT_ID = "finance-502004"
REGION = "us-central1"
BUCKET_NAME = "cloud-ai-platform-5198f7b8-0786-40a1-802e-78049446b994"
BQ_DATASET = "finance"
BQ_TABLE = "gold_price_forecast"

bq = bigquery.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)

def fetch_recent(days=15):
    t = yf.Ticker("GC=F")
    df = t.history(period=f"{days}d")
    df = df.reset_index()
    df["date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.date
    df["series_id"] = "GOLD"
    df["price"] = df["Close"].astype(float)
    return df[["date", "series_id", "price"]].dropna().drop_duplicates("date")

def merge_into_bigquery(df):
    # Load to temp table
    temp_table = f"{PROJECT_ID}.{BQ_DATASET}.gold_temp"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        schema=[
            bigquery.SchemaField("date", "DATE"),
            bigquery.SchemaField("series_id", "STRING"),
            bigquery.SchemaField("price", "FLOAT"),
        ],
    )
    df_load = df.copy()
    df_load["date"] = df_load["date"].astype(str)
    bq.load_table_from_dataframe(df_load, temp_table, job_config=job_config).result()

    # MERGE
    merge_sql = f"""
    MERGE `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}` T
    USING `{temp_table}` S
    ON T.date = S.date AND T.series_id = S.series_id
    WHEN MATCHED THEN
      UPDATE SET price = S.price
    WHEN NOT MATCHED THEN
      INSERT (date, series_id, price) VALUES (S.date, S.series_id, S.price)
    """
    bq.query(merge_sql).result()
    print("✅ BigQuery MERGE completed")

def update_gcs(df):
    # For GCS we still write the full recent window (simple)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob("data/gold_price_forecast.csv")
    blob.upload_from_string(df.to_csv(index=False), content_type="text/csv")
    print("✅ GCS updated")

if __name__ == "__main__":
    df = fetch_recent(20)
    print(df.tail())
    merge_into_bigquery(df)
    update_gcs(df)
