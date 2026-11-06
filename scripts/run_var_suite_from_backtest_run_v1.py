#!/usr/bin/env python3
"""
Package H — offline backtest returns to VaR suite evidence wiring CLI v1.

Wires explicit backtest run artifacts through the existing var_suite_adapter to
canonical suite_report.json and suite_report.md.  Evidence-only; no promotion,
apply, runtime, or registry mutation.

Usage:
    python3 scripts/run_var_suite_from_backtest_run_v1.py \\
        --run-dir results/backtest/run_001 \\
        --output-dir reports/var_suite/run_001

    python3 scripts/run_var_suite_from_backtest_run_v1.py \\
        --strategy-returns-manifest configs/strategy_returns.toml \\
        --strategy-id demo_strategy \\
        --output-dir reports/var_suite/demo_strategy
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.risk.validation.var_suite_backtest_wiring_v1 import (
    DEFAULT_ROLLING_WINDOW,
    VarSuiteBacktestWiringError,
    run_backtest_var_suite_wiring_v1,
)

EXIT_OK = 0
EXIT_WIRING_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline Package H: wire explicit backtest returns to VaR suite evidence reports."
        )
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Explicit backtest run directory containing equity artifacts.",
    )
    parser.add_argument(
        "--strategy-returns-manifest",
        type=Path,
        default=None,
        help="Explicit strategy_returns manifest TOML path.",
    )
    parser.add_argument(
        "--strategy-id",
        type=str,
        default=None,
        help="Strategy id key inside [strategy_returns] (required with --strategy-returns-manifest).",
    )
    parser.add_argument(
        "--manifest-base-dir",
        type=Path,
        default=None,
        help="Optional base directory for relative run_dir paths in the manifest.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit output directory for suite reports (must not exist).",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=DEFAULT_ROLLING_WINDOW,
        help=f"Rolling historical VaR window (default: {DEFAULT_ROLLING_WINDOW}).",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.95,
        help="VaR confidence level (default: 0.95).",
    )
    parser.add_argument(
        "--significance",
        type=float,
        default=0.05,
        help="Statistical test significance level (default: 0.05).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.strategy_returns_manifest is not None and not args.strategy_id:
        print(
            "ERROR: --strategy-id is required with --strategy-returns-manifest",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if args.run_dir is None and args.strategy_returns_manifest is None:
        print("ERROR: --run-dir or --strategy-returns-manifest is required", file=sys.stderr)
        return EXIT_USAGE_ERROR

    try:
        result = run_backtest_var_suite_wiring_v1(
            run_dir=args.run_dir,
            strategy_returns_manifest=args.strategy_returns_manifest,
            strategy_id=args.strategy_id,
            manifest_base_dir=args.manifest_base_dir,
            output_dir=args.output_dir,
            window=args.window,
            confidence_level=args.confidence,
            significance=args.significance,
        )
    except VarSuiteBacktestWiringError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_WIRING_ERROR
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_WIRING_ERROR

    print(f"overall_result={result.suite_result.overall_result}")
    print(f"observations={result.suite_result.observations}")
    print(f"output_dir={result.output_dir.name}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
