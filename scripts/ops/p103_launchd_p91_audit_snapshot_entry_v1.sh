#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

SUP_BASE_DIR="${SUP_BASE_DIR:-out/ops/online_readiness_supervisor}"
MIN_TICKS="${MIN_TICKS:-2}"
MAX_AGE_SEC="${MAX_AGE_SEC:-900}"
MODE="${MODE:-shadow}"

# If OUT_DIR not set, pick newest run_*
if [ -z "${OUT_DIR:-}" ]; then
  latest="$(ls -1 "$SUP_BASE_DIR" 2>/dev/null | grep '^run_' | LC_ALL=C sort | tail -n 1 || true)"
  if [ -z "$latest" ]; then
    echo "P103_P91_ENTRY_FAIL: no_run_dirs sup_base_dir=$SUP_BASE_DIR" >&2
    exit 3
  fi
  OUT_DIR="$SUP_BASE_DIR/$latest"
fi

export OUT_DIR MIN_TICKS MAX_AGE_SEC MODE

# Run the canonical one-shot runner (writes EVI+bundle+pin)
exec bash scripts/ops/p91_audit_snapshot_runner_v1.sh
