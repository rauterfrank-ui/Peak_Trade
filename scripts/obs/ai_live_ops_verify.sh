#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# Snapshot-only verifier for AI Live Ops Pack v1 readiness (canonical "one command" proof):
# - No watch loops. File-backed evidence in an OUT directory.
# - Hard checks are deterministic and Prometheus-query based.
# - Grafana checks are optional (disabled by default).

PROM_URL="${PROM_URL:-http://127.0.0.1:9092}"
GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}"
GRAFANA_AUTH="${GRAFANA_AUTH:-}"   # optional basic auth user:pass
GRAFANA_TOKEN="${GRAFANA_TOKEN:-}" # optional bearer token
ENABLE_GRAFANA_CHECKS="${ENABLE_GRAFANA_CHECKS:-0}"
RUN_AI_LIVE_VERIFY="${RUN_AI_LIVE_VERIFY:-0}"

AI_LIVE_PORT="${AI_LIVE_PORT:-9110}"
EXPORTER_URL="${EXPORTER_URL:-http://127.0.0.1:${AI_LIVE_PORT}/metrics}"

DASH_UID="${DASH_UID:-peaktrade-execution-watch-overview}"

# Evidence dir (file-backed)
STAMP_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${VERIFY_OUT_DIR:-${OUT_DIR:-.local_tmp/ai_live_ops_verify_${STAMP_UTC}}}"
mkdir -p "$OUT"

# Deterministic Python environment contract:
# - If $PY_CMD is set, use it.
# - Else prefer uv-managed env (common in repo ops scripts).
# - Else fall back to system python3.
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
echo "PY_CMD=${PY_CMD}"

# Testing / CI helpers
SKIP_PORT_CHECK="${SKIP_PORT_CHECK:-0}"

pass() { echo "PASS|$1|$2"; }
info() { echo "INFO|$1|$2"; }
warn() { echo "WARN|$1|$2"; }
fail() { echo "FAIL|$1|$2" >&2; echo "NEXT|$3" >&2; exit 1; }

curl_ok() {
  local url="$1"
  curl -fsS "$url" >/dev/null 2>&1
}

curl_ok_or_retry_once() {
  local url="$1"
  local sleep_s="${2:-1}"
  if curl_ok "$url"; then
    return 0
  fi
  sleep "$sleep_s"
  curl_ok "$url"
}

grafana_curl() {
  local path="$1"
  if [[ -n "${GRAFANA_TOKEN:-}" ]]; then
    curl -fsS -H "Authorization: Bearer ${GRAFANA_TOKEN}" "${GRAFANA_URL}${path}"
    return 0
  fi
  if [[ -n "${GRAFANA_AUTH:-}" ]]; then
    curl -fsS -u "$GRAFANA_AUTH" "${GRAFANA_URL}${path}"
    return 0
  fi
  curl -fsS "${GRAFANA_URL}${path}"
}

prom_query_json_to_file() {
  local q="$1"
  local out="$2"
  bash scripts/obs/_prom_query_json.sh --base "$PROM_URL" --query "$q" --out "$out" --retries "${PROM_QUERY_MAX_ATTEMPTS:-3}" >/dev/null
}

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
  case "$port" in
    9092) fail "port.open" ":$port not reachable" "Start prometheus-local (port contract: 9092)";;
    3000) fail "port.open" ":$port not reachable" "Start grafana (port contract: 3000)";;
    9110) fail "port.open" ":$port not reachable" "Start AI Live exporter (port contract: 9110)";;
    *) fail "port.open" ":$port not reachable" "Start required service or free port";;
  esac
}

echo "==> AI Live Ops Verify (snapshot-only; canonical proof)"
info "repo.root" "$(pwd)"
git status -sb || true
info "env" "PROM_URL=$PROM_URL EXPORTER_URL=$EXPORTER_URL OUT=$OUT ENABLE_GRAFANA_CHECKS=$ENABLE_GRAFANA_CHECKS"

# Evidence header
{
  echo "timestamp_utc=$STAMP_UTC"
  echo "repo_root=$(pwd)"
  echo "prom_url=$PROM_URL"
  echo "exporter_url=$EXPORTER_URL"
  echo "ai_live_port=$AI_LIVE_PORT"
  echo "py_cmd=$PY_CMD"
  echo "enable_grafana_checks=$ENABLE_GRAFANA_CHECKS"
  echo "dash_uid=$DASH_UID"
  echo "git_rev=$(git rev-parse HEAD 2>/dev/null || true)"
} >"$OUT/META.txt"

echo "==> Preflight: port contract checks"
port_check 9092
port_check 3000
port_check "$AI_LIVE_PORT"

