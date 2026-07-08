#!/usr/bin/env python3
from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path
from typing import Sequence


PREFERRED_OWNER_RELATIVE_PATH = (
    "scripts/ops/materialize_final_research_fleet_offline_economic_evaluation_execution_v0.py"
)

VERDICT_BLOCKED_RUNNER_RESOLUTION_NOT_EXACTLY_ONE = (
    "EXECUTE_BOUNDED_OFFLINE_ECONOMIC_EVALUATION_FROM_RATIFIED_SCOPE_NO_RETRY_V0_"
    "BLOCKED_RUNNER_RESOLUTION_NOT_EXACTLY_ONE"
)

LIVE_AUTHORIZED = False
READY_FOR_OPERATOR_ARMING = False
ORDERS_ALLOWED = False
SCHEDULER_RUNTIME_ALLOWED = False
SHADOW_AUTHORIZED = False
PAPER_AUTHORIZED = False
TESTNET_AUTHORIZED = False
CANARY_AUTHORIZED = False
RETRY_MODE = "NO_RETRY"
UNMODIFIED_BINDING_RETRY_ALLOWED = False


class RunnerResolutionError(RuntimeError):
    pass


def repo_root_from_runner() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_preferred_runner(repo_root: Path) -> Path:
    preferred = repo_root / PREFERRED_OWNER_RELATIVE_PATH
    resolved = [preferred] if preferred.is_file() else []
    if len(resolved) != 1:
        raise RunnerResolutionError(
            f"{VERDICT_BLOCKED_RUNNER_RESOLUTION_NOT_EXACTLY_ONE}: "
            f"preferred_runner={PREFERRED_OWNER_RELATIVE_PATH!r} "
            f"resolved_count={len(resolved)}"
        )
    return resolved[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="execute_bounded_offline_economic_evaluation_from_ratified_scope_no_retry_v0",
        description=(
            "Dedicated fail-closed no-retry entry point for the ratified bounded "
            "offline economic evaluation scope. This script resolves exactly one "
            "canonical existing offline evaluation owner and delegates execution "
            "without granting runtime, order, scheduler, shadow, paper, testnet, "
            "canary, or live authority."
        ),
    )
    parser.add_argument(
        "--print-delegate-only",
        action="store_true",
        help="Print the resolved delegate path and exit without executing it.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    known_args, passthrough_args = parser.parse_known_args(argv)

    repo_root = repo_root_from_runner()
    delegate = resolve_preferred_runner(repo_root)

    if known_args.print_delegate_only:
        print(delegate)
        return 0

    old_argv = sys.argv[:]
    try:
        sys.argv = [str(delegate), *passthrough_args]
        repo_root_str = str(repo_root)
        if repo_root_str not in sys.path:
            sys.path.insert(0, repo_root_str)
        runpy.run_path(str(delegate), run_name="__main__")
    finally:
        sys.argv = old_argv

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
