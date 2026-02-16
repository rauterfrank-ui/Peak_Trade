#!/usr/bin/env bash
# P72: Unified shadow loop pack — P71 health gate first, then P68 shadow loop (paper/shadow only)
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

TS="${TS_OVERRIDE:-$(date -u +%Y%m%dT%H%M%SZ)}"
OUT_DIR="${OUT_DIR_OVERRIDE:-out/ops/p72_shadowloop_pack_${TS}}"
MODE="${MODE_OVERRIDE:-shadow}"
RUN_ID="${RUN_ID_OVERRIDE:-p72_pack_${TS}}"
ITERATIONS="${ITERATIONS_OVERRIDE:-1}"
INTERVAL="${INTERVAL_OVERRIDE:-0}"
ALLOW_BULL_STRATEGIES="${ALLOW_BULL_STRATEGIES_OVERRIDE:-}"
ALLOW_BEAR_STRATEGIES="${ALLOW_BEAR_STRATEGIES_OVERRIDE:-}"

mkdir -p "$OUT_DIR"

# 1) P71 health gate (must PASS before loop)
OUT_DIR_OVERRIDE="$OUT_DIR" \
  MODE_OVERRIDE="$MODE" \
  RUN_ID_OVERRIDE="${RUN_ID}_gate" \
  ALLOW_BULL_STRATEGIES_OVERRIDE="$ALLOW_BULL_STRATEGIES" \
  ALLOW_BEAR_STRATEGIES_OVERRIDE="$ALLOW_BEAR_STRATEGIES" \
  bash scripts/ops/p71_health_gate_v1.sh

# 2) P68 shadow loop (only if gate passed)
OUT_DIR="$OUT_DIR" \
  MODE="$MODE" \
  RUN_ID="${RUN_ID}_loop" \
  ITERATIONS="$ITERATIONS" \
  INTERVAL="$INTERVAL" \
  bash scripts/ops/run_shadow_loop_v1.sh

echo "P72_SHADOWLOOP_PACK_OK out_dir=${OUT_DIR}"
