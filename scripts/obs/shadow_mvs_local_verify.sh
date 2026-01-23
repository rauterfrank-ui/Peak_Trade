#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}"
PROM_URL="${PROM_URL:-http://127.0.0.1:9092}"
EXPORTER_URL="${EXPORTER_URL:-${SHADOW_MVS_EXPORTER_URL:-http://127.0.0.1:9109/metrics}}"
GRAFANA_AUTH="${GRAFANA_AUTH:-admin:admin}"
DASH_UID="${DASH_UID:-peaktrade-shadow-pipeline-mvs}"

pass() {
  # Machine-readable, operator-friendly.
  # Format: PASS|<check_id>|<message>
  echo "PASS|$1|$2"
}

fail() {
  # Format:
  # FAIL|<check_id>|<message>
  # NEXT|<phase_hint>
  # RESULT=FAIL
  echo "FAIL|$1|$2" >&2
  echo "NEXT|$3" >&2
  echo "RESULT=FAIL" >&2
  exit 1
}

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

prom_query_json() {
  # Robust Prometheus /api/v1/query fetch with gating + evidence on failure.
  local q="${1:-}"
  if [[ -z "${q:-}" ]]; then
    echo "prom_query_json: missing query" >&2
    return 2
  fi
  bash scripts/obs/_prom_query_json.sh \
    --base "$PROM_URL" \
    --query "$q" \
    --retries "${PROM_QUERY_MAX_ATTEMPTS:-3}"
}

grafana_get_json_or_fail() {
  local path="$1"
  local url="${GRAFANA_URL%/}${path}"
  local resp body code
  resp="$(curl -sS -u "$GRAFANA_AUTH" -w $'\n%{http_code}' "$url" || true)"
  body="${resp%$'\n'*}"
  code="${resp##*$'\n'}"

  if [[ "$code" == "401" || "$code" == "403" ]]; then
    fail "grafana.auth" "Grafana auth failed for ${path} (HTTP $code). Expected default admin/admin." "Phase F-1 (Grafana Login/DS)"
  fi
  if [[ "$code" != "200" ]]; then
    fail "grafana.http" "Grafana request failed for ${path} (HTTP ${code})." "Phase F-1 (Grafana Login/DS)"
  fi
  printf '%s' "$body"
}

echo "==> Shadow MVS verify (snapshot-only; max 1 retry per endpoint)"

echo "==> Check: Prometheus ready"
if curl_ok_or_retry_once "$PROM_URL/-/ready" 1; then
  pass "prometheus.ready" "$PROM_URL/-/ready"
else
  fail "prometheus.ready" "Prometheus not ready: $PROM_URL/-/ready" "Phase F-2 (Prometheus Target DOWN)"
fi

echo "==> Check: Exporter /metrics reachable + contract series present"
if ! curl_ok_or_retry_once "$EXPORTER_URL" 1; then
  fail "exporter.http" "Exporter not reachable: $EXPORTER_URL" "Phase F-3 (/metrics leer/alt)"
fi
exporter_metrics="$(curl -fsS "$EXPORTER_URL" 2>/dev/null || true)"
if [[ -z "${exporter_metrics:-}" ]]; then
  fail "exporter.body" "Exporter /metrics empty: $EXPORTER_URL" "Phase F-3 (/metrics leer/alt)"
fi
printf '%s' "$exporter_metrics" | grep -q '^shadow_mvs_up' || fail "exporter.series" "Missing series: shadow_mvs_up" "Phase F-3 (/metrics leer/alt)"
printf '%s' "$exporter_metrics" | grep -q '^peak_trade_pipeline_events_total' || fail "exporter.series" "Missing series: peak_trade_pipeline_events_total" "Phase F-3 (/metrics leer/alt)"
pass "exporter.metrics" "shadow_mvs_up + peak_trade_pipeline_events_total present"

