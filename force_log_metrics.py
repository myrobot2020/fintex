from google.cloud import aiplatform
from datetime import datetime

aiplatform.init(
    project="finance-502004",
    location="us-central1",
    experiment="gold-forecast-experiment"
)

# Use a unique name to avoid conflicts
run_name = f"summary-report-{datetime.now().strftime('%H%M%S')}"

print(f"🚀 Creating summary run: {run_name}")

with aiplatform.start_run(run_name) as run:
    # Log the key comparison metrics manually
    run.log_metrics({
        "automl_r_squared": 0.58,
        "arima_baseline_mae": 15.42,
        "arima_baseline_rmse": 22.10
    })
    run.log_params({
        "status": "production_ready",
        "api_url": "https://gold-forecast-api-411809922304.us-central1.run.app"
    })

print(f"✅ Successfully logged to {run_name}")
