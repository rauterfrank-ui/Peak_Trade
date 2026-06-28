#!/usr/bin/env python3
"""
Offline learning loop comparison completion evidence v1.

Consumes exactly one verified comparison_checkpoint_v1 bundle and produces a
manifested LEVEL_3 completion evidence artifact. Non-authorizing: no promotion,
runtime, deployment, or order side-effects.

Usage:
    python3 scripts/run_comparison_completion_evidence_v1.py \\
        --checkpoint-bundle-dir /path/to/checkpoint_bundle \\
        --output-dir /var/evidence/comparison_completion_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_completion_evidence_v1 import (
    ComparisonCompletionEvidenceError,
    produce_comparison_completion_evidence_v1,
)

EXIT_OK = 0
EXIT_COMPLETION_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline comparison completion evidence v1: produce LEVEL_3 "
            "non-authorizing completion evidence from one verified checkpoint bundle."
        )
    )
    parser.add_argument(
        "--checkpoint-bundle-dir",
        type=Path,
        required=True,
        help="Explicit path to a published comparison_checkpoint_v1 bundle.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit completion evidence output directory (must not exist; outside /tmp).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.checkpoint_bundle_dir.is_dir():
        print(
            "[comparison_completion_evidence_v1] ERROR: checkpoint bundle not found: "
            f"{args.checkpoint_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        result = produce_comparison_completion_evidence_v1(
            checkpoint_bundle_dir=args.checkpoint_bundle_dir,
            output_dir=args.output_dir,
        )
    except ComparisonCompletionEvidenceError as exc:
        print(
            f"[comparison_completion_evidence_v1] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_COMPLETION_ERROR

    print(
        "[comparison_completion_evidence_v1] OK "
        f"comparison_definition_id={result.comparison_definition_id} "
        f"artifact_id={result.artifact_id} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
