#!/usr/bin/env python3
"""
Offline comparison promotion candidate model/parameter identity binding v1.

Consumes exactly one verified comparison_promotion_candidate_eligibility_evidence_v1 bundle,
producing a manifested LEVEL_3 non-authorizing model/parameter identity binding artifact.

Usage:
    python3 scripts/run_comparison_promotion_candidate_model_parameter_identity_binding_v1.py \\
        --eligibility-evidence-bundle-dir /path/to/eligibility_evidence \\
        --output-dir /var/evidence/model_parameter_identity_binding_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_promotion_candidate_model_parameter_identity_binding_v1 import (
    ComparisonPromotionCandidateModelParameterIdentityBindingError,
    ComparisonPromotionCandidateModelParameterIdentityBindingInputs,
    produce_comparison_promotion_candidate_model_parameter_identity_binding_v1,
)

EXIT_OK = 0
EXIT_EVIDENCE_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline comparison promotion candidate model/parameter identity binding v1: "
            "bind digest-bound model and parameter set identities from verified eligibility "
            "evidence."
        )
    )
    parser.add_argument(
        "--eligibility-evidence-bundle-dir",
        type=Path,
        required=True,
        help=(
            "Explicit path to a published comparison_promotion_candidate_eligibility_evidence_v1 "
            "bundle."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit model/parameter identity binding output directory (must not exist).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.eligibility_evidence_bundle_dir.is_dir():
        print(
            "[comparison_promotion_candidate_model_parameter_identity_binding_v1] ERROR: "
            f"eligibility evidence bundle not found: {args.eligibility_evidence_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    inputs = ComparisonPromotionCandidateModelParameterIdentityBindingInputs(
        eligibility_evidence_bundle_dir=args.eligibility_evidence_bundle_dir,
    )

    try:
        result = produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except ComparisonPromotionCandidateModelParameterIdentityBindingError as exc:
        print(
            f"[comparison_promotion_candidate_model_parameter_identity_binding_v1] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_EVIDENCE_ERROR

    print(
        "[comparison_promotion_candidate_model_parameter_identity_binding_v1] OK "
        f"comparison_definition_id={result.comparison_definition_id} "
        f"model_parameter_identity_binding_status="
        f"{result.model_parameter_identity_binding_status} "
        f"model_identity_ref={result.model_identity_ref} "
        f"parameter_set_identity_ref={result.parameter_set_identity_ref} "
        f"artifact_id={result.artifact_id} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
