#!/usr/bin/env bash
set -euo pipefail

MODE="${MODE:-shadow}"
DRY_RUN="${DRY_RUN:-YES}"
ENABLE="${P117_ENABLE_EXEC_EVI:-NO}"

deny_vars=(LIVE RECORD TRADING_ENABLE EXECUTION_ENABLE PT_ARMED PT_CONFIRM_TOKEN KRAKEN_API_KEY BINANCE_API_KEY COINBASE_API_KEY OKX_API_KEY BYBIT_API_KEY API_KEY API_SECRET)
for v in "${deny_vars[@]}"; do
  if [[ -n "${!v:-}" ]]; then
    echo "P117_GUARD_FAIL deny_env_var=$v" >&2
    exit 3
  fi
done

if [[ "$MODE" != "shadow" && "$MODE" != "paper" ]]; then
  echo "P117_GUARD_FAIL mode_invalid=$MODE" >&2
  exit 3
fi
if [[ "$DRY_RUN" != "YES" ]]; then
  echo "P117_GUARD_FAIL dry_run_must_be_yes=$DRY_RUN" >&2
  exit 3
fi

if [[ "$ENABLE" != "YES" ]]; then
  echo "P117_SKIP enable=${ENABLE}"
  exit 0
fi

# run P116 (creates out/ops artifacts + pin)
MODE="$MODE" DRY_RUN="$DRY_RUN" bash scripts/ops/p116_execution_session_evidence_v1.sh
echo "P117_OK"
