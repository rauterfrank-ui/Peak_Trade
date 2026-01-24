#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}"
GRAFANA_AUTH="${GRAFANA_AUTH:-admin:admin}"
PROM_URL="${PROM_URL:-http://127.0.0.1:9092}"

VERIFY_OUT_DIR="${VERIFY_OUT_DIR:-}"
RUN_TS_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
if [ -z "$VERIFY_OUT_DIR" ]; then
  VERIFY_OUT_DIR="docs/ops/evidence/assets/EV_GRAFANA_VERIFY_V2_${RUN_TS_UTC}"
fi

mkdir -p "$VERIFY_OUT_DIR"
export VERIFY_OUT_DIR

pass() { echo "PASS|$1|$2"; }
fail() {
  echo "FAIL|$1|$2" >&2
  echo "EVIDENCE_DIR|$VERIFY_OUT_DIR" >&2
  echo "NEXT|$3" >&2
  echo "RESULT=FAIL" >&2
  exit 1
}

require_tool() {
  command -v "$1" >/dev/null 2>&1 || fail "preflight.tool" "Missing required tool: $1" "Install $1 and re-run"
}

require_tool curl
require_tool python3

GRAFANA_HELPER="./scripts/obs/_grafana_api_json.sh"
PROM_HELPER="./scripts/obs/_prom_query_json.sh"
if [ ! -f "$GRAFANA_HELPER" ]; then
  fail "preflight.helper" "Missing helper: $GRAFANA_HELPER" "Ensure scripts are present"
fi
if [ ! -f "$PROM_HELPER" ]; then
  fail "preflight.helper" "Missing helper: $PROM_HELPER" "Ensure scripts are present"
fi

echo "== Grafana Verify v2 (operator-grade, deterministic) =="
echo "EVIDENCE_DIR|$VERIFY_OUT_DIR"
echo "EVIDENCE|grafana=$GRAFANA_URL"
echo "EVIDENCE|prometheus=$PROM_URL"

echo "==> 1) Grafana reachable + login ok (API)"
health_out="$VERIFY_OUT_DIR/grafana_api_health.json"
if ! bash "$GRAFANA_HELPER" --base "$GRAFANA_URL" --path "/api/health" --out "$health_out" --retries 10 --timeout 3 >/dev/null; then
  fail "grafana.health" "Grafana /api/health not reachable" "Run ./scripts/obs/grafana_local_up.sh and re-run"
fi
pass "grafana.health" "$health_out"

user_out="$VERIFY_OUT_DIR/grafana_api_user.json"
if ! bash "$GRAFANA_HELPER" --base "$GRAFANA_URL" --path "/api/user" --auth "$GRAFANA_AUTH" --out "$user_out" --retries 2 --timeout 3 >/dev/null; then
  fail "grafana.auth" "Grafana login failed (check credentials: GRAFANA_AUTH=user:pass)" "Try: bash scripts/obs/grafana_local_down.sh && bash scripts/obs/grafana_local_up.sh (resets volumes) or export GRAFANA_AUTH=..."
fi
pass "grafana.auth" "$user_out"

echo "==> 2) Enumerate dashpack dashboard JSONs (repo) + collect UIDs"
uids_json="$VERIFY_OUT_DIR/dashpack_uids.json"
uids_txt="$VERIFY_OUT_DIR/dashpack_uids.txt"
python3 - <<'PY'
import json
import os
from pathlib import Path

root = Path(".")
dash_dir = root / "docs" / "webui" / "observability" / "grafana" / "dashboards"
paths = sorted(dash_dir.glob("*/*.json"))
uids = []
for p in paths:
    doc = json.loads(p.read_text(encoding="utf-8"))
    uid = doc.get("uid")
    title = doc.get("title")
    if not isinstance(uid, str) or not uid:
        raise SystemExit(f"missing uid in {p}")
    if not isinstance(title, str) or not title:
        raise SystemExit(f"missing title in {p}")
    uids.append(uid)

out_dir = Path(os.environ["VERIFY_OUT_DIR"])
(out_dir / "dashpack_uids.json").write_text(
    json.dumps({"uids": uids}, indent=2) + "\n", encoding="utf-8"
)
(out_dir / "dashpack_uids.txt").write_text("\n".join(uids) + "\n", encoding="utf-8")
print(f"uids={len(uids)}")
PY
pass "dashpack.uids" "$uids_json"

echo "==> 3) Fetch each provisioned dashboard by UID (Grafana API) + validate JSON"
dash_api_dir="$VERIFY_OUT_DIR/grafana_dashboards_by_uid"
mkdir -p "$dash_api_dir"

while IFS= read -r uid; do
  [ -n "$uid" ] || continue
  out="$dash_api_dir/${uid}.json"
  if ! bash "$GRAFANA_HELPER" --base "$GRAFANA_URL" --path "/api/dashboards/uid/${uid}" --auth "$GRAFANA_AUTH" --out "$out" --retries 8 --timeout 5 >/dev/null; then
    fail "grafana.dashboard.get" "Failed to fetch dashboard uid=${uid}" "Restart Grafana to reload provisioned dashboards (grafana_local_down/up) and re-run"
  fi
  if ! python3 - <<PY
