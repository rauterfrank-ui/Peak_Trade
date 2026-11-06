#!/usr/bin/env bash
set -euo pipefail

# Online Readiness Daemon v1 (paper/shadow only)
# Uses: scripts/ops/run_online_readiness_now.sh (P76 wrapper -> P71 -> P72 -> P76)

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

# --- config (env) ---
MODE="${MODE:-shadow}"                 # shadow|paper (live/record are blocked in stack)
INTERVAL_SEC="${INTERVAL_SEC:-60}"    # sleep between ticks
MAX_TICKS="${MAX_TICKS:-0}"           # 0 = run forever
OUT_DIR_BASE="${OUT_DIR_BASE:-out/ops/online_readiness_daemon}"  # base dir for tick outputs
RUN_ID_PREFIX="${RUN_ID_PREFIX:-p77}"  # prefix used for per-tick run_id
PIDFILE="${PIDFILE:-/tmp/peaktrade_online_readiness_daemon_v1.pid}"
LOGFILE="${LOGFILE:-/tmp/peaktrade_online_readiness_daemon_v1.log}"

# --- guards ---
case "$MODE" in
  shadow|paper) ;;
  *) echo "ERR: MODE must be shadow|paper (got: $MODE)" >&2; exit 2;;
esac

if [ -e "$PIDFILE" ]; then
  oldpid="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [ -n "${oldpid:-}" ] && kill -0 "$oldpid" 2>/dev/null; then
    echo "ERR: daemon already running pid=$oldpid (pidfile=$PIDFILE)" >&2
    exit 2
  fi
fi

mkdir -p "$(dirname "$PIDFILE")" "$(dirname "$LOGFILE")" "$OUT_DIR_BASE"
echo $$ > "$PIDFILE"

cleanup() {
  rm -f "$PIDFILE" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "P77_DAEMON_START pid=$$ mode=$MODE out_dir_base=$OUT_DIR_BASE interval_sec=$INTERVAL_SEC max_ticks=$MAX_TICKS" | tee -a "$LOGFILE"

tick=0
while :; do
  tick=$((tick + 1))
  if [ "$MAX_TICKS" -ne 0 ] && [ "$tick" -gt "$MAX_TICKS" ]; then
    echo "P77_DAEMON_STOP reason=max_ticks tick=$tick" | tee -a "$LOGFILE"
    break
  fi

  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  run_id="${RUN_ID_PREFIX}_${ts}_t$(printf "%04d" "$tick")"
  out_dir="${OUT_DIR_BASE}/${run_id}"

  mkdir -p "$out_dir"

  # run_online_readiness_now uses OUT_DIR, RUN_ID, MODE, ITERATIONS, INTERVAL
  OUT_DIR="$out_dir" RUN_ID="$run_id" MODE="$MODE" ITERATIONS="1" INTERVAL="0" \
    bash scripts/ops/run_online_readiness_now.sh \
      >"$out_dir/P77_TICK.log" 2>&1 || {
        rc=$?
        echo "P77_TICK_FAIL tick=$tick rc=$rc out_dir=$out_dir" | tee -a "$LOGFILE"
        # keep going; operator can inspect out_dir
      }

  echo "P77_TICK_OK tick=$tick out_dir=$out_dir" | tee -a "$LOGFILE"

  if [ "$INTERVAL_SEC" -gt 0 ]; then
    sleep "$INTERVAL_SEC"
  fi
done

echo "P77_DAEMON_EXIT pid=$$" | tee -a "$LOGFILE"
