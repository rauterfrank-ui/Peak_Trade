#!/usr/bin/env bash
# Poll PR 1106 until MERGED, then sync main + cleanup + Stage1 smoke.
# Usage: bash scripts/ops/poll_pr1106_then_sync_stage1.sh

set -euo pipefail
cd "${0%/*}/../.."

git fetch origin --prune

while true; do
  state="$(gh pr view 1106 --json state --jq .state)"
  echo "$(date -u +%FT%TZ) PR1106 state=$state"
  gh pr checks 1106 || true
  if [ "$state" = "MERGED" ]; then
    break
  fi
  sleep 60
done

echo "=== PR 1106 merged, syncing main ==="
git checkout main
git fetch origin --prune
git pull --ff-only origin main

git branch -D pr-09-stage1-required-artifacts 2>/dev/null || true

echo "=== Stage1 end-to-end smoke on main ==="
RUN_DATE="$(date -u +%F)"
REPORT_ROOT="reports/obs/stage1"
RUN_DATE="$RUN_DATE" REPORT_ROOT="$REPORT_ROOT" bash scripts/obs/stage1_run_daily.sh

python3 - <<'PY'
import json
from pathlib import Path
v=json.loads(Path("reports/obs/stage1/validation.json").read_text(encoding="utf-8"))
print("ok:", v.get("ok"))
print("errors:", v.get("errors", [])[:10])
PY
