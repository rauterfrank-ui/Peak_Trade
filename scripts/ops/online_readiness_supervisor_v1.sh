#!/usr/bin/env bash
# P78/P80/P81 — Online Readiness Supervisor v1
# Exit codes: 0 ok, 2 usage, 3 not_allowed, 4 gate_fail, 5 internal
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

MODE="${MODE:-shadow}"              # paper|shadow only
OUT_DIR="${OUT_DIR:-out/ops/p78_supervisor}"
RUN_ID="${RUN_ID:-p78}"
INTERVAL="${INTERVAL:-30}"          # seconds
ITERATIONS="${ITERATIONS:-0}"       # 0 = infinite
PIDFILE="${PIDFILE:-/tmp/p78_online_readiness_supervisor.pid}"
LOCKFILE="${LOCKFILE:-/tmp/p78_online_readiness_supervisor.lock}"
MAX_LOGS="${MAX_LOGS:-50}"
MAX_TICK_DIRS="${MAX_TICK_DIRS:-100}"   # P81: max tick_* dirs to retain
BACKOFF_SEC="${BACKOFF_SEC:-5}"         # P81: sleep after transient failure
STOP="${STOP:-0}"                   # 1 = stop mode (terminate existing supervisor)
ACTION="${ACTION:-}"                # "stop" = same as STOP=1
CHECK_MODE="${CHECK_MODE:-p86}"     # P87: p76 = go/no-go only; p86 = readiness+ingest gate (default)

# Exit code constants
EXIT_OK=0
EXIT_USAGE=2
EXIT_NOT_ALLOWED=3
EXIT_GATE_FAIL=4
EXIT_INTERNAL=5

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

# --- P81: flock/lockfile (prevent double-start without pidfile race) ---
if command -v flock >/dev/null 2>&1; then
  exec 200>"${LOCKFILE}"
  if ! flock -x -n 200; then
    echo "ERR: could not acquire lock (another supervisor instance running?) lockfile=${LOCKFILE}" >&2
    exit $EXIT_NOT_ALLOWED
  fi
fi

# --- P80: Idempotent start (refuse double-start, handle stale pidfile) ---
if [ -e "${PIDFILE}" ]; then
  pid="$(cat "${PIDFILE}" 2>/dev/null || true)"
  if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
    echo "ERR: supervisor already running pid=${pid} (pidfile=${PIDFILE}). Use STOP=1 or ACTION=stop to terminate." >&2
    exit $EXIT_NOT_ALLOWED
  fi
  rm -f "${PIDFILE}" 2>/dev/null || true
fi

mkdir -p "$OUT_DIR"
echo $$ > "$PIDFILE"

# --- P81: trap cleanup (pidfile + lockfile) ---
cleanup() {
  rm -f "$PIDFILE" 2>/dev/null || true
  if [ -n "${LOCKFILE:-}" ] && [ -e "${LOCKFILE}" ]; then
    rm -f "${LOCKFILE}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

# --- P81: write meta.json ---
write_meta() {
  local last_tick="${1:-}"
  local last_ts="${2:-}"
  python3 - "${OUT_DIR}" "${MODE}" "${RUN_ID}" "$$" "${last_tick}" "${last_ts}" <<'PY'
import json, sys, os
out_dir, mode, run_id, pid, last_tick, last_ts = sys.argv[1:7]
path = os.path.join(out_dir, "supervisor_meta.json")
doc = {
    "version": "p81_supervisor_meta_v1",
    "pid": int(pid),
    "mode": mode,
    "run_id": run_id,
    "last_tick": last_tick or None,
    "last_tick_ts": last_ts or None,
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(doc, f, indent=2)
PY
}

write_meta "" ""

# --- P81: rotate policy (max logs + max tick dirs) ---
rotate_logs() {
  ls -1t "$OUT_DIR"/P78_TICK_*.log 2>/dev/null | tail -n +"$((MAX_LOGS+1))" | xargs -I{} rm -f "{}" 2>/dev/null || true
}
rotate_tick_dirs() {
  ls -1td "$OUT_DIR"/tick_* 2>/dev/null | tail -n +"$((MAX_TICK_DIRS+1))" | xargs -I{} rm -rf "{}" 2>/dev/null || true
}

tick() {
  local ts
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  local tick_dir="$OUT_DIR/tick_${ts}"
  mkdir -p "$tick_dir"

  local rc=0
  if [ "${CHECK_MODE}" = "p86" ]; then
    MODE="$MODE" RUN_ID="${RUN_ID}_${ts}" OUT_DIR="$tick_dir" \
      bash scripts/ops/p86_gate_v1.sh >"$OUT_DIR/P78_TICK_${ts}.log" 2>&1 || rc=$?
  else
    OUT_DIR_OVERRIDE="$tick_dir" RUN_ID_OVERRIDE="${RUN_ID}_${ts}" MODE_OVERRIDE="$MODE" ITERATIONS_OVERRIDE="1" INTERVAL_OVERRIDE="0" \
      bash scripts/ops/online_readiness_go_no_go_v1.sh >"$OUT_DIR/P78_TICK_${ts}.log" 2>&1 || rc=$?
  fi

  rotate_logs
  rotate_tick_dirs

  echo "P78_TICK_OK ts=$ts mode=$MODE out_dir=$tick_dir rc=$rc" >>"$OUT_DIR/P78_SUPERVISOR.ndjson"
  write_meta "tick_${ts}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  # --- P81: jitter/backoff on transient failure ---
  if [ "$rc" -ne 0 ] && [ "${BACKOFF_SEC}" -gt 0 ]; then
    echo "P81_BACKOFF: tick rc=$rc sleeping ${BACKOFF_SEC}s" >>"$OUT_DIR/P78_SUPERVISOR.ndjson"
    sleep "${BACKOFF_SEC}"
  fi
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
