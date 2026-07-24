"""
Full Pre-Training / Waiting SDK
Gold Price Forecasting - Vertex AI
Includes:
- BigQuery data load
- BigQuery ML ARIMA_PLUS baseline
- Feature Store + features
- Experiment logging
"""

from google.cloud import aiplatform, bigquery, storage
from datetime import datetime
import os

# ======================
# CONFIG
# ======================
PROJECT_ID = "finance-502004"
REGION = "us-central1"
BUCKET_NAME = "cloud-ai-platform-5198f7b8-0786-40a1-802e-78049446b994"
STAGING_BUCKET = f"gs://{BUCKET_NAME}"

# Using absolute path or relative to script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_CSV = os.path.join(SCRIPT_DIR, "gold_price_forecast.csv")

BQ_DATASET = "finance"
BQ_TABLE = "gold_price_forecast"
BQ_MODEL = "gold_arima_baseline"

FEATURESTORE_ID = "gold_featurestore"
ENTITY_TYPE_ID = "gold"
EXPERIMENT_NAME = "gold-forecast-experiments"

# ======================
# Clients
# ======================
aiplatform.init(
    project=PROJECT_ID,
    location=REGION,
    staging_bucket=STAGING_BUCKET,
    experiment=EXPERIMENT_NAME,
)
bq_client = bigquery.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)

print("✅ Clients initialized")

# ======================
# 1. BigQuery Dataset + Load Data
# ======================
def setup_bigquery_data():
    dataset_id = f"{PROJECT_ID}.{BQ_DATASET}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = REGION
    bq_client.create_dataset(dataset, exists_ok=True)
    print(f"✅ BigQuery dataset ready: {BQ_DATASET}")

    # Upload CSV to GCS
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob("data/gold_price_forecast.csv")
    blob.upload_from_filename(LOCAL_CSV)
    gcs_uri = f"gs://{BUCKET_NAME}/data/gold_price_forecast.csv"
    print(f"✅ CSV uploaded to {gcs_uri}")

    # Load into BigQuery
    table_id = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition="WRITE_TRUNCATE",
    )
    load_job = bq_client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    load_job.result()
    print(f"✅ Data loaded into {table_id}")
    return table_id

# ======================
# 2. BigQuery ML ARIMA_PLUS Baseline
# ======================
def create_arima_baseline():
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
    SELECT date, series_id, price
    FROM `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}`
    """

    print("🚀 Training BigQuery ML ARIMA_PLUS baseline...")
    job = bq_client.query(sql)
    job.result()
    print(f"✅ ARIMA baseline created: {model_id}")
    return model_id

def run_arima_forecast(model_id):
    sql = f"""
    SELECT forecast_timestamp, forecast_value
    FROM ML.FORECAST(MODEL `{model_id}`,
                     STRUCT(14 AS horizon, 0.95 AS confidence_level))
    ORDER BY forecast_timestamp
    LIMIT 20
    """
    try:
        df = bq_client.query(sql).to_dataframe()
        print("\nARIMA 14-day forecast (sample):")
        print(df.head(10))
        return df
    except Exception:
        print("\nARIMA 14-day forecast (sample - manual print):")
        results = bq_client.query(sql).result()
        for i, row in enumerate(results):
            if i >= 10: break
            print(f"{row.forecast_timestamp}: {row.forecast_value}")

# ======================
# 3. Feature Store
# ======================
def setup_featurestore():
    try:
        fs = aiplatform.Featurestore(FEATURESTORE_ID)
        print(f"✅ Featurestore already exists: {FEATURESTORE_ID}")
        return fs
    except Exception:
        print(f"🚀 Creating Featurestore: {FEATURESTORE_ID}")
        fs = aiplatform.Featurestore.create(
            featurestore_id=FEATURESTORE_ID,
            online_store_fixed_node_count=1,
        )
        print(f"✅ Featurestore created")
        return fs

def setup_entity_features(fs):
    try:
        entity_type = fs.get_entity_type(ENTITY_TYPE_ID)
        print(f"✅ Entity type exists: {ENTITY_TYPE_ID}")
        return entity_type
    except Exception:
        print(f"🚀 Creating entity type: {ENTITY_TYPE_ID}")
        entity_type = fs.create_entity_type(
            entity_type_id=ENTITY_TYPE_ID,
            description="Gold price entity",
        )

    print("🚀 Creating features...")
    entity_type.batch_create_features(
        feature_configs={
            "price": {"value_type": "DOUBLE", "description": "Gold closing price"},
            "lag_1": {"value_type": "DOUBLE", "description": "1-day lag"},
            "lag_7": {"value_type": "DOUBLE", "description": "7-day lag"},
            "rolling_mean_7": {"value_type": "DOUBLE", "description": "7-day rolling mean"},
            "rolling_mean_30": {"value_type": "DOUBLE", "description": "30-day rolling mean"},
        }
    )
    print("✅ Features created")
    return entity_type

# ======================
# 4. Experiment logging
# ======================
def log_to_experiment(arima_model_id):
    run_name = f"pretrain-setup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    with aiplatform.start_run(run_name):
        aiplatform.log_params({
            "stage": "pre-training",
            "arima_model": arima_model_id,
            "featurestore": FEATURESTORE_ID,
            "entity_type": ENTITY_TYPE_ID,
            "dataset": f"{BQ_DATASET}.{BQ_TABLE}",
        })
        aiplatform.log_metrics({
            "arima_ready": 1.0,
            "featurestore_ready": 1.0,
            "num_features": 5.0,
        })

    print(f"✅ Logged to Experiment: {run_name}")

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    print("\n🚀 Full Pre-Training SDK starting...\n")

    # 1. Data
    setup_bigquery_data()

    # 2. ARIMA baseline
    arima_model_id = create_arima_baseline()
    run_arima_forecast(arima_model_id)

    # 3. Feature Store
    fs = setup_featurestore()
    setup_entity_features(fs)

    # 4. Experiment
    log_to_experiment(arima_model_id)

    print("\n✅ All pre-training steps complete!")
    print(f"ARIMA model   : {arima_model_id}")
    print(f"Featurestore  : {FEATURESTORE_ID}")
    print(f"Experiment    : {EXPERIMENT_NAME}")
    print("\nYou can now wait for the AutoML Forecasting model to finish.")
