#!/usr/bin/env python3
"""
Grafana Dashpack Datasource Fix v1

Goal:
- Eliminate non-existent datasource references (e.g. DS_LOCAL) in provisioned dashboards
  without any Grafana UI clicks.
- Provisioned datasources are readOnly => datasource UID cannot be changed via Grafana API.
  Therefore we normalize dashboard JSON to only reference UIDs that exist in local setup.

Usage:
  python3 scripts/obs/grafana_dashpack_datasource_fix_v1.py --check
  python3 scripts/obs/grafana_dashpack_datasource_fix_v1.py --apply
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ALLOW_UIDS = {
    "peaktrade-prometheus-local",
    "peaktrade-prometheus-main",
    "peaktrade-prometheus-shadow",
    "peaktrade-prometheus",
}

ALLOW_NAMES = {
    "prometheus-local",
    "prometheus-main",
    "prometheus-shadow",
    "prometheus",
}

NAME_TO_UID = {
    "prometheus-local": "peaktrade-prometheus-local",
    "prometheus-main": "peaktrade-prometheus-main",
    "prometheus-shadow": "peaktrade-prometheus-shadow",
    "prometheus": "peaktrade-prometheus",
}

DEFAULT_UID = "peaktrade-prometheus-local"

DS_VAR_TO_UID = {
    "DS_LOCAL": "peaktrade-prometheus-local",
    "DS_MAIN": "peaktrade-prometheus-main",
    "DS_SHADOW": "peaktrade-prometheus-shadow",
}


@dataclass(frozen=True)
class Replacement:
    path: str
    before: str
    after: str


def _is_str(x: Any) -> bool:
    return isinstance(x, str) and len(x) > 0


def _extract_ds_var(s: str) -> str | None:
    """
    Recognize common Grafana datasource-variable forms:
    - ${DS_LOCAL}
    - $DS_LOCAL
    - DS_LOCAL
    """
    raw = s.strip()
    if raw.startswith("${") and raw.endswith("}"):
        raw = raw[2:-1].strip()
    elif raw.startswith("$"):
        raw = raw[1:].strip()
    if raw in DS_VAR_TO_UID:
        return raw
    return None


def _normalize_uid_string(uid: str) -> tuple[str, bool]:
    """
    Normalize a datasource UID-like string to a real, provisioned UID.
    Returns (new_uid, changed?).
    """
    if uid in ALLOW_UIDS:
        return uid, False

    # Sometimes Grafana exports can put the name in the uid field.
    if uid in ALLOW_NAMES:
        return NAME_TO_UID[uid], True

    var = _extract_ds_var(uid)
    if var is not None:
        mapped = DS_VAR_TO_UID[var]
        if mapped != uid:
            return mapped, True
        return uid, False

    return DEFAULT_UID, True


def _normalize_datasource_value(value: Any) -> tuple[Any, list[Replacement]]:
    """
    Normalize a "datasource" field that can be:
    - dict: {"type": "...", "uid": "..."}
    - string: "prometheus-local" / "peaktrade-prometheus-local" / "DS_LOCAL" / ...
    """
    reps: list[Replacement] = []

    if isinstance(value, dict):
        uid = value.get("uid")
        if _is_str(uid):
            new_uid, changed = _normalize_uid_string(uid)
            if changed:
                reps.append(Replacement(path="", before=uid, after=new_uid))
                value["uid"] = new_uid
        # If dict has no uid (or uid not a string), we leave it unchanged.
        return value, reps

    if _is_str(value):
        # Old-style: datasource as string (usually by name)
        s = value
        if s in ALLOW_UIDS or s in ALLOW_NAMES:
            return value, reps
        var = _extract_ds_var(s)
        if var is not None:
            # For string-form datasource, prefer the known name if possible.
            mapped_uid = DS_VAR_TO_UID[var]
            # Convert uid -> name when it’s one of ours (for better compat with old schema).
            mapped_name = next((n for n, u in NAME_TO_UID.items() if u == mapped_uid), None)
            new_s = mapped_name or mapped_uid
            reps.append(Replacement(path="", before=s, after=new_s))
            return new_s, reps

        # Unknown => safe default by name where possible
        reps.append(Replacement(path="", before=s, after="prometheus-local"))
        return "prometheus-local", reps

    # null / bool / other: leave unchanged
    return value, reps


def _walk_and_fix(node: Any, base_path: str = "") -> list[Replacement]:
    reps: list[Replacement] = []

    if isinstance(node, dict):
        # First: if this dict itself has a datasource key.
        if "datasource" in node:
            before = node["datasource"]
            after, ds_reps = _normalize_datasource_value(before)
            if ds_reps:
                # Attach full path to each replacement
                for r in ds_reps:
                    reps.append(
                        Replacement(
                            path=f"{base_path}.datasource" if base_path else "datasource",
                            before=r.before,
                            after=r.after,
                        )
                    )
                node["datasource"] = after

        # Recurse
        for k, v in list(node.items()):
            child_path = f"{base_path}.{k}" if base_path else str(k)
            reps.extend(_walk_and_fix(v, child_path))
        return reps

    if isinstance(node, list):
        for i, it in enumerate(node):
            child_path = f"{base_path}[{i}]" if base_path else f"[{i}]"
            reps.extend(_walk_and_fix(it, child_path))
        return reps

    return reps


def _iter_dashboard_files(root: Path) -> Iterable[Path]:
    dash_dir = root / "docs" / "webui" / "observability" / "grafana" / "dashboards"
    yield from sorted(dash_dir.glob("**/*.json"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize Grafana dashpack datasource refs.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="dry-run; exit 1 if changes needed")
    mode.add_argument("--apply", action="store_true", help="apply changes in-place")
    parser.add_argument(
        "--root",
        default=".",
        help="repo root (default: .); dashboards are read under docs/webui/observability/grafana/dashboards/",
    )
    args = parser.parse_args()

    root = Path(args.root)
    files = list(_iter_dashboard_files(root))
    if not files:
        print("no dashboard json files found", file=sys.stderr)
        return 2

    total_files_changed = 0
    total_replacements = 0

    for p in files:
        try:
            raw = p.read_text(encoding="utf-8")
            doc = json.loads(raw)
        except Exception as e:  # noqa: BLE001 - CLI tool
            print(f"ERROR: failed to parse {p}: {e}", file=sys.stderr)
            return 2

        reps = _walk_and_fix(doc)
        if reps:
            total_files_changed += 1
            total_replacements += len(reps)
            print(f"{p}: replacements={len(reps)}")
            # Keep output compact but useful
            for r in reps[:8]:
                print(f"  - {r.path}: {r.before!r} -> {r.after!r}")
            if len(reps) > 8:
                print(f"  - ... ({len(reps) - 8} more)")

            if args.apply:
                p.write_text(
                    json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
        else:
            print(f"{p}: ok")

    print(
        f"SUMMARY files_total={len(files)} files_changed={total_files_changed} replacements={total_replacements}"
    )

    if args.check and total_files_changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
