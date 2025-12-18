#!/usr/bin/env bash
set -euo pipefail

RUN_ID="${1:-}"
RESULTS_DIR="${RESULTS_DIR:-results}"
TEMPLATE_PATH="${TEMPLATE_PATH:-templates/quarto/backtest_report.qmd}"

if ! command -v quarto >/dev/null 2>&1; then
  echo "WARN: quarto not installed; skipping report render." >&2
  exit 0
fi

if [ ! -f "$TEMPLATE_PATH" ]; then
  echo "ERROR: template not found: $TEMPLATE_PATH" >&2
  exit 2
fi

if [ -z "$RUN_ID" ]; then
  RUN_ID="$(ls -1t "$RESULTS_DIR" 2>/dev/null | head -n 1 || true)"
fi

if [ -z "$RUN_ID" ]; then
  echo "ERROR: no run_id found in $RESULTS_DIR" >&2
  exit 2
fi

RUN_DIR="$RESULTS_DIR/$RUN_ID"
if [ ! -d "$RUN_DIR" ]; then
  echo "ERROR: run dir not found: $RUN_DIR" >&2
  exit 2
fi

OUT_DIR="$RUN_DIR/report"
mkdir -p "$OUT_DIR"

WORK_DIR="$OUT_DIR/_quarto_work"
RUN_STAGE="$WORK_DIR/_run"
mkdir -p "$RUN_STAGE"

# stage artifacts (best effort)
cp -f "$RUN_DIR/report_snippet.md" "$RUN_STAGE/report_snippet.md" 2>/dev/null || true
cp -f "$RUN_DIR/stats.json" "$RUN_STAGE/stats.json" 2>/dev/null || true
cp -f "$RUN_DIR/equity.csv" "$RUN_STAGE/equity.csv" 2>/dev/null || true
cp -f "$RUN_DIR/config_snapshot.json" "$RUN_STAGE/config_snapshot.json" 2>/dev/null || true

# copy template into the workdir (so relative includes work)
cp -f "$TEMPLATE_PATH" "$WORK_DIR/backtest_report.qmd"

quarto render "$WORK_DIR/backtest_report.qmd" --output-dir "$OUT_DIR"

# normalize filename if needed
if [ -f "$OUT_DIR/backtest_report.html" ]; then
  mv -f "$OUT_DIR/backtest_report.html" "$OUT_DIR/backtest.html"
fi

echo "OK: rendered $OUT_DIR/backtest.html"
