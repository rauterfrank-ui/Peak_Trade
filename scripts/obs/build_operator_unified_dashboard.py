#!/usr/bin/env python3
"""Build unified Operator dashboard: Operator Home + AI Live (Execution Watch)."""

import copy
import json
import pathlib
import re

# --- datasource pinning (Grafana-only) ---
UID_SHADOW = "prom_local_9092"
ROW_TITLES_SHADOW = {
    "Stack Fingerprint",
    "Health invariants (shadow)",
    "Shadow pipeline signals (throughput, errors, latency, risk blocks)",
}
# Panels that use metrics from metricsd/web (Prom 9092), not AI Live (9094)
SIGNALS_ORDERS_PANEL_TITLES = {
    "Total Signals (Range)",
    "Signals / min (1m)",
    "Orders Approved (Range)",
    "Orders Blocked (Range)",
}
_SHADOW_EXPR_PAT = re.compile(
    r"(shadow_mvs|peaktrade_shadow|shadow_|pipeline_|risk_block|intent\s*→\s*ack)",
    re.IGNORECASE,
)


def _pin_panel_to_shadow(panel: dict) -> None:
    panel["datasource"] = {"type": "prometheus", "uid": UID_SHADOW}
    for t in panel.get("targets", []) or []:
        ds = t.get("datasource")
        if isinstance(ds, dict) and ds.get("type") == "prometheus":
            t["datasource"] = {"type": "prometheus", "uid": UID_SHADOW}


def _panel_is_shadow(panel: dict) -> bool:
    title = panel.get("title") or ""
    if "shadow" in title.lower() or "pipeline" in title.lower():
        return True
    for t in panel.get("targets", []) or []:
        expr = t.get("expr") or ""
        if _SHADOW_EXPR_PAT.search(expr):
            return True
    return False


def _pin_shadow_panels_in_dashboard(d: dict) -> None:
    active_shadow_row = False
    for panel in d.get("panels", []) or []:
        if not isinstance(panel, dict):
            continue
        if panel.get("type") == "row":
            t = (panel.get("title") or "").strip()
            active_shadow_row = t in ROW_TITLES_SHADOW
            continue
        if active_shadow_row or _panel_is_shadow(panel):
            _pin_panel_to_shadow(panel)


def _pin_stack_fingerprint_panels(d: dict) -> None:
    """Pin Stack Fingerprint panels to prom_local_9092 regardless of $ds."""
    for panel in d.get("panels") or []:
        if not isinstance(panel, dict):
            continue
        title = (panel.get("title") or "").strip()
        if not title.startswith("Stack Fingerprint:"):
            continue
        panel["datasource"] = {"type": "prometheus", "uid": UID_SHADOW}


def _pin_signals_orders_panels(d: dict) -> None:
    """Pin Signals/Orders panels to prom_local_9092 (metricsd/web), not $ds (AI Live)."""
    for panel in d.get("panels") or []:
        if not isinstance(panel, dict):
            continue
        title = (panel.get("title") or "").strip()
        if title not in SIGNALS_ORDERS_PANEL_TITLES:
            continue
        panel["datasource"] = {"type": "prometheus", "uid": UID_SHADOW}
        for t in panel.get("targets", []) or []:
            if (
                isinstance(t.get("datasource"), dict)
                and t["datasource"].get("type") == "prometheus"
            ):
                t["datasource"] = {"type": "prometheus", "uid": UID_SHADOW}
            elif "expr" in t:
                t["datasource"] = {"type": "prometheus", "uid": UID_SHADOW}


# Panels to make robust to 0/NaN (show 0 instead of "No data")
NODATA_ROBUST_TITLES = (
    "Total Signals (Range)",
    "Signals / min (1m)",
    "Orders Approved (Range)",
    "Orders Blocked (Range)",
    "Execution Watch req/s (by endpoint, status)",
    "Execution Watch latency p95 (by endpoint)",
)


def _walk_panels(panels):
    for p in panels or []:
        if not isinstance(p, dict):
            continue
        yield p
        for child in _walk_panels(p.get("panels") or []):
            yield child


def _apply_nodata_robustness(d: dict) -> None:
    """Set noValue=0, spanNulls, relax reduce (last), drop filtering transforms for no-data tiles."""
    for panel in _walk_panels(d.get("panels") or []):
        title = (panel.get("title") or "").strip()
        if title not in NODATA_ROBUST_TITLES:
            continue
        fc = panel.setdefault("fieldConfig", {})
        defaults = fc.setdefault("defaults", {})
        defaults["noValue"] = "0"
        defaults.setdefault("custom", {})["spanNulls"] = True
        xforms = panel.get("transformations") or []
        keep = [
            t
            for t in xforms
            if (t.get("id") or "").lower()
            not in {"filterfieldsbyname", "filterbyvalue", "organize", "groupby", "reduce"}
        ]
        if keep != xforms:
            panel["transformations"] = keep
        if (panel.get("type") or "").lower() in {"stat", "gauge", "bargauge", "table"}:
            ro = panel.setdefault("options", {}).setdefault("reduceOptions", {})
            ro["calcs"] = ["last"]
            ro.setdefault("fields", "")
            ro.setdefault("values", False)


