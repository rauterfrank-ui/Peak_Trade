#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

MODE="${MODE:-shadow}"              # paper|shadow only
OUT_DIR="${OUT_DIR:-out/ops/p78_supervisor}"
RUN_ID="${RUN_ID:-p78}"
INTERVAL="${INTERVAL:-30}"          # seconds
ITERATIONS="${ITERATIONS:-0}"       # 0 = infinite
PIDFILE="${PIDFILE:-/tmp/p78_online_readiness_supervisor.pid}"
MAX_LOGS="${MAX_LOGS:-50}"
STOP="${STOP:-0}"                   # 1 = stop mode (terminate existing supervisor)
ACTION="${ACTION:-}"                # "stop" = same as STOP=1

case "$MODE" in paper|shadow) ;; *)
  echo "ERR: MODE must be paper|shadow (live/record blocked)" >&2
  exit 2
esac

# --- P80: Stop mode (STOP=1 or ACTION=stop) ---
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
  exit 0
fi

# --- P80: Idempotent start (refuse double-start, handle stale pidfile) ---
if [ -e "${PIDFILE}" ]; then
  pid="$(cat "${PIDFILE}" 2>/dev/null || true)"
  if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
    echo "ERR: supervisor already running pid=${pid} (pidfile=${PIDFILE}). Use STOP=1 or ACTION=stop to terminate." >&2
    exit 2
  fi
  # stale pidfile: process dead, remove and proceed
  rm -f "${PIDFILE}" 2>/dev/null || true
fi

mkdir -p "$OUT_DIR"
echo $$ > "$PIDFILE"

cleanup() {
  rm -f "$PIDFILE" 2>/dev/null || true
}
trap cleanup EXIT

rotate_logs() {
  # keep last MAX_LOGS logs, delete older
  ls -1t "$OUT_DIR"/P78_TICK_*.log 2>/dev/null | tail -n +"$((MAX_LOGS+1))" | xargs -I{} rm -f "{}" 2>/dev/null || true
}

tick() {
  local ts
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  local tick_dir="$OUT_DIR/tick_${ts}"
  mkdir -p "$tick_dir"

  # run P76 (go/no-go); write stdout/stderr to log
  OUT_DIR_OVERRIDE="$tick_dir" RUN_ID_OVERRIDE="${RUN_ID}_${ts}" MODE_OVERRIDE="$MODE" ITERATIONS_OVERRIDE="1" INTERVAL_OVERRIDE="0" \
    bash scripts/ops/online_readiness_go_no_go_v1.sh >"$OUT_DIR/P78_TICK_${ts}.log" 2>&1 || true

  rotate_logs

  # lightweight marker
  echo "P78_TICK_OK ts=$ts mode=$MODE out_dir=$tick_dir" >>"$OUT_DIR/P78_SUPERVISOR.ndjson"
}

n=0
while :; do
  tick
  n="$((n+1))"
  if [ "$ITERATIONS" -ne 0 ] && [ "$n" -ge "$ITERATIONS" ]; then
    break
  fi
  [ "$INTERVAL" -eq 0 ] || sleep "$INTERVAL"
done
