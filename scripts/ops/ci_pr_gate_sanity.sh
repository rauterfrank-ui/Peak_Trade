#!/usr/bin/env bash
set -euo pipefail

CFG="config/ci/required_status_checks.json"
WF=".github/workflows/ci.yml"

# 1) hygiene contract must be green
python3 scripts/ci/validate_required_checks_hygiene.py \
  --config "$CFG" \
  --workflows .github/workflows \
  --strict

# 2) required_contexts must be exactly ["PR Gate"]
jq -e '.required_contexts == ["PR Gate"]' "$CFG" >/dev/null
rg -n '^\s*"required_contexts"\s*:\s*\[\s*"PR Gate"\s*\]\s*,?\s*$' "$CFG"

# 3) workflow must expose visible check name "PR Gate" (job-id is pr-gate)
rg -n '^\s*pr-gate:\s*$' "$WF"
rg -n '^\s*name:\s*"?PR Gate"?\s*$' "$WF"

# 4) print the exact block for audit / screenshot
nl -ba "$WF" | sed -n '334,352p'

echo "OK: required check name matches workflow-visible check name: PR Gate"
