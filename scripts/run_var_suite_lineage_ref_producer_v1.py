#!/usr/bin/env python3
"""
Offline Package J — VAR_SUITE LineageRef producer from explicit existing report directory.

Produces a validated, deterministic VAR_SUITE LineageRef JSON artifact only.
No VaR suite execution, promotion, apply, runtime, registry mutation, or live authority.

Usage:
    python3 scripts/run_var_suite_lineage_ref_producer_v1.py \\
        --report-dir reports/var_suite/run_pass_all \\
        --output reports/lineage_refs/var_suite_run_pass_all.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.governance.promotion_loop.var_suite_lineage_ref_producer_v1 import (
    VarSuiteLineageRefProducerError,
    produce_var_suite_lineage_ref_v1_to_path,
)

EXIT_OK = 0
EXIT_PRODUCER_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline Package J VAR_SUITE LineageRef producer: explicit existing "
            "VaR suite report directory to validated reference-only JSON artifact."
        )
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        required=True,
        help="Explicit path to an existing VaR suite report directory containing suite_report.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination path for the validated VAR_SUITE LineageRef JSON file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        result = produce_var_suite_lineage_ref_v1_to_path(
            report_dir=args.report_dir,
            output_path=args.output,
            fail_closed_if_exists=True,
        )
    except VarSuiteLineageRefProducerError as exc:
        print(f"[var_suite_lineage_ref] ERROR: {exc}", file=sys.stderr)
        return EXIT_PRODUCER_ERROR
    except OSError as exc:
        print(f"[var_suite_lineage_ref] ERROR: {exc}", file=sys.stderr)
        return EXIT_PRODUCER_ERROR

    print(
        "[var_suite_lineage_ref] wrote validated VAR_SUITE LineageRef to "
        f"{args.output} (ref_id={result.ref.ref_id}, digest={result.ref.digest})"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
