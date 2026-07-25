"""
Run a Batch Prediction job for the Gold Forecast Model
"""
from google.cloud import aiplatform

PROJECT_ID = "finance-502004"
REGION = "us-central1"
MODEL_ID = "7996651861547417600"
BUCKET_NAME = "cloud-ai-platform-5198f7b8-0786-40a1-802e-78049446b994"
GCS_CSV_URI = f"gs://{BUCKET_NAME}/data/gold_price_forecast.csv"
GCS_DESTINATION_PREFIX = f"gs://{BUCKET_NAME}/predictions/"

aiplatform.init(project=PROJECT_ID, location=REGION)

print(f"🚀 Starting Batch Prediction for Model: {MODEL_ID}")
model = aiplatform.Model(MODEL_ID)

batch_job = model.batch_predict(
    job_display_name="gold-batch-forecast-manual",
    gcs_source=GCS_CSV_URI,
    gcs_destination_prefix=GCS_DESTINATION_PREFIX,
    instances_format="csv",
    predictions_format="csv",
    machine_type="n1-standard-4",
)

print(f"🚀 Batch prediction job submitted: {batch_job.resource_name}")
print("Monitor the job in the Google Cloud Console.")
