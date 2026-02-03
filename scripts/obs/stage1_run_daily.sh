#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/Peak_Trade"

# Deterministic date anchor (can be injected by caller/CI)
RUN_DATE="${RUN_DATE:-$(date -u +%F)}"
# Align with Stage1 default reports root (get_reports_root()).
REPORT_ROOT="${REPORT_ROOT:-reports/obs/stage1}"

# Prefer project venv if present
if [ -f ".venv/bin/activate" ]; then
  source ".venv/bin/activate"
  PY="python"
else
  PY="python3"
fi

DATE="$(date +%F)"
mkdir -p "logs/obs/stage1"

echo "=== Stage1 DAILY $(date -Iseconds) ==="
"$PY" "scripts/obs/stage1_daily_snapshot.py" --fail-on-new-alerts

# Generate deterministic index for WebUI/ops consumption
"$PY" scripts/obs/stage1_report_index.py \
  --root "${REPORT_ROOT}" \
  --out "${REPORT_ROOT}/index.json" \
  --run-date "${RUN_DATE}"

# Validate index against disk artifacts (fail-fast).
"$PY" scripts/obs/validate_stage1_index.py \
  --root "${REPORT_ROOT}" \
  --index "${REPORT_ROOT}/index.json" \
  --out "${REPORT_ROOT}/validation.json" \
  --require "${RUN_DATE}_snapshot.md" \
  --require "${RUN_DATE}_summary.json" \
  --require "stage1_trend.json" || exit 2

echo "=== done ==="
