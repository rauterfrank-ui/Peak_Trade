#!/usr/bin/env python3
"""Offline autonomous_non_live_orchestration_to_canary_readiness_input_v1 producer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.canary_micro_live_readiness_v1 import (
    CanaryMicroLiveReadinessError,
    build_canary_readiness_input_request_from_plan_bundle,
    default_canary_readiness_input_request,
    produce_autonomous_non_live_orchestration_to_canary_readiness_input_v1,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline autonomous_non_live_orchestration_to_canary_readiness_input_v1: "
            "project verified STEP-27 orchestration plan into a non-authorizing "
            "canary/micro-live readiness input."
        )
    )
    parser.add_argument(
        "--source-plan-bundle-dir",
        type=Path,
        default=None,
        help="Verified autonomous_non_live_orchestration_plan_v1 durable evidence bundle",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.output_dir.exists():
        print(
            "[autonomous_non_live_orchestration_to_canary_readiness_input_v1] ERROR: output exists",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        if args.source_plan_bundle_dir is not None:
            if not args.source_plan_bundle_dir.is_dir():
                print(
                    "[autonomous_non_live_orchestration_to_canary_readiness_input_v1] ERROR: "
                    "source plan bundle not found",
                    file=sys.stderr,
                )
                return EXIT_USAGE_ERROR
            request = build_canary_readiness_input_request_from_plan_bundle(
                args.source_plan_bundle_dir
            )
        else:
            request = default_canary_readiness_input_request()

        result = produce_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
            request=request,
            output_dir=args.output_dir,
        )
    except CanaryMicroLiveReadinessError as exc:
        print(
            f"[autonomous_non_live_orchestration_to_canary_readiness_input_v1] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "artifact_id": result.artifact_id,
                "canary_input_status": result.canary_input_status,
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
