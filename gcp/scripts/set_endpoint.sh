#!/usr/bin/env bash
set -euo pipefail
if [ $# -lt 1 ]; then
echo "Usage: $0 <VERTEX_ENDPOINT_RESOURCE_OR_ID>"
exit 1
fi
ENDPOINT_VALUE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SCRIPT_DIR}/../config.env"
sed -i.bak "s|^VERTEX_ENDPOINT_ID=.*|VERTEX_ENDPOINT_ID=${ENDPOINT_VALUE}|" "${CONFIG}"
source "${CONFIG}"
bash "${SCRIPT_DIR}/deploy_api.sh"
