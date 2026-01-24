#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

RUNTIME_DIR="scripts/obs/.runtime"
JSONL_PATH="${JSONL_PATH:-$RUNTIME_DIR/ai_live_smoke_test.jsonl}"
#
# AI Live Port Contract v1:
# - Prometheus-local scrapes job=ai_live at host.docker.internal:9110
# - Therefore, local ops scripts MUST use port 9110 by default and MUST NOT
#   silently fall back to other ports (would cause false negatives in Prom/Grafana).
AI_LIVE_PORT="${AI_LIVE_PORT:-9110}"
EXPORTER_PORT="${PEAK_TRADE_AI_EXPORTER_PORT:-$AI_LIVE_PORT}"
PROM_URL="${PROM_URL:-http://127.0.0.1:9092}"
JOB_NAME="${JOB_NAME:-ai_live}"

resolve_py_cmd() {
  # Deterministic Python environment contract:
  # - If $PY_CMD is set, use it.
  # - Else prefer uv-managed env (ensures prometheus_client available for exporter).
  # - Else fall back to system python3.
  if [[ -n "${PY_CMD:-}" ]]; then
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
echo "PY_CMD=${PY_CMD}"

mkdir -p "$RUNTIME_DIR"
rm -f "$JSONL_PATH"
touch "$JSONL_PATH"  # ensure exporter won't miss first events (tail-from-end)

pass() { echo "PASS|$1|$2"; }
fail() { echo "FAIL|$1|$2" >&2; echo "NEXT|$3" >&2; exit 1; }

port_listeners_best_effort() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true
  fi
}

port_is_in_use() {
  local port="$1"
  # Prefer lsof (macOS compatible); fallback to python socket bind probe.
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi
  "${PY_ARR[@]}" - "$port" <<'PY'
import socket, sys
port = int(sys.argv[1])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", port))
except OSError:
    raise SystemExit(0)  # in use
finally:
    try:
        s.close()
    except Exception:
        pass
raise SystemExit(1)  # free
PY
}

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
  "${PY_ARR[@]}" scripts/obs/ai_live_exporter.py >"$log_path" 2>&1 &
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

if port_is_in_use "$EXPORTER_PORT"; then
  echo "ERROR|port_contract|AI Live exporter port is in use: :$EXPORTER_PORT" >&2
  echo "" >&2
  echo "Best-effort process info (lsof):" >&2
  port_listeners_best_effort "$EXPORTER_PORT" >&2
  echo "" >&2
  echo "AI Live Port Contract v1:" >&2
  echo "- Prometheus-local expects job=ai_live at host.docker.internal:9110 (default local ops contract)." >&2
  echo "- This smoke test will NOT fall back to another port, because that would break Prom/Grafana verification." >&2
  echo "" >&2
  echo "How to resolve:" >&2
  echo "- Stop the process currently listening on :$EXPORTER_PORT (recommended)." >&2
  echo "- Or (not recommended) run ai_live exporter elsewhere AND explicitly update Prometheus scrape target to match." >&2
  echo "" >&2
  fail "exporter.port" "Port :$EXPORTER_PORT busy (contract violation)" "Free port 9110 and re-run"
fi

if ! start_exporter "$EXPORTER_PORT"; then
  echo "--- exporter log (tail) ---" >&2
  tail -n 120 "$RUNTIME_DIR/ai_live_smoke_exporter.log" >&2 || true
  fail "exporter.start" "Exporter failed to start on :$EXPORTER_PORT" "Check python env / dependencies"
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
"${PY_ARR[@]}" scripts/obs/emit_ai_live_sample_events.py --out "$JSONL_PATH" --n 50 --interval-ms 200 >/dev/null

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
