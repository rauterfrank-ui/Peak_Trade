#!/usr/bin/env python3
"""
Offline Package L — bind BACKTEST run directory + LineageRef to durable evidence.

Produces a validated durable evidence bundle with binding index and MANIFEST.sha256 only.
No backtest execution, promotion, apply, runtime, registry mutation, or live authority.

Usage:
    python3 scripts/run_backtest_durable_evidence_binding_v1.py \\
        --run-dir reports/backtests/completed-run-001 \\
        --backtest-lineage-ref reports/lineage_refs/backtest_completed-run-001.json \\
        --output-dir /var/evidence/backtest_bundle_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.backtest_durable_evidence_binding_v1 import (
    BacktestDurableEvidenceBindingError,
    produce_backtest_durable_evidence_bundle_v1,
)

EXIT_OK = 0
EXIT_BINDING_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline Package L: bind validated BACKTEST run directory and "
            "LineageRef to durable evidence (index + MANIFEST.sha256)."
        )
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Explicit path to a completed backtest run directory containing run_summary.json.",
    )
    parser.add_argument(
        "--backtest-lineage-ref",
        type=Path,
        required=True,
        help="Explicit path to a validated Package I BACKTEST LineageRef JSON file.",
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

    if not args.run_dir.is_dir():
        print(
            f"[backtest_durable_evidence_binding] ERROR: run directory not found: {args.run_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if not args.backtest_lineage_ref.is_file():
        print(
            "[backtest_durable_evidence_binding] ERROR: "
            f"backtest lineage ref not found: {args.backtest_lineage_ref}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        result = produce_backtest_durable_evidence_bundle_v1(
            run_dir=args.run_dir,
            backtest_lineage_ref_path=args.backtest_lineage_ref,
            output_dir=args.output_dir,
        )
    except BacktestDurableEvidenceBindingError as exc:
        print(f"[backtest_durable_evidence_binding] ERROR: {exc}", file=sys.stderr)
        return EXIT_BINDING_ERROR

    print(
        "[backtest_durable_evidence_binding] wrote durable evidence bundle to "
        f"{result.output_dir} (run_ref_id={result.run_ref_id})"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
