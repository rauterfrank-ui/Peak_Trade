#!/usr/bin/env python3
"""
Offline comparison completion + research validity binding v1.

Consumes exactly one verified comparison_completion_evidence_v1 bundle and one
verified research_validity_evidence_v1 bundle, producing a manifested LEVEL_3
non-authorizing sibling binding artifact.

Usage:
    python3 scripts/run_comparison_completion_research_validity_binding_v1.py \\
        --completion-evidence-bundle-dir /path/to/completion_bundle \\
        --research-validity-evidence-bundle-dir /path/to/validity_bundle \\
        --output-dir /var/evidence/completion_validity_binding_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_completion_research_validity_binding_v1 import (
    ComparisonCompletionResearchValidityBindingError,
    ComparisonCompletionResearchValidityBindingInputs,
    produce_comparison_completion_research_validity_binding_v1,
)

EXIT_OK = 0
EXIT_BINDING_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline comparison completion research validity binding v1: bind "
            "LEVEL_3 non-authorizing completion and research validity evidence."
        )
    )
    parser.add_argument(
        "--completion-evidence-bundle-dir",
        type=Path,
        required=True,
        help="Explicit path to a published comparison_completion_evidence_v1 bundle.",
    )
    parser.add_argument(
        "--research-validity-evidence-bundle-dir",
        type=Path,
        required=True,
        help="Explicit path to a published research_validity_evidence_v1 bundle.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit binding output directory (must not exist; outside /tmp).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.completion_evidence_bundle_dir.is_dir():
        print(
            "[comparison_completion_research_validity_binding_v1] ERROR: "
            f"completion bundle not found: {args.completion_evidence_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if not args.research_validity_evidence_bundle_dir.is_dir():
        print(
            "[comparison_completion_research_validity_binding_v1] ERROR: "
            f"research validity bundle not found: "
            f"{args.research_validity_evidence_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    inputs = ComparisonCompletionResearchValidityBindingInputs(
        completion_evidence_bundle_dir=args.completion_evidence_bundle_dir,
        research_validity_evidence_bundle_dir=args.research_validity_evidence_bundle_dir,
    )

    try:
        result = produce_comparison_completion_research_validity_binding_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except ComparisonCompletionResearchValidityBindingError as exc:
        print(
            f"[comparison_completion_research_validity_binding_v1] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_BINDING_ERROR

    print(
        "[comparison_completion_research_validity_binding_v1] OK "
        f"comparison_definition_id={result.comparison_definition_id} "
        f"binding_status={result.binding_status} "
        f"shared_lineage_status={result.shared_lineage_status} "
        f"artifact_id={result.artifact_id} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
