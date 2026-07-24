"""
Gold Price Forecasting - Vertex AI (Agent Platform) Full SDK Script
Project: finance-502004
Region: us-central1
"""

from google.cloud import aiplatform
from google.cloud import storage
from google.cloud.aiplatform import gapic
import os
from datetime import datetime

# ======================
# CONFIG
# ======================
PROJECT_ID = "finance-502004"
REGION = "us-central1"
BUCKET_NAME = "cloud-ai-platform-5198f7b8-0786-40a1-802e-78049446b994"
STAGING_BUCKET = f"gs://{BUCKET_NAME}"
LOCAL_CSV = "gold_price_forecast.csv"
GCS_CSV_URI = f"gs://{BUCKET_NAME}/data/gold_price_forecast.csv"

# ======================
# 1. Initialize
# ======================
aiplatform.init(
    project=PROJECT_ID,
    location=REGION,
    staging_bucket=STAGING_BUCKET,
)

print("✅ Vertex AI initialized")

# ======================
# 2. Upload CSV to GCS
# ======================
def upload_csv():
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob("data/gold_price_forecast.csv")
    blob.upload_from_filename(LOCAL_CSV)
    print(f"✅ Uploaded → {GCS_CSV_URI}")

# ======================
# 3. Create TimeSeries Dataset
# ======================
def create_dataset():
    dataset = aiplatform.TimeSeriesDataset.create(
        display_name="gold-price-forecast-dataset",
        gcs_source=[GCS_CSV_URI],
    )
    print(f"✅ Dataset created: {dataset.resource_name}")
    return dataset

# ======================
# 4. Feature Store (simple)
# ======================
def create_featurestore():
    featurestore = aiplatform.Featurestore.create(
        featurestore_id="gold_featurestore",
        online_store_fixed_node_count=1,
    )
    print(f"✅ Featurestore created: {featurestore.resource_name}")

    # Create entity type
    entity_type = featurestore.create_entity_type(
        entity_type_id="gold",
        description="Gold price entity",
    )

    # Create features
    entity_type.batch_create_features(
        feature_configs={
            "price": {"value_type": "DOUBLE", "description": "Gold closing price"},
            "lag_1": {"value_type": "DOUBLE", "description": "1-day lag"},
            "rolling_mean_7": {"value_type": "DOUBLE", "description": "7-day rolling mean"},
        }
    )
    print("✅ Features created in Feature Store")
    return featurestore

# ======================
# 5. Train AutoML Forecasting Model + Experiment
# ======================
def train_model(dataset):
    # Start Experiment
    aiplatform.init(experiment="gold-forecast-experiment")
    aiplatform.start_run(f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}")

    job = aiplatform.AutoMLForecastingTrainingJob(
        display_name="gold-forecast-training-job",
        optimization_objective="minimize-rmse",
        column_specs={
            "date": "timestamp",
            "price": "numeric",
        },
    )

    model = job.run(
        dataset=dataset,
        target_column="price",
        time_column="date",
        time_series_identifier_column="series_id",
        unavailable_at_forecast_columns=["price"],
        available_at_forecast_columns=["date"],
        data_granularity_unit="day",
        data_granularity_count=1,
        forecast_horizon=14,
        context_window=90,
        budget_milli_node_hours=2000,          # ~2 node hours
        model_display_name="gold-forecast-model-v1",
    )

    aiplatform.end_run()
    print(f"✅ Model trained & registered: {model.resource_name}")
    return model

# ======================
# 6. Deploy to Endpoint
# ======================
def deploy_endpoint(model):
    endpoint = model.deploy(
        deployed_model_display_name="gold-forecast-endpoint",
        machine_type="n1-standard-4",
        min_replica_count=1,
        max_replica_count=1,
        traffic_percentage=100,
    )
    print(f"✅ Endpoint deployed: {endpoint.resource_name}")
    return endpoint

# ======================
# 7. Batch Prediction
# ======================
def run_batch_prediction(model):
    batch_job = model.batch_predict(
        job_display_name="gold-batch-forecast",
        gcs_source=GCS_CSV_URI,
        gcs_destination_prefix=f"gs://{BUCKET_NAME}/predictions/",
        predictions_format="csv",
        machine_type="n1-standard-4",
    )
    batch_job.wait()
    print(f"✅ Batch prediction finished: {batch_job.resource_name}")
    return batch_job

# ======================
# 8. Model Monitoring (basic setup)
# ======================
def setup_monitoring(endpoint, model):
    # Note: Full monitoring setup usually needs more config.
    # This creates a basic monitoring job skeleton.
    print("ℹ️  Model Monitoring can be enabled from the console on the Endpoint.")
    print(f"   Endpoint: {endpoint.resource_name}")
    print(f"   Model: {model.resource_name}")

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    print("\n🚀 Starting Gold Price Forecasting Pipeline on Vertex AI\n")

    # Step 1: Upload
    upload_csv()

    # Step 2: Dataset
    dataset = create_dataset()

    # Step 3: Feature Store (optional - can comment out if you want faster run)
    # featurestore = create_featurestore()

    # Step 4: Train
    model = train_model(dataset)

    # Step 5: Deploy Endpoint
    endpoint = deploy_endpoint(model)

    # Step 6: Batch Prediction
    batch_job = run_batch_prediction(model)

    # Step 7: Monitoring note
    setup_monitoring(endpoint, model)

    print("\n✅ All done!")
    print(f"Dataset   : {dataset.resource_name}")
    print(f"Model     : {model.resource_name}")
    print(f"Endpoint  : {endpoint.resource_name}")
