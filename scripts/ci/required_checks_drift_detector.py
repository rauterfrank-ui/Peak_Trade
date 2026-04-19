"""Deprecated compatibility wrapper for required checks drift detection."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
import sys


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Deprecated compatibility wrapper. "
            "Use scripts/ops/reconcile_required_checks_branch_protection.py --check."
        )
    )
    p.add_argument(
        "--required-config",
        default="config/ci/required_status_checks.json",
        help="JSON required checks config path (default: config/ci/required_status_checks.json)",
    )
    p.add_argument(
        "--workflows-dir",
        default=".github/workflows",
        help="Deprecated and ignored (kept for backwards compatibility)",
    )
    p.add_argument(
        "--compare-live",
        action="store_true",
        default=False,
        help="Deprecated alias. Live compare is the canonical default check behavior.",
    )
    p.add_argument(
        "--strict-live",
        action="store_true",
        default=False,
        help="Deprecated and ignored (fail-closed is canonical default).",
    )
    p.add_argument(
        "--owner",
        default="rauterfrank-ui",
        help="GitHub owner/org for canonical reconciliation check",
    )
    p.add_argument(
        "--repo",
        default="Peak_Trade",
        help="GitHub repo for canonical reconciliation check",
    )
    p.add_argument(
        "--branch-pattern",
        default="main",
        help="Branch pattern (mapped to --branch for canonical reconciliation check)",
    )
    return p.parse_args()


def _build_reconciler_cmd(args: argparse.Namespace) -> list[str]:
    repo_root = Path(__file__).resolve().parents[2]
    reconciler = repo_root / "scripts" / "ops" / "reconcile_required_checks_branch_protection.py"
    return [
        sys.executable,
        str(reconciler),
        "--check",
        "--required-config",
        args.required_config,
        "--owner",
        args.owner,
        "--repo",
        args.repo,
        "--branch",
        args.branch_pattern,
    ]


def main() -> int:
    args = _parse_args()
    print(
        "DEPRECATED: scripts/ci/required_checks_drift_detector.py now redirects to "
        "scripts/ops/reconcile_required_checks_branch_protection.py --check",
        file=sys.stderr,
    )
    if args.workflows_dir != ".github/workflows":
        print("NOTE: --workflows-dir is deprecated and ignored.", file=sys.stderr)
    if args.compare_live:
        print(
            "NOTE: --compare-live is deprecated; live compare is canonical default.",
            file=sys.stderr,
        )
    if args.strict_live:
        print(
            "NOTE: --strict-live is deprecated and ignored (fail-closed default).", file=sys.stderr
        )

    cmd = _build_reconciler_cmd(args)
    result = subprocess.run(cmd, check=False, cwd=Path(__file__).resolve().parents[2])
    if result.returncode == 0:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
