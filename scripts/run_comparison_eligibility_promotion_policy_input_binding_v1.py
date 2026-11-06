#!/usr/bin/env python3
"""
Offline comparison eligibility promotion policy input binding v1.

Consumes exactly one verified comparison_promotion_candidate_input_v1 bundle,
producing a manifested LEVEL_3 neutral policy-input binding artifact.

Usage:
    python3 scripts/run_comparison_eligibility_promotion_policy_input_binding_v1.py \\
        --candidate-input-bundle-dir /path/to/step3_bundle \\
        --output-dir /var/evidence/policy_input_binding_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_eligibility_promotion_policy_input_binding_v1 import (
    ComparisonEligibilityPromotionPolicyInputBindingError,
    ComparisonEligibilityPromotionPolicyInputBindingInputs,
    produce_comparison_eligibility_promotion_policy_input_binding_v1,
)

EXIT_OK = 0
EXIT_EVIDENCE_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline comparison eligibility promotion policy input binding v1: "
            "digest-bind verified candidate input and eligibility evidence into a "
            "neutral policy-input binding without selection, acceptance, policy, "
            "eligibility recomputation, or ConfigPatch mutation."
        )
    )
    parser.add_argument(
        "--candidate-input-bundle-dir",
        type=Path,
        required=True,
        help=("Explicit path to a published comparison_promotion_candidate_input_v1 bundle."),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit policy input binding output directory (must not exist).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.candidate_input_bundle_dir.is_dir():
        print(
            "[comparison_eligibility_promotion_policy_input_binding_v1] ERROR: "
            "candidate input bundle not found: "
            f"{args.candidate_input_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    inputs = ComparisonEligibilityPromotionPolicyInputBindingInputs(
        candidate_input_bundle_dir=args.candidate_input_bundle_dir,
    )

    try:
        result = produce_comparison_eligibility_promotion_policy_input_binding_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except ComparisonEligibilityPromotionPolicyInputBindingError as exc:
        print(
            f"[comparison_eligibility_promotion_policy_input_binding_v1] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_EVIDENCE_ERROR

    print(
        "[comparison_eligibility_promotion_policy_input_binding_v1] OK "
        f"comparison_definition_id={result.comparison_definition_id} "
        f"eligibility_policy_input_binding_status="
        f"{result.eligibility_policy_input_binding_status} "
        f"candidate_identity_ref={result.candidate_identity_ref} "
        f"config_patch_manifest_id={result.config_patch_manifest_id} "
        f"artifact_id={result.artifact_id} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
