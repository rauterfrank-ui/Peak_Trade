#!/usr/bin/env python3
"""
Offline durable evidence binding for comparison_ssot.v1 result manifest.

Produces a validated durable evidence bundle with binding index and MANIFEST.sha256 only.
No comparison evaluation, result production, definition binding, promotion, or runtime.

Usage:
    python3 scripts/run_comparison_ssot_result_durable_evidence_binding_v1.py \\
        --manifest-path /path/to/comparison_result_manifest_v1.json \\
        --output-dir /var/evidence/comparison_result_bundle_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1 import (
    ComparisonSsotResultDurableEvidenceBindingError,
    produce_comparison_ssot_result_durable_evidence_bundle_v1,
)

EXIT_OK = 0
EXIT_BINDING_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline durable evidence binding: bind validated "
            "comparison_result_manifest_v1.json to durable evidence "
            "(index + MANIFEST.sha256)."
        )
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        required=True,
        help="Explicit path to comparison_result_manifest_v1.json.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit durable evidence bundle directory (must not exist; outside /tmp).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.manifest_path.is_file():
        print(
            "[comparison_ssot_result_durable_evidence_binding] ERROR: "
            f"manifest not found: {args.manifest_path}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        result = produce_comparison_ssot_result_durable_evidence_bundle_v1(
            manifest_path=args.manifest_path,
            output_dir=args.output_dir,
        )
    except ComparisonSsotResultDurableEvidenceBindingError as exc:
        print(
            f"[comparison_ssot_result_durable_evidence_binding] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_BINDING_ERROR

    print(
        "[comparison_ssot_result_durable_evidence_binding] wrote durable evidence bundle to "
        f"{result.output_dir} (comparison_definition_id={result.comparison_definition_id})"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
