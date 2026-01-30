#!/usr/bin/env python3
"""
Grafana Dashpack — Datasource Variable Lint

Fail conditions:
  - Any dashboard contains legacy datasource variables: DS_LOCAL, DS_MAIN, DS_SHADOW
  - Any dashboard contains any string references to DS_LOCAL/DS_MAIN/DS_SHADOW (e.g. ${DS_LOCAL})
  - Any *panel* has a Prometheus datasource uid that is not "${ds}"

Usage:
  python3 scripts/obs/grafana_dashpack_ds_var_lint.py
  python3 scripts/obs/grafana_dashpack_ds_var_lint.py --paths docs/webui/observability/grafana/dashboards
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


LEGACY_DS_VARS = {"DS_LOCAL", "DS_MAIN", "DS_SHADOW"}


@dataclass(frozen=True)
class Finding:
    path: str
    message: str
    value: Any | None = None


def _iter_dashboard_files(paths: list[str]) -> list[Path]:
    if not paths:
        paths = ["docs/webui/observability/grafana/dashboards"]

    out: list[Path] = []
    for raw in paths:
        if any(ch in raw for ch in ["*", "?", "["]):
            out.extend(Path().glob(raw))
            continue
        p = Path(raw)
        if p.is_dir():
            out.extend(p.glob("**/*.json"))
        elif p.is_file() and p.suffix == ".json":
            out.append(p)
        else:
            out.extend(Path().glob(raw))

    files = sorted({p for p in out if p.is_file() and p.suffix == ".json"})
    return files


def _walk_strings(node: Any, base_path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk_strings(v, f"{base_path}.{k}")
    elif isinstance(node, list):
        for i, it in enumerate(node):
            yield from _walk_strings(it, f"{base_path}[{i}]")
    elif isinstance(node, str):
        yield base_path, node


def _walk_panels(dashboard: dict) -> Iterable[tuple[str, dict]]:
    panels = dashboard.get("panels")
    if not isinstance(panels, list):
        return
    stack: list[tuple[str, dict]] = []
    for i, p in enumerate(panels):
        if isinstance(p, dict):
            stack.append((f"$.panels[{i}]", p))
    while stack:
        path, panel = stack.pop()
        yield path, panel
        sub = panel.get("panels")
        if isinstance(sub, list):
            for i, sp in enumerate(sub):
                if isinstance(sp, dict):
                    stack.append((f"{path}.panels[{i}]", sp))


def lint_dashboard(doc: dict) -> list[Finding]:
    findings: list[Finding] = []

    # Legacy variables in templating.list
    templ = doc.get("templating")
    if isinstance(templ, dict):
        lst = templ.get("list")
        if isinstance(lst, list):
            for i, v in enumerate(lst):
                if (
                    isinstance(v, dict)
                    and v.get("type") == "datasource"
                    and v.get("name") in LEGACY_DS_VARS
                ):
                    findings.append(
                        Finding(
                            path=f"$.templating.list[{i}]",
                            message="legacy datasource variable present",
                            value={"name": v.get("name"), "type": v.get("type")},
                        )
                    )

    # Any string occurrence of legacy DS vars (best-effort)
    for path, s in _walk_strings(doc):
        for var in LEGACY_DS_VARS:
            if var in s:
                findings.append(
                    Finding(
                        path=path,
                        message=f"legacy datasource reference string contains {var}",
                        value=s,
                    )
                )
                break

    # Panel Prometheus datasource must be ${ds}
    for ppath, panel in _walk_panels(doc):
        ds = panel.get("datasource")
        if isinstance(ds, dict) and ds.get("type") == "prometheus":
            uid = ds.get("uid")
            if uid != "${ds}":
                findings.append(
                    Finding(
                        path=f"{ppath}.datasource.uid",
                        message='panel prometheus datasource uid must be "${ds}"',
                        value=uid,
                    )
                )
        elif isinstance(ds, str):
            # A panel with string datasource is always suspicious here; require ${ds}
            if ds != "${ds}":
                findings.append(
                    Finding(
                        path=f"{ppath}.datasource",
                        message='panel datasource must be dict with prometheus uid "${ds}" (found string)',
                        value=ds,
                    )
                )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lint Grafana dashpack ds variable canonicalization."
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        default=[],
        help="files/dirs/globs to scan (default: docs/webui/observability/grafana/dashboards)",
    )
    args = parser.parse_args()

    files = _iter_dashboard_files(args.paths)
    if not files:
        print("ERROR: no dashboard json files found (check --paths)", file=sys.stderr)
        return 2

    total_findings = 0
    bad_files = 0

    for p in files:
        try:
            raw = p.read_text(encoding="utf-8")
            doc = json.loads(raw)
        except Exception as e:  # noqa: BLE001 - CLI tool
            print(f"ERROR: failed to parse {p}: {e}", file=sys.stderr)
            return 2

        if not isinstance(doc, dict):
            print(
                f"ERROR: unexpected dashboard JSON root type in {p} (expected object)",
                file=sys.stderr,
            )
            return 2

        findings = lint_dashboard(doc)
        if findings:
            bad_files += 1
            total_findings += len(findings)
            print(f"{p}: FAIL findings={len(findings)}")
            for f in findings:
                if f.value is None:
                    print(f"  - {f.path}: {f.message}")
                else:
                    # keep values compact
                    v = f.value
                    if isinstance(v, str) and len(v) > 240:
                        v = v[:240] + "...(truncated)"
                    print(f"  - {f.path}: {f.message} value={v!r}")
        else:
            print(f"{p}: OK")

    print(f"SUMMARY dashboards={len(files)} bad_files={bad_files} findings={total_findings}")
    return 1 if total_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
