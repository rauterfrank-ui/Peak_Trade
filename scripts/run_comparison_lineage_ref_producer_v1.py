#!/usr/bin/env python3
"""
Offline COMPARISON LineageRef producer from explicit result manifest directory.

Produces a validated, deterministic COMPARISON LineageRef JSON artifact only.
No comparison execution, promotion, apply, runtime, registry mutation, or live authority.

Usage:
    python3 scripts/run_comparison_lineage_ref_producer_v1.py \\
        --manifest-dir reports/comparisons/def-id-abc \\
        --output reports/lineage_refs/comparison_def-id-abc.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.governance.promotion_loop.comparison_lineage_ref_producer_v1 import (
    ComparisonLineageRefProducerError,
    produce_comparison_lineage_ref_v1_to_path,
)

EXIT_OK = 0
EXIT_PRODUCER_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline COMPARISON LineageRef producer: explicit result manifest "
            "directory to validated reference-only JSON artifact."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        required=True,
        help=("Explicit path to a directory containing comparison_result_manifest_v1.json."),
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination path for the validated COMPARISON LineageRef JSON file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        result = produce_comparison_lineage_ref_v1_to_path(
            manifest_dir=args.manifest_dir,
            output_path=args.output,
            fail_closed_if_exists=True,
        )
    except ComparisonLineageRefProducerError as exc:
        print(f"[comparison_lineage_ref] ERROR: {exc}", file=sys.stderr)
        return EXIT_PRODUCER_ERROR
    except OSError as exc:
        print(f"[comparison_lineage_ref] ERROR: {exc}", file=sys.stderr)
        return EXIT_PRODUCER_ERROR

    print(
        "[comparison_lineage_ref] wrote validated COMPARISON LineageRef to "
        f"{args.output} (ref_id={result.ref.ref_id}, digest={result.ref.digest})"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
