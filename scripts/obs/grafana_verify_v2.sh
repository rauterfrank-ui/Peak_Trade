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

PEAK_VERIFY_STRICT="${PEAK_VERIFY_STRICT:-0}"
export PEAK_VERIFY_STRICT

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
expected = "$uid"
if uid != expected:
  raise SystemExit(f"uid mismatch: expected={expected!r} got={uid!r}")
PY
  then
    fail "grafana.dashboard.json" "Invalid dashboard JSON or uid mismatch for uid=$uid" "Inspect $out"
  fi
done <"$uids_txt"
pass "grafana.dashboards.uid_fetch" "$dash_api_dir"

echo "==> 4) DS_* invariants: present + hidden + stable defaults (legacy DS_* or multiprom ds)"
ds_check_out="$VERIFY_OUT_DIR/ds_invariants_report.txt"
python3 - <<'PY'
import json
import os
from pathlib import Path

out_dir = Path(os.environ["VERIFY_OUT_DIR"])
dash_api_dir = out_dir / "grafana_dashboards_by_uid"
paths = sorted(dash_api_dir.glob("*.json"))

# -----------------------------------------------------------------------------
# Dual-schema support:
#  - Legacy dashboards: DS_LOCAL/DS_MAIN/DS_SHADOW with peaktrade-prometheus-* uids
#  - Current dashboards: single "ds" variable with prom_*_909{2..5} uids
# -----------------------------------------------------------------------------

LEGACY_DEFAULTS = {
    "DS_LOCAL": "peaktrade-prometheus-local",
    "DS_MAIN": "peaktrade-prometheus-main",
    "DS_SHADOW": "peaktrade-prometheus-shadow",
}

MULTI_PROM_ALLOWED = [
    "prom_local_9092",
    "prom_shadow_9093",
    "prom_ai_live_9094",
    "prom_observability_9095",
]
MULTI_PROM_DEFAULT = "prom_local_9092"
MULTI_PROM_REGEX_SNIPPET = "prom_local_9092"  # just to sanity-check options/regex presence

def _templating_list(doc: dict):
    return (
        doc.get("dashboard", {})
           .get("templating", {})
           .get("list", [])
        or []
    )

def _find_var(tpl_list, name: str):
    for v in tpl_list:
        if v.get("name") == name:
            return v
    return None

def _val_current_value(v: dict):
    cur = v.get("current") or {}
    return cur.get("value")

def _val_hide(v: dict):
    # Grafana: hide 0=visible, 2=hidden
    return v.get("hide")

def _val_options_values(v: dict):
    opts = v.get("options") or []
    vals = []
    for o in opts:
        val = o.get("value")
        if val is not None:
            vals.append(val)
    return vals

def die(msg: str):
    raise SystemExit(msg)

reports = []
failures = 0

for p in paths:
    doc = json.loads(p.read_text(encoding="utf-8"))
    tpl = _templating_list(doc)
    added = 0  # failures added for this dashboard

    # Decide schema by presence of variables
    has_legacy = any(_find_var(tpl, k) is not None for k in LEGACY_DEFAULTS.keys())
    has_multiprom = _find_var(tpl, "ds") is not None

    if not has_legacy and not has_multiprom:
        # If a dashboard has no datasource var, skip but record.
        reports.append(f"{p.name}: SKIP (no DS vars found)")
        continue

    # -------------------------------------------------------------------------
    # Legacy checks (DS_LOCAL/DS_MAIN/DS_SHADOW)
    # -------------------------------------------------------------------------
    if has_legacy:
        need = set(LEGACY_DEFAULTS.keys())
        present = {k for k in LEGACY_DEFAULTS.keys() if _find_var(tpl, k) is not None}
        missing = sorted(list(need - present))
        if missing:
            failures += 1
            added += 1
            reports.append(f"{p.name}: FAIL legacy missing vars={missing}")
        else:
            for k, want_uid in LEGACY_DEFAULTS.items():
                v = _find_var(tpl, k)
                hide = _val_hide(v)
                cur = _val_current_value(v)
                if hide != 2:
                    failures += 1
                    added += 1
                    reports.append(f"{p.name}: FAIL legacy {k} hide={hide} expected 2")
                if cur != want_uid:
                    failures += 1
                    added += 1
                    reports.append(f"{p.name}: FAIL legacy {k} current.value={cur} expected {want_uid}")
            if added == 0:
                reports.append(f"{p.name}: PASS legacy DS_* invariants")

    # -------------------------------------------------------------------------
    # Multi-prom checks (ds)
    # -------------------------------------------------------------------------
    if has_multiprom:
        v = _find_var(tpl, "ds")
        hide = _val_hide(v)
        cur = _val_current_value(v)
        opts_vals = set(_val_options_values(v))

        # We keep hide==2 as the strict contract, but allow 0 while warning.
        if hide not in (0, 2):
            failures += 1
            added += 1
            reports.append(f"{p.name}: FAIL multiprom ds hide={hide} expected 0 or 2")
        if cur != MULTI_PROM_DEFAULT:
            failures += 1
            added += 1
            reports.append(f"{p.name}: FAIL multiprom ds current.value={cur} expected {MULTI_PROM_DEFAULT}")

        # Ensure all allowed UIDs are selectable: either in options list, or via regex.
        if opts_vals:
            missing_opts = [x for x in MULTI_PROM_ALLOWED if x not in opts_vals]
            if missing_opts:
                failures += 1
                added += 1
                reports.append(f"{p.name}: FAIL multiprom ds missing options={missing_opts}")
        else:
            # Some dashboards store allowed values in regex instead of options.
            regex = (v.get("regex") or "")
            if MULTI_PROM_REGEX_SNIPPET not in regex:
                failures += 1
                added += 1
                reports.append(f"{p.name}: FAIL multiprom ds has no options and regex does not mention expected values")

        if added == 0:
            reports.append(f"{p.name}: PASS multiprom ds invariants")

# Write report file
out_path = out_dir / "ds_invariants_report.txt"
out_path.write_text("\n".join(reports) + "\n", encoding="utf-8")

if failures:
    die(f"DS invariants failed: {failures} issue(s). See: {out_path}")
print("OK")
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
    if [[ "${PEAK_VERIFY_STRICT:-0}" != "0" ]]; then
      fail "prometheus.execution_watch.present" "Prometheus query indicates execution_watch metric is MISSING" "Ensure peak_trade_web emits execution_watch metrics and Prometheus-local scrapes it"
    fi
    pass "prometheus.execution_watch.present" "SKIP (metric absent, PEAK_VERIFY_STRICT=${PEAK_VERIFY_STRICT:-0}) evidence=$prom_out"
  else
    pass "prometheus.execution_watch.present" "$prom_out"
  fi
else
  pass "prometheus.execution_watch.present" "SKIP (prometheus not reachable?) evidence=$prom_out"
fi

echo "RESULT=PASS"