import json
from pathlib import Path
p=Path("$out")
doc=json.loads(p.read_text(encoding="utf-8"))
d=doc.get("dashboard") or {}
uid = d.get("uid")
if uid != "$uid":
  raise SystemExit(f"uid mismatch: expected={\"$uid\"} got={uid!r}")
PY
  then
    fail "grafana.dashboard.json" "Invalid dashboard JSON or uid mismatch for uid=$uid" "Inspect $out"
  fi
done <"$uids_txt"
pass "grafana.dashboards.uid_fetch" "$dash_api_dir"

echo "==> 4) DS_* invariants: present + hidden + stable defaults"
ds_check_out="$VERIFY_OUT_DIR/ds_invariants_report.txt"
python3 - <<'PY'
import json
import os
from pathlib import Path

out_dir = Path(os.environ["VERIFY_OUT_DIR"])
dash_api_dir = out_dir / "grafana_dashboards_by_uid"
paths = sorted(dash_api_dir.glob("*.json"))
expected_defaults = {
    "DS_LOCAL": "peaktrade-prometheus-local",
    "DS_MAIN": "peaktrade-prometheus-main",
    "DS_SHADOW": "peaktrade-prometheus-shadow",
}
need = set(expected_defaults.keys())

problems = []
for p in paths:
    doc = json.loads(p.read_text(encoding="utf-8"))
    dash = doc.get("dashboard") or {}
    uid = dash.get("uid")
    templ = (dash.get("templating") or {}).get("list") or []
    ds_vars = [t for t in templ if isinstance(t, dict) and t.get("type") == "datasource"]
    by_name = {t.get("name"): t for t in ds_vars if isinstance(t.get("name"), str)}
    missing = sorted(need - set(by_name.keys()))
    if missing:
        problems.append(f"{uid}: missing_vars={missing}")
        continue
    for name, want_uid in expected_defaults.items():
        t = by_name[name]
        hide = t.get("hide")
        cur = t.get("current") or {}
        cur_val = cur.get("value")
        if hide != 2:
            problems.append(f"{uid}: {name}.hide={hide!r} expected=2")
        if cur_val != want_uid:
            problems.append(f"{uid}: {name}.current.value={cur_val!r} expected={want_uid!r}")

report = out_dir / "ds_invariants_report.txt"
if problems:
    report.write_text("\n".join(problems) + "\n", encoding="utf-8")
    raise SystemExit("DS invariants failed; see " + str(report))
report.write_text("ok\n", encoding="utf-8")
print("ok")
PY
pass "dashpack.ds_invariants" "$ds_check_out"

echo "==> 5) Navigation/Drilldowns: all internal /d/<uid> links resolvable (UID exists)"
links_report="$VERIFY_OUT_DIR/link_uid_report.txt"
python3 - <<'PY'
import json
import re
import os
from pathlib import Path

out_dir = Path(os.environ["VERIFY_OUT_DIR"])
uids = set((out_dir / "dashpack_uids.txt").read_text(encoding="utf-8").splitlines())
dash_api_dir = out_dir / "grafana_dashboards_by_uid"
paths = sorted(dash_api_dir.glob("*.json"))

uid_re = re.compile(r"^/d/([^/?]+)(?:/[^?]+)?(?:\\?.*)?$")

missing = []
for p in paths:
    doc = json.loads(p.read_text(encoding="utf-8"))
    dash = doc.get("dashboard") or {}
    src = dash.get("uid")

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "url" and isinstance(v, str):
                    yield v
                else:
                    yield from walk(v)
        elif isinstance(x, list):
            for it in x:
                yield from walk(it)

    for url in walk(dash):
        m = uid_re.match(url)
        if not m:
            continue
        target = m.group(1)
        if target not in uids:
            missing.append(f"{src}: {url} -> missing_uid={target}")

report = out_dir / "link_uid_report.txt"
if missing:
    report.write_text("\n".join(missing) + "\n", encoding="utf-8")
    raise SystemExit("Missing linked UIDs; see " + str(report))
report.write_text("ok\n", encoding="utf-8")
print("ok")
PY
pass "dashpack.link_uids" "$links_report"

echo "==> 6) Optional: Prometheus-local smoke (execution_watch metric present)"
prom_out="$VERIFY_OUT_DIR/prom_query_execution_watch_present.json"
prom_q='((absent(peak_trade_execution_watch_requests_total) OR on() vector(0)))'
if bash "$PROM_HELPER" --base "$PROM_URL" --query "$prom_q" --out "$prom_out" --retries 5 --timeout 3 >/dev/null; then
  if ! python3 - <<PY
import json
from pathlib import Path
doc=json.loads(Path("$prom_out").read_text(encoding="utf-8"))
data=doc.get("data") or {}
res=data.get("result") or []
if not res:
  raise SystemExit("empty result")
val = (((res[0] or {}).get("value") or [None, None])[1])
if str(val) != "0":
  raise SystemExit(f"expected 0 (PRESENT) got {val!r}")
PY
  then
    fail "prometheus.execution_watch.present" "Prometheus query indicates execution_watch metric is MISSING" "Ensure peak_trade_web emits execution_watch metrics and Prometheus-local scrapes it"
  fi
  pass "prometheus.execution_watch.present" "$prom_out"
else
  pass "prometheus.execution_watch.present" "SKIP (prometheus not reachable?) evidence=$prom_out"
fi

echo "RESULT=PASS"
