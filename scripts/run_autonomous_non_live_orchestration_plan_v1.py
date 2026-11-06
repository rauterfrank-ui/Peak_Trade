#!/usr/bin/env python3
"""Offline autonomous_non_live_orchestration_plan_v1 producer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1 import (
    AutonomousNonLiveOrchestrationError,
    build_plan_request_from_orchestration_input_bundle,
    default_autonomous_non_live_orchestration_plan_request,
    produce_autonomous_non_live_orchestration_plan_v1,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline autonomous_non_live_orchestration_plan_v1: build a declarative "
            "non-authorizing non-live orchestration plan from verified orchestration input."
        )
    )
    parser.add_argument(
        "--source-orchestration-input-bundle-dir",
        type=Path,
        default=None,
        help="Verified runtime_observation_to_orchestration_input_v1 durable evidence bundle",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.output_dir.exists():
        print("[autonomous_non_live_orchestration_plan_v1] ERROR: output exists", file=sys.stderr)
        return EXIT_USAGE_ERROR

    try:
        if args.source_orchestration_input_bundle_dir is not None:
            if not args.source_orchestration_input_bundle_dir.is_dir():
                print(
                    "[autonomous_non_live_orchestration_plan_v1] ERROR: "
                    "source orchestration input bundle not found",
                    file=sys.stderr,
                )
                return EXIT_USAGE_ERROR
            request = build_plan_request_from_orchestration_input_bundle(
                args.source_orchestration_input_bundle_dir
            )
        else:
            request = default_autonomous_non_live_orchestration_plan_request()

        result = produce_autonomous_non_live_orchestration_plan_v1(
            request=request,
            output_dir=args.output_dir,
        )
    except AutonomousNonLiveOrchestrationError as exc:
        print(f"[autonomous_non_live_orchestration_plan_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "plan_id": result.plan_id,
                "plan_status": result.plan_status,
                "decision_code": result.decision_code,
                "output_dir": result.output_dir.as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
