#!/usr/bin/env bash
set -euo pipefail

# ======================
# CONFIG
# ======================
PROJECT_ID="finance-502004"
API_SA_NAME="gold-api-sa"
PIPELINE_SA_NAME="gold-pipeline-sa"

API_SA_EMAIL="${API_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
PIPELINE_SA_EMAIL="${PIPELINE_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🚀 Setting up IAM Patterns for Fintex Project..."

# 1. Create Service Accounts if they don't exist
gcloud iam service-accounts create "${API_SA_NAME}" \
    --display-name="Gold Forecast API Service Account" \
    --project="${PROJECT_ID}" 2>/dev/null || true

gcloud iam service-accounts create "${PIPELINE_SA_NAME}" \
    --display-name="Gold Pipeline/Ingestion Service Account" \
    --project="${PROJECT_ID}" 2>/dev/null || true

# 2. API Service Account Roles (Least Privilege for Cloud Run)
echo "🔑 Assigning roles to API Service Account..."
ROLES_API=(
    "roles/aiplatform.user"       # To call Vertex Endpoints
    "roles/bigquery.dataEditor"   # To log predictions to BQ
    "roles/bigquery.jobUser"      # To run ARIMA queries
    "roles/logging.logWriter"     # For Cloud Run logs
)

for role in "${ROLES_API[@]}"; do
    gcloud project add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${API_SA_EMAIL}" \
        --role="${role}" --condition=None
done

# 3. Pipeline Service Account Roles (Ingestion + Training)
echo "🔑 Assigning roles to Pipeline Service Account..."
ROLES_PIPELINE=(
    "roles/aiplatform.admin"      # To manage datasets and training jobs
    "roles/bigquery.dataEditor"   # To update gold price tables
    "roles/bigquery.jobUser"      # To run ingestion jobs
    "roles/storage.objectAdmin"   # To upload CSVs to GCS
    "roles/logging.logWriter"     # For logs
)

for role in "${ROLES_PIPELINE[@]}"; do
    gcloud project add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${PIPELINE_SA_EMAIL}" \
        --role="${role}" --condition=None
done

# 4. Grant Pub/Sub Publisher to Cloud Scheduler (System Pattern)
# This usually requires the Google-managed service account for Scheduler
SCHEDULER_SA="service-$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SCHEDULER_SA}" \
    --role="roles/pubsub.publisher" --condition=None

echo "✅ IAM Patterns applied."
