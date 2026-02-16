#!/usr/bin/env bash
set -euo pipefail

epoch_now() {
  python3 - <<'PY'
import time
print(int(time.time()))
PY
}

mtime_epoch() {
  python3 - "$1" <<'PY'
import os, sys
print(int(os.path.getmtime(sys.argv[1])))
PY
}

usage() {
  cat <<'USAGE' >&2
Usage:
  OUT_DIR=<run_dir> bash scripts/ops/p90_supervisor_metrics_v1.sh
  bash scripts/ops/p90_supervisor_metrics_v1.sh --out-dir <run_dir>

Outputs:
  stdout: JSON summary
Exit codes:
  0 ok
  2 usage/missing
USAGE
}

OUT_DIR="${OUT_DIR:-}"
if [ "${1:-}" = "--out-dir" ]; then
  OUT_DIR="${2:-}"
  shift 2 || true
fi

[ -n "${OUT_DIR}" ] || { echo "P90_ERR: missing OUT_DIR" >&2; usage; exit 2; }
[ -d "${OUT_DIR}" ] || { echo "P90_ERR: OUT_DIR not found: ${OUT_DIR}" >&2; exit 2; }

# Collect ticks (tick_*)
TICKS=()
while IFS= read -r d; do TICKS+=("$d"); done < <(find "${OUT_DIR}" -maxdepth 1 -type d -name 'tick_*' | LC_ALL=C sort)
TICK_COUNT="${#TICKS[@]}"

LATEST_TICK=""
if [ "${TICK_COUNT}" -gt 0 ]; then
  LATEST_TICK="${TICKS[$((TICK_COUNT-1))]}"
fi

# Parse READY/NOT_READY from latest P76_RESULT.txt if present
LATEST_P76_PATH=""
LATEST_P76_STATUS="unknown"
LATEST_P76_MODE="unknown"

if [ -n "${LATEST_TICK}" ]; then
  if [ -f "${LATEST_TICK}/p76/P76_RESULT.txt" ]; then
    LATEST_P76_PATH="${LATEST_TICK}/p76/P76_RESULT.txt"
    if grep -q '^P76_READY' "${LATEST_P76_PATH}"; then
      LATEST_P76_STATUS="ready"
    elif grep -q '^P76_NOT_READY' "${LATEST_P76_PATH}"; then
      LATEST_P76_STATUS="not_ready"
    fi
    if grep -q 'mode=shadow' "${LATEST_P76_PATH}"; then
      LATEST_P76_MODE="shadow"
    elif grep -q 'mode=paper' "${LATEST_P76_PATH}"; then
      LATEST_P76_MODE="paper"
    fi
  fi
fi

# Age seconds (best-effort) based on filesystem mtime of latest tick dir
AGE_SEC=""
if [ -n "${LATEST_TICK}" ]; then
  now="$(epoch_now)"
  mt="$(mtime_epoch "${LATEST_TICK}" 2>/dev/null || echo "")"
  if [ -n "${mt}" ]; then
    AGE_SEC="$((now-mt))"
  fi
fi

# Thresholds (env-overridable)
MAX_AGE_SEC="${MAX_AGE_SEC:-900}"
MIN_TICKS="${MIN_TICKS:-2}"

ALERTS=()
if [ "${TICK_COUNT}" -lt "${MIN_TICKS}" ]; then
  ALERTS+=("insufficient_ticks")
fi
if [ -n "${AGE_SEC}" ] && [ "${AGE_SEC}" -gt "${MAX_AGE_SEC}" ]; then
  ALERTS+=("ticks_stale")
fi
if [ "${LATEST_P76_STATUS}" != "ready" ]; then
  ALERTS+=("p76_not_ready_or_missing")
fi

export P90_TICK_COUNT="${TICK_COUNT}"
export P90_LATEST_TICK="${LATEST_TICK:-}"
export P90_AGE_SEC="${AGE_SEC:-}"
export P90_LATEST_P76_PATH="${LATEST_P76_PATH:-}"
export P90_LATEST_P76_STATUS="${LATEST_P76_STATUS}"
export P90_LATEST_P76_MODE="${LATEST_P76_MODE}"
export P90_ALERTS="$(IFS=,; echo "${ALERTS[*]-}")"
export MAX_AGE_SEC
export MIN_TICKS

python3 - <<'PY'
import json, os

def _as_int(x, default=None):
    try:
        return int(x)
    except Exception:
        return default

alerts_str = os.environ.get("P90_ALERTS", "")
alerts = [a for a in alerts_str.split(",") if a]

out = {
  "version": "p90_supervisor_metrics_v1",
  "out_dir": os.environ.get("OUT_DIR"),
  "tick_count": _as_int(os.environ.get("P90_TICK_COUNT",""), 0),
  "latest_tick": os.environ.get("P90_LATEST_TICK") or None,
  "age_sec": _as_int(os.environ.get("P90_AGE_SEC",""), None),
  "latest_p76_result_path": os.environ.get("P90_LATEST_P76_PATH") or None,
  "latest_p76_status": os.environ.get("P90_LATEST_P76_STATUS","unknown"),
  "latest_p76_mode": os.environ.get("P90_LATEST_P76_MODE","unknown"),
  "thresholds": {
    "max_age_sec": _as_int(os.environ.get("MAX_AGE_SEC","900"), 900),
    "min_ticks": _as_int(os.environ.get("MIN_TICKS","2"), 2),
  },
  "alerts": alerts,
}
print(json.dumps(out, sort_keys=True))
PY
