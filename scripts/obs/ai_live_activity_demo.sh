#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# Deterministic local demo: ensure AI decision activity is non-empty and run_id-scoped.
# - No watch loops. Bounded waits only.
# - File-backed evidence (OUT dir) + PASS/FAIL.
#
# Defaults assume current repo reality:
# - exporter on :9110
# - prometheus-local on :9092
#
# Env overrides:
# - PROM_URL, EXPORTER_URL, AI_LIVE_PORT
# - RUN_ID (default: demo), COMPONENT (default: execution_watch)
# - VERIFY_OUT_DIR / OUT_DIR
# - EVENTS_JSONL (if you want a fixed path; default: <OUT>/ai_live_demo.jsonl)
# - SKIP_EXPORTER_START=1 (use an already-running exporter; requires EXPORTER_URL)
# - SKIP_PORT_CHECK=1 (for hermetic tests)

PROM_URL="${PROM_URL:-http://127.0.0.1:9092}"
AI_LIVE_PORT="${AI_LIVE_PORT:-9110}"
EXPORTER_URL="${EXPORTER_URL:-http://127.0.0.1:${AI_LIVE_PORT}/metrics}"

RUN_ID="${RUN_ID:-demo}"
COMPONENT="${COMPONENT:-execution_watch}"

SKIP_EXPORTER_START="${SKIP_EXPORTER_START:-0}"
SKIP_PORT_CHECK="${SKIP_PORT_CHECK:-0}"

STAMP_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${VERIFY_OUT_DIR:-${OUT_DIR:-.local_tmp/ai_live_activity_demo_${STAMP_UTC}}}"
mkdir -p "$OUT"

EVENTS_JSONL="${EVENTS_JSONL:-$OUT/ai_live_demo.jsonl}"
mkdir -p "$(dirname "$EVENTS_JSONL")" 2>/dev/null || true
touch "$EVENTS_JSONL"

