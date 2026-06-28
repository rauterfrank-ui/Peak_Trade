#!/usr/bin/env python3
"""
Offline comparison promotion candidate input v1.

Consumes exactly one verified comparison_config_patch_manifest_cross_domain_lineage_binding_v1
bundle, producing a manifested LEVEL_3 neutral candidate input artifact.

Usage:
    python3 scripts/run_comparison_promotion_candidate_input_v1.py \\
        --cross-domain-lineage-binding-bundle-dir /path/to/step2_bundle \\
        --output-dir /var/evidence/candidate_input_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_promotion_candidate_input_v1 import (
    ComparisonPromotionCandidateInputError,
    ComparisonPromotionCandidateInputInputs,
    produce_comparison_promotion_candidate_input_v1,
)

EXIT_OK = 0
EXIT_EVIDENCE_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline comparison promotion candidate input v1: aggregate verified "
            "cross-domain lineage into a neutral digest-bound candidate input without "
            "selection, acceptance, policy, or ConfigPatch mutation."
        )
    )
    parser.add_argument(
        "--cross-domain-lineage-binding-bundle-dir",
        type=Path,
        required=True,
        help=(
            "Explicit path to a published "
            "comparison_config_patch_manifest_cross_domain_lineage_binding_v1 bundle."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit candidate input output directory (must not exist).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.cross_domain_lineage_binding_bundle_dir.is_dir():
        print(
            "[comparison_promotion_candidate_input_v1] ERROR: "
            "cross-domain lineage binding bundle not found: "
            f"{args.cross_domain_lineage_binding_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    inputs = ComparisonPromotionCandidateInputInputs(
        cross_domain_lineage_binding_bundle_dir=args.cross_domain_lineage_binding_bundle_dir,
    )

    try:
        result = produce_comparison_promotion_candidate_input_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except ComparisonPromotionCandidateInputError as exc:
        print(
            f"[comparison_promotion_candidate_input_v1] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_EVIDENCE_ERROR

    print(
        "[comparison_promotion_candidate_input_v1] OK "
        f"comparison_definition_id={result.comparison_definition_id} "
        f"candidate_input_status={result.candidate_input_status} "
        f"candidate_identity_ref={result.candidate_identity_ref} "
        f"config_patch_manifest_id={result.config_patch_manifest_id} "
        f"artifact_id={result.artifact_id} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
