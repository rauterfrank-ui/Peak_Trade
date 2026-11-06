#!/usr/bin/env python3
"""Run CURRENT productive Golden Happy Vector startability evaluator (read-only)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CURRENT productive GHV startability evaluator (AUTHORITY=NONE)",
    )
    parser.add_argument(
        "--golden-vector-root",
        type=Path,
        default=None,
        help="Reference golden vector bundle directory",
    )
    parser.add_argument(
        "--expected-baseline-sha",
        type=str,
        default="ffbc8fbe606640fff19b1094a1873b3f684499c7",
    )
    parser.add_argument(
        "--live-inputs-required",
        action="store_true",
        help="Also require live/ephemeral input readiness (not used in default GHV mode)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON report path",
    )
    args = parser.parse_args()

    from src.ops.full_core_live_path_composition_root_v1.current_productive_golden_happy_vector_startability_evaluator_v1 import (
        evaluate_current_productive_golden_happy_vector_startability_v1,
        report_to_machine_json_v1,
    )

    report = evaluate_current_productive_golden_happy_vector_startability_v1(
        repository_root=REPO_ROOT,
        golden_vector_root=args.golden_vector_root,
        expected_baseline_sha=args.expected_baseline_sha,
        actual_head_sha=_git_head(),
        live_inputs_required=args.live_inputs_required,
    )
    payload = report_to_machine_json_v1(report)
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    ok = report.structurally_startable and report.golden_vector_replay_valid
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
