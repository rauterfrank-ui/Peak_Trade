#!/usr/bin/env python3
"""
Grafana Dashpack — Datasource Variable Canonicalization

Goal
  Canonicalize all provisioned dashboards to use a single datasource variable: ${ds}

Rules (idempotent)
  - Remove legacy datasource variables: DS_LOCAL, DS_MAIN, DS_SHADOW
  - Ensure variable "ds" exists (type=datasource, query=prometheus) with:
      regex: ^(prom_local_9092|prom_shadow_9093|prom_ai_live_9094|prom_observability_9095)$
      refresh: 1
      current: prom_local_9092 (text+value)
  - Rewrite all Prometheus datasource references to {"type":"prometheus","uid":"${ds}"} when uid is not already "${ds}"
  - Replace string occurrences of ${DS_LOCAL}/${DS_MAIN}/${DS_SHADOW} -> ${ds} (and $DS_* -> $ds)

Usage
  python3 scripts/obs/grafana_dashpack_ds_var_canonicalize.py --dry-run
  python3 scripts/obs/grafana_dashpack_ds_var_canonicalize.py --apply
  python3 scripts/obs/grafana_dashpack_ds_var_canonicalize.py --apply --paths docs/webui/observability/grafana/dashboards/overview
  python3 scripts/obs/grafana_dashpack_ds_var_canonicalize.py --dry-run --out .local_tmp/ds_var_report.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable


LEGACY_DS_VARS = {"DS_LOCAL", "DS_MAIN", "DS_SHADOW"}

CANON_DS_NAME = "ds"
CANON_DS_LABEL = "Datasource"
CANON_DS_QUERY = "prometheus"
CANON_DS_REGEX = "^(prom_local_9092|prom_shadow_9093|prom_ai_live_9094|prom_observability_9095)$"
CANON_DS_REFRESH = 1
CANON_DS_DEFAULT = "prom_local_9092"


@dataclass(frozen=True)
class Change:
    kind: str
    path: str
    before: Any
    after: Any


def _iter_dashboard_files(paths: list[str]) -> list[Path]:
    if not paths:
        paths = ["docs/webui/observability/grafana/dashboards"]

    out: list[Path] = []
    for raw in paths:
        # Allow glob patterns and plain paths
        if any(ch in raw for ch in ["*", "?", "["]):
            out.extend(Path().glob(raw))
            continue

        p = Path(raw)
        if p.is_dir():
            out.extend(p.glob("**/*.json"))
        elif p.is_file() and p.suffix == ".json":
            out.append(p)
        else:
            # Best-effort: treat as glob-like
            out.extend(Path().glob(raw))

    files = sorted({p for p in out if p.is_file() and p.suffix == ".json"})
    return files


def _ensure_templating_list(doc: dict) -> list[Change]:
    changes: list[Change] = []
    templ = doc.get("templating")
    if not isinstance(templ, dict):
        doc["templating"] = {"list": []}
        changes.append(Change("add", "$.templating", None, {"list": []}))
        return changes
    lst = templ.get("list")
    if not isinstance(lst, list):
        templ["list"] = []
        changes.append(Change("add", "$.templating.list", None, []))
    return changes


def _canonical_ds_var() -> dict[str, Any]:
    # Note: for datasource variables, Grafana stores current.value as datasource UID.
    # In the target local stack, names and UIDs are stable and match these strings.
    return {
        "name": CANON_DS_NAME,
        "label": CANON_DS_LABEL,
        "type": "datasource",
        "query": CANON_DS_QUERY,
        "regex": CANON_DS_REGEX,
        "refresh": CANON_DS_REFRESH,
        "hide": 0,
        "multi": False,
        "includeAll": False,
        "allValue": None,
        "sort": 0,
        "skipUrlSync": False,
        "current": {"text": CANON_DS_DEFAULT, "value": CANON_DS_DEFAULT},
        "options": [],
    }


def _canonicalize_templating(doc: dict) -> tuple[list[Change], int, bool]:
    """
    Returns: (changes, legacy_vars_removed_count, ds_added)
    """
    changes: list[Change] = []
    _ensure_templating_list(doc)
    templ_list = doc["templating"]["list"]
    assert isinstance(templ_list, list)

    # Remove legacy vars
    before_len = len(templ_list)
    new_list: list[Any] = []
    removed = 0
    for i, v in enumerate(templ_list):
        if isinstance(v, dict) and v.get("name") in LEGACY_DS_VARS and v.get("type") == "datasource":
            removed += 1
            changes.append(Change("remove", f"$.templating.list[{i}]", v, None))
            continue
        new_list.append(v)
    if removed:
        doc["templating"]["list"] = new_list
        templ_list = new_list
    assert len(templ_list) == (before_len - removed)

    # Ensure ds var exists (update if present, insert if absent)
    ds_added = False
    ds_idx = None
    for i, v in enumerate(templ_list):
        if isinstance(v, dict) and v.get("name") == CANON_DS_NAME and v.get("type") == "datasource":
            ds_idx = i
            break

    canon = _canonical_ds_var()
    if ds_idx is None:
        templ_list.insert(0, canon)
        changes.append(Change("add", "$.templating.list[0]", None, canon))
        ds_added = True
    else:
        cur = templ_list[ds_idx]
        assert isinstance(cur, dict)
        # Minimal but strict: set required canonical fields
        for k, v in canon.items():
            if cur.get(k) != v:
                before = cur.get(k)
                cur[k] = v
                changes.append(Change("set", f"$.templating.list[{ds_idx}].{k}", before, v))

    return changes, removed, ds_added


def _rewrite_string_refs(node: Any, base_path: str = "$") -> list[Change]:
    changes: list[Change] = []

    if isinstance(node, dict):
        for k, v in list(node.items()):
            child = f"{base_path}.{k}"
            changes.extend(_rewrite_string_refs(v, child))
        return changes

    if isinstance(node, list):
        for i, it in enumerate(node):
            child = f"{base_path}[{i}]"
            changes.extend(_rewrite_string_refs(it, child))
        return changes

    if isinstance(node, str):
        before = node
        after = before
        after = after.replace("${DS_LOCAL}", "${ds}")
        after = after.replace("${DS_MAIN}", "${ds}")
        after = after.replace("${DS_SHADOW}", "${ds}")
        after = after.replace("$DS_LOCAL", "$ds")
        after = after.replace("$DS_MAIN", "$ds")
        after = after.replace("$DS_SHADOW", "$ds")
        # Also remove plain-token occurrences (e.g. in markdown titles, and URL-encoded "$%7BDS_LOCAL%7D")
        after = re.sub(r"\bDS_LOCAL\b", "ds", after)
        after = re.sub(r"\bDS_MAIN\b", "ds", after)
        after = re.sub(r"\bDS_SHADOW\b", "ds", after)
        # URL-encoded forms (e.g. "%7BDS_LOCAL%7D") don't satisfy \b boundaries due to hex chars.
        after = after.replace("DS_LOCAL", "ds").replace("DS_MAIN", "ds").replace("DS_SHADOW", "ds")
        if after != before:
            changes.append(Change("replace", base_path, before, after))
        return changes

    return changes


def _is_prometheus_datasource_dict(ds: Any) -> bool:
    return isinstance(ds, dict) and ds.get("type") == "prometheus"


def _canonical_prom_ds() -> dict[str, str]:
    return {"type": "prometheus", "uid": "${ds}"}


def _rewrite_prometheus_datasources(node: Any, base_path: str = "$") -> list[Change]:
    changes: list[Change] = []

    if isinstance(node, dict):
        if "datasource" in node:
            ds = node["datasource"]
            if _is_prometheus_datasource_dict(ds):
                uid = ds.get("uid")
                if uid != "${ds}":
                    before = dict(ds)
                    node["datasource"] = _canonical_prom_ds()
                    changes.append(Change("set", f"{base_path}.datasource", before, node["datasource"]))
            elif isinstance(ds, str):
                # old-style string datasource (only rewrite when it's clearly prometheus-ish)
                if ds == "prometheus" or ds.startswith("prom_") or ds.startswith("prometheus") or ds.startswith("peaktrade-prometheus") or ds.startswith("${DS_") or ds.startswith("$DS_") or ds.startswith("DS_"):
                    before = ds
                    node["datasource"] = _canonical_prom_ds()
                    changes.append(Change("set", f"{base_path}.datasource", before, node["datasource"]))

        for k, v in list(node.items()):
            child = f"{base_path}.{k}"
            changes.extend(_rewrite_prometheus_datasources(v, child))
        return changes

    if isinstance(node, list):
        for i, it in enumerate(node):
            child = f"{base_path}[{i}]"
            changes.extend(_rewrite_prometheus_datasources(it, child))
        return changes

    return changes


def canonicalize_dashboard(doc: dict) -> tuple[dict, list[Change], dict[str, int]]:
    changes: list[Change] = []
    stats = {
        "legacy_vars_removed": 0,
        "ds_vars_added": 0,
        "ds_var_fields_set": 0,
        "string_rewrites": 0,
        "prom_ds_rewrites": 0,
    }

    templ_changes, removed, ds_added = _canonicalize_templating(doc)
    changes.extend(templ_changes)
    stats["legacy_vars_removed"] += removed
    stats["ds_vars_added"] += 1 if ds_added else 0
    stats["ds_var_fields_set"] += sum(1 for c in templ_changes if c.kind == "set" and c.path.startswith("$.templating.list["))

    string_changes = _rewrite_string_refs(doc)
    if string_changes:
        # Apply the string rewrites via a second pass mutating walk (we stored only changes)
        # For idempotency + correctness, we mutate in-place while walking again.
        _apply_string_changes(doc)
        changes.extend(string_changes)
        stats["string_rewrites"] += len(string_changes)

    prom_changes = _rewrite_prometheus_datasources(doc)
    changes.extend(prom_changes)
    stats["prom_ds_rewrites"] += len(prom_changes)

    return doc, changes, stats


def _apply_string_changes(node: Any) -> None:
    if isinstance(node, dict):
        for k, v in list(node.items()):
            if isinstance(v, str):
                node[k] = (
                    v.replace("${DS_LOCAL}", "${ds}")
                    .replace("${DS_MAIN}", "${ds}")
                    .replace("${DS_SHADOW}", "${ds}")
                    .replace("$DS_LOCAL", "$ds")
                    .replace("$DS_MAIN", "$ds")
                    .replace("$DS_SHADOW", "$ds")
                )
                node[k] = re.sub(r"\bDS_LOCAL\b", "ds", node[k])
                node[k] = re.sub(r"\bDS_MAIN\b", "ds", node[k])
                node[k] = re.sub(r"\bDS_SHADOW\b", "ds", node[k])
                node[k] = node[k].replace("DS_LOCAL", "ds").replace("DS_MAIN", "ds").replace("DS_SHADOW", "ds")
            else:
                _apply_string_changes(v)
    elif isinstance(node, list):
        for i, it in enumerate(node):
            if isinstance(it, str):
                node[i] = (
                    it.replace("${DS_LOCAL}", "${ds}")
                    .replace("${DS_MAIN}", "${ds}")
                    .replace("${DS_SHADOW}", "${ds}")
                    .replace("$DS_LOCAL", "$ds")
                    .replace("$DS_MAIN", "$ds")
                    .replace("$DS_SHADOW", "$ds")
                )
                node[i] = re.sub(r"\bDS_LOCAL\b", "ds", node[i])
                node[i] = re.sub(r"\bDS_MAIN\b", "ds", node[i])
                node[i] = re.sub(r"\bDS_SHADOW\b", "ds", node[i])
                node[i] = node[i].replace("DS_LOCAL", "ds").replace("DS_MAIN", "ds").replace("DS_SHADOW", "ds")
            else:
                _apply_string_changes(it)


def main() -> int:
    parser = argparse.ArgumentParser(description="Canonicalize Grafana dashpack datasource variable to ${ds}.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="dry run (default)")
    mode.add_argument("--apply", action="store_true", help="apply changes in-place")
    parser.add_argument(
        "--paths",
        nargs="*",
        default=[],
        help="files/dirs/globs to scan (default: docs/webui/observability/grafana/dashboards)",
    )
    parser.add_argument("--out", default=None, help="optional JSON report output path")
    args = parser.parse_args()

    apply = bool(args.apply)
    if not args.apply and not args.dry_run:
        # default
        apply = False

    files = _iter_dashboard_files(args.paths)
    if not files:
        print("ERROR: no dashboard json files found (check --paths)", file=sys.stderr)
        return 2

    dashboards_scanned = 0
    dashboards_modified = 0
    total_changes = 0
    totals = {
        "legacy_vars_removed": 0,
        "ds_vars_added": 0,
        "ds_var_fields_set": 0,
        "string_rewrites": 0,
        "prom_ds_rewrites": 0,
    }

    report: dict[str, Any] = {
        "dashboards_scanned": 0,
        "dashboards_modified": 0,
        "totals": {},
        "files": [],
    }

    for p in files:
        dashboards_scanned += 1
        try:
            raw = p.read_text(encoding="utf-8")
            doc = json.loads(raw)
        except Exception as e:  # noqa: BLE001 - CLI tool
            print(f"ERROR: failed to parse {p}: {e}", file=sys.stderr)
            return 2

        if not isinstance(doc, dict):
            print(f"ERROR: unexpected dashboard JSON root type in {p} (expected object)", file=sys.stderr)
            return 2

        _, changes, stats = canonicalize_dashboard(doc)

        dashboards_changed = bool(changes)
        if dashboards_changed:
            dashboards_modified += 1
            total_changes += len(changes)
            for k in totals:
                totals[k] += stats.get(k, 0)

        # Console output (compact)
        if dashboards_changed:
            print(f"{p}: changes={len(changes)}")
            for c in changes[:10]:
                print(f"  - {c.kind} {c.path}")
            if len(changes) > 10:
                print(f"  - ... ({len(changes) - 10} more)")
        else:
            print(f"{p}: ok")

        if dashboards_changed and apply:
            p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        report["files"].append(
            {
                "path": str(p),
                "changed": dashboards_changed,
                "changes": [asdict(c) for c in changes],
                "stats": stats,
            }
        )

    report["dashboards_scanned"] = dashboards_scanned
    report["dashboards_modified"] = dashboards_modified
    report["totals"] = totals

    print(
        "SUMMARY "
        + " ".join(
            [
                f"dashboards_scanned={dashboards_scanned}",
                f"dashboards_modified={dashboards_modified}",
                f"changes={total_changes}",
                f"legacy_vars_removed={totals['legacy_vars_removed']}",
                f"ds_vars_added={totals['ds_vars_added']}",
                f"string_rewrites={totals['string_rewrites']}",
                f"prom_ds_rewrites={totals['prom_ds_rewrites']}",
            ]
        )
    )

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"WROTE report={out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
