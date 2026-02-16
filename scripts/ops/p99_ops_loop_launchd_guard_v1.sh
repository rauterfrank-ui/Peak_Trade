#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# -------------------------
# HARD GUARDRAILS
# -------------------------
# Force safe modes regardless of caller / plist env.
export MODE="shadow"
export DRY_RUN="YES"

# Never allow execution/live/record paths.
# (If any of these are set externally, fail hard.)
deny_vars=(
  "LIVE"
  "RECORD"
  "EXECUTION_ENABLE"
  "TRADING_ENABLE"
  "ENABLE_LIVE_TRADING"
  "ARM_LIVE"
  "PT_ARMED"
  "PT_ENABLED"
  "PT_CONFIRM_LIVE"
  "PT_CONFIRM_MERGE" # unrelated but keep paranoia
)

for v in "${deny_vars[@]}"; do
  if [ "${!v:-}" != "" ]; then
    echo "P99_GUARD_FAIL: env_var_not_allowed $v is set" >&2
    exit 3
  fi
done

# Block typical exchange secret envs if present (readiness loop should not need them).
# Adjust list if you have canonical names in repo; this is a safety net.
secretish=(
  "KRAKEN_API_KEY" "KRAKEN_API_SECRET"
  "BINANCE_API_KEY" "BINANCE_API_SECRET"
  "COINBASE_API_KEY" "COINBASE_API_SECRET"
  "OKX_API_KEY" "OKX_API_SECRET"
  "EXCHANGE_API_KEY" "EXCHANGE_API_SECRET"
  "CCXT_API_KEY" "CCXT_API_SECRET"
  "API_KEY" "API_SECRET"
)

for v in "${secretish[@]}"; do
  if [ "${!v:-}" != "" ]; then
    echo "P99_GUARD_FAIL: secret_env_not_allowed $v is set" >&2
    exit 3
  fi
done

# Require OUT_DIR to point into out/ops to keep artifacts local + predictable.
OUT_DIR_DEFAULT="out/ops/online_readiness_supervisor/$(ls -1 out/ops/online_readiness_supervisor 2>/dev/null | grep '^run_' | LC_ALL=C sort | tail -n 1)"
export OUT_DIR="${OUT_DIR:-$OUT_DIR_DEFAULT}"

case "$OUT_DIR" in
  out/ops/*|*/out/ops/*) : ;;
  *)
    echo "P99_GUARD_FAIL: OUT_DIR must be under out/ops (got: $OUT_DIR)" >&2
    exit 3
    ;;
esac

# Run the P99 CLI (read-only orchestrator on top of P98)
exec python3 -m src.ops.p99.ops_loop_cli_v1 --mode "$MODE"
