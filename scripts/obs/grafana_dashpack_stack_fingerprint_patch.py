#!/usr/bin/env python3
"""
Grafana Dashpack — Stack Fingerprint Patch

Patch a dashboard JSON by inserting a deterministic "Stack Fingerprint" block at the top.

Primary target:
  docs/webui/observability/grafana/dashboards/overview/peaktrade-operator-home.json

Design goals:
- deterministic: fixed grid positions
- idempotent: safe re-run; no duplicate panels; no repeated y-shifts
- backup: .ops_local/backup_dashboards/...
- all new panels: datasource.uid == "${ds}"

Usage:
  python3 scripts/obs/grafana_dashpack_stack_fingerprint_patch.py --dashboard <path>            # dry-run
  python3 scripts/obs/grafana_dashpack_stack_fingerprint_patch.py --dashboard <path> --apply   # apply + backup
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


FINGERPRINT_ROW_TITLE = "Stack Fingerprint"
PANEL_TITLES = {
    "active": "Stack Fingerprint: Active Stacks",
    "count": "Stack Fingerprint: Target Count",
    "table": "Stack Fingerprint: Targets UP",
}

# Fixed layout (Grafana grid is 24 columns wide)
# We insert:
#   row: y=0 h=1 w=24
#   stats row: y=1 h=6 (two stats side-by-side, each w=12)
#   table: y=7 h=10 w=24
INSERT_BLOCK_HEIGHT = 17  # total y-shift applied to existing panels once


def utc_ts_compact() -> str:
    return dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    # Keep it stable-ish; deterministic output helps reviews.
    txt = json.dumps(payload, indent=2, ensure_ascii=False)
    path.write_text(txt + "\n", encoding="utf-8")


def ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def backup_file(src: Path, repo_root: Path) -> Path:
    rel = src.relative_to(repo_root)
    out = (
        repo_root
        / ".ops_local"
        / "backup_dashboards"
        / rel.parent
        / f"{rel.stem}.{utc_ts_compact()}.bak.json"
    )
    ensure_parent(out)
    out.write_bytes(src.read_bytes())
    return out


def get_repo_root(start: Path) -> Path:
    # best-effort: walk up until .git found
    cur = start.resolve()
    for _ in range(20):
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start.resolve()


def find_dashboard_panels(dash: Dict[str, Any]) -> List[Dict[str, Any]]:
    panels = dash.get("panels")
    if isinstance(panels, list):
        return panels
    return []


def max_panel_id(panels: List[Dict[str, Any]]) -> int:
    m = 0
    for p in panels:
        try:
            m = max(m, int(p.get("id", 0)))
        except Exception:
            pass
    return m


def has_fingerprint_block(panels: List[Dict[str, Any]]) -> bool:
    # detect by row title OR any of the expected panel titles
    for p in panels:
        if str(p.get("type", "")).lower() == "row" and p.get("title") == FINGERPRINT_ROW_TITLE:
            return True
        t = p.get("title")
        if t in PANEL_TITLES.values():
            return True
    return False


def shift_panels_down(panels: List[Dict[str, Any]], delta_y: int) -> None:
    for p in panels:
        gp = p.get("gridPos")
        if isinstance(gp, dict) and "y" in gp:
            try:
                gp["y"] = int(gp["y"]) + delta_y
            except Exception:
                # if y is weird, don’t crash; keep as-is
                pass


def mk_datasource(uid_expr: str = "${ds}") -> Dict[str, Any]:
    return {"type": "prometheus", "uid": uid_expr}


def mk_row_panel(panel_id: int) -> Dict[str, Any]:
    return {
        "id": panel_id,
        "type": "row",
        "title": FINGERPRINT_ROW_TITLE,
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0},
        "panels": [],
    }


def mk_stat_panel_active_stacks(panel_id: int) -> Dict[str, Any]:
    return {
        "id": panel_id,
        "type": "stat",
        "title": PANEL_TITLES["active"],
        "datasource": mk_datasource("${ds}"),
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 1},
        "targets": [
            {
                "refId": "A",
                "expr": 'count by (stack) (up{stack=~".+"})',
                "instant": True,
                "range": False,
                "legendFormat": "{{stack}}",
            }
        ],
        "options": {
            "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""},
            "orientation": "horizontal",
            "textMode": "auto",
            "colorMode": "value",
            "graphMode": "none",
            "justifyMode": "auto",
        },
        "fieldConfig": {
            "defaults": {
                "mappings": [],
                "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]},
            },
            "overrides": [],
        },
    }


def mk_stat_panel_target_count(panel_id: int) -> Dict[str, Any]:
    return {
        "id": panel_id,
        "type": "stat",
        "title": PANEL_TITLES["count"],
        "datasource": mk_datasource("${ds}"),
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 1},
        "targets": [
            {
                "refId": "A",
                "expr": 'count(up{stack=~".+"})',
                "instant": True,
                "range": False,
                "legendFormat": "__auto",
            }
        ],
        "options": {
            "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""},
            "orientation": "horizontal",
            "textMode": "auto",
            "colorMode": "value",
            "graphMode": "none",
            "justifyMode": "auto",
        },
        "fieldConfig": {
            "defaults": {
                "mappings": [],
                "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]},
            },
            "overrides": [],
        },
    }


def mk_table_panel_targets_up(panel_id: int) -> Dict[str, Any]:
    return {
        "id": panel_id,
        "type": "table",
        "title": PANEL_TITLES["table"],
        "datasource": mk_datasource("${ds}"),
        "gridPos": {"h": 10, "w": 24, "x": 0, "y": 7},
        "targets": [
            {
                "refId": "A",
                "expr": 'up{stack=~".+"} == 1',
                "instant": True,
                "range": False,
                "legendFormat": "__auto",
            }
        ],
        "options": {
            "showHeader": True,
            "cellHeight": "sm",
            "footer": {"show": False},
        },
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "align": "auto",
                    "displayMode": "auto",
                    "inspect": False,
                }
            },
            "overrides": [],
        },
    }


def patch_dashboard(dash: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    notes: List[str] = []

    panels = find_dashboard_panels(dash)
    if not panels:
        dash["panels"] = []
        panels = dash["panels"]

    if has_fingerprint_block(panels):
        notes.append("SKIP: fingerprint block already present (idempotent).")
        return dash, notes

    shift_panels_down(panels, INSERT_BLOCK_HEIGHT)
    notes.append(f"SHIFT: moved existing panels down by delta_y={INSERT_BLOCK_HEIGHT}.")

    next_id = max_panel_id(panels) + 1

    row = mk_row_panel(next_id)
    next_id += 1
    p_active = mk_stat_panel_active_stacks(next_id)
    next_id += 1
    p_count = mk_stat_panel_target_count(next_id)
    next_id += 1
    p_table = mk_table_panel_targets_up(next_id)
    next_id += 1

    dash["panels"] = [row, p_active, p_count, p_table] + panels
    notes.append("ADD: inserted row + 3 panels at dashboard top (Stack Fingerprint).")

    return dash, notes


def main() -> int:
    ap = argparse.ArgumentParser(description="Insert Stack Fingerprint block into dashboard JSON.")
    ap.add_argument(
        "--dashboard",
        default="docs/webui/observability/grafana/dashboards/overview/peaktrade-operator-home.json",
        help="Path to dashboard JSON (repo-relative).",
    )
    ap.add_argument(
        "--apply", action="store_true", help="Write changes to file (default is dry-run)."
    )
    args = ap.parse_args()

    dash_path = Path(args.dashboard)
    if not dash_path.exists():
        print(f"ERROR: dashboard not found: {dash_path}")
        return 2

    repo_root = get_repo_root(dash_path.parent)
    abs_dash = (
        (repo_root / dash_path).resolve() if not dash_path.is_absolute() else dash_path.resolve()
    )
    if not abs_dash.exists():
        abs_dash = dash_path.resolve()

    payload = load_json(abs_dash)
    # Grafana JSON may wrap dashboard under "dashboard"
    if "dashboard" in payload and isinstance(payload["dashboard"], dict):
        dash_obj = payload["dashboard"]
        wrapped = True
    else:
        dash_obj = payload
        wrapped = False

    original = copy.deepcopy(dash_obj)
    patched, notes = patch_dashboard(dash_obj)

    changed = json.dumps(original, sort_keys=True) != json.dumps(patched, sort_keys=True)
    print("== Stack Fingerprint Patch ==")
    print(f"dashboard: {abs_dash}")
    for n in notes:
        print(f"- {n}")
    print(f"changed: {changed}")
    print(f"mode: {'APPLY' if args.apply else 'DRY-RUN'}")

    if args.apply and changed:
        b = backup_file(abs_dash, repo_root)
        print(f"backup: {b}")
        if wrapped:
            payload["dashboard"] = patched
            write_json(abs_dash, payload)
        else:
            write_json(abs_dash, patched)
        print("write: OK")
    else:
        print("write: (skipped)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
