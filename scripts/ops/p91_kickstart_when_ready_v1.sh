#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

UID_NUM="$(id -u)"
LABEL="${P91_LABEL:-com.peaktrade.p91-audit-snapshot-runner}"
SUP_BASE="${SUP_BASE_DIR:-out/ops/online_readiness_supervisor}"
MIN_TICKS="${MIN_TICKS:-2}"

_out_dir_default() {
  if [ ! -d "$SUP_BASE" ]; then
    return 0
  fi
  # newest run_* (lexicographic works for UTC timestamps)
  ls -1 "$SUP_BASE" 2>/dev/null | grep '^run_' | LC_ALL=C sort | tail -n 1
}

if [ -z "${OUT_DIR:-}" ]; then
  latest="$(_out_dir_default || true)"
  if [ -n "${latest:-}" ]; then
    OUT_DIR="$SUP_BASE/$latest"
    export OUT_DIR
  fi
fi

if [ -z "${OUT_DIR:-}" ] || [ ! -d "$OUT_DIR" ]; then
  echo "P91_KICKSTART_NOT_READY reason=out_dir_missing out_dir=${OUT_DIR:-} base=$SUP_BASE" >&2
  exit 3
fi

ticks="$(ls -1 "$OUT_DIR" 2>/dev/null | grep '^tick_' | wc -l | tr -d ' ')"
ticks="${ticks:-0}"

if [ "$ticks" -lt "$MIN_TICKS" ]; then
  echo "P91_KICKSTART_NOT_READY reason=insufficient_ticks need=$MIN_TICKS have=$ticks out_dir=$OUT_DIR" >&2
  exit 3
fi

# DRY_RUN: sandbox/CI-safe path (skip launchctl)
DRY_RUN="${DRY_RUN:-}"
case "$DRY_RUN" in
  YES|yes|1|true|TRUE)
    echo "P91_DRY_RUN_OK out_dir=$OUT_DIR ticks=$ticks label=$LABEL"
    exit 0
    ;;
esac

launchctl kickstart -k "gui/${UID_NUM}/${LABEL}"
echo "P91_KICKSTART_OK out_dir=$OUT_DIR ticks=$ticks label=$LABEL"
