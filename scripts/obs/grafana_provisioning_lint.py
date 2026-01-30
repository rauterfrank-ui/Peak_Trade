#!/usr/bin/env python3
"""
Lint Grafana provisioning datasources:
- ensure at most ONE datasource has isDefault: true across all datasource files
- optional: enforce that canonical DS names exist in multi_prom.yml (best-effort)

Usage:
  python3 scripts/obs/grafana_provisioning_lint.py
  python3 scripts/obs/grafana_provisioning_lint.py --path docs/webui/observability/grafana/provisioning/datasources
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import yaml  # type: ignore
except Exception as e:  # noqa: BLE001 - CLI tool
    raise SystemExit("Missing dependency: pyyaml. Install via pip (dev): pip install pyyaml") from e


CANONICAL_DS_NAMES = {
    "prom_local_9092",
    "prom_shadow_9093",
    "prom_ai_live_9094",
    "prom_observability_9095",
}


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def iter_datasources(obj: Any) -> List[Dict[str, Any]]:
    # Grafana expects: apiVersion: 1, datasources: [ ... ]
    if isinstance(obj, dict) and isinstance(obj.get("datasources"), list):
        out: List[Dict[str, Any]] = []
        for d in obj["datasources"]:
            if isinstance(d, dict):
                out.append(d)
        return out
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--path",
        default="docs/webui/observability/grafana/provisioning/datasources",
        help="Folder with Grafana datasource provisioning YAML files.",
    )
    args = ap.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"ERROR: provisioning folder not found: {root}")
        return 2

    # Convention: legacy/disabled provisioning files can be parked under a subfolder
    # that should not be scanned by this lint (and typically not by Grafana either).
    # This matches the operator workflow that moves old yaml files into:
    #   <datasources>/legacy_disabled/
    files = sorted(
        [
            p
            for p in root.rglob("*")
            if p.suffix.lower() in (".yml", ".yaml") and "legacy_disabled" not in p.parts
        ]
    )
    if not files:
        print(f"ERROR: no yaml files found under: {root}")
        return 2

    defaults: List[Tuple[str, str]] = []  # (file, datasource_name)
    names: List[str] = []
    errors: List[str] = []

    for f in files:
        try:
            obj = load_yaml(f)
        except Exception as e:  # noqa: BLE001 - CLI tool
            errors.append(f"YAML parse error: {f}: {e}")
            continue

        for ds in iter_datasources(obj):
            n = str(ds.get("name", "")).strip()
            if n:
                names.append(n)
            if bool(ds.get("isDefault", False)) is True:
                defaults.append((str(f), n or "<unnamed>"))

    if len(defaults) > 1:
        errors.append("More than one datasource isDefault:true:")
        for file_, name in defaults:
            errors.append(f"  - {name} @ {file_}")

    # Best-effort: ensure canonical names exist somewhere (usually multi_prom.yml)
    missing = sorted(CANONICAL_DS_NAMES.difference(set(names)))
    if missing:
        errors.append("Missing canonical datasource names in provisioning YAMLs:")
        for m in missing:
            errors.append(f"  - {m}")

    if errors:
        print("FAIL: grafana provisioning lint")
        for e in errors:
            print(e)
        return 1

    d0 = defaults[0] if defaults else ("<none>", "<none>")
    print("PASS: grafana provisioning lint")
    print(f"default: {d0[1]} ({d0[0]})")
    print(f"datasources_seen: {len(set(names))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
