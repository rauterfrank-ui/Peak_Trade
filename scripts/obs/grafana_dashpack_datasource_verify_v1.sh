#!/usr/bin/env bash
set -euo pipefail

# Grafana Dashpack Datasource Verify v1 (API-based, file-backed)
#
# Output:
# - .local_tmp/grafana_ds_verify_<UTCSTAMP>/
#   - datasources.json
#   - dashboards_list.json
#   - dashboard_<uid>.json (one per dashboard)
#   - DS_VERIFY_SUMMARY.txt
#
# Auth:
# - Uses Basic Auth from env GRAFANA_AUTH (user:pass), default admin:admin

cd "$(git rev-parse --show-toplevel)"

GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}"
GRAFANA_AUTH="${GRAFANA_AUTH:-admin:admin}"

RUN_TS_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR=".local_tmp/grafana_ds_verify_${RUN_TS_UTC}"
mkdir -p "$OUT_DIR"
export OUT_DIR
export GRAFANA_URL

curl -sS -u "$GRAFANA_AUTH" "$GRAFANA_URL/api/datasources" -o "$OUT_DIR/datasources.json"
curl -sS -u "$GRAFANA_AUTH" "$GRAFANA_URL/api/search?type=dash-db" -o "$OUT_DIR/dashboards_list.json"

python3 - <<'PY'
import json
import os
from pathlib import Path

out_dir = Path(os.environ["OUT_DIR"])
ds_path = out_dir / "datasources.json"
lst_path = out_dir / "dashboards_list.json"

datasources = json.loads(ds_path.read_text(encoding="utf-8"))
uids = {d.get("uid") for d in datasources if isinstance(d, dict) and isinstance(d.get("uid"), str)}

search = json.loads(lst_path.read_text(encoding="utf-8"))
dash_uids = []
for it in search:
    if not isinstance(it, dict):
        continue
    uid = it.get("uid")
    if isinstance(uid, str) and uid:
        dash_uids.append(uid)

(out_dir / "dashboard_uids.txt").write_text("\n".join(sorted(set(dash_uids))) + "\n", encoding="utf-8")
(out_dir / "datasource_uids.txt").write_text("\n".join(sorted(uids)) + "\n", encoding="utf-8")
print(f"dashboards={len(set(dash_uids))} datasources={len(uids)}")
PY

while IFS= read -r uid; do
  [ -n "$uid" ] || continue
  curl -sS -u "$GRAFANA_AUTH" "$GRAFANA_URL/api/dashboards/uid/$uid" -o "$OUT_DIR/dashboard_${uid}.json"
done <"$OUT_DIR/dashboard_uids.txt"

python3 - <<'PY'
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ALLOW_UIDS = {
    "peaktrade-prometheus-local",
    "peaktrade-prometheus-main",
    "peaktrade-prometheus-shadow",
    "peaktrade-prometheus",
}
ALLOW_NAMES = {"prometheus-local", "prometheus-main", "prometheus-shadow", "prometheus"}

out_dir = Path(os.environ["OUT_DIR"])
ds_uids = set((out_dir / "datasource_uids.txt").read_text(encoding="utf-8").splitlines())


@dataclass(frozen=True)
class Offender:
    dashboard_uid: str
    file: str
    path: str
    value: str
    reason: str


def is_str(x: Any) -> bool:
    return isinstance(x, str) and len(x) > 0


def walk_ds_refs(node: Any, base: str = ""):
    if isinstance(node, dict):
        if "datasource" in node:
            yield (base + ".datasource" if base else "datasource", node["datasource"])
        for k, v in node.items():
            child = f"{base}.{k}" if base else str(k)
            yield from walk_ds_refs(v, child)
    elif isinstance(node, list):
        for i, it in enumerate(node):
            child = f"{base}[{i}]" if base else f"[{i}]"
            yield from walk_ds_refs(it, child)


def check_ds_value(v: Any) -> tuple[bool, str]:
    # ok? , reason-if-not
    if v is None:
        return True, "absent_or_null"
    if isinstance(v, dict):
        uid = v.get("uid")
        if uid is None:
            # If no uid is specified, Grafana may use default datasource.
            return True, "dict_no_uid"
        if is_str(uid):
            if uid in ALLOW_UIDS and uid in ds_uids:
                return True, "ok_uid"
            if uid in ALLOW_UIDS and uid not in ds_uids:
                return False, "uid_allowlisted_but_missing_in_runtime"
            if uid in ds_uids:
                return False, "uid_exists_but_not_allowlisted"
            return False, "uid_missing_in_runtime"
        return False, "uid_not_string"
    if is_str(v):
        if v in ALLOW_NAMES:
            return True, "ok_name"
        if v in ALLOW_UIDS:
            return (v in ds_uids), ("ok_uid" if v in ds_uids else "uid_allowlisted_but_missing_in_runtime")
        return False, "string_not_allowlisted"
    return True, "non_string_non_dict"


offenders: list[Offender] = []
total_refs = 0
total_dash = 0

for p in sorted(out_dir.glob("dashboard_*.json")):
    total_dash += 1
    doc = json.loads(p.read_text(encoding="utf-8"))
    dash = doc.get("dashboard") if isinstance(doc, dict) else None
    dash_uid = None
    if isinstance(dash, dict):
        dash_uid = dash.get("uid")
    if not isinstance(dash_uid, str) or not dash_uid:
        dash_uid = p.stem.replace("dashboard_", "")

    # Verify only "datasource" keys (panels/targets/templating/annotations/etc.)
    for path, v in walk_ds_refs(dash if dash is not None else doc):
        ok, reason = check_ds_value(v)
        total_refs += 1
        if not ok:
            # Best-effort render value for summary
            if isinstance(v, dict):
                vv = json.dumps(v, sort_keys=True)
            else:
                vv = repr(v)
            offenders.append(
                Offender(
                    dashboard_uid=dash_uid,
                    file=p.name,
                    path=path,
                    value=vv,
                    reason=reason,
                )
            )

hard_ok = len(offenders) == 0

summary_lines = []
summary_lines.append(f"hard_ok={str(hard_ok)}")
summary_lines.append(f"grafana_url={os.environ.get('GRAFANA_URL','')}")
summary_lines.append(f"dashboards={total_dash}")
summary_lines.append(f"datasource_refs_scanned={total_refs}")
summary_lines.append(f"offenders={len(offenders)}")
summary_lines.append("")
if offenders:
    summary_lines.append("OFFENDERS:")
    for o in offenders:
        summary_lines.append(f"- dashboard_uid={o.dashboard_uid} file={o.file} path={o.path} reason={o.reason} value={o.value}")

(out_dir / "DS_VERIFY_SUMMARY.txt").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
print("\n".join(summary_lines))
PY

echo "OUT_DIR=$OUT_DIR"
