#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.env"
gcloud pubsub topics create "${PUBSUB_TOPIC_INGEST}" --project="${PROJECT_ID}" 2>/dev/null || true
gcloud pubsub topics create "${PUBSUB_TOPIC_RETRAIN}" --project="${PROJECT_ID}" 2>/dev/null || true
gcloud pubsub subscriptions create "${PUBSUB_TOPIC_INGEST}-sub" --topic="${PUBSUB_TOPIC_INGEST}" --project="${PROJECT_ID}" 2>/dev/null || true
gcloud pubsub subscriptions create "${PUBSUB_TOPIC_RETRAIN}-sub" --topic="${PUBSUB_TOPIC_RETRAIN}" --project="${PROJECT_ID}" 2>/dev/null || true
echo "Pub/Sub ready."
