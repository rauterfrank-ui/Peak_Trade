#!/usr/bin/env python3
"""
Offline comparison promotion candidate identity binding v1.

Consumes exactly one verified comparison_completion_promotion_input_binding_v1 bundle
and exactly one explicit verified candidate identity bundle, producing a manifested
LEVEL_3 non-authorizing candidate identity binding artifact.

Usage:
    python3 scripts/run_comparison_promotion_candidate_identity_binding_v1.py \\
        --promotion-input-binding-bundle-dir /path/to/promotion_input_binding \\
        --candidate-identity-bundle-dir /path/to/candidate_identity \\
        --output-dir /var/evidence/candidate_identity_binding_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_promotion_candidate_identity_binding_v1 import (
    ComparisonPromotionCandidateIdentityBindingError,
    ComparisonPromotionCandidateIdentityBindingInputs,
    produce_comparison_promotion_candidate_identity_binding_v1,
)

EXIT_OK = 0
EXIT_BINDING_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline comparison promotion candidate identity binding v1: bind "
            "LEVEL_3 promotion input evidence to an explicit verified candidate identity."
        )
    )
    parser.add_argument(
        "--promotion-input-binding-bundle-dir",
        type=Path,
        required=True,
        help=(
            "Explicit path to a published comparison_completion_promotion_input_binding_v1 bundle."
        ),
    )
    parser.add_argument(
        "--candidate-identity-bundle-dir",
        type=Path,
        required=True,
        help=(
            "Explicit path to a verified candidate identity bundle "
            "(candidate_lineage_manifest_v1 or comparison_metric_input durable binding)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit candidate identity binding output directory (must not exist; outside /tmp).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.promotion_input_binding_bundle_dir.is_dir():
        print(
            "[comparison_promotion_candidate_identity_binding_v1] ERROR: "
            f"promotion input binding bundle not found: "
            f"{args.promotion_input_binding_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    if not args.candidate_identity_bundle_dir.is_dir():
        print(
            "[comparison_promotion_candidate_identity_binding_v1] ERROR: "
            f"candidate identity bundle not found: {args.candidate_identity_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    inputs = ComparisonPromotionCandidateIdentityBindingInputs(
        promotion_input_binding_bundle_dir=args.promotion_input_binding_bundle_dir,
        candidate_identity_bundle_dir=args.candidate_identity_bundle_dir,
    )

    try:
        result = produce_comparison_promotion_candidate_identity_binding_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except ComparisonPromotionCandidateIdentityBindingError as exc:
        print(
            f"[comparison_promotion_candidate_identity_binding_v1] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_BINDING_ERROR

    print(
        "[comparison_promotion_candidate_identity_binding_v1] OK "
        f"comparison_definition_id={result.comparison_definition_id} "
        f"candidate_identity_binding_status={result.candidate_identity_binding_status} "
        f"shared_lineage_status={result.shared_lineage_status} "
        f"candidate_identity_ref={result.candidate_identity_ref} "
        f"candidate_identity_source_type={result.candidate_identity_source_type} "
        f"artifact_id={result.artifact_id} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
