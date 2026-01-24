#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# Snapshot-only verifier for AI Live Ops Pack v1 readiness:
# - No watch loops. Bounded retries are kept minimal and deterministic.

PROM_URL="${PROM_URL:-http://127.0.0.1:9092}"
GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}"
GRAFANA_AUTH="${GRAFANA_AUTH:-}"   # optional basic auth user:pass
GRAFANA_TOKEN="${GRAFANA_TOKEN:-}" # optional bearer token

AI_LIVE_PORT="${AI_LIVE_PORT:-9110}"
EXPORTER_URL="${EXPORTER_URL:-http://127.0.0.1:${AI_LIVE_PORT}/metrics}"

DASH_UID="${DASH_UID:-peaktrade-execution-watch-overview}"

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

echo "==> AI Live Ops Verify (snapshot-only)"
info "repo.root" "$(pwd)"
git status -sb || true
info "env" "PROM_URL=$PROM_URL GRAFANA_URL=$GRAFANA_URL EXPORTER_URL=$EXPORTER_URL DASH_UID=$DASH_UID"

echo "==> Preflight: port contract checks"
port_check 9092
port_check 3000
port_check "$AI_LIVE_PORT"

echo "==> Preflight: endpoints reachable"
if curl_ok_or_retry_once "$PROM_URL/-/ready" 1; then
  pass "prometheus.ready" "$PROM_URL/-/ready"
else
  fail "prometheus.ready" "Prometheus not ready: $PROM_URL/-/ready" "Start prometheus-local (scripts/obs/grafana_local_up.sh)"
fi

if curl_ok_or_retry_once "$GRAFANA_URL/api/health" 2; then
  pass "grafana.health" "$GRAFANA_URL/api/health"
else
  fail "grafana.health" "Grafana health failed: $GRAFANA_URL/api/health" "Start grafana-only (scripts/obs/grafana_local_up.sh)"
fi

echo "==> Exporter: /metrics reachable"
if curl_ok_or_retry_once "$EXPORTER_URL" 1; then
  pass "exporter.http" "$EXPORTER_URL"
else
  fail "exporter.http" "Exporter not reachable: $EXPORTER_URL" "Start exporter on port 9110 (Port Contract v1)"
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
  echo "$targets_json" | head -c 1200 || true
  fail "prometheus.targets" "Target not UP: job=ai_live" "Fix exporter/port contract (9110) or Prometheus scrape target"
fi

echo "==> PromQL: up{job=\"ai_live\"} should be 1"
OUT_UP="/tmp/pt_ai_live_ops_verify_up.json"
rm -f "$OUT_UP"
prom_query_json_to_file 'max(up{job="ai_live"})' "$OUT_UP"
up_value="$("${PY_ARR[@]}" -c '
import json
from pathlib import Path
doc=json.loads(Path("/tmp/pt_ai_live_ops_verify_up.json").read_text(encoding="utf-8"))
res=(doc.get("data") or {}).get("result") or []
if not res:
    print("nan")
    raise SystemExit(0)
v=res[0].get("value") or [None,"0"]
try:
    x=float(v[1])
except Exception:
    x=float("nan")
print(x)
')" || true
info "prometheus.up" "max=${up_value}"
if "${PY_ARR[@]}" - "$up_value" >/dev/null 2>&1 <<'PY'
import math, sys
x=float(sys.argv[1])
raise SystemExit(0 if (not math.isnan(x) and x >= 1.0) else 1)
PY
then
  pass "prometheus.query.up" "max(up{job=\"ai_live\"}) == 1"
else
  fail "prometheus.query.up" "max(up{job=\"ai_live\"}) != 1" "Check Prometheus target health and exporter /metrics"
fi

echo "==> Rules: AI Live Ops Pack v1 loaded + alert names present"
rules_json="$(curl -fsS "$PROM_URL/api/v1/rules" 2>/dev/null || true)"
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
ai=sorted([n for n in have if n.startswith("AI_LIVE_")])
missing=sorted(want - have)
print(f"groups={len(groups)}")
print("ai_live_alerts=" + ",".join(ai))
if len(groups) <= 0:
  print("missing_alerts=__groups__")
  raise SystemExit(1)
if missing:
  print("missing_alerts=" + ",".join(missing))
  raise SystemExit(1)
' <<<"$rules_json" 2>/dev/null
)" && rules_ok=1 || rules_ok=0

rules_groups="$(printf '%s\n' "$rules_check_out" | sed -n 's/^groups=//p' | head -n 1 || true)"
rules_ai_live="$(printf '%s\n' "$rules_check_out" | sed -n 's/^ai_live_alerts=//p' | head -n 1 || true)"
info "prometheus.rules.groups" "count=${rules_groups:-unknown}"
info "prometheus.rules.ai_live" "${rules_ai_live:-}"

if [[ "$rules_ok" = "1" ]]; then
  pass "prometheus.rules" "groups>0 + required AI_LIVE_* alerts present"
else
  echo "$rules_json" | head -c 2000 || true
  fail "prometheus.rules" "Rules missing or alert names missing" "Ensure DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml mounts /etc/prometheus/rules"
fi

echo "==> Alerts: counts by state (top 10)"
alerts_json="$(curl -fsS "$PROM_URL/api/v1/alerts" 2>/dev/null || true)"
"${PY_ARR[@]}" -c '
import json, sys
doc=json.loads(sys.stdin.read() or "{}")
alerts=(doc.get("data") or {}).get("alerts") or []
counts={"firing":0,"pending":0,"inactive":0,"unknown":0}
rows=[]
for a in alerts:
  lab=a.get("labels") or {}
  name=str(lab.get("alertname",""))
  st=str(a.get("state") or "unknown").lower()
  if st in counts:
    counts[st] += 1
  else:
    counts["unknown"] += 1
  rows.append((name, st))
print("INFO|alerts.counts|firing=%d pending=%d inactive=%d unknown=%d" % (counts["firing"], counts["pending"], counts["inactive"], counts["unknown"]))
for name, st in sorted(rows)[:10]:
  print("INFO|alerts.sample|alertname=%s state=%s" % (name, st))
' <<<"$alerts_json" 2>/dev/null || true

echo "==> Grafana API (optional): dashboard uid exists"
if [[ -z "${GRAFANA_TOKEN:-}" && -z "${GRAFANA_AUTH:-}" ]]; then
  info "grafana.api.skip" "SKIP grafana api (no creds)"
else
  if grafana_curl "/api/user" >/dev/null 2>&1; then
    pass "grafana.auth" "api/user ok"
  else
    fail "grafana.auth" "Grafana auth failed for api/user" "Set GRAFANA_AUTH or GRAFANA_TOKEN (or reset grafana volumes)"
  fi
  if grafana_curl "/api/dashboards/uid/${DASH_UID}" >/dev/null 2>&1; then
    pass "grafana.dashboard.uid" "${DASH_UID}"
  else
    fail "grafana.dashboard.uid" "Dashboard UID missing/unreachable: ${DASH_UID}" "Check provisioning + dashpack JSON"
  fi
fi

echo ""
echo "RESULT=PASS"
