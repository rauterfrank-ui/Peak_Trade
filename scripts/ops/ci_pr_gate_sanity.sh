#!/usr/bin/env bash
set -euo pipefail

CFG="config/ci/required_status_checks.json"
WF=".github/workflows/ci.yml"

# 1) hygiene contract must be green
python3 scripts/ci/validate_required_checks_hygiene.py \
  --config "$CFG" \
  --workflows .github/workflows \
  --strict

# 2) JSON SSOT must define non-empty required contexts and not regress to PR Gate-only legacy
jq -e '.required_contexts | type == "array" and length > 0' "$CFG" >/dev/null
jq -e '.required_contexts != ["PR Gate"]' "$CFG" >/dev/null
rg -n '^\s*"required_contexts"\s*:' "$CFG"

# 3) workflow must keep required-contexts JSON contract marker
rg -n 'required_contexts - ignored_contexts' "$WF"

echo "OK: JSON SSOT required-checks contract is present and PR Gate-only legacy is absent."
