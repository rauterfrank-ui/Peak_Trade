#!/usr/bin/env python3
"""Offline canary_micro_live_readiness_evidence_v1 producer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.canary_micro_live_readiness_v1 import (
    CanaryMicroLiveReadinessError,
    build_readiness_request_from_canary_input_bundle,
    default_canary_micro_live_readiness_request,
    produce_canary_micro_live_readiness_evidence_v1,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline canary_micro_live_readiness_evidence_v1: build non-authorizing "
            "canary/micro-live readiness evidence from verified canary readiness input."
        )
    )
    parser.add_argument(
        "--source-canary-input-bundle-dir",
        type=Path,
        default=None,
        help=(
            "Verified autonomous_non_live_orchestration_to_canary_readiness_input_v1 "
            "durable evidence bundle"
        ),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.output_dir.exists():
        print("[canary_micro_live_readiness_evidence_v1] ERROR: output exists", file=sys.stderr)
        return EXIT_USAGE_ERROR

    try:
        if args.source_canary_input_bundle_dir is not None:
            if not args.source_canary_input_bundle_dir.is_dir():
                print(
                    "[canary_micro_live_readiness_evidence_v1] ERROR: "
                    "source canary input bundle not found",
                    file=sys.stderr,
                )
                return EXIT_USAGE_ERROR
            request = build_readiness_request_from_canary_input_bundle(
                args.source_canary_input_bundle_dir
            )
        else:
            request = default_canary_micro_live_readiness_request()

        result = produce_canary_micro_live_readiness_evidence_v1(
            request=request,
            output_dir=args.output_dir,
        )
    except CanaryMicroLiveReadinessError as exc:
        print(f"[canary_micro_live_readiness_evidence_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "readiness_id": result.readiness_id,
                "readiness_status": result.readiness_status,
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
