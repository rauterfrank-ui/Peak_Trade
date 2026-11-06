#!/usr/bin/env python3
"""
Offline comparison promotion candidate eligibility evidence v1.

Consumes exactly one verified comparison_promotion_candidate_identity_binding_v1 bundle,
producing a manifested LEVEL_3 non-authorizing eligibility evidence artifact.

Usage:
    python3 scripts/run_comparison_promotion_candidate_eligibility_evidence_v1.py \\
        --candidate-identity-binding-bundle-dir /path/to/candidate_identity_binding \\
        --output-dir /var/evidence/candidate_eligibility_evidence_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_promotion_candidate_eligibility_evidence_v1 import (
    ComparisonPromotionCandidateEligibilityEvidenceError,
    ComparisonPromotionCandidateEligibilityEvidenceInputs,
    produce_comparison_promotion_candidate_eligibility_evidence_v1,
)

EXIT_OK = 0
EXIT_EVIDENCE_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline comparison promotion candidate eligibility evidence v1: evaluate "
            "LEVEL_3 structural eligibility from a verified candidate identity binding."
        )
    )
    parser.add_argument(
        "--candidate-identity-binding-bundle-dir",
        type=Path,
        required=True,
        help=(
            "Explicit path to a published comparison_promotion_candidate_identity_binding_v1 "
            "bundle."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit eligibility evidence output directory (must not exist; outside /tmp).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.candidate_identity_binding_bundle_dir.is_dir():
        print(
            "[comparison_promotion_candidate_eligibility_evidence_v1] ERROR: "
            f"candidate identity binding bundle not found: "
            f"{args.candidate_identity_binding_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    inputs = ComparisonPromotionCandidateEligibilityEvidenceInputs(
        candidate_identity_binding_bundle_dir=args.candidate_identity_binding_bundle_dir,
    )

    try:
        result = produce_comparison_promotion_candidate_eligibility_evidence_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except ComparisonPromotionCandidateEligibilityEvidenceError as exc:
        print(
            f"[comparison_promotion_candidate_eligibility_evidence_v1] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_EVIDENCE_ERROR

    print(
        "[comparison_promotion_candidate_eligibility_evidence_v1] OK "
        f"comparison_definition_id={result.comparison_definition_id} "
        f"candidate_eligibility_status={result.candidate_eligibility_status} "
        f"candidate_identity_ref={result.candidate_identity_ref} "
        f"artifact_id={result.artifact_id} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
