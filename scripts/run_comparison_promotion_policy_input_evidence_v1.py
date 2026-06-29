#!/usr/bin/env python3
"""
Offline comparison promotion policy input evidence v1.

Consumes exactly one verified comparison_eligibility_promotion_policy_input_binding_v1
bundle, producing a manifested LEVEL_3 neutral promotion-policy-input evidence artifact.

Usage:
    python3 scripts/run_comparison_promotion_policy_input_evidence_v1.py \\
        --policy-input-binding-bundle-dir /path/to/step4_bundle \\
        --output-dir /var/evidence/policy_input_evidence_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_promotion_policy_input_evidence_v1 import (
    ComparisonPromotionPolicyInputEvidenceError,
    ComparisonPromotionPolicyInputEvidenceInputs,
    produce_comparison_promotion_policy_input_evidence_v1,
)

EXIT_OK = 0
EXIT_EVIDENCE_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline comparison promotion policy input evidence v1: "
            "digest-bind verified policy input binding into complete "
            "promotion-policy-input evidence without selection, acceptance, "
            "policy execution, eligibility recomputation, or ConfigPatch mutation."
        )
    )
    parser.add_argument(
        "--policy-input-binding-bundle-dir",
        type=Path,
        required=True,
        help=(
            "Explicit path to a published "
            "comparison_eligibility_promotion_policy_input_binding_v1 bundle."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit promotion policy input evidence output directory (must not exist).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.policy_input_binding_bundle_dir.is_dir():
        print(
            "[comparison_promotion_policy_input_evidence_v1] ERROR: "
            "policy input binding bundle not found: "
            f"{args.policy_input_binding_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    inputs = ComparisonPromotionPolicyInputEvidenceInputs(
        policy_input_binding_bundle_dir=args.policy_input_binding_bundle_dir,
    )

    try:
        result = produce_comparison_promotion_policy_input_evidence_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except ComparisonPromotionPolicyInputEvidenceError as exc:
        print(
            f"[comparison_promotion_policy_input_evidence_v1] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_EVIDENCE_ERROR

    print(
        "[comparison_promotion_policy_input_evidence_v1] OK "
        f"comparison_definition_id={result.comparison_definition_id} "
        f"promotion_policy_input_evidence_status="
        f"{result.promotion_policy_input_evidence_status} "
        f"candidate_identity_ref={result.candidate_identity_ref} "
        f"config_patch_manifest_id={result.config_patch_manifest_id} "
        f"artifact_id={result.artifact_id} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