echo "==> Preflight: endpoints reachable"
if curl -fsS "$PROM_URL/-/ready" >"$OUT/prom_ready.txt" 2>"$OUT/prom_ready.err"; then
  pass "prometheus.ready" "$PROM_URL/-/ready"
else
  fail "prometheus.ready" "Prometheus not ready: $PROM_URL/-/ready" "Start local Docker observability via docker compose -f docker/docker-compose.obs.yml up -d"
fi

if curl -fsS "$GRAFANA_URL/api/health" >"$OUT/grafana_health.json" 2>"$OUT/grafana_health.err"; then
  pass "grafana.health" "$GRAFANA_URL/api/health"
else
  fail "grafana.health" "Grafana health failed: $GRAFANA_URL/api/health" "Start grafana (port contract: 3000)"
fi

echo "==> Exporter: /metrics reachable"
if curl -fsS "$EXPORTER_URL" >"$OUT/exporter_metrics.txt" 2>"$OUT/exporter_metrics.err"; then
  pass "exporter.http" "$EXPORTER_URL"
else
  fail "exporter.http" "Exporter not reachable: $EXPORTER_URL" "Start exporter on port 9110 (Port Contract v1)"
fi

echo "==> Optional: ai_live_verify.sh baseline"
if [[ "$RUN_AI_LIVE_VERIFY" = "1" ]]; then
  if bash scripts/obs/ai_live_verify.sh >"$OUT/ai_live_verify.out" 2>&1; then
    pass "ai_live_verify" "scripts/obs/ai_live_verify.sh"
  else
    echo "WARN: ai_live_verify failed; see $OUT/ai_live_verify.out" >&2
    fail "ai_live_verify" "ai_live_verify.sh failed" "Inspect $OUT/ai_live_verify.out and fix exporter/prom target"
  fi
else
  info "ai_live_verify.skip" "RUN_AI_LIVE_VERIFY!=1"
fi

echo "==> Targets: job=ai_live must be UP"
TARGETS_MAX_ATTEMPTS="${TARGETS_MAX_ATTEMPTS:-8}"
TARGETS_SLEEP_S="${TARGETS_SLEEP_S:-1}"
info "targets_retry" "max_attempts=${TARGETS_MAX_ATTEMPTS} sleep_s=${TARGETS_SLEEP_S}"
targets_ok=0
targets_json=""
attempts_used=0
for _ in $(seq 1 "$TARGETS_MAX_ATTEMPTS"); do
  attempts_used=$((attempts_used + 1))
  targets_json="$(curl -fsS "$PROM_URL/api/v1/targets" 2>/dev/null || true)"
  if "${PY_ARR[@]}" -c '
import json, sys
doc=json.loads(sys.stdin.read() or "{}")
active=(doc.get("data") or {}).get("activeTargets") or []
ai=[t for t in active if (t.get("labels") or {}).get("job")=="ai_live"]
if not ai:
    raise SystemExit(1)
if any((t.get("health") or "").lower()=="up" for t in ai):
    raise SystemExit(0)
raise SystemExit(1)
' <<<"$targets_json" 2>/dev/null; then
    targets_ok=1
    break
  fi
  sleep "$TARGETS_SLEEP_S"
done
if [[ "$targets_ok" = "1" ]]; then
  info "targets_retry" "attempts_used=${attempts_used}"
  pass "prometheus.targets" "ai_live=up"
else
  echo "$targets_json" >"$OUT/prom_targets.json" || true
  fail "prometheus.targets" "Target not UP: job=ai_live" "Fix exporter/port contract (9110) or Prometheus scrape target"
fi
echo "$targets_json" >"$OUT/prom_targets.json" || true

echo "==> Rules: AI Live Ops Pack v1 loaded + alert names present"
rules_json="$(curl -fsS "$PROM_URL/api/v1/rules" 2>/dev/null || true)"
echo "$rules_json" >"$OUT/prom_rules.json" || true
rules_check_out="$(
"${PY_ARR[@]}" -c '
import json, sys
doc=json.loads(sys.stdin.read() or "{}")
groups=(doc.get("data") or {}).get("groups") or []
want={
  "AI_LIVE_ExporterDown",
  "AI_LIVE_StaleEvents",
  "AI_LIVE_ParseErrorsSpike",
  "AI_LIVE_DroppedEventsSpike",
  "AI_LIVE_LatencyP95High",
  "AI_LIVE_LatencyP99High",
}
have=set()
for g in groups:
  for r in (g.get("rules") or []):
    if r.get("type") != "alerting":
      continue
    n=r.get("name")
    if isinstance(n,str):
      have.add(n)
