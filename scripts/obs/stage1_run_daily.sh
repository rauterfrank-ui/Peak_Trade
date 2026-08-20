#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
cd "$ROOT"

# Deterministic date anchor (can be injected by caller/CI)
RUN_DATE="${RUN_DATE:-$(date -u +%F)}"
# Align with Stage1 default reports root (get_reports_root()).
REPORT_ROOT="${REPORT_ROOT:-reports/obs/stage1}"

PY="$ROOT/scripts/pt"

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
