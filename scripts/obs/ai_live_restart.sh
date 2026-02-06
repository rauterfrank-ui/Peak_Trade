#!/usr/bin/env bash
# Start or restore the AI Live Prometheus exporter on :9110 (or given port).
# Prometheus-local scrapes job=ai_live at host.docker.internal:9110; do not change port without updating scrape config.
#
# Usage: ./scripts/obs/ai_live_restart.sh [PORT]
# Default PORT=9110.
#
# If something is already listening on the port, this script kills it and starts a fresh exporter.
# Requires PEAK_TRADE_AI_EVENTS_JSONL (script creates an empty file if unset for heartbeat-only).
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

PORT="${1:-9110}"
RUNTIME_DIR="scripts/obs/.runtime"
JSONL_PATH="${PEAK_TRADE_AI_EVENTS_JSONL:-$RUNTIME_DIR/ai_live_restart.jsonl}"
LOG_PATH="$RUNTIME_DIR/ai_live_restart.log"
PID_PATH="$RUNTIME_DIR/ai_live_restart.pid"

resolve_py_cmd() {
  if [[ -n "${PY_CMD:-}" ]]; then
    return 0
  fi
  # Deterministic: prefer repo-local obs venv (no uv, no global pip).
  REPO_ROOT="$(pwd)"
  if [[ -x "$REPO_ROOT/.venv_obs/bin/python" ]]; then
    PY_CMD="$REPO_ROOT/.venv_obs/bin/python"
    return 0
  fi
  if command -v uv >/dev/null 2>&1; then
    PY_CMD="uv run python"
  else
    PY_CMD="python3"
  fi
}
resolve_py_cmd
read -r -a PY_ARR <<<"${PY_CMD}"

mkdir -p "$RUNTIME_DIR"
touch "$JSONL_PATH"

# Kill any process already listening on PORT so we can bind.
kill_listeners() {
  local port="$1"
  local pids
  if ! command -v lsof >/dev/null 2>&1; then
    return 0
  fi
  pids=$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)
  if [[ -n "$pids" ]]; then
    echo "Killing existing listener(s) on :$port (PIDs: $pids)" >&2
    echo "$pids" | xargs kill 2>/dev/null || true
    sleep 0.5
  fi
}

kill_listeners "$PORT"

# Start exporter (same env contract as ai_live_smoke_test.sh / ai_live_activity_demo.sh)
PEAK_TRADE_AI_EVENTS_JSONL="$JSONL_PATH" \
PEAK_TRADE_AI_RUN_ID="${PEAK_TRADE_AI_RUN_ID:-restart}" \
PEAK_TRADE_AI_COMPONENT="${PEAK_TRADE_AI_COMPONENT:-execution_watch}" \
PEAK_TRADE_AI_EXPORTER_PORT="$PORT" \
"${PY_ARR[@]}" scripts/obs/ai_live_exporter.py >>"$LOG_PATH" 2>&1 &
EXPORTER_PID=$!
echo "$EXPORTER_PID" >"$PID_PATH"
sleep 0.5

if ! kill -0 "$EXPORTER_PID" 2>/dev/null; then
  echo "Exporter failed to start. Last lines of $LOG_PATH:" >&2
  tail -n 30 "$LOG_PATH" >&2
  echo "" >&2
  echo "If you see 'prometheus_client not available': install deps (e.g. pip install prometheus-client) or use a venv/uv Python and set PY_CMD (e.g. PY_CMD='uv run python' or PY_CMD='/path/to/venv/bin/python')." >&2
  exit 1
fi

echo "ai_live_exporter started port=$PORT pid=$EXPORTER_PID log=$LOG_PATH pidfile=$PID_PATH"
echo "Metrics: http://127.0.0.1:${PORT}/metrics"
