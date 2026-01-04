#!/usr/bin/env python3
"""
VaR Backtest Suite CLI Runner.

Runs complete VaR backtest suite (Kupiec POF, Basel Traffic Light,
Christoffersen IND/CC) and generates deterministic JSON + Markdown reports.

Phase 8C: Suite Report & Regression Guard

Usage:
    python scripts/risk/run_var_backtest_suite.py \\
        --returns-file data/returns.csv \\
        --var-file data/var.csv \\
        --confidence 0.95 \\
        --output-dir results/var_backtest/

Example:
    python scripts/risk/run_var_backtest_suite.py \\
        --returns-file tests/fixtures/var/returns_100d.csv \\
        --var-file tests/fixtures/var/var_95.csv \\
        --confidence 0.95 \\
        --output-dir /tmp/var_suite/
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# Add src/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.risk.validation.suite_runner import run_var_backtest_suite
from src.risk.validation.report_formatter import (
    format_suite_result_json,
    format_suite_result_markdown,
)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run VaR Backtest Suite (Kupiec POF, Basel, Christoffersen IND/CC)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--returns-file",
        type=str,
        required=True,
        help="Path to returns CSV file (1 column, indexed by date)",
    )
    parser.add_argument(
        "--var-file",
        type=str,
        required=True,
        help="Path to VaR CSV file (1 column, indexed by date, positive values)",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.95,
        help="VaR confidence level (default: 0.95)",
    )
    parser.add_argument(
        "--significance",
        type=float,
        default=0.05,
        help="Statistical test significance level (default: 0.05)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/var_backtest_suite",
        help="Output directory for reports (default: results/var_backtest_suite)",
    )
    parser.add_argument(
        "--print-markdown",
        action="store_true",
        help="Print Markdown report to stdout",
    )

    args = parser.parse_args()

    # Load data
    print(f"Loading returns from: {args.returns_file}")
    returns = pd.read_csv(args.returns_file, index_col=0, parse_dates=True).squeeze("columns")

    print(f"Loading VaR from: {args.var_file}")
    var_series = pd.read_csv(args.var_file, index_col=0, parse_dates=True).squeeze("columns")

    # Validate
    if len(returns) == 0:
        print("ERROR: Returns file is empty", file=sys.stderr)
        sys.exit(1)

    if len(var_series) == 0:
        print("ERROR: VaR file is empty", file=sys.stderr)
        sys.exit(1)

    print(f"Data loaded: {len(returns)} observations")

    # Run suite
    print(f"Running VaR backtest suite (confidence: {args.confidence:.2%})...")
    result = run_var_backtest_suite(
        returns=returns,
        var_series=var_series,
        confidence_level=args.confidence,
        significance=args.significance,
    )

    # Format reports
    json_report = format_suite_result_json(result)
    markdown_report = format_suite_result_markdown(result)

    # Write outputs
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "suite_report.json"
    markdown_path = output_dir / "suite_report.md"

    with open(json_path, "w") as f:
        f.write(json_report)
    print(f"✓ JSON report written to: {json_path}")

    with open(markdown_path, "w") as f:
        f.write(markdown_report)
    print(f"✓ Markdown report written to: {markdown_path}")

    # Optional: print markdown to stdout
    if args.print_markdown:
        print("\n" + "=" * 80)
        print(markdown_report)
        print("=" * 80)

    # Exit code based on overall result
    if result.overall_result == "PASS":
        print(f"\n✅ Suite PASSED (all tests green)")
        sys.exit(0)
    else:
        print(f"\n❌ Suite FAILED (see report for details)")
        sys.exit(1)


if __name__ == "__main__":
    main()
