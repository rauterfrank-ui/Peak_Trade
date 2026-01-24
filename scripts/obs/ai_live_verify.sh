#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

PROM_URL="${PROM_URL:-http://127.0.0.1:9092}"
EXPORTER_URL="${EXPORTER_URL:-http://127.0.0.1:9110/metrics}"
JOB_NAME="${JOB_NAME:-ai_live}"

pass() {
  echo "PASS|$1|$2"
}

fail() {
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

echo "==> AI Live verify (snapshot-only; max 1 retry per endpoint)"

echo "==> Check: Prometheus ready"
if curl_ok_or_retry_once "$PROM_URL/-/ready" 1; then
  pass "prometheus.ready" "$PROM_URL/-/ready"
else
  fail "prometheus.ready" "Prometheus not ready: $PROM_URL/-/ready" "Phase AI-1 (Prometheus DOWN)"
fi

echo "==> Check: Exporter /metrics reachable + contract series present"
if ! curl_ok_or_retry_once "$EXPORTER_URL" 1; then
  fail "exporter.http" "Exporter not reachable: $EXPORTER_URL" "Phase AI-2 (Exporter DOWN)"
fi
exporter_metrics="$(curl -fsS "$EXPORTER_URL" 2>/dev/null || true)"
if [[ -z "${exporter_metrics:-}" ]]; then
  fail "exporter.body" "Exporter /metrics empty: $EXPORTER_URL" "Phase AI-2 (Exporter DOWN)"
fi

printf '%s' "$exporter_metrics" | grep -q '^peaktrade_ai_live_heartbeat' || fail "exporter.series" "Missing series: peaktrade_ai_live_heartbeat" "Phase AI-2 (Exporter metrics mismatch)"
printf '%s' "$exporter_metrics" | grep -q '^peaktrade_ai_decisions_total' || fail "exporter.series" "Missing series: peaktrade_ai_decisions_total" "Phase AI-2 (Exporter metrics mismatch)"
printf '%s' "$exporter_metrics" | grep -q '^peaktrade_ai_actions_total' || fail "exporter.series" "Missing series: peaktrade_ai_actions_total" "Phase AI-2 (Exporter metrics mismatch)"
pass "exporter.metrics" "core series present (heartbeat/decisions/actions)"

echo "==> Sample: exporter metrics (first matches)"
printf '%s\n' "$exporter_metrics" | grep -E '^(peaktrade_ai_live_heartbeat|peaktrade_ai_decisions_total|peaktrade_ai_actions_total|peaktrade_ai_last_decision_timestamp_seconds|peaktrade_ai_decision_latency_seconds_)' | head -n 12 || true

echo "==> Check: Prometheus targets contains job=${JOB_NAME}=up"
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
import json, os, sys
job = os.environ.get("JOB_NAME","ai_live")
doc = json.loads(sys.stdin.read() or "{}")
if doc.get("status") != "success":
    raise SystemExit(1)
active = doc.get("data", {}).get("activeTargets", [])
jobs = {(t.get("labels",{}).get("job"), (t.get("health") or "").lower()) for t in active}
if (job,"up") not in jobs:
    raise SystemExit(1)
' <<<"$targets_json" 2>/dev/null; then
    targets_ok=1
    break
  fi
  sleep "$TARGETS_SLEEP_S"
done
if [[ "$targets_ok" != "1" ]]; then
  echo "$targets_json" | head -c 2000 >&2 || true
  fail "prometheus.targets" "Prometheus target not UP: job=$JOB_NAME" "Phase AI-3 (Prometheus Target DOWN)"
fi
echo "INFO|targets_retry=attempts_used=${attempts_used}"
pass "prometheus.targets" "$JOB_NAME=up"

echo "==> Check: Golden PromQL returns data (best-effort warmup)"
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
  local sleep_s="${3:-${WARMUP_SLEEP_S:-2}}"
  for _ in $(seq 1 "$attempts"); do
    if prom_query_non_empty_once "$q" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$sleep_s"
  done
  return 1
}

if ! prom_query_non_empty_with_retries "up{job=\"$JOB_NAME\"}" "${UP_QUERY_MAX_ATTEMPTS:-3}" "${UP_QUERY_SLEEP_S:-1}"; then
  fail "prometheus.query" "Query returned no data: up{job=\"$JOB_NAME\"}" "Phase AI-3 (Prometheus Target DOWN)"
fi
pass "prometheus.query" "up{job=\"$JOB_NAME\"} non-empty"

echo ""
echo "EVIDENCE|exporter=$EXPORTER_URL|series=peaktrade_ai_live_heartbeat,peaktrade_ai_decisions_total,peaktrade_ai_actions_total"
echo "EVIDENCE|prometheus=$PROM_URL|target=$JOB_NAME:up"
echo "RESULT=PASS"
