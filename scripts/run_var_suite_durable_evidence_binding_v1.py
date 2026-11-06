#!/usr/bin/env python3
"""
Offline Package K — bind VAR_SUITE report directory + LineageRef to durable evidence.

Produces a validated durable evidence bundle with binding index and MANIFEST.sha256 only.
No VaR execution, promotion, apply, runtime, registry mutation, or live authority.

Usage:
    python3 scripts/run_var_suite_durable_evidence_binding_v1.py \\
        --report-dir reports/var_suite/run_pass_all \\
        --var-suite-lineage-ref reports/lineage_refs/var_suite_run_pass_all.json \\
        --output-dir /var/evidence/var_suite_bundle_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.var_suite_durable_evidence_binding_v1 import (
    VarSuiteDurableEvidenceBindingError,
    produce_var_suite_durable_evidence_bundle_v1,
)

EXIT_OK = 0
EXIT_BINDING_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline Package K: bind validated VAR_SUITE report directory and "
            "LineageRef to durable evidence (index + MANIFEST.sha256)."
        )
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        required=True,
        help="Explicit path to an existing VaR suite report directory containing suite_report.json.",
    )
    parser.add_argument(
        "--var-suite-lineage-ref",
        type=Path,
        required=True,
        help="Explicit path to a validated Package J VAR_SUITE LineageRef JSON file.",
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

    if not args.report_dir.is_dir():
        print(
            "[var_suite_durable_evidence_binding] ERROR: "
            f"report directory not found: {args.report_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if not args.var_suite_lineage_ref.is_file():
        print(
            "[var_suite_durable_evidence_binding] ERROR: "
            f"var suite lineage ref not found: {args.var_suite_lineage_ref}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        result = produce_var_suite_durable_evidence_bundle_v1(
            report_dir=args.report_dir,
            var_suite_lineage_ref_path=args.var_suite_lineage_ref,
            output_dir=args.output_dir,
        )
    except VarSuiteDurableEvidenceBindingError as exc:
        print(f"[var_suite_durable_evidence_binding] ERROR: {exc}", file=sys.stderr)
        return EXIT_BINDING_ERROR

    print(
        "[var_suite_durable_evidence_binding] wrote durable evidence bundle to "
        f"{result.output_dir} (report_ref_id={result.report_ref_id})"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
