#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}"
PROM_URL="${PROM_URL:-http://127.0.0.1:9092}"
if [[ -z "${GRAFANA_TOKEN:-}" ]]; then
  if [[ -z "${GRAFANA_AUTH:-}" && -n "${GF_SECURITY_ADMIN_USER:-}" && -n "${GF_SECURITY_ADMIN_PASSWORD:-}" ]]; then
    GRAFANA_AUTH="${GF_SECURITY_ADMIN_USER}:${GF_SECURITY_ADMIN_PASSWORD}"
  fi
fi
if [[ -z "${GRAFANA_TOKEN:-}" && -z "${GRAFANA_AUTH:-}" ]]; then
  echo "ERROR: Grafana auth missing. Set GRAFANA_TOKEN (preferred) or GRAFANA_AUTH=user:pass." >&2
  exit 2
fi

pass() {
  echo "PASS|$1|$2"
}

fail() {
  echo "FAIL|$1|$2" >&2
  echo "NEXT|$3" >&2
  echo "RESULT=FAIL" >&2
  exit 1
}

echo "==> Check: Dashpack v2 operator summary JSON present (file-based)"
OP_SUMMARY_JSON="docs/webui/observability/grafana/dashboards/overview/peaktrade-operator-summary.json"
if [[ ! -f "$OP_SUMMARY_JSON" ]]; then
  echo "FAIL|dashpack.v2.operator_summary|Missing dashboard JSON: $OP_SUMMARY_JSON" >&2
  echo "NEXT|Create/commit operator summary dashboard JSON (ux pack v2)" >&2
  echo "RESULT=FAIL" >&2
  exit 12
fi
pass "dashpack.v2.operator_summary" "$OP_SUMMARY_JSON"

curl_ok() {
  local url="$1"
  curl -fsS "$url" >/dev/null 2>&1
}

grafana_get_json_or_fail() {
  local path="$1"
  local url="${GRAFANA_URL%/}${path}"
  local resp body code
  resp="$(curl -sS -u "$GRAFANA_AUTH" -w $'\n%{http_code}' "$url" || true)"
  body="${resp%$'\n'*}"
  code="${resp##*$'\n'}"

  if [[ "$code" == "401" || "$code" == "403" ]]; then
    fail "grafana.auth" "Grafana auth failed for ${path} (HTTP $code). Set GRAFANA_AUTH=user:pass or use .env." "Check Grafana credentials/volumes"
  fi
  if [[ "$code" != "200" ]]; then
    fail "grafana.http" "Grafana request failed for ${path} (HTTP ${code})." "Check Grafana container/logs"
  fi
  printf '%s' "$body"
}

echo "==> Grafana local verify (snapshot-only)"

echo "==> Check: Prometheus ready"
if curl_ok "$PROM_URL/-/ready"; then
  pass "prometheus.ready" "$PROM_URL/-/ready"
else
  fail "prometheus.ready" "Prometheus not ready: $PROM_URL/-/ready" "Start stack (grafana_local_up) and re-run"
fi

echo "==> Check: Grafana health (bounded retries; snapshot-only)"
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
  fail "grafana.health" "Grafana health not OK: $GRAFANA_URL/api/health" "Restart Grafana (grafana_local_down/up)"
fi

echo "==> Check: Grafana datasources (local/main/shadow) provisioned"
ds_json="$(grafana_get_json_or_fail "/api/datasources")"
ds_check="$(
  python3 -c '
import json, sys
ds = json.loads(sys.stdin.read() or "[]")
want = {
  "peaktrade-prometheus-local": ("prometheus-local", True),
  "peaktrade-prometheus-main": ("prometheus-main", False),
  "peaktrade-prometheus-shadow": ("prometheus-shadow", False),
}
by_uid = {d.get("uid"): d for d in ds if isinstance(d, dict)}
missing = [uid for uid in want.keys() if uid not in by_uid]
if missing:
  raise SystemExit("missing_uids=" + ",".join(sorted(missing)))

problems = []
for uid, (name, is_default) in want.items():
  d = by_uid[uid]
  if d.get("name") != name:
    problems.append(f"uid={uid} name={d.get('name')!r} expected={name!r}")
  if bool(d.get("isDefault")) != bool(is_default):
    problems.append(f"uid={uid} isDefault={d.get('isDefault')!r} expected={is_default!r}")
if problems:
  raise SystemExit(" ; ".join(problems))
print("ok")
' <<<"$ds_json" 2>/dev/null || true
)"
if [[ "${ds_check:-}" != "ok" ]]; then
  fail "grafana.datasources" "Datasource provisioning mismatch: ${ds_check:-unknown}" "Check provisioning mount + datasources YAML"
fi
pass "grafana.datasources" "local/main/shadow provisioned (uids stable)"

echo "==> Check: Dashboards provisioned and mapped to folders (from file structure)"
search_json="$(grafana_get_json_or_fail "/api/search?type=dash-db")"
dash_check="$(
  python3 -c '
import json, sys
items = json.loads(sys.stdin.read() or "[]")
want = {
  "peaktrade-execution-watch-overview": "execution",
  "peaktrade-overview": "overview",
  "peaktrade-shadow-pipeline-mvs": "shadow",
  "peaktrade-labeled-local": "http",
  "peaktrade-system-health": "overview",
}
by_uid = {it.get("uid"): it for it in items if isinstance(it, dict)}
missing = [uid for uid in want.keys() if uid not in by_uid]
if missing:
  raise SystemExit("missing_dash_uids=" + ",".join(sorted(missing)))

