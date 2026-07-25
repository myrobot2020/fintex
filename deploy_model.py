"""
Deploy the trained Gold Forecast Model to a Vertex AI Endpoint
"""
from google.cloud import aiplatform

PROJECT_ID = "finance-502004"
REGION = "us-central1"
MODEL_ID = "projects/411809922304/locations/us-central1/models/7996651861547417600"
ENDPOINT_NAME = "gold-forecast-endpoint"

aiplatform.init(project=PROJECT_ID, location=REGION)

print(f"🚀 Loading model: {MODEL_ID}")
model = aiplatform.Model(MODEL_ID)

print(f"🚀 Creating endpoint: {ENDPOINT_NAME}")
endpoint = aiplatform.Endpoint.create(display_name=ENDPOINT_NAME)

print(f"🚀 Deploying model to endpoint (this takes ~15-20 mins)...")
endpoint.deploy(
    model=model,
    deployed_model_display_name="gold-forecast-v1",
    machine_type="n1-standard-4",
    min_replica_count=1,
    max_replica_count=1,
)

print(f"✅ Deployment complete!")
print(f"Endpoint Resource Name: {endpoint.resource_name}")
print(f"Endpoint ID: {endpoint.name}")
