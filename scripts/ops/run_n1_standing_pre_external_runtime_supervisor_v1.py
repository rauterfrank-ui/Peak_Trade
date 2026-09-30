#!/usr/bin/env python3
"""Canonical entry: N=1 standing PRE_EXTERNAL runtime supervisor (orchestration only)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _origin_main_sha() -> str:
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "origin/main"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip()
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Start N=1 standing PRE_EXTERNAL runtime supervisor (one session)."
    )
    parser.add_argument("--public-store", type=Path, required=True)
    parser.add_argument("--private-store", type=Path, required=True)
    parser.add_argument("--lane-state", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--origin-main-sha", default=_origin_main_sha())
    parser.add_argument("--dry-run-config", action="store_true")
    args = parser.parse_args()

    if args.dry_run_config:
        print(
            json.dumps(
                {
                    "launcher": "run_n1_standing_pre_external_runtime_supervisor_v1.py",
                    "repo_root": str(REPO_ROOT),
                    "origin_main_sha": args.origin_main_sha,
                    "note": "Full run requires bound instrument, authorization, observation source, "
                    "and F1-M9 evaluator — use tests or operator harness for inject transport.",
                },
                indent=2,
            )
        )
        return 0

    print(
        "ERROR:INTERACTIVE_FULL_RUN_REQUIRES_OPERATOR_HARNESS",
        file=sys.stderr,
    )
    print(
        "Use tests/ops/test_n1_standing_pre_external_runtime_supervisor_v1.py "
        "or extend this launcher with authorized inject transport binding.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
