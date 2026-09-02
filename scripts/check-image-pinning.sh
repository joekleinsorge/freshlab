#!/usr/bin/env bash
set -euo pipefail

refs="$({
  rg --no-heading --no-line-number --only-matching \
    --glob '*.yaml' --glob '*.yml' --glob '!**/charts/**' \
    "image:[[:space:]]*['\"]?[^'\"[:space:]]+" . || true
} | sed -E "s/.*image:[[:space:]]*['\"]?([^'\"[:space:]]+).*/\1/" | sort -u)"

unpinned=()
while IFS= read -r ref; do
  [[ -z "$ref" ]] && continue
  [[ "$ref" == *'{{'* || "$ref" == *'${'* ]] && continue
  if [[ "$ref" != *@sha256:* ]]; then
    unpinned+=("$ref")
  fi
done <<< "$refs"

if ((${#unpinned[@]} == 0)); then
  echo "All discovered image references are digest-pinned."
  exit 0
fi

echo "Images not pinned by digest:"
printf ' - %s\n' "${unpinned[@]}"

if [[ "${FAIL_ON_UNPINNED_IMAGES:-false}" == "true" ]]; then
  exit 1
fi
