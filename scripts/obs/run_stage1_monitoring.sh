#!/bin/bash
set -euo pipefail

# ============================================================
# Peak_Trade - Stage 1 Monitoring (Daily Routine)
# ============================================================
#
# Führt täglich aus:
#   1) Daily Snapshot (analysiert letzte 24h)
#   2) Trend Report (zeigt Go/No-Go Signal)
#
# Usage:
#   bash scripts/obs/run_stage1_monitoring.sh
#
# Automation (crontab):
#   0 8 * * * cd /path/to/Peak_Trade && bash scripts/obs/run_stage1_monitoring.sh >> logs/stage1_cron.log 2>&1
# ============================================================

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT" || exit 1

RUN_DATE="${RUN_DATE:-$(date -u +%F)}"
# Align with Stage1 default reports root (get_reports_root()).
REPORT_ROOT="${REPORT_ROOT:-reports/obs/stage1}"

echo "============================================================"
echo "Peak_Trade — Stage 1 Daily Monitoring"
echo "Time: $(date -Iseconds)"
echo "Repo: $REPO_ROOT"
echo "============================================================"
echo

# -----------------------------
# 1) Daily Snapshot
# -----------------------------
echo "=== 1) Generating Daily Snapshot ==="
python3 scripts/obs/stage1_daily_snapshot.py
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ Daily snapshot OK (no new alerts detected)"
elif [ $EXIT_CODE -eq 2 ]; then
  echo "⚠️ Daily snapshot WARNING (new alerts detected, see report)"
else
  echo "❌ Daily snapshot FAILED (exit code: $EXIT_CODE)"
  exit $EXIT_CODE
fi

echo
echo "=== 2) Generating Trend Report (last 14 days) ==="
python3 scripts/obs/stage1_trend_report.py --days 14

echo
echo "============================================================"
echo "✅ Stage 1 Monitoring Complete"
echo "============================================================"
echo
echo "Reports:"
echo "  - Latest snapshot: reports/obs/stage1/$(date +%F)_snapshot.md"
echo "  - Trend report: (see above)"
echo
echo "Next steps:"
echo "  - Review reports for anomalies"
echo "  - Check 'New alerts (24h)' in snapshot"
echo "  - If trend stable for 1-2 weeks → proceed to Stage 2 (Webhook)"

python3 scripts/obs/stage1_report_index.py \
  --root "${REPORT_ROOT}" \
  --out "${REPORT_ROOT}/index.json" \
  --run-date "${RUN_DATE}"

python3 scripts/obs/validate_stage1_index.py \
  --root "${REPORT_ROOT}" \
  --index "${REPORT_ROOT}/index.json" \
  --out "${REPORT_ROOT}/validation.json" \
  --require "${RUN_DATE}_snapshot.md" \
  --require "${RUN_DATE}_summary.json" \
  --require "stage1_trend.json" || exit 2
