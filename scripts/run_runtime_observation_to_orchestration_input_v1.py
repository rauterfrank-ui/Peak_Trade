#!/usr/bin/env python3
"""Offline runtime_observation_to_orchestration_input_v1 producer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1 import (
    AutonomousNonLiveOrchestrationError,
    build_orchestration_input_request_from_learning_input_bundle,
    build_orchestration_input_request_from_observation_bundle,
    default_runtime_observation_to_orchestration_input_request,
    produce_runtime_observation_to_orchestration_input_v1,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline runtime_observation_to_orchestration_input_v1: project verified "
            "STEP-26 runtime observation or learning input evidence into a non-authorizing "
            "orchestration input."
        )
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--source-observation-bundle-dir",
        type=Path,
        default=None,
        help="Verified runtime_observation_bundle_v1 durable evidence bundle",
    )
    source.add_argument(
        "--source-learning-input-bundle-dir",
        type=Path,
        default=None,
        help="Verified runtime_to_learning_input_v1 durable evidence bundle",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.output_dir.exists():
        print(
            "[runtime_observation_to_orchestration_input_v1] ERROR: output exists",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        if args.source_observation_bundle_dir is not None:
            if not args.source_observation_bundle_dir.is_dir():
                print(
                    "[runtime_observation_to_orchestration_input_v1] ERROR: "
                    "source observation bundle not found",
                    file=sys.stderr,
                )
                return EXIT_USAGE_ERROR
            request = build_orchestration_input_request_from_observation_bundle(
                args.source_observation_bundle_dir
            )
        elif args.source_learning_input_bundle_dir is not None:
            if not args.source_learning_input_bundle_dir.is_dir():
                print(
                    "[runtime_observation_to_orchestration_input_v1] ERROR: "
                    "source learning input bundle not found",
                    file=sys.stderr,
                )
                return EXIT_USAGE_ERROR
            request = build_orchestration_input_request_from_learning_input_bundle(
                args.source_learning_input_bundle_dir
            )
        else:
            request = default_runtime_observation_to_orchestration_input_request()

        result = produce_runtime_observation_to_orchestration_input_v1(
            request=request,
            output_dir=args.output_dir,
        )
    except AutonomousNonLiveOrchestrationError as exc:
        print(f"[runtime_observation_to_orchestration_input_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "artifact_id": result.artifact_id,
                "orchestration_input_status": result.orchestration_input_status,
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
