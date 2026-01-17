#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}"
PROM_URL="${PROM_URL:-http://127.0.0.1:9092}"
EXPORTER_URL="${SHADOW_MVS_EXPORTER_URL:-http://127.0.0.1:9109/metrics}"
GRAFANA_AUTH="${GRAFANA_AUTH:-admin:admin}"
DASH_UID="${DASH_UID:-peaktrade-shadow-pipeline-mvs}"

wait_http_ok() {
  local url="$1"
  local tries="${2:-60}"
  local sleep_s="${3:-1}"
  local i=1
  while [[ $i -le $tries ]]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$sleep_s"
    i=$((i + 1))
  done
  echo "❌ Timeout waiting for: $url" >&2
  return 1
}

grafana_get_json() {
  local path="$1"
  local url="${GRAFANA_URL%/}${path}"
  local resp body code
  resp="$(curl -sS -u "$GRAFANA_AUTH" -w $'\n%{http_code}' "$url" || true)"
  body="${resp%$'\n'*}"
  code="${resp##*$'\n'}"

  if [[ "$code" == "401" || "$code" == "403" ]]; then
    echo "❌ Grafana auth failed for ${path} (HTTP $code). Check credentials (default: admin/admin) or reset volumes via ./scripts/obs/shadow_mvs_local_down.sh" >&2
    return 1
  fi
  if [[ "$code" != "200" ]]; then
    echo "❌ Grafana request failed for ${path} (HTTP ${code})." >&2
    return 1
  fi
  printf '%s' "$body"
}

echo "==> Waiting for Prometheus ready: $PROM_URL"
wait_http_ok "$PROM_URL/-/ready" 60 1

echo "==> Checking shadow MVS exporter is reachable: $EXPORTER_URL"
wait_http_ok "$EXPORTER_URL" 30 1
curl -fsS "$EXPORTER_URL" | grep -q '^shadow_mvs_up' || {
  echo "❌ Exporter metrics missing: shadow_mvs_up" >&2
  exit 1
}
curl -fsS "$EXPORTER_URL" | grep -q '^peak_trade_pipeline_events_total' || {
  echo "❌ Exporter metrics missing: peak_trade_pipeline_events_total" >&2
  exit 1
}
echo "✅ Exporter metrics ok"

echo "==> Waiting for Grafana health: $GRAFANA_URL"
wait_http_ok "$GRAFANA_URL/api/health" 90 1

echo "==> Checking Grafana datasources (expects prometheus-local default)"
ds_json="$(
  grafana_get_json "/api/datasources" || exit 1
)"
python3 -c '
import json, sys
ds = json.loads(sys.stdin.read())
want_uid = "peaktrade-prometheus-local"
uids = [d.get("uid") for d in ds]
match = [d for d in ds if d.get("uid")==want_uid]
if not match:
    raise SystemExit(f"missing datasource uid={want_uid}; got uids={uids}")
if match[0].get("isDefault") is not True:
    raise SystemExit(f"datasource {want_uid} is not default")
url = match[0].get("url","")
if "host.docker.internal:9092" not in url:
    raise SystemExit(f"unexpected datasource url={url}")
print("✅ Grafana datasource ok:", want_uid, url)
' <<<"$ds_json"

echo "==> Checking Grafana dashboard is provisioned (uid=$DASH_UID)"
search_json="$(
  grafana_get_json "/api/search?type=dash-db" || exit 1
)"
python3 -c '
import json, os, sys
uid = os.environ.get("DASH_UID","peaktrade-shadow-pipeline-mvs")
items = json.loads(sys.stdin.read())
uids = [it.get("uid") for it in items]
if uid not in uids:
    raise SystemExit(f"dashboard uid not found: {uid}. got={uids}")
print("✅ Grafana dashboard visible:", uid)
' <<<"$search_json"

echo "==> Checking Prometheus targets are UP (expects mock exporter)"
target_ok() {
  curl -fsS "$PROM_URL/api/v1/targets" | python3 -c '
import json, sys
doc = json.load(sys.stdin)
status = doc.get("status")
assert status == "success", f"targets status={status}"
active = doc.get("data", {}).get("activeTargets", [])
jobs = {(t.get("labels",{}).get("job"), t.get("health")) for t in active}
assert ("shadow_mvs","up") in jobs, f"shadow_mvs target not up; jobs={sorted(jobs)}"
'
}

for _ in $(seq 1 25); do
  if target_ok >/dev/null 2>&1; then
    echo "✅ Prometheus target UP: shadow_mvs"
    break
  fi
  sleep 1
done

target_ok >/dev/null 2>&1 || {
  echo "❌ Prometheus target not UP: shadow_mvs" >&2
  curl -fsS "$PROM_URL/api/v1/targets" | head -c 2000 >&2 || true
  echo "" >&2
  exit 1
}

prom_query_ok() {
  local q="$1"
  local tries="${2:-25}"
  local sleep_s="${3:-1}"
  local i=1
  while [[ $i -le $tries ]]; do
    if curl -fsS -G "$PROM_URL/api/v1/query" --data-urlencode "query=$q" 2>/dev/null | python3 -c '
import json, sys
try:
    doc = json.load(sys.stdin)
except Exception:
    raise SystemExit(1)
if doc.get("status") != "success":
    raise SystemExit(1)
res = doc.get("data", {}).get("result", [])
if not res:
    raise SystemExit(1)
' >/dev/null 2>&1; then
      return 0
    fi
    sleep "$sleep_s"
    i=$((i + 1))
  done
  echo "❌ Prometheus query did not return data in time: $q" >&2
  return 1
}

echo "==> Checking core Shadow MVS queries return data"
prom_query_ok 'sum by (mode, stage) (rate(peak_trade_pipeline_events_total{mode="shadow"}[5m]))'
prom_query_ok 'sum by (mode, reason) (rate(peak_trade_risk_blocks_total{mode="shadow"}[5m]))'
prom_query_ok 'histogram_quantile(0.95, sum by (le, mode) (rate(peak_trade_pipeline_latency_seconds_bucket{edge="intent_to_ack",mode="shadow"}[5m])))'

echo ""
echo "✅ OK: grafana-only + prometheus-local + shadow-mvs dashboard provisioned; targets and queries are healthy."
