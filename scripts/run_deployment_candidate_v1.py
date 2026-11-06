#!/usr/bin/env python3
"""Offline deployment candidate v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.deploy_inactive_v1 import (
    DeployInactiveError,
    default_deployment_candidate_evaluation_input,
    produce_deployment_candidate_v1,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline deployment candidate v1: deterministically evaluate whether a "
            "runtime-eligible candidate satisfies DEPLOYABLE prerequisites; produce "
            "non-authorizing evidence."
        )
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.output_dir.exists():
        print("[deployment_candidate_v1] ERROR: output exists", file=sys.stderr)
        return EXIT_USAGE_ERROR

    try:
        result = produce_deployment_candidate_v1(
            request=default_deployment_candidate_evaluation_input(),
            output_dir=args.output_dir,
        )
    except DeployInactiveError as exc:
        print(f"[deployment_candidate_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "deployment_candidate_id": result.deployment_candidate_id,
                "deployment_candidate_status": result.deployment_candidate_status,
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
