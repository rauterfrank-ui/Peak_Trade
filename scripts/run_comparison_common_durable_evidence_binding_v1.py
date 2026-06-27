#!/usr/bin/env python3
"""
Offline durable evidence binding for common comparison chain bundles.

Aggregates already-bound metric-input, definition, and result durable evidence
bundles into one common bundle with cross-reference index and MANIFEST.sha256 only.
No comparison execution, producer re-run, promotion, or runtime.

Usage:
    python3 scripts/run_comparison_common_durable_evidence_binding_v1.py \\
        --definition-bound-bundle-dir /path/to/definition_bound_bundle \\
        --result-bound-bundle-dir /path/to/result_bound_bundle \\
        --metric-input-bound-bundle-dir /path/to/mi_bound_a \\
        --metric-input-bound-bundle-dir /path/to/mi_bound_b \\
        --output-dir /var/evidence/comparison_common_bundle_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    ComparisonCommonDurableEvidenceBindingError,
    produce_comparison_common_durable_evidence_bundle_v1,
)

EXIT_OK = 0
EXIT_BINDING_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline durable evidence binding: aggregate verified comparison "
            "metric-input, definition, and result bound bundles into a common bundle."
        )
    )
    parser.add_argument(
        "--definition-bound-bundle-dir",
        type=Path,
        required=True,
        help="Explicit path to comparison definition durable evidence bound bundle.",
    )
    parser.add_argument(
        "--result-bound-bundle-dir",
        type=Path,
        required=True,
        help="Explicit path to comparison result durable evidence bound bundle.",
    )
    parser.add_argument(
        "--metric-input-bound-bundle-dir",
        type=Path,
        action="append",
        required=True,
        dest="metric_input_bound_bundle_dirs",
        help=(
            "Explicit path to one comparison metric-input durable evidence bound bundle. "
            "Repeat for each definition input ref (2..32)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit common durable evidence bundle directory (must not exist; outside /tmp).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.definition_bound_bundle_dir.is_dir():
        print(
            "[comparison_common_durable_evidence_binding] ERROR: "
            f"definition bound bundle not found: {args.definition_bound_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if not args.result_bound_bundle_dir.is_dir():
        print(
            "[comparison_common_durable_evidence_binding] ERROR: "
            f"result bound bundle not found: {args.result_bound_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    for path in args.metric_input_bound_bundle_dirs:
        if not path.is_dir():
            print(
                "[comparison_common_durable_evidence_binding] ERROR: "
                f"metric input bound bundle not found: {path}",
                file=sys.stderr,
            )
            return EXIT_USAGE_ERROR

    try:
        result = produce_comparison_common_durable_evidence_bundle_v1(
            definition_bound_bundle_dir=args.definition_bound_bundle_dir,
            result_bound_bundle_dir=args.result_bound_bundle_dir,
            metric_input_bound_bundle_dirs=args.metric_input_bound_bundle_dirs,
            output_dir=args.output_dir,
        )
    except ComparisonCommonDurableEvidenceBindingError as exc:
        print(
            f"[comparison_common_durable_evidence_binding] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_BINDING_ERROR

    print(
        "[comparison_common_durable_evidence_binding] wrote common durable evidence bundle to "
        f"{result.output_dir} (comparison_definition_id={result.comparison_definition_id}, "
        f"metric_input_binding_count={result.metric_input_binding_count})"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
