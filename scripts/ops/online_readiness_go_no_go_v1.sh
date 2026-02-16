#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

MODE="${MODE:-shadow}"
OUT_DIR="${OUT_DIR:-}"
RUN_ID="${RUN_ID:-}"
ITERATIONS="${ITERATIONS:-1}"
INTERVAL="${INTERVAL:-0}"

# Optional preferred overrides
OUT_DIR_OVERRIDE="${OUT_DIR_OVERRIDE:-}"
RUN_ID_OVERRIDE="${RUN_ID_OVERRIDE:-}"
MODE_OVERRIDE="${MODE_OVERRIDE:-}"
ITERATIONS_OVERRIDE="${ITERATIONS_OVERRIDE:-}"
INTERVAL_OVERRIDE="${INTERVAL_OVERRIDE:-}"

# Canonical resolution: *_OVERRIDE wins
FINAL_OUT_DIR="${OUT_DIR_OVERRIDE:-$OUT_DIR}"
FINAL_RUN_ID="${RUN_ID_OVERRIDE:-$RUN_ID}"
FINAL_MODE="${MODE_OVERRIDE:-$MODE}"
FINAL_ITERATIONS="${ITERATIONS_OVERRIDE:-$ITERATIONS}"
FINAL_INTERVAL="${INTERVAL_OVERRIDE:-$INTERVAL}"

[ -n "$FINAL_OUT_DIR" ] || { echo "ERR: OUT_DIR (or OUT_DIR_OVERRIDE) required" >&2; exit 2; }
[ -n "$FINAL_RUN_ID" ] || { echo "ERR: RUN_ID (or RUN_ID_OVERRIDE) required" >&2; exit 2; }

mkdir -p "$FINAL_OUT_DIR"

# Always pin env into the run dir (operator audit trail)
cat > "$FINAL_OUT_DIR/ONLINE_READINESS_ENV.json" <<EOF
{
  "mode": "$(printf '%s' "$FINAL_MODE")",
  "iterations": "$(printf '%s' "$FINAL_ITERATIONS")",
  "interval": "$(printf '%s' "$FINAL_INTERVAL")",
  "out_dir": "$(printf '%s' "$FINAL_OUT_DIR")",
  "run_id": "$(printf '%s' "$FINAL_RUN_ID")",
  "contract": "p76_online_readiness_go_no_go_v1",
  "ts_utc": "$(date -u +%Y%m%dT%H%M%SZ)"
}
EOF

# 1) Health gate (P71) — must pass
if ! OUT_DIR_OVERRIDE="$FINAL_OUT_DIR" RUN_ID_OVERRIDE="${FINAL_RUN_ID}_gate" MODE_OVERRIDE="$FINAL_MODE" \
  bash scripts/ops/p71_health_gate_v1.sh 2>&1 | tee "$FINAL_OUT_DIR/P71_GATE.log"; then
  echo "P76_NOT_READY reason=p71_health_gate_failed out_dir=$FINAL_OUT_DIR" | tee "$FINAL_OUT_DIR/P76_RESULT.txt"
  exit 3
fi

# 2) Shadowloop pack (P72) — must complete (P72 runs P71 internally; we already passed above)
if ! OUT_DIR="$FINAL_OUT_DIR" RUN_ID="${FINAL_RUN_ID}_pack" MODE="$FINAL_MODE" \
  ITERATIONS="$FINAL_ITERATIONS" INTERVAL="$FINAL_INTERVAL" \
  bash scripts/ops/p72_shadowloop_pack_v1.sh 2>&1 | tee "$FINAL_OUT_DIR/P72_PACK.log"; then
  echo "P76_NOT_READY reason=p72_pack_failed out_dir=$FINAL_OUT_DIR" | tee "$FINAL_OUT_DIR/P76_RESULT.txt"
  exit 4
fi

echo "P76_READY out_dir=$FINAL_OUT_DIR run_id=$FINAL_RUN_ID mode=$FINAL_MODE" | tee "$FINAL_OUT_DIR/P76_RESULT.txt"
exit 0
