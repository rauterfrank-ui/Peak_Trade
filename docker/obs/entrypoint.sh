#!/bin/bash
set -euo pipefail

# Peak_Trade – Phase 16L: Ops Runner Entrypoint
# Dispatches stage1 monitoring commands

REPORTS_ROOT="${PEAK_REPORTS_DIR:-/reports}"

case "${1:-}" in
    stage1-snapshot)
        echo "==> Running Stage1 Daily Snapshot..."
        exec python scripts/obs/stage1_daily_snapshot.py --reports-root "$REPORTS_ROOT" "${@:2}"
        ;;
    stage1-trends)
        echo "==> Running Stage1 Weekly Trend Report..."
        exec python scripts/obs/stage1_trend_report.py --reports-root "$REPORTS_ROOT" "${@:2}"
        ;;
    --help|-h|help|"")
        cat <<EOF
Peak_Trade – Ops Runner (Phase 16L)

USAGE:
  docker run --rm -v \$(pwd)/reports:/reports peaktrade-ops <COMMAND>

COMMANDS:
  stage1-snapshot   Run daily snapshot (obs/stage1)
  stage1-trends     Run weekly trend report (obs/stage1)
  --help            Show this help

ENVIRONMENT:
  PEAK_REPORTS_DIR  Override reports root (default: /reports)

EXAMPLES:
  docker run --rm -v \$(pwd)/reports:/reports peaktrade-ops stage1-snapshot
  docker run --rm -v \$(pwd)/reports:/reports peaktrade-ops stage1-trends --days 21
EOF
        exit 0
        ;;
    *)
        echo "ERROR: Unknown command: $1" >&2
        echo "Run with --help for usage." >&2
        exit 2
        ;;
esac