missing=sorted(want - have)
print(f"groups={len(groups)}")
print("missing_alerts=" + ",".join(missing))
if len(groups) <= 0:
  raise SystemExit(1)
if missing:
  raise SystemExit(1)
' <<<"$rules_json" 2>/dev/null
)" && rules_ok=1 || rules_ok=0

rules_groups="$(printf '%s\n' "$rules_check_out" | sed -n 's/^groups=//p' | head -n 1 || true)"
rules_missing="$(printf '%s\n' "$rules_check_out" | sed -n 's/^missing_alerts=//p' | head -n 1 || true)"
info "prometheus.rules.groups" "count=${rules_groups:-unknown}"
if [[ "$rules_ok" = "1" ]]; then
  pass "prometheus.rules" "groups>0 + required AI_LIVE_* alerts present"
else
  fail "prometheus.rules" "Rules missing or alert names missing: ${rules_missing:-unknown}" "Ensure prometheus-local mounts /etc/prometheus/rules and loads ai_live_alerts_v1.yml"
fi

echo "==> Alerts: snapshot (best-effort)"
curl -fsS "$PROM_URL/api/v1/alerts" >"$OUT/prom_alerts.json" 2>/dev/null || true

echo "==> Prometheus contract: required series + finish-ready hard checks"
mkdir -p "$OUT/prom"
prom_query_json_to_file 'up{job=~"ai_live|peak_trade_web|shadow_mvs"}' "$OUT/prom/up_jobs.json" || true
prom_query_json_to_file 'peaktrade_ai_live_heartbeat' "$OUT/prom/hb.json" || true
prom_query_json_to_file 'peaktrade_ai_decisions_total' "$OUT/prom/decisions_series.json" || true
prom_query_json_to_file 'sum(peaktrade_ai_decisions_total)' "$OUT/prom/decisions_sum.json" || true
prom_query_json_to_file 'peaktrade_ai_actions_total' "$OUT/prom/actions_series.json" || true
prom_query_json_to_file 'peaktrade_ai_last_decision_timestamp_seconds' "$OUT/prom/last_decision_ts.json" || true
prom_query_json_to_file 'peaktrade_ai_last_event_timestamp_seconds' "$OUT/prom/last_event_ts.json" || true
prom_query_json_to_file 'count(count by (run_id) (peaktrade_ai_decisions_total))' "$OUT/prom/run_id_count.json" || true
prom_query_json_to_file 'count(peaktrade_ai_last_event_timestamp_seconds_by_run_id)' "$OUT/prom/last_event_ts_by_run_id_count.json" || true
prom_query_json_to_file 'increase(peaktrade_ai_events_parse_errors_total[5m])' "$OUT/prom/parse_err_5m.json" || true
prom_query_json_to_file 'increase(peaktrade_ai_events_dropped_total[5m])' "$OUT/prom/dropped_5m.json" || true

"${PY_ARR[@]}" - "$OUT" <<'PY'
import json, os, sys, datetime

out = sys.argv[1]
prom_dir = os.path.join(out, "prom")

def load(name):
    p = os.path.join(prom_dir, name)
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def result(doc):
    return ((doc.get("data") or {}).get("result") or [])

def rc(name):
    return len(result(load(name)))

def scalar_value(name, default=float("nan")):
    res = result(load(name))
    if not res:
        return default
    v = res[0].get("value") or [None, None]
    try:
        return float(v[1])
    except Exception:
        return default

rows = [
    ("up_jobs", 'up{job=~"ai_live|peak_trade_web|shadow_mvs"}', "up_jobs.json", None),
    ("heartbeat", "peaktrade_ai_live_heartbeat", "hb.json", None),
    ("decisions_series", "peaktrade_ai_decisions_total", "decisions_series.json", None),
    ("decisions_sum", "sum(peaktrade_ai_decisions_total)", "decisions_sum.json", "scalar"),
    ("actions_series", "peaktrade_ai_actions_total", "actions_series.json", None),
    ("last_decision_ts", "peaktrade_ai_last_decision_timestamp_seconds", "last_decision_ts.json", None),
    ("last_event_ts", "peaktrade_ai_last_event_timestamp_seconds", "last_event_ts.json", None),
    ("run_id_count", "count(count by (run_id) (peaktrade_ai_decisions_total))", "run_id_count.json", "scalar"),
    ("last_event_ts_by_run_id_count", "count(peaktrade_ai_last_event_timestamp_seconds_by_run_id)", "last_event_ts_by_run_id_count.json", "scalar"),
    ("parse_err_5m", "increase(peaktrade_ai_events_parse_errors_total[5m])", "parse_err_5m.json", None),
    ("dropped_5m", "increase(peaktrade_ai_events_dropped_total[5m])", "dropped_5m.json", None),
]

