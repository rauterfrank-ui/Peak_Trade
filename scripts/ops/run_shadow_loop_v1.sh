#!/usr/bin/env bash
# P68: Safe shadow loop runner (paper/shadow only, no live/record)
# Wraps P67 scheduler CLI for deterministic, evidence-writing runs.
set -euo pipefail

MODE="${MODE:-shadow}"
RUN_ID="${RUN_ID:-p68_shadow}"
OUT_DIR="${OUT_DIR:-}"
ITERATIONS="${ITERATIONS:-1}"
INTERVAL="${INTERVAL:-0}"

if [[ -z "$OUT_DIR" ]]; then
  echo "ERR: OUT_DIR must be set for evidence writes"
  exit 1
fi

cd "$(git rev-parse --show-toplevel)"
python3 -m src.ops.p67.shadow_session_scheduler_cli_v1 \
  --mode "$MODE" \
  --run-id "$RUN_ID" \
  --out-dir "$OUT_DIR" \
  --iterations "$ITERATIONS" \
  --interval-seconds "$INTERVAL"
