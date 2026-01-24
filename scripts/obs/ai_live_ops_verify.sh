#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# Snapshot-only verifier for AI Live Ops Pack v1 readiness:
# - No watch loops. Bounded retries are kept minimal and deterministic.

PROM_URL="${PROM_URL:-http://127.0.0.1:9092}"
GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}"
GRAFANA_AUTH="${GRAFANA_AUTH:-admin:admin}"

AI_LIVE_PORT="${AI_LIVE_PORT:-9110}"
EXPORTER_URL="${EXPORTER_URL:-http://127.0.0.1:${AI_LIVE_PORT}/metrics}"

DASH_UID="${DASH_UID:-peaktrade-execution-watch-overview}"

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
  if [[ -n "${GRAFANA_AUTH:-}" ]]; then
    curl -fsS -u "$GRAFANA_AUTH" "${GRAFANA_URL}${path}"
  else
    curl -fsS "${GRAFANA_URL}${path}"
  fi
}

prom_query_json_to_file() {
  local q="$1"
  local out="$2"
  bash scripts/obs/_prom_query_json.sh --base "$PROM_URL" --query "$q" --out "$out" --retries "${PROM_QUERY_MAX_ATTEMPTS:-3}" >/dev/null
}

port_check() {
  local port="$1"
  if [[ "${SKIP_PORT_CHECK}" = "1" ]]; then
    info "port.check.skip" "SKIP_PORT_CHECK=1"
    return 0
  fi
  if command -v lsof >/dev/null 2>&1; then
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      pass "port.listen" ":$port LISTEN"
      return 0
    fi
    fail "port.listen" ":$port not listening" "Start required service or free port"
  fi
  info "port.check.skip" "lsof not available"
}

echo "==> AI Live Ops Verify (snapshot-only)"
info "env" "PROM_URL=$PROM_URL GRAFANA_URL=$GRAFANA_URL EXPORTER_URL=$EXPORTER_URL DASH_UID=$DASH_UID"

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

if [[ -n "${GRAFANA_AUTH:-}" ]]; then
  if grafana_curl "/api/user" >/dev/null 2>&1; then
    pass "grafana.auth" "api/user ok"
  else
    fail "grafana.auth" "Grafana auth failed for api/user" "Reset volumes: bash scripts/obs/grafana_local_down.sh then grafana_local_up.sh"
  fi
else
  info "grafana.auth.skip" "GRAFANA_AUTH empty (no auth)"
fi

echo "==> Preflight: port contract checks"
port_check 9092
port_check 3000

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
  if python3 -c '
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
up_ok="$(python3 -c '
import json
from pathlib import Path
doc=json.loads(Path("/tmp/pt_ai_live_ops_verify_up.json").read_text(encoding="utf-8"))
res=(doc.get("data") or {}).get("result") or []
if not res: raise SystemExit(1)
v=res[0].get("value") or [None,"0"]
try:
    x=float(v[1])
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if x >= 1.0 else 1)
')" || true
if [[ "${up_ok:-}" = "" ]]; then
  pass "prometheus.query.up" "max(up{job=\"ai_live\"}) >= 1"
else
  fail "prometheus.query.up" "max(up{job=\"ai_live\"}) != 1" "Check Prometheus target health and exporter /metrics"
fi

echo "==> Rules: AI Live Ops Pack v1 loaded + alert names present"
rules_json="$(curl -fsS "$PROM_URL/api/v1/rules" 2>/dev/null || true)"
if python3 -c '
import json, sys
doc=json.loads(sys.stdin.read() or "{}")
groups=(doc.get("data") or {}).get("groups") or []
names=[g.get("name") for g in groups if isinstance(g, dict)]
if "ai_live_ops_pack_v1" not in names:
    raise SystemExit(1)
want={
  "AI_LIVE_ExporterDown",
  "AI_LIVE_StaleEvents",
  "AI_LIVE_ParseErrorsSpike",
  "AI_LIVE_DroppedEventsSpike",
  "AI_LIVE_LatencyP95High",
}
have=set()
for g in groups:
  if g.get("name") != "ai_live_ops_pack_v1":
    continue
  for r in (g.get("rules") or []):
    if r.get("type") != "alerting":
      continue
    n=r.get("name")
    if isinstance(n,str):
      have.add(n)
missing=sorted(want - have)
if missing:
  print("missing_alerts=", missing)
  raise SystemExit(1)
raise SystemExit(0)
' <<<"$rules_json" >/dev/null 2>&1; then
  pass "prometheus.rules" "ai_live_ops_pack_v1 loaded + required alerts present"
else
  echo "$rules_json" | head -c 2000 || true
  fail "prometheus.rules" "Rules missing or alert names missing" "Ensure DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml mounts /etc/prometheus/rules"
fi

echo "==> Alerts: counts by state (top 10)"
alerts_json="$(curl -fsS "$PROM_URL/api/v1/alerts" 2>/dev/null || true)"
python3 -c '
import json, sys
doc=json.loads(sys.stdin.read() or "{}")
alerts=(doc.get("data") or {}).get("alerts") or []
ai=[a for a in alerts if (a.get("labels") or {}).get("alertname","").startswith("AI_LIVE_")]
counts={}
for a in ai:
  st=(a.get("state") or "unknown").lower()
  counts[st]=counts.get(st,0)+1
print("INFO|alerts.counts|" + " ".join([f"{k}={counts[k]}" for k in sorted(counts)]))
for a in ai[:10]:
  lab=a.get("labels") or {}
  print("INFO|alerts.sample|alertname=%s state=%s severity=%s" % (lab.get("alertname"), a.get("state"), lab.get("severity")))
' <<<"$alerts_json" 2>/dev/null || true

echo "==> Dashboard: uid exists + ops row invariants"
dash_json="$(grafana_curl "/api/dashboards/uid/${DASH_UID}")"
if python3 -c '
import json, sys
doc=json.loads(sys.stdin.read() or "{}")
dash=doc.get("dashboard") or {}
panels=dash.get("panels") or []
rows=[p for p in panels if isinstance(p,dict) and p.get("type")=="row"]
row_titles=[p.get("title") for p in rows]
if "AI Live — Ops Summary" not in row_titles:
  raise SystemExit(1)
exprs=[]
def walk(o):
  if isinstance(o, dict):
    for k,v in o.items():
      if k=="expr" and isinstance(v,str):
        exprs.append(v)
      else:
        walk(v)
  elif isinstance(o, list):
    for it in o:
      walk(it)
walk(dash)
if not any("ALERTS" in e for e in exprs):
  raise SystemExit(1)
ops_panels=[p for p in panels if isinstance(p,dict) and p.get("type")!="row" and (p.get("gridPos") or {}).get("y")==1]
ops_exprs=[]
for p in ops_panels:
  for t in (p.get("targets") or []):
    if isinstance(t,dict) and isinstance(t.get("expr"),str):
      ops_exprs.append(t["expr"])
if not ops_exprs:
  raise SystemExit(1)
if any("or on() vector(0)" not in e for e in ops_exprs):
  raise SystemExit(1)
raise SystemExit(0)
' <<<"$dash_json" >/dev/null 2>&1; then
  pass "grafana.dashboard" "uid ok + ops row ok + ALERTS query + hardened expressions"
else
  fail "grafana.dashboard" "Dashboard invariants failed (uid/ops row/ALERTS/hardening)" "Check provisioning + dashboard JSON pack"
fi

echo ""
echo "RESULT=PASS"