src_op = pathlib.Path(
    "docs/webui/observability/grafana/dashboards/overview/peaktrade-operator-home.json"
)
src_ai = pathlib.Path(
    "docs/webui/observability/grafana/dashboards/execution/peaktrade-execution-watch-overview.json"
)
out = pathlib.Path(
    "docs/webui/observability/grafana/dashboards/overview/peaktrade-operator-unified.json"
)

op = json.loads(src_op.read_text())
ai = json.loads(src_ai.read_text())


def ensure_ds_var(d):
    lst = d.setdefault("templating", {}).setdefault("list", [])
    names = {v.get("name") for v in lst if isinstance(v, dict)}
    if "ds" not in names:
        lst.append(
            {
                "name": "ds",
                "type": "datasource",
                "label": "Datasource",
                "query": "prometheus",
                "current": {
                    "selected": True,
                    "text": "prom_ai_live_9094",
                    "value": "prom_ai_live_9094",
                },
                "refresh": 1,
                "options": [],
            }
        )

    # carry over AI variables if missing (run_id used by AI panels/annotations)
    def copy_var(name):
        for v in ai.get("templating", {}).get("list", []):
            if v.get("name") == name and name not in names:
                lst.append(copy.deepcopy(v))

    for nm in ["run_id", "ai_run_id", "accept_markers", "reject_markers"]:
        copy_var(nm)


def max_y(panels):
    m = 0
    for p in panels:
        if not isinstance(p, dict):
            continue
        gp = p.get("gridPos") or {}
        y = gp.get("y", 0)
        h = gp.get("h", 0)
        m = max(m, y + h)
        if "panels" in p:
            m = max(m, max_y(p.get("panels") or []))
    return m


def shift_panels(panels, dy):
    for p in panels:
        if not isinstance(p, dict):
            continue
        gp = p.get("gridPos")
        if isinstance(gp, dict):
            gp["y"] = gp.get("y", 0) + dy
        if "panels" in p:
            shift_panels(p.get("panels") or [], dy)


def extract_ai_sections(ai_obj):
    """Take everything EXCEPT the Stack Fingerprint row to avoid duplicates."""
    out_panels = []
    for p in ai_obj.get("panels", []):
        title = (p.get("title") or "").strip()
        if title == "Stack Fingerprint":
            continue
        out_panels.append(copy.deepcopy(p))
    return out_panels


# Build unified dashboard from operator-home base
u = copy.deepcopy(op)

u["title"] = "Peak_Trade — Operator Unified"
u["uid"] = "peaktrade-operator-unified"
u["tags"] = sorted(set((u.get("tags") or []) + ["operator", "unified", "ai_live"]))
u["schemaVersion"] = u.get("schemaVersion", 39)
u["version"] = int(u.get("version", 0)) + 1
u["time"] = u.get("time") or {"from": "now-1h", "to": "now"}
u["refresh"] = u.get("refresh") or "10s"

ensure_ds_var(u)
# Unified default: AI Live datasource (Stack Fingerprint panels stay pinned to prom_local_9092)
for v in u.get("templating", {}).get("list", []):
    if isinstance(v, dict) and v.get("name") == "ds":
        v["current"] = {"selected": True, "text": "prom_ai_live_9094", "value": "prom_ai_live_9094"}
        break

base_panels = u.get("panels", []) or []
dy = max_y(base_panels) + 1

ai_panels = extract_ai_sections(ai)
shift_panels(ai_panels, dy)

# Row divider for AI section
base_panels.append(
    {
        "type": "row",
        "title": "AI Live (Execution Watch)",
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": dy},
        "panels": [],
    }
)
shift_panels(ai_panels, 1)
base_panels.extend(ai_panels)

u["panels"] = base_panels

# Optional: carry over annotations from AI dashboard (accept/reject markers)
if ai.get("annotations") and not u.get("annotations", {}).get("list"):
    u["annotations"] = copy.deepcopy(ai["annotations"])
elif ai.get("annotations") and u.get("annotations", {}).get("list"):
    existing = {a.get("name") for a in u["annotations"]["list"] if isinstance(a, dict)}
    for a in ai["annotations"].get("list", []):
        if isinstance(a, dict) and a.get("name") not in existing:
            u["annotations"]["list"].append(copy.deepcopy(a))

_pin_shadow_panels_in_dashboard(u)
_pin_stack_fingerprint_panels(u)
_pin_signals_orders_panels(u)
_apply_nodata_robustness(u)

out.write_text(json.dumps(u, indent=2) + "\n")
print("WROTE", out)