resolve_py_cmd() {
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

pass() { echo "PASS|$1|$2"; }
info() { echo "INFO|$1|$2"; }
fail() { echo "FAIL|$1|$2" >&2; echo "NEXT|$3" >&2; exit 1; }

tcp_connect_ok() {
  local host="$1"
  local port="$2"
  "${PY_ARR[@]}" - "$host" "$port" >/dev/null 2>&1 <<'PY'
import socket, sys
host = sys.argv[1]
port = int(sys.argv[2])
with socket.create_connection((host, port), timeout=0.4):
    pass
PY
}

port_check() {
  local port="$1"
  if [[ "${SKIP_PORT_CHECK}" = "1" ]]; then
    info "port.check.skip" "SKIP_PORT_CHECK=1"
    return 0
  fi
  if tcp_connect_ok "127.0.0.1" "$port"; then
    pass "port.open" ":$port"
    return 0
  fi
  fail "port.open" ":$port not reachable" "Start required service or free port"
}

echo "==> AI Live Activity Demo (snapshot-only)"
info "repo.root" "$(pwd)"
git status -sb || true
info "env" "PROM_URL=$PROM_URL EXPORTER_URL=$EXPORTER_URL OUT=$OUT RUN_ID=$RUN_ID COMPONENT=$COMPONENT SKIP_EXPORTER_START=$SKIP_EXPORTER_START"

{
  echo "timestamp_utc=$STAMP_UTC"
  echo "repo_root=$(pwd)"
  echo "prom_url=$PROM_URL"
  echo "exporter_url=$EXPORTER_URL"
  echo "ai_live_port=$AI_LIVE_PORT"
  echo "run_id=$RUN_ID"
  echo "component=$COMPONENT"
  echo "events_jsonl=$EVENTS_JSONL"
  echo "py_cmd=$PY_CMD"
} >"$OUT/META.txt"

echo "==> Preflight: port checks"
port_check 9092
port_check "$AI_LIVE_PORT"

echo "==> Preflight: Prometheus ready (snapshot)"
curl -fsS "$PROM_URL/-/ready" >"$OUT/prom_ready.txt" 2>"$OUT/prom_ready.err" || fail "prometheus.ready" "Prometheus not ready: $PROM_URL/-/ready" "Start prometheus-local (:9092)"
pass "prometheus.ready" "$PROM_URL/-/ready"

EXPORTER_PID=""
cleanup() {
  if [[ -n "${EXPORTER_PID:-}" ]]; then
    kill "$EXPORTER_PID" >/dev/null 2>&1 || true
    wait "$EXPORTER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

if [[ "$SKIP_EXPORTER_START" != "1" ]]; then
  echo "==> Start exporter (background) on :$AI_LIVE_PORT"
  PEAK_TRADE_AI_EVENTS_JSONL="$EVENTS_JSONL" \
  PEAK_TRADE_AI_RUN_ID="$RUN_ID" \
  PEAK_TRADE_AI_COMPONENT="$COMPONENT" \
  PEAK_TRADE_AI_EXPORTER_PORT="$AI_LIVE_PORT" \
  "${PY_ARR[@]}" scripts/obs/ai_live_exporter.py --port "$AI_LIVE_PORT" >"$OUT/exporter.log" 2>&1 &
  EXPORTER_PID="$!"
  echo "$EXPORTER_PID" >"$OUT/exporter.pid"
  sleep 0.2
fi

echo "==> Wait for exporter /metrics (bounded)"
MAX_RETRIES="${MAX_RETRIES:-30}"
RETRY_SLEEP_S="${RETRY_SLEEP_S:-0.2}"
ok=0
for _ in $(seq 1 "$MAX_RETRIES"); do
  if curl -fsS "$EXPORTER_URL" >/dev/null 2>&1; then
    ok=1
    break
  fi
  sleep "$RETRY_SLEEP_S"
done
if [[ "$ok" != "1" ]]; then
  fail "exporter.http" "Exporter not reachable: $EXPORTER_URL" "Ensure exporter is running on :9110 (or set EXPORTER_URL + SKIP_EXPORTER_START=1)"
fi
pass "exporter.http" "$EXPORTER_URL"

echo "==> Scrape exporter before emit (file-backed)"
curl -fsS "$EXPORTER_URL" >"$OUT/exporter_metrics_before.txt" 2>"$OUT/exporter_metrics_before.err" || true

echo "==> Emit deterministic activity (>=1 accept + >=1 reject)"
"${PY_ARR[@]}" scripts/obs/emit_ai_live_sample_events.py --out "$EVENTS_JSONL" --n 2 --interval-ms 0 --run-id "$RUN_ID" --component "$COMPONENT" >"$OUT/emitter.out" 2>&1 || fail "emitter" "emit_ai_live_sample_events failed" "Inspect $OUT/emitter.out"
pass "emitter" "wrote 2 events to $EVENTS_JSONL"

sleep 0.3

echo "==> Scrape exporter after emit (file-backed)"
curl -fsS "$EXPORTER_URL" >"$OUT/exporter_metrics.txt" 2>"$OUT/exporter_metrics.err" || true

"${PY_ARR[@]}" - "$OUT/exporter_metrics.txt" "$RUN_ID" <<'PY'
import sys
txt_path=sys.argv[1]
run_id=sys.argv[2]
txt=open(txt_path,"r",encoding="utf-8",errors="replace").read()
has_accept=f'decision="accept"' in txt and f'run_id="{run_id}"' in txt and "peaktrade_ai_decisions_total" in txt
has_reject=f'decision="reject"' in txt and f'run_id="{run_id}"' in txt and "peaktrade_ai_decisions_total" in txt
if not (has_accept and has_reject):
    raise SystemExit(1)
PY
pass "exporter.activity" "decisions_total includes accept+reject for run_id=$RUN_ID"

echo "==> Prometheus query snapshots (file-backed JSON)"
mkdir -p "$OUT/prom"

q() {
  local name="$1"
  local expr="$2"
  bash scripts/obs/_prom_query_json.sh --base "$PROM_URL" --query "$expr" --out "$OUT/prom/$name.json" --retries "${PROM_QUERY_MAX_ATTEMPTS:-3}" --timeout "${PROM_QUERY_TIMEOUT_S:-10}" >/dev/null
}

q up_jobs 'up{job=~"ai_live|peak_trade_web|shadow_mvs"}'
q hb 'peaktrade_ai_live_heartbeat'
q decisions 'peaktrade_ai_decisions_total'
q actions 'peaktrade_ai_actions_total'
q run_id_count 'count(count by (run_id) (peaktrade_ai_decisions_total))'
q last_event_ts_by_run_id 'peaktrade_ai_last_event_timestamp_seconds_by_run_id'

echo "==> Evidence summary"
"${PY_ARR[@]}" - "$OUT" <<'PY'
import json, os, sys, datetime
out=sys.argv[1]
prom=os.path.join(out,"prom")

def rc(name):
    p=os.path.join(prom,f"{name}.json")
    try:
        doc=json.load(open(p,"r",encoding="utf-8"))
        res=((doc.get("data") or {}).get("result") or [])
        return len(res)
    except Exception:
        return -1

rows=["up_jobs","hb","decisions","actions","run_id_count","last_event_ts_by_run_id"]
counts={k:rc(k) for k in rows}
hard_ok = True
reasons=[]
if counts["decisions"] <= 0:
    hard_ok=False; reasons.append("prom_decisions_empty")
if counts["run_id_count"] <= 0:
    hard_ok=False; reasons.append("prom_run_id_count_empty")

lines=[]
lines.append(f"timestamp_utc={datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")
lines.append(f"hard_ok={hard_ok}")
for k in rows:
    lines.append(f"{k}_rc={counts[k]}")
lines.append("hard_fail_reasons=" + (",".join(reasons) if reasons else ""))
open(os.path.join(out,"AI_ACTIVITY_DEMO_SUMMARY.txt"),"w",encoding="utf-8").write("\n".join(lines)+"\n")
print("\n".join(lines))
raise SystemExit(0 if hard_ok else 1)
PY

echo ""
echo "Evidence dir: $OUT"
echo "Post these:"
echo "  $OUT/AI_ACTIVITY_DEMO_SUMMARY.txt"
echo "  $OUT/prom/decisions.json"
echo "  $OUT/prom/run_id_count.json"
echo ""
echo "RESULT=PASS"
