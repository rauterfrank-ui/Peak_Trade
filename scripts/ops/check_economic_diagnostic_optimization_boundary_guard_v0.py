#!/usr/bin/env python3
"""Fail-closed PR diff guard for economic/diagnostic optimization boundary v0.

Exit codes:
  0 — admissible or no boundary-governed changes
  1 — forbidden surface touched or impact unknown on boundary-governed diff
  2 — configuration or git error
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.governance.economic_diagnostic_optimization_boundary_v0 import (  # noqa: E402
    build_boundary_report,
    forbidden_surface_changed_count,
)


def _git_changed_files(repo_root: Path, base: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        result = subprocess.run(
            ["git", "diff", "--name-only", base, "HEAD"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git diff failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Economic/diagnostic optimization boundary guard: fail-closed on forbidden "
            "canonical trading-logic owner mutations."
        )
    )
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Git base ref for diff (default: origin/main).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=_REPO_ROOT,
        help="Repository root.",
    )
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Explicit changed file (repeatable). When set, skips git diff.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path to write machine-readable boundary report JSON.",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()

    try:
        changed = (
            list(args.changed_file)
            if args.changed_file
            else _git_changed_files(repo_root, args.base)
        )
    except Exception as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 2

    report = build_boundary_report(changed, repo_root=repo_root)
    payload = report.to_dict()
    payload["FORBIDDEN_SURFACE_CHANGED_COUNT"] = forbidden_surface_changed_count(report)

    if args.json_out is not None:
        args.json_out.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    print(json.dumps(payload, indent=2, sort_keys=True))

    if report.admissible:
        print("economic_diagnostic_optimization_boundary_guard_v0: PASS")
        return 0

    print("economic_diagnostic_optimization_boundary_guard_v0: FAIL", file=sys.stderr)
    print(f"  reason_codes={list(report.reason_codes)}", file=sys.stderr)
    print(
        f"  FORBIDDEN_SURFACE_CHANGED_COUNT={forbidden_surface_changed_count(report)}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
