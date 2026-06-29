#!/usr/bin/env python3
"""Offline runtime performance comparison input v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.runtime_observation_feedback_v1 import (
    LEARNING_INPUT_ARTIFACT_REL,
    RuntimeObservationFeedbackError,
    default_runtime_performance_comparison_input_request,
    produce_runtime_performance_comparison_input_v1,
    reverify_runtime_to_learning_input_v1,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline runtime performance comparison input v1: build a deterministic "
            "comparison-readiness input from a verified learning input; does not execute "
            "comparison or select winners."
        )
    )
    parser.add_argument("--runtime-learning-input-bundle-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.runtime_learning_input_bundle_dir.is_dir():
        print(
            "[runtime_performance_comparison_input_v1] ERROR: learning input bundle not found",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if args.output_dir.exists():
        print(
            "[runtime_performance_comparison_input_v1] ERROR: output exists",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        learning_input = reverify_runtime_to_learning_input_v1(
            output_dir=args.runtime_learning_input_bundle_dir
        )
        request = default_runtime_performance_comparison_input_request(
            learning_input,
            runtime_learning_input_ref=str(
                args.runtime_learning_input_bundle_dir / LEARNING_INPUT_ARTIFACT_REL
            ),
            runtime_learning_input_digest=str(learning_input.get("output_digest", "")),
        )
        result = produce_runtime_performance_comparison_input_v1(
            request=request,
            output_dir=args.output_dir,
        )
    except RuntimeObservationFeedbackError as exc:
        print(
            f"[runtime_performance_comparison_input_v1] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "comparison_input_id": result.comparison_input_id,
                "comparison_readiness_status": result.comparison_readiness_status,
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
