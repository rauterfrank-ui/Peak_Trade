#!/usr/bin/env bash
set -euo pipefail

MODE="${MODE:-shadow}"          # paper|shadow (live/record bleiben geblockt)
ITERATIONS="${ITERATIONS:-1}"
INTERVAL="${INTERVAL:-0}"
RUN_ID="${RUN_ID:-p76_now}"
OUT_DIR="${OUT_DIR:-out/ops/p76_run_${RUN_ID}_$(date -u +%Y%m%dT%H%M%SZ)}"

mkdir -p "$OUT_DIR"

echo "[run] MODE=$MODE ITERATIONS=$ITERATIONS INTERVAL=$INTERVAL RUN_ID=$RUN_ID OUT_DIR=$OUT_DIR"

OUT_DIR="$OUT_DIR" RUN_ID="$RUN_ID" MODE="$MODE" ITERATIONS="$ITERATIONS" INTERVAL="$INTERVAL" \
  bash scripts/ops/online_readiness_go_no_go_v1.sh | tee "$OUT_DIR/RUN.log"

echo "[run] DONE. out_dir=$OUT_DIR"