echo "==> Check: Grafana health"
# Grafana can take a few seconds after container start; bounded retries (snapshot-only).
GRAFANA_HEALTH_MAX_ATTEMPTS="${GRAFANA_HEALTH_MAX_ATTEMPTS:-12}"
GRAFANA_HEALTH_SLEEP_S="${GRAFANA_HEALTH_SLEEP_S:-1}"
grafana_ok=0
for _ in $(seq 1 "$GRAFANA_HEALTH_MAX_ATTEMPTS"); do
  if curl_ok "$GRAFANA_URL/api/health"; then
    grafana_ok=1
    break
  fi
  sleep "$GRAFANA_HEALTH_SLEEP_S"
done
if [[ "$grafana_ok" == "1" ]]; then
  pass "grafana.health" "$GRAFANA_URL/api/health"
else
  fail "grafana.health" "Grafana health not OK: $GRAFANA_URL/api/health" "Phase F-1 (Grafana Login/DS)"
fi

echo "==> Check: Grafana datasource + dashboard provisioned"
ds_json="$(grafana_get_json_or_fail "/api/datasources")"
grafana_ds_ok="$(
  python3 -c '
import json, sys
ds = json.loads(sys.stdin.read())
want_uid = "peaktrade-prometheus-local"
match = [d for d in ds if d.get("uid")==want_uid]
if not match:
    raise SystemExit("missing datasource uid=peaktrade-prometheus-local")
d = match[0]
if d.get("isDefault") is not True:
    raise SystemExit("datasource peaktrade-prometheus-local is not default")
url = d.get("url","")
if "host.docker.internal:9092" not in url:
    raise SystemExit(f"unexpected datasource url={url}")
print(url)
' <<<"$ds_json" 2>/dev/null || true
)"
if [[ -z "${grafana_ds_ok:-}" ]]; then
  fail "grafana.datasource" "Datasource provisioning mismatch (expected uid=peaktrade-prometheus-local default url contains host.docker.internal:9092)" "Phase F-1 (Grafana Login/DS)"
fi
pass "grafana.datasource" "peaktrade-prometheus-local default url=$grafana_ds_ok"

search_json="$(grafana_get_json_or_fail "/api/search?type=dash-db")"
python3 -c '
import json, os, sys
uid = os.environ.get("DASH_UID","peaktrade-shadow-pipeline-mvs")
items = json.loads(sys.stdin.read())
uids = [it.get("uid") for it in items]
if uid not in uids:
    raise SystemExit(1)
' <<<"$search_json" 2>/dev/null || fail "grafana.dashboard" "Dashboard uid not found: $DASH_UID" "Phase F-1 (Grafana Login/DS)"
pass "grafana.dashboard" "dashboard_uid=$DASH_UID"

echo "==> Check: Prometheus targets contains shadow_mvs=up"
# Retry contract (snapshot-only): Prometheus can be "ready" while /api/v1/targets is briefly empty
# right after bring-up. We use bounded retries (no watch loops).
TARGETS_MAX_ATTEMPTS="${TARGETS_MAX_ATTEMPTS:-8}"
TARGETS_SLEEP_S="${TARGETS_SLEEP_S:-1}"
echo "INFO|targets_retry=max_attempts=${TARGETS_MAX_ATTEMPTS}|sleep_s=${TARGETS_SLEEP_S}"
targets_ok=0
targets_json=""
attempts_used=0
for _ in $(seq 1 "$TARGETS_MAX_ATTEMPTS"); do
  attempts_used=$((attempts_used + 1))
  targets_json="$(curl -fsS "$PROM_URL/api/v1/targets" 2>/dev/null || true)"
  if python3 -c '
import json, sys
doc = json.loads(sys.stdin.read() or "{}")
if doc.get("status") != "success":
    raise SystemExit(1)
active = doc.get("data", {}).get("activeTargets", [])
jobs = {(t.get("labels",{}).get("job"), (t.get("health") or "").lower()) for t in active}
if ("shadow_mvs","up") not in jobs:
    raise SystemExit(1)
' <<<"$targets_json" 2>/dev/null; then
    targets_ok=1
    break
  fi
  sleep "$TARGETS_SLEEP_S"
