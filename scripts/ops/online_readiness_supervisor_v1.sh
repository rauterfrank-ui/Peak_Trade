#!/usr/bin/env bash
# P78/P80/P81 — Online Readiness Supervisor v1
# Exit codes: 0 stopped or unarmed, 2 usage, 3 not allowed, 4 retired
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

MODE="${MODE:-shadow}"              # paper|shadow only
OUT_DIR="${OUT_DIR:-out/ops/p78_supervisor}"
PIDFILE="${PIDFILE:-/tmp/p78_online_readiness_supervisor.pid}"
STOP="${STOP:-0}"                   # 1 = stop mode (terminate existing supervisor)
ACTION="${ACTION:-}"                # "stop" = same as STOP=1
CHECK_MODE="${CHECK_MODE:-p86}"     # Retain the historical selector for callers

# Exit code constants
EXIT_OK=0
EXIT_USAGE=2
EXIT_NOT_ALLOWED=3
EXIT_GATE_FAIL=4

case "$MODE" in paper|shadow) ;; *)
  echo "ERR: MODE must be paper|shadow (live/record blocked)" >&2
  exit $EXIT_NOT_ALLOWED
esac

case "${CHECK_MODE}" in p76|p86) ;; *)
  echo "ERR: CHECK_MODE must be p76|p86 (got ${CHECK_MODE})" >&2
  exit $EXIT_USAGE
esac

# --- P84: Stop mode (STOP=1 or ACTION=stop) — allowed without SUPERVISOR_ENABLE ---
if [ "${STOP}" = "1" ] || [ "${ACTION}" = "stop" ]; then
  if [ -e "${PIDFILE}" ]; then
    pid="$(cat "${PIDFILE}" 2>/dev/null || true)"
    if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
      echo "P80_STOP: sending SIGTERM to pid=${pid}"
      kill -TERM "${pid}" 2>/dev/null || true
      for _ in $(seq 1 30); do
        kill -0 "${pid}" 2>/dev/null || break
        sleep 1
      done
      if kill -0 "${pid}" 2>/dev/null; then
        echo "P80_STOP: pid ${pid} still alive after 30s, sending SIGKILL" >&2
        kill -KILL "${pid}" 2>/dev/null || true
        sleep 1
      fi
    fi
    rm -f "${PIDFILE}" 2>/dev/null || true
    echo "P80_STOP_OK pidfile=${PIDFILE}"
  else
    echo "P80_STOP_OK pidfile=${PIDFILE} (already absent)"
  fi
  exit $EXIT_OK
fi

# --- P84: Safe-default guardrails (start path only) ---
# (a) MODE=paper requires explicit opt-in
if [ "$MODE" = "paper" ] && [ "${SUPERVISOR_ALLOW_PAPER:-}" != "YES" ]; then
  echo "ERR: MODE=paper requires SUPERVISOR_ALLOW_PAPER=YES (safe-by-default)" >&2
  exit $EXIT_NOT_ALLOWED
fi
# (b) OUT_DIR must be set and under out/ops/
if [ -z "${OUT_DIR:-}" ]; then
  echo "ERR: OUT_DIR must be set (safe-by-default)" >&2
  exit $EXIT_USAGE
fi
OUT_ABS="${OUT_DIR}"
[[ "$OUT_ABS" != /* ]] && OUT_ABS="$ROOT/$OUT_ABS"
if [[ "$OUT_ABS" != "$ROOT/out/ops" && "$OUT_ABS" != "$ROOT/out/ops/"* ]]; then
  echo "ERR: OUT_DIR must be under out/ops/ (got ${OUT_DIR})" >&2
  exit $EXIT_NOT_ALLOWED
fi
# (c) SUPERVISOR_ENABLE=YES required to start (explicit opt-in; exit 0 = not armed, no restart loop)
if [ "${SUPERVISOR_ENABLE:-}" != "YES" ]; then
  echo "SUPERVISOR_NOT_ARMED: SUPERVISOR_ENABLE=YES required. Add to unit/env to arm." >&2
  exit $EXIT_OK
fi

echo "SUPERVISOR_NOT_READY: ${CHECK_MODE} was retired" >&2
exit "$EXIT_GATE_FAIL"