problems = []
for uid, folder in want.items():
  it = by_uid[uid]
  folder_title = str(it.get("folderTitle") or "")
  # Grafana behavior can vary: some setups report just the leaf folder name, others
  # include a root folder (e.g. "Peak_Trade / overview"). Be tolerant and require
  # the expected folder to appear as a leaf.
  ok = (folder_title == folder) or folder_title.endswith("/" + folder) or folder_title.endswith(" " + folder)
  if not ok:
    problems.append(f"uid={uid} folderTitle={folder_title!r} expected_leaf={folder!r}")
if problems:
  raise SystemExit(" ; ".join(problems))
print("ok")
' <<<"$search_json" 2>/dev/null || true
)"
if [[ "${dash_check:-}" != "ok" ]]; then
  fail "grafana.dashboards" "Dashboard provisioning/folder mapping mismatch: ${dash_check:-unknown}" "Check dashboards.yaml + dashboard paths"
fi
pass "grafana.dashboards" "Dashboards loaded under execution/overview/shadow/http"

echo "==> Check: Dashboard templating vars (optional; requires Grafana API)"
dash_vars_ok=1
for uid in peaktrade-execution-watch-overview peaktrade-overview peaktrade-shadow-pipeline-mvs peaktrade-labeled-local peaktrade-system-health; do
  djson="$(grafana_get_json_or_fail "/api/dashboards/uid/${uid}")"
  want_vars="$(
    python3 -c '
import json, os, sys
uid = os.environ.get("DASH_UID","")
doc = json.loads(sys.stdin.read() or "{}")
dash = doc.get("dashboard") or {}
templ = (dash.get("templating") or {}).get("list") or []
names = [t.get("name") for t in templ if isinstance(t, dict) and t.get("type")=="datasource"]
names = [n for n in names if isinstance(n, str)]
want = {
  "peaktrade-execution-watch-overview": {"DS_LOCAL","DS_MAIN","DS_SHADOW"},
  "peaktrade-overview": {"DS_LOCAL","DS_MAIN"},
  "peaktrade-shadow-pipeline-mvs": {"DS_SHADOW"},
  "peaktrade-labeled-local": {"DS_LOCAL"},
  "peaktrade-system-health": {"DS_LOCAL","DS_MAIN","DS_SHADOW"},
}
need = want.get(uid, set())
have = set(names)
missing = sorted(need - have)
if missing:
  raise SystemExit("missing_vars=" + ",".join(missing))
print("ok")
' <<<"$djson" 2>/dev/null || true
  )"
  if [[ "${want_vars:-}" != "ok" ]]; then
    dash_vars_ok=0
    break
  fi
done
if [[ "$dash_vars_ok" == "1" ]]; then
  pass "grafana.dashboard.vars" "Datasource variables present (local/main/shadow conventions)"
else
  fail "grafana.dashboard.vars" "Dashboard templating vars mismatch for uid=$uid" "Check dashboard JSON templating.list datasource vars"
fi

echo "==> Check: Datasource health (Grafana -> Prometheus)"
ds_health_ok=1
main_health_ok=1
for uid in peaktrade-prometheus-local peaktrade-prometheus-shadow peaktrade-prometheus-main; do
  # /api/datasources/uid/<uid>/health returns JSON with status=OK when reachable.
  url="${GRAFANA_URL%/}/api/datasources/uid/${uid}/health"
  resp="$(curl -sS -u "$GRAFANA_AUTH" -w $'\n%{http_code}' "$url" || true)"
  body="${resp%$'\n'*}"
  code="${resp##*$'\n'}"
  if [[ "$code" != "200" ]]; then
    if [[ "$uid" == "peaktrade-prometheus-main" ]]; then
      main_health_ok=0
      continue
    fi
    ds_health_ok=0
    echo "$body" | head -c 500 >&2 || true
    break
  fi
  if ! python3 -c 'import json,sys; j=json.loads(sys.stdin.read() or "{}"); s=str(j.get("status") or ""); raise SystemExit(0 if s=="OK" else 1)' <<<"$body" 2>/dev/null; then
    if [[ "$uid" == "peaktrade-prometheus-main" ]]; then
      main_health_ok=0
      continue
    fi
    ds_health_ok=0
    echo "$body" | head -c 500 >&2 || true
    break
  fi
done
if [[ "$ds_health_ok" != "1" ]]; then
  fail "grafana.datasource.health" "Grafana datasource health not OK (one or more Prometheus endpoints unreachable)" "Ensure Prometheus endpoints are up/reachable"
fi
pass "grafana.datasource.health" "Grafana datasource health OK (local+shadow)"
if [[ "$main_health_ok" == "1" ]]; then
  pass "grafana.datasource.health.main" "Grafana datasource health OK (main)"
else
  pass "grafana.datasource.health.main" "Grafana datasource health not OK (main) (optional)"
fi

echo ""
echo "EVIDENCE|grafana=$GRAFANA_URL"
echo "EVIDENCE|prometheus=$PROM_URL"
echo "RESULT=PASS"
