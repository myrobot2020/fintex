#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.env"
gcloud run deploy "${CLOUD_RUN_SERVICE}" \
--source "${SCRIPT_DIR}/../api" \
--region "${CLOUD_RUN_REGION}" \
--project "${PROJECT_ID}" \
--allow-unauthenticated \
--set-env-vars "PROJECT_ID=${PROJECT_ID},VERTEX_LOCATION=${VERTEX_LOCATION},VERTEX_ENDPOINT_ID=${VERTEX_ENDPOINT_ID},BQ_DATASET=${BQ_DATASET},BQ_TABLE_PREDICTIONS=${BQ_TABLE_PREDICTIONS}" \
--memory 512Mi --cpu 1 --min-instances 0 --max-instances 3
echo "Deployed."
