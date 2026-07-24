#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.env"
gcloud pubsub topics create "${PUBSUB_TOPIC_INGEST}" --project="${PROJECT_ID}" 2>/dev/null || true
gcloud pubsub topics create "${PUBSUB_TOPIC_RETRAIN}" --project="${PROJECT_ID}" 2>/dev/null || true
gcloud scheduler jobs create pubsub "${SCHEDULER_INGEST_JOB}" \
--project="${PROJECT_ID}" --location="${REGION}" \
--schedule="0 6 * * *" --time-zone="Asia/Kolkata" \
--topic="${PUBSUB_TOPIC_INGEST}" \
--message-body='{"action":"ingest","source":"scheduler"}' 2>/dev/null || \
gcloud scheduler jobs update pubsub "${SCHEDULER_INGEST_JOB}" \
--project="${PROJECT_ID}" --location="${REGION}" \
--schedule="0 6 * * *" --time-zone="Asia/Kolkata" \
--topic="${PUBSUB_TOPIC_INGEST}" \
--message-body='{"action":"ingest","source":"scheduler"}'
gcloud scheduler jobs create pubsub "${SCHEDULER_RETRAIN_JOB}" \
--project="${PROJECT_ID}" --location="${REGION}" \
--schedule="0 7 * * 1" --time-zone="Asia/Kolkata" \
--topic="${PUBSUB_TOPIC_RETRAIN}" \
--message-body='{"action":"retrain","source":"scheduler"}' 2>/dev/null || \
gcloud scheduler jobs update pubsub "${SCHEDULER_RETRAIN_JOB}" \
--project="${PROJECT_ID}" --location="${REGION}" \
--schedule="0 7 * * 1" --time-zone="Asia/Kolkata" \
--topic="${PUBSUB_TOPIC_RETRAIN}" \
--message-body='{"action":"retrain","source":"scheduler"}'
echo "Scheduler ready."
