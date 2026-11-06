#!/usr/bin/env python3
"""
Offline Package I — BACKTEST LineageRef producer from explicit completed run directory.

Produces a validated, deterministic BACKTEST LineageRef JSON artifact only.
No backtest start, promotion, apply, runtime, registry mutation, or live authority.

Usage:
    python3 scripts/run_backtest_lineage_ref_producer_v1.py \\
        --run-dir reports/backtests/run-001 \\
        --output reports/lineage_refs/backtest_run-001.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.governance.promotion_loop.backtest_lineage_ref_producer_v1 import (
    BacktestLineageRefProducerError,
    produce_backtest_lineage_ref_v1_to_path,
)

EXIT_OK = 0
EXIT_PRODUCER_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline Package I BACKTEST LineageRef producer: explicit completed "
            "backtest run directory to validated reference-only JSON artifact."
        )
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Explicit path to a completed backtest run directory containing run_summary.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination path for the validated BACKTEST LineageRef JSON file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        result = produce_backtest_lineage_ref_v1_to_path(
            run_dir=args.run_dir,
            output_path=args.output,
            fail_closed_if_exists=True,
        )
    except BacktestLineageRefProducerError as exc:
        print(f"[backtest_lineage_ref] ERROR: {exc}", file=sys.stderr)
        return EXIT_PRODUCER_ERROR
    except OSError as exc:
        print(f"[backtest_lineage_ref] ERROR: {exc}", file=sys.stderr)
        return EXIT_PRODUCER_ERROR

    print(
        "[backtest_lineage_ref] wrote validated BACKTEST LineageRef to "
        f"{args.output} (ref_id={result.ref.ref_id}, digest={result.ref.digest})"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