done
if [[ "$targets_ok" != "1" ]]; then
  echo "$targets_json" | head -c 2000 >&2 || true
  fail "prometheus.targets" "Prometheus target not UP: job=shadow_mvs" "Phase F-2 (Prometheus Target DOWN)"
fi
echo "INFO|targets_retry=attempts_used=${attempts_used}"
pass "prometheus.targets" "shadow_mvs=up"

prom_query_non_empty_once() {
  local q="$1"
  local json
  if ! json="$(prom_query_json "$q")"; then
    return 1
  fi
  printf '%s' "$json" | python3 -c '
import json, sys
doc = json.load(sys.stdin)
if doc.get("status") != "success":
    raise SystemExit(1)
res = doc.get("data", {}).get("result", [])
if not res:
    raise SystemExit(1)
# Treat NaN as "not ready" (common during warmup for rate()/histogram_quantile()).
for item in res:
    v = item.get("value")
    if not isinstance(v, list) or len(v) < 2:
        continue
    s = str(v[1]).strip().lower()
    if s not in ("nan", "+nan", "-nan"):
        raise SystemExit(0)
raise SystemExit(1)
'
}

prom_query_non_empty_with_retries() {
  local q="$1"
  local attempts="${2:-${WARMUP_MAX_ATTEMPTS:-4}}"
  local sleep_s="${3:-${WARMUP_SLEEP_S:-6}}"
  local i=0
  for _ in $(seq 1 "$attempts"); do
    i=$((i + 1))
    if prom_query_non_empty_once "$q" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$sleep_s"
  done
  return 1
}

echo "==> Check: Golden PromQL returns data (Snapshot)"
if ! prom_query_non_empty_with_retries 'up{job="shadow_mvs"}' "${UP_QUERY_MAX_ATTEMPTS:-3}" "${UP_QUERY_SLEEP_S:-1}"; then
  fail "prometheus.query" "Query returned no data: up{job=\"shadow_mvs\"}" "Phase F-2 (Prometheus Target DOWN)"
fi
pass "prometheus.query" "up{job=\"shadow_mvs\"} non-empty"

if ! prom_query_non_empty_with_retries 'sum by (mode, stage) (rate(peak_trade_pipeline_events_total{job="shadow_mvs"}[5m]))'; then
  fail "prometheus.query" "Query returned no data: pipeline events (rate, job=shadow_mvs)" "Phase F-4 (Panels leer)"
fi
pass "prometheus.query" "pipeline events (rate, job=shadow_mvs) non-empty"

if ! prom_query_non_empty_with_retries 'sum by (mode, reason) (rate(peak_trade_risk_blocks_total{job="shadow_mvs"}[5m]))'; then
  fail "prometheus.query" "Query returned no data: risk blocks (rate, job=shadow_mvs)" "Phase F-4 (Panels leer)"
fi
pass "prometheus.query" "risk blocks (rate, job=shadow_mvs) non-empty"

if ! prom_query_non_empty_with_retries 'histogram_quantile(0.95, sum by (le) (rate(peak_trade_pipeline_latency_seconds_bucket{job="shadow_mvs",edge="intent_to_ack"}[5m])))'; then
  fail "prometheus.query" "Query returned no data: latency p95 intent_to_ack (rate, job=shadow_mvs)" "Phase F-4 (Panels leer)"
fi
pass "prometheus.query" "latency p95 intent_to_ack (rate, job=shadow_mvs) non-empty"

echo ""
echo "EVIDENCE|exporter=$EXPORTER_URL|series=shadow_mvs_up,peak_trade_pipeline_events_total"
echo "EVIDENCE|prometheus=$PROM_URL|target=shadow_mvs:up"
echo "EVIDENCE|grafana=$GRAFANA_URL|ds_uid=peaktrade-prometheus-local"
echo "EVIDENCE|dashboard_uid=$DASH_UID"
echo "RESULT=PASS"
echo "INFO|See Contract: docs/webui/observability/SHADOW_MVS_CONTRACT.md"
