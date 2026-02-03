#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/Peak_Trade"

if [ -f ".venv/bin/activate" ]; then
  source ".venv/bin/activate"
  PY="python"
else
  PY="python3"
fi

RUN_DATE="${RUN_DATE:-$(date -u +%F)}"
# Align with Stage1 default reports root (get_reports_root()).
REPORT_ROOT="${REPORT_ROOT:-reports/obs/stage1}"

DATE="$(date +%F)"
OUT="reports/obs/stage1/${DATE}_trend.md"

echo "=== Stage1 WEEKLY $(date -Iseconds) ===" > "$OUT"
"$PY" "scripts/obs/stage1_trend_report.py" --days 14 >> "$OUT"
echo "=== wrote: $OUT ==="

"$PY" scripts/obs/stage1_report_index.py \
  --root "${REPORT_ROOT}" \
  --out "${REPORT_ROOT}/index.json" \
  --run-date "${RUN_DATE}"

"$PY" scripts/obs/validate_stage1_index.py \
  --root "${REPORT_ROOT}" \
  --index "${REPORT_ROOT}/index.json" \
  --out "${REPORT_ROOT}/validation.json" \
  --require "data.json" \
  --require "report.md" || exit 2
