#!/bin/bash
# Decrypt and apply all SOPS-encrypted Kubernetes secret manifests in this directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "${SOPS_AGE_KEY_FILE:-}" && -f "${SCRIPT_DIR}/../key.txt" ]]; then
  export SOPS_AGE_KEY_FILE="${SCRIPT_DIR}/../key.txt"
fi

shopt -s nullglob
for file in "${SCRIPT_DIR}"/*.sops.yaml "${SCRIPT_DIR}"/*.sops.yml; do
  echo "Applying secret: $file"
  sops -d "$file" | kubectl apply -f -
done
