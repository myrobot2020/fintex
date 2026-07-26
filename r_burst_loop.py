"""
Automated "10 INR Burst" Loop for R Champion
1. Checks if R model beats XGBoost (MAE < 46.79)
2. Deploys to Vertex Endpoint for 1 minute
3. Generates 1 prediction
4. Kills deployment immediately to save cost
"""
import time
from google.cloud import aiplatform

# CONFIG
PROJECT_ID = "finance-502004"
REGION = "us-central1"
ENDPOINT_ID = "8004731072988315648"
BUCKET = "cloud-ai-platform-5198f7b8-0786-40a1-802e-78049446b994"
XGBOOST_MAE = 46.79

aiplatform.init(project=PROJECT_ID, location=REGION)

def run_burst_demo(r_mae):
    print(f"🧐 Comparing R ({r_mae}) vs XGBoost ({XGBOOST_MAE})...")

    if r_mae >= XGBOOST_MAE:
        print("❌ R did not beat XGBoost. Skipping deployment to save money.")
        return

    print("🔥 VICTORY! Starting the 10 INR Burst Deployment...")

    # 1. Register the R Model (Assuming container is built)
    # We use a placeholder URI for the demo R container
    print("🚀 Registering R model to Vertex Registry...")
    model = aiplatform.Model.upload(
        display_name="r-champion-v2-scalper",
        serving_container_image_uri=f"{REGION}-docker.pkg.dev/{PROJECT_ID}/gold-repo/gold-forecast-api:latest", # Reusing repo
        artifact_uri=f"gs://{BUCKET}/models/r_v2/"
    )

    # 2. Deploy (The expensive 15 minutes)
    print("🚀 Deploying to Endpoint... (Estimated cost: 8 INR)")
    endpoint = aiplatform.Endpoint(ENDPOINT_ID)
    deployed_model = endpoint.deploy(
        model=model,
        machine_type="n1-standard-2",
        min_replica_count=1,
        max_replica_count=1,
    )

    # 3. Inference
    print("⚡ MODEL IS LIVE. Sending prediction request...")
    prediction = endpoint.predict(instances=[{"date": "2026-07-25"}])
    print(f"✅ Prediction Result: {prediction.predictions[0]}")

    # 4. Immediate Kill (The "Safety Switch")
    print("🛑 DEMO OVER. Killing deployment to return to 0 INR/hr...")
    endpoint.undeploy_all()
    print("✅ All models undeployed. Billing stopped.")

if __name__ == "__main__":
    # Simulated MAE from our new R script (v2)
    # In your R notebook, run accuracy(fit) to get the real number
    R_MAE_RESULT = 42.15

    run_burst_demo(R_MAE_RESULT)
