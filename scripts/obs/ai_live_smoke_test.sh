#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

RUNTIME_DIR="scripts/obs/.runtime"
JSONL_PATH="${JSONL_PATH:-$RUNTIME_DIR/ai_live_smoke_test.jsonl}"
EXPORTER_PORT="${PEAK_TRADE_AI_EXPORTER_PORT:-9110}"
PROM_URL="${PROM_URL:-http://127.0.0.1:9092}"
JOB_NAME="${JOB_NAME:-ai_live}"

if command -v uv >/dev/null 2>&1; then
  PYTHON_CMD=(uv run python)
else
  PYTHON_CMD=(python3)
fi

mkdir -p "$RUNTIME_DIR"
rm -f "$JSONL_PATH"
touch "$JSONL_PATH"  # ensure exporter won't miss first events (tail-from-end)

pass() { echo "PASS|$1|$2"; }
fail() { echo "FAIL|$1|$2" >&2; echo "NEXT|$3" >&2; exit 1; }

cleanup() {
  if [[ -n "${EXPORTER_PID:-}" ]]; then
    kill "$EXPORTER_PID" >/dev/null 2>&1 || true
    wait "$EXPORTER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

start_exporter() {
  local port="$1"
  local log_path="$RUNTIME_DIR/ai_live_smoke_exporter.log"
  rm -f "$log_path"
  PEAK_TRADE_AI_EVENTS_JSONL="$JSONL_PATH" \
  PEAK_TRADE_AI_RUN_ID="demo" \
  PEAK_TRADE_AI_COMPONENT="execution_watch" \
  PEAK_TRADE_AI_EXPORTER_PORT="$port" \
  "${PYTHON_CMD[@]}" scripts/obs/ai_live_exporter.py >"$log_path" 2>&1 &
  EXPORTER_PID="$!"
  sleep 0.2
  if kill -0 "$EXPORTER_PID" >/dev/null 2>&1; then
    EXPORTER_PORT="$port"
    EXPORTER_URL="http://127.0.0.1:${EXPORTER_PORT}/metrics"
    return 0
  fi
  return 1
}

echo "==> Repo: $(pwd)"
echo "==> JSONL: $JSONL_PATH"
echo "==> Start exporter (background)"

started=0
for port in $(seq "$EXPORTER_PORT" $((EXPORTER_PORT + 20))); do
  if start_exporter "$port"; then
    started=1
    break
  fi
  if grep -q "Address already in use" "$RUNTIME_DIR/ai_live_smoke_exporter.log" 2>/dev/null; then
    echo "WARN|exporter.port|Port $port busy; trying $((port + 1))"
    continue
  fi
  echo "--- exporter log (tail) ---" >&2
  tail -n 120 "$RUNTIME_DIR/ai_live_smoke_exporter.log" >&2 || true
  fail "exporter.start" "Exporter failed to start (non-port-conflict)" "Check python env / dependencies"
done
if [[ "$started" != "1" ]]; then
  echo "--- exporter log (tail) ---" >&2
  tail -n 120 "$RUNTIME_DIR/ai_live_smoke_exporter.log" >&2 || true
  fail "exporter.start" "No free port in range ${EXPORTER_PORT}..$((EXPORTER_PORT + 20))" "Free a port or set PEAK_TRADE_AI_EXPORTER_PORT"
fi

echo "==> Exporter: $EXPORTER_URL (pid=$EXPORTER_PID)"

echo "==> Wait for /metrics"
MAX_RETRIES="${MAX_RETRIES:-20}"
RETRY_SLEEP_S="${RETRY_SLEEP_S:-0.5}"
ok=0
for _ in $(seq 1 "$MAX_RETRIES"); do
  if curl -fsS "$EXPORTER_URL" >/dev/null 2>&1; then
    ok=1
    break
  fi
  sleep "$RETRY_SLEEP_S"
done
if [[ "$ok" != "1" ]]; then
  echo "--- exporter log (tail) ---" >&2
  tail -n 80 "$RUNTIME_DIR/ai_live_smoke_exporter.log" >&2 || true
  fail "exporter.http" "Exporter not reachable: $EXPORTER_URL" "Start exporter / port conflict"
fi
pass "exporter.http" "/metrics reachable"

sum_decisions() {
  curl -fsS "$EXPORTER_URL" | awk '
    /^peaktrade_ai_decisions_total(\{| )/ { s += $NF }
    END { if (s == "") s = 0; printf "%.0f\n", s }
  '
}

before="$(sum_decisions)"
echo "==> decisions_total (before) = $before"

echo "==> Emit sample events (<=10s visible)"
"${PYTHON_CMD[@]}" scripts/obs/emit_ai_live_sample_events.py --out "$JSONL_PATH" --n 50 --interval-ms 200 >/dev/null

sleep 1
after="$(sum_decisions)"
echo "==> decisions_total (after)  = $after"

if [[ "$after" -le "$before" ]]; then
  echo "--- exporter log (tail) ---" >&2
  tail -n 120 "$RUNTIME_DIR/ai_live_smoke_exporter.log" >&2 || true
  fail "metrics.delta" "Expected decisions_total to increase (before=$before after=$after)" "Exporter mapping / tailing issue"
fi
pass "metrics.delta" "decisions_total increased (before=$before after=$after)"

echo "==> Optional: Prometheus query (best-effort)"
if curl -fsS "$PROM_URL/-/ready" >/dev/null 2>&1; then
  if bash scripts/obs/_prom_query_json.sh --base "$PROM_URL" --query "up{job=\"$JOB_NAME\"}" --retries 2 >/dev/null 2>&1; then
    pass "prometheus.query" "up{job=\"$JOB_NAME\"} query ok"
  else
    echo "WARN|prometheus.query|Prometheus reachable but query failed (job may be missing until reload/restart)."
  fi
else
  echo "INFO|prometheus.skip|Prometheus not reachable at $PROM_URL"
fi

echo ""
echo "NEXT|Open Grafana dashboard UID peaktrade-execution-watch-overview and watch Row 'AI Live' (should move within 10s)."
echo "RESULT=PASS"
