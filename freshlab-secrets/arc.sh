#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "${SOPS_AGE_KEY_FILE:-}" && -f "${SCRIPT_DIR}/../key.txt" ]]; then
  export SOPS_AGE_KEY_FILE="${SCRIPT_DIR}/../key.txt"
fi

sops -d "${SCRIPT_DIR}/runners-gh-arc-app.sops.yaml" | kubectl apply -f -
