#!/usr/bin/env python3
"""
Offline learning loop comparison checkpoint v1.

Records a non-authoritative, durable checkpoint over an already-published and
self-verified Common Comparison Durable Evidence Bundle v1. Optional soft
cross-check against a pre-published Comparison Lineage Ref v1.

Usage:
    python3 scripts/run_comparison_checkpoint_v1.py \\
        --common-bundle-dir /path/to/common_bundle \\
        --output-dir /var/evidence/comparison_checkpoint_001 \\
        [--lineage-ref-path /path/to/comparison_ref.json]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_checkpoint_v1 import (
    ComparisonCheckpointError,
    produce_comparison_checkpoint_v1,
)

EXIT_OK = 0
EXIT_CHECKPOINT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline learning loop comparison checkpoint v1: record a "
            "non-authoritative durable mark over a verified common comparison bundle."
        )
    )
    parser.add_argument(
        "--common-bundle-dir",
        type=Path,
        required=True,
        help="Explicit path to a published common comparison durable evidence bundle.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit checkpoint output directory (must not exist; outside /tmp).",
    )
    parser.add_argument(
        "--lineage-ref-path",
        type=Path,
        default=None,
        help="Optional explicit path to a pre-published Comparison Lineage Ref JSON.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.common_bundle_dir.is_dir():
        print(
            f"[comparison_checkpoint_v1] ERROR: common bundle not found: {args.common_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if args.lineage_ref_path is not None and not args.lineage_ref_path.is_file():
        print(
            f"[comparison_checkpoint_v1] ERROR: lineage ref not found: {args.lineage_ref_path}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        result = produce_comparison_checkpoint_v1(
            common_bundle_dir=args.common_bundle_dir,
            output_dir=args.output_dir,
            lineage_ref_path=args.lineage_ref_path,
        )
    except ComparisonCheckpointError as exc:
        print(f"[comparison_checkpoint_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CHECKPOINT_ERROR

    print(
        "[comparison_checkpoint_v1] wrote checkpoint to "
        f"{result.output_dir} (comparison_definition_id={result.comparison_definition_id}, "
        f"checkpoint_id={result.checkpoint_id})"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
