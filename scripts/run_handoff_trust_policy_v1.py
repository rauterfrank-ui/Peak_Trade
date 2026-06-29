#!/usr/bin/env python3
"""
Offline handoff trust policy v1.

Consumes exactly one verified versioned_strategy_model_parameter_artifact_v1 bundle,
producing a manifested LEVEL_3 non-authorizing trust/admissibility evaluation.

Usage:
    python3 scripts/run_handoff_trust_policy_v1.py \\
        --versioned-artifact-bundle-dir /path/to/versioned_artifact \\
        [--consumer-contract-ref /path/to/consumer_contract.json] \\
        --output-dir /var/evidence/handoff_trust_policy_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.handoff_trust_policy_v1 import (
    HandoffTrustPolicyError,
    HandoffTrustPolicyInputs,
    produce_handoff_trust_policy_v1,
)

EXIT_OK = 0
EXIT_TRUST_POLICY_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline handoff trust policy v1: deterministically evaluate whether a "
            "verified versioned strategy/model/parameter artifact could be handed off "
            "offline without executing handoff, invoking consumers, promotion authority, "
            "ConfigPatch mutation, or runtime authority."
        )
    )
    parser.add_argument(
        "--versioned-artifact-bundle-dir",
        type=Path,
        required=True,
        help="Explicit path to a published versioned_strategy_model_parameter_artifact_v1 bundle.",
    )
    parser.add_argument(
        "--consumer-contract-ref",
        type=Path,
        default=None,
        help=(
            "Optional offline consumer capability contract file or directory. "
            "When omitted, the embedded default consumer contract is used."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit handoff trust policy output directory (must not exist).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.versioned_artifact_bundle_dir.is_dir():
        print(
            "[handoff_trust_policy_v1] ERROR: versioned artifact bundle not found: "
            f"{args.versioned_artifact_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if args.consumer_contract_ref is not None and not args.consumer_contract_ref.exists():
        print(
            "[handoff_trust_policy_v1] ERROR: consumer contract ref not found: "
            f"{args.consumer_contract_ref}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    inputs = HandoffTrustPolicyInputs(
        versioned_artifact_bundle_dir=args.versioned_artifact_bundle_dir,
        consumer_contract_ref=args.consumer_contract_ref,
    )

    try:
        result = produce_handoff_trust_policy_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except HandoffTrustPolicyError as exc:
        print(f"[handoff_trust_policy_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_TRUST_POLICY_ERROR

    print(
        "[handoff_trust_policy_v1] OK "
        f"comparison_definition_id={result.comparison_definition_id} "
        f"trust_result={result.trust_result} "
        f"compatibility_result={result.compatibility_result} "
        f"versioned_artifact_ref={result.versioned_artifact_ref} "
        f"artifact_id={result.artifact_id} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
