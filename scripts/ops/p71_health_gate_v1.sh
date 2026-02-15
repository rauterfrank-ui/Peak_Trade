#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
ROOT="$(pwd)"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

TS="${TS_OVERRIDE:-$(date -u +%Y%m%dT%H%M%SZ)}"
OUT_DIR="${OUT_DIR_OVERRIDE:-out/ops/p71_health_gate_${TS}}"
MODE="${MODE_OVERRIDE:-shadow}"
RUN_ID="${RUN_ID_OVERRIDE:-p71_gate_${TS}}"
# ITERATIONS_OVERRIDE reserved (P64 is single-shot)
ITERATIONS="${ITERATIONS_OVERRIDE:-1}"
ALLOW_BULL_STRATEGIES="${ALLOW_BULL_STRATEGIES_OVERRIDE:-}"
ALLOW_BEAR_STRATEGIES="${ALLOW_BEAR_STRATEGIES_OVERRIDE:-}"

mkdir -p "$OUT_DIR"

cat > "${OUT_DIR}/p71_run_gate.py" <<PY
from pathlib import Path
from src.ops.p71 import run_online_readiness_health_gate_v1, P71GateContextV1

prices = [0.001] * 240
allow_bull = [s for s in "${ALLOW_BULL_STRATEGIES}".split(",") if s] or None
allow_bear = [s for s in "${ALLOW_BEAR_STRATEGIES}".split(",") if s] or None

ctx = P71GateContextV1(
    mode="${MODE}",
    run_id="${RUN_ID}",
    out_dir=Path("${OUT_DIR}"),
    allow_bull_strategies=allow_bull,
    allow_bear_strategies=allow_bear,
)

out = run_online_readiness_health_gate_v1(prices, ctx)
print(out["overall_ok"])
PY

python3 "${OUT_DIR}/p71_run_gate.py" | tee "${OUT_DIR}/P71_OK.txt" >/dev/null

if ! grep -q "^True$" "${OUT_DIR}/P71_OK.txt"; then
  echo "P71_GATE_FAIL out_dir=${OUT_DIR}" >&2
  exit 3
fi

echo "P71_GATE_OK out_dir=${OUT_DIR}"
