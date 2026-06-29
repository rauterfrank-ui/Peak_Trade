#!/usr/bin/env python3
"""Offline runtime-to-learning input v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.runtime_observation_feedback_v1 import (
    OBSERVATION_ARTIFACT_REL,
    RuntimeObservationFeedbackError,
    default_runtime_to_learning_input_request,
    produce_runtime_to_learning_input_v1,
    reverify_runtime_observation_bundle_v1,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline runtime-to-learning input v1: transform a verified runtime "
            "observation bundle into a non-authorizing learning input."
        )
    )
    parser.add_argument("--runtime-observation-bundle-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.runtime_observation_bundle_dir.is_dir():
        print(
            "[runtime_to_learning_input_v1] ERROR: observation bundle not found",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if args.output_dir.exists():
        print("[runtime_to_learning_input_v1] ERROR: output exists", file=sys.stderr)
        return EXIT_USAGE_ERROR

    try:
        observation = reverify_runtime_observation_bundle_v1(
            output_dir=args.runtime_observation_bundle_dir
        )
        request = default_runtime_to_learning_input_request(
            observation,
            source_observation_ref=str(
                args.runtime_observation_bundle_dir / OBSERVATION_ARTIFACT_REL
            ),
            source_observation_digest=str(observation.get("output_digest", "")),
            source_observation_status=str(observation.get("observation_status", "")),
        )
        result = produce_runtime_to_learning_input_v1(
            request=request,
            output_dir=args.output_dir,
        )
    except RuntimeObservationFeedbackError as exc:
        print(f"[runtime_to_learning_input_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "learning_input_id": result.learning_input_id,
                "learning_input_status": result.learning_input_status,
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
