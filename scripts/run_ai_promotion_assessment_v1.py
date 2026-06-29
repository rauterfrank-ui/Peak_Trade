#!/usr/bin/env python3
"""
Offline AI promotion assessment v1.

Consumes exactly one verified comparison_promotion_policy_decision_v1 bundle,
producing a manifested LEVEL_3 non-authorizing assessment artifact.

Usage:
    python3 scripts/run_ai_promotion_assessment_v1.py \\
        --policy-decision-bundle-dir /path/to/policy_decision_bundle \\
        --output-dir /var/evidence/ai_assessment_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.ai_promotion_assessment_v1 import (
    AiPromotionAssessmentError,
    AiPromotionAssessmentInputs,
    produce_ai_promotion_assessment_v1,
)

EXIT_OK = 0
EXIT_ASSESSMENT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline AI promotion assessment v1: deterministically assess a verified "
            "policy decision without override, promotion authority, ConfigPatch mutation, "
            "external model calls, or runtime authority."
        )
    )
    parser.add_argument(
        "--policy-decision-bundle-dir",
        type=Path,
        required=True,
        help="Explicit path to a published comparison_promotion_policy_decision_v1 bundle.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit AI promotion assessment output directory (must not exist).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.policy_decision_bundle_dir.is_dir():
        print(
            "[ai_promotion_assessment_v1] ERROR: policy decision bundle not found: "
            f"{args.policy_decision_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    inputs = AiPromotionAssessmentInputs(
        policy_decision_bundle_dir=args.policy_decision_bundle_dir,
    )

    try:
        result = produce_ai_promotion_assessment_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except AiPromotionAssessmentError as exc:
        print(f"[ai_promotion_assessment_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_ASSESSMENT_ERROR

    print(
        "[ai_promotion_assessment_v1] OK "
        f"comparison_definition_id={result.comparison_definition_id} "
        f"assessment_result={result.assessment_result} "
        f"assessment_confidence_class={result.assessment_confidence_class} "
        f"policy_decision_ref={result.policy_decision_ref} "
        f"artifact_id={result.artifact_id} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
