"""
BigQuery ML ARIMA_PLUS Baseline for Gold Price Forecasting
Can run while AutoML training is still going.
"""

from google.cloud import bigquery
from google.cloud import storage
import pandas as pd
from datetime import datetime
import os

# ======================
# CONFIG
# ======================
PROJECT_ID = "finance-502004"
REGION = "us-central1"
BUCKET_NAME = "cloud-ai-platform-5198f7b8-0786-40a1-802e-78049446b994"
# Using absolute path or relative to script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_CSV = os.path.join(SCRIPT_DIR, "gold_price_forecast.csv")

BQ_DATASET = "finance"
BQ_TABLE = "gold_price_forecast"
BQ_MODEL = "gold_arima_baseline"

# ======================
# 1. Create BigQuery client
# ======================
bq_client = bigquery.Client(project=PROJECT_ID)

print("✅ BigQuery client ready")

# ======================
# 2. Create dataset if needed
# ======================
def create_dataset():
    dataset_id = f"{PROJECT_ID}.{BQ_DATASET}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = REGION

    try:
        bq_client.create_dataset(dataset, exists_ok=True)
        print(f"✅ Dataset ready: {BQ_DATASET}")
    except Exception as e:
        print(f"Dataset note: {e}")

# ======================
# 3. Load CSV into BigQuery
# ======================
def load_csv_to_bq():
    table_id = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition="WRITE_TRUNCATE",
    )

    # First upload CSV to GCS (safer)
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob("data/gold_price_forecast.csv")
    blob.upload_from_filename(LOCAL_CSV)
    gcs_uri = f"gs://{BUCKET_NAME}/data/gold_price_forecast.csv"

    load_job = bq_client.load_table_from_uri(
        gcs_uri,
        table_id,
        job_config=job_config,
    )
    load_job.result()
    print(f"✅ Data loaded into {table_id}")

# ======================
# 4. Create ARIMA_PLUS model
# ======================
def create_arima_model():
    model_id = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_MODEL}"

    sql = f"""
    CREATE OR REPLACE MODEL `{model_id}`
    OPTIONS(
      MODEL_TYPE = 'ARIMA_PLUS',
      TIME_SERIES_TIMESTAMP_COL = 'date',
      TIME_SERIES_DATA_COL = 'price',
      TIME_SERIES_ID_COL = 'series_id',
      HORIZON = 14,
      AUTO_ARIMA = TRUE,
      DATA_FREQUENCY = 'DAILY'
    ) AS
    SELECT
      date,
      series_id,
      price
    FROM
      `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}`
    """

    print("🚀 Training BigQuery ML ARIMA_PLUS model...")
    job = bq_client.query(sql)
    job.result()
    print(f"✅ ARIMA_PLUS model created: {model_id}")
    return model_id

# ======================
# 5. Generate forecast
# ======================
def generate_forecast(model_id):
    sql = f"""
    SELECT
      forecast_timestamp, forecast_value, standard_error, confidence_level, prediction_interval_lower_bound, prediction_interval_upper_bound
    FROM
      ML.FORECAST(MODEL `{model_id}`,
                  STRUCT(14 AS horizon, 0.95 AS confidence_level))
    ORDER BY
      forecast_timestamp
    """

    print("🔮 Generating 14-day forecast...")
    try:
        df = bq_client.query(sql).to_dataframe()
        print("\nForecast (first 10 rows):")
        print(df.head(10))
        return df
    except Exception as e:
        print(f"Note: Could not use pandas to_dataframe (probably missing db-dtypes). Printing results manually.")
        results = bq_client.query(sql).result()
        print(f"{'Timestamp':<25} | {'Value':<15}")
        print("-" * 45)
        for i, row in enumerate(results):
            if i >= 10: break
            print(f"{str(row.forecast_timestamp):<25} | {row.forecast_value:<15.4f}")
        return results

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    print("\n🚀 BigQuery ML ARIMA Baseline starting...\n")

    create_dataset()
    load_csv_to_bq()
    model_id = create_arima_model()
    forecast_df = generate_forecast(model_id)

    print("\n✅ Baseline ready!")
    print(f"Model : {model_id}")
    print("You can later compare this against your AutoML Forecasting model in Experiments.")