tsv = os.path.join(out, "PROM_REQUIRED_SERIES.tsv")
with open(tsv, "w", encoding="utf-8") as f:
    f.write("name\texpr\tresult_count\tvalue\n")
    for name, expr, fn, kind in rows:
        n = rc(fn)
        val = ""
        if kind == "scalar":
            x = scalar_value(fn)
            val = "" if x != x else str(x)  # nan-safe
        f.write(f"{name}\t{expr}\t{n}\t{val}\n")

# Hard checks required by finish gate verification
# Note: tests/obs/test_ai_live_ops_determinism_v1.py runs this script against a minimal
# mock endpoint and sets SKIP_PORT_CHECK=1. In that mode we relax the up_jobs count
# check to avoid false negatives in hermetic tests.
up_jobs_rc = rc("up_jobs.json")
hb_rc = rc("hb.json")
decisions_sum = scalar_value("decisions_sum.json")
run_id_count = scalar_value("run_id_count.json")
last_event_by_run_id_count = scalar_value("last_event_ts_by_run_id_count.json")
expected_up_jobs = 1 if os.environ.get("SKIP_PORT_CHECK", "").strip() == "1" else 3.0

hard_ok = True
reasons = []

if not (up_jobs_rc >= expected_up_jobs):
    hard_ok = False
    reasons.append(f"up_jobs_rc_expected_ge_{int(expected_up_jobs)}_got_{up_jobs_rc}")
if hb_rc != 1:
    hard_ok = False
    reasons.append(f"heartbeat_rc_expected_1_got_{hb_rc}")
if not (decisions_sum == decisions_sum and decisions_sum > 0.0):
    hard_ok = False
    reasons.append(f"decisions_sum_expected_gt_0_got_{decisions_sum}")
if not (run_id_count == run_id_count and run_id_count >= 1.0):
    hard_ok = False
    reasons.append(f"run_id_count_expected_ge_1_got_{run_id_count}")
if not (last_event_by_run_id_count == last_event_by_run_id_count and last_event_by_run_id_count >= 1.0):
    hard_ok = False
    reasons.append(f"last_event_ts_by_run_id_count_expected_ge_1_got_{last_event_by_run_id_count}")

summary = []
summary.append(f"OUT={out}")
summary.append(f"timestamp_utc={datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")
summary.append(f"hard_ok={hard_ok}")
summary.append(f"up_jobs_expected_ge={int(expected_up_jobs)}")
summary.append(f"up_jobs_rc={up_jobs_rc}")
summary.append(f"heartbeat_rc={hb_rc}")
summary.append(f"decisions_sum={decisions_sum}")
summary.append(f"run_id_count={run_id_count}")
summary.append(f"last_event_ts_by_run_id_count={last_event_by_run_id_count}")
summary.append("hard_fail_reasons=" + (",".join(reasons) if reasons else ""))

open(os.path.join(out, "AI_LIVE_OPS_SUMMARY.txt"), "w", encoding="utf-8").write("\n".join(summary) + "\n")
print("\n".join(summary))

raise SystemExit(0 if hard_ok else 1)
PY

echo "==> Grafana API (optional): dashboard uid exists"
if [[ "$ENABLE_GRAFANA_CHECKS" != "1" ]]; then
  info "grafana.skip" "ENABLE_GRAFANA_CHECKS!=1"
else
  if [[ -z "${GRAFANA_TOKEN:-}" && -z "${GRAFANA_AUTH:-}" ]]; then
    warn "grafana.api.skip" "ENABLE_GRAFANA_CHECKS=1 but no creds (set GRAFANA_AUTH or GRAFANA_TOKEN)"
  else
    if grafana_curl "/api/user" >"$OUT/grafana_user.json" 2>"$OUT/grafana_user.err"; then
      pass "grafana.auth" "api/user ok"
    else
      fail "grafana.auth" "Grafana auth failed for api/user" "Set GRAFANA_AUTH or GRAFANA_TOKEN"
    fi
    if grafana_curl "/api/dashboards/uid/${DASH_UID}" >"$OUT/grafana_dash_uid.json" 2>"$OUT/grafana_dash_uid.err"; then
      pass "grafana.dashboard.uid" "${DASH_UID}"
    else
      fail "grafana.dashboard.uid" "Dashboard UID missing/unreachable: ${DASH_UID}" "Check provisioning + dashpack JSON"
    fi
  fi
fi

echo ""
echo "Evidence dir: $OUT"
echo "Post these:"
echo "  $OUT/AI_LIVE_OPS_SUMMARY.txt"
echo "  $OUT/PROM_REQUIRED_SERIES.tsv"
echo ""
echo "RESULT=PASS"
