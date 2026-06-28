#!/usr/bin/env python3
"""
Offline comparison completion promotion input binding v1.

Consumes exactly one verified comparison_completion_research_validity_binding_v1 bundle,
producing a manifested LEVEL_3 non-authorizing promotion input binding artifact.

Usage:
    python3 scripts/run_comparison_completion_promotion_input_binding_v1.py \\
        --completion-validity-binding-bundle-dir /path/to/binding_bundle \\
        --output-dir /var/evidence/promotion_input_binding_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_completion_promotion_input_binding_v1 import (
    ComparisonCompletionPromotionInputBindingError,
    ComparisonCompletionPromotionInputBindingInputs,
    produce_comparison_completion_promotion_input_binding_v1,
)

EXIT_OK = 0
EXIT_BINDING_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline comparison completion promotion input binding v1: bind "
            "LEVEL_3 non-authorizing completion+validity evidence to promotion input."
        )
    )
    parser.add_argument(
        "--completion-validity-binding-bundle-dir",
        type=Path,
        required=True,
        help=(
            "Explicit path to a published "
            "comparison_completion_research_validity_binding_v1 bundle."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit promotion input binding output directory (must not exist; outside /tmp).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.completion_validity_binding_bundle_dir.is_dir():
        print(
            "[comparison_completion_promotion_input_binding_v1] ERROR: "
            f"upstream binding bundle not found: "
            f"{args.completion_validity_binding_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    inputs = ComparisonCompletionPromotionInputBindingInputs(
        completion_validity_binding_bundle_dir=args.completion_validity_binding_bundle_dir,
    )

    try:
        result = produce_comparison_completion_promotion_input_binding_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except ComparisonCompletionPromotionInputBindingError as exc:
        print(
            f"[comparison_completion_promotion_input_binding_v1] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_BINDING_ERROR

    print(
        "[comparison_completion_promotion_input_binding_v1] OK "
        f"comparison_definition_id={result.comparison_definition_id} "
        f"promotion_input_binding_status={result.promotion_input_binding_status} "
        f"shared_lineage_status={result.shared_lineage_status} "
        f"artifact_id={result.artifact_id} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
