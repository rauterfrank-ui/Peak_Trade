"""Detect drift between required status checks list and workflows producing them (best-effort)."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Detect drift between required status checks list and workflows producing them (best-effort)"
    )
    p.add_argument(
        "--required-list",
        default=".github/required_status_checks_main.txt",
    )
    p.add_argument(
        "--workflows-dir",
        default=".github/workflows",
    )
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    req = [
        l.strip()
        for l in Path(args.required_list).read_text(encoding="utf-8").splitlines()
        if l.strip() and not l.strip().startswith("#")
    ]
    wf_paths = sorted(Path(args.workflows_dir).glob("*.yml")) + sorted(
        Path(args.workflows_dir).glob("*.yaml")
    )

    produced = set()
    for p in wf_paths:
        d = yaml.safe_load(p.read_text(encoding="utf-8"))
        name = d.get("name", "")
        if name:
            produced.add(name)
        jobs = d.get("jobs") or {}
        for jid, j in jobs.items():
            jname = (j or {}).get("name")
            if jname:
                produced.add(jname)
                # Heuristic: expand matrix job names (e.g. "tests (${{ matrix.python-version }})")
                if "matrix.python-version" in str(jname):
                    matrix = (j or {}).get("strategy", {}).get("matrix", {})
                    pv = matrix.get("python-version", [])
                    if isinstance(pv, list):
                        for v in pv:
                            produced.add(f"tests ({v})")
                    elif pv:
                        produced.add(f"tests ({pv})")
            else:
                produced.add(jid)

    missing = [r for r in req if r not in produced]
    if missing:
        print("DRIFT_MISSING_CONTEXTS:")
        for m in missing:
            print("-", m)
        return 2
    print("DRIFT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
