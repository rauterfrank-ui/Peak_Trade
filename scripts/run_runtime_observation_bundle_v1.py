#!/usr/bin/env python3
"""Offline runtime observation bundle v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.runtime_observation_feedback_v1 import (
    RuntimeObservationFeedbackError,
    default_runtime_observation_bundle_input,
    produce_runtime_observation_bundle_v1,
    verify_source_evidence_bundle,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline runtime observation bundle v1: bind preexisting durable runtime "
            "evidence into a non-authorizing observation bundle."
        )
    )
    parser.add_argument(
        "--source-evidence-bundle-dir",
        type=Path,
        default=None,
        help="Optional preexisting durable evidence bundle with MANIFEST.sha256",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.output_dir.exists():
        print("[runtime_observation_bundle_v1] ERROR: output exists", file=sys.stderr)
        return EXIT_USAGE_ERROR

    request_kwargs: dict[str, object] = {}
    if args.source_evidence_bundle_dir is not None:
        if not args.source_evidence_bundle_dir.is_dir():
            print(
                "[runtime_observation_bundle_v1] ERROR: source evidence bundle not found",
                file=sys.stderr,
            )
            return EXIT_USAGE_ERROR
        try:
            manifest_digest = verify_source_evidence_bundle(args.source_evidence_bundle_dir)
        except RuntimeObservationFeedbackError as exc:
            print(f"[runtime_observation_bundle_v1] ERROR: {exc}", file=sys.stderr)
            return EXIT_CONTRACT_ERROR
        request_kwargs["source_evidence_bundle_dir"] = str(args.source_evidence_bundle_dir)
        request_kwargs["source_manifest_digest"] = manifest_digest

    try:
        result = produce_runtime_observation_bundle_v1(
            request=default_runtime_observation_bundle_input(**request_kwargs),
            output_dir=args.output_dir,
        )
    except RuntimeObservationFeedbackError as exc:
        print(f"[runtime_observation_bundle_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "observation_bundle_id": result.observation_bundle_id,
                "observation_status": result.observation_status,
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
