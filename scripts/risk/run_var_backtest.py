#!/usr/bin/env python3
"""
VaR Backtest CLI Runner
=======================

Command-line interface for running VaR backtests with Kupiec POF test.

Exit Codes:
  0 - ACCEPT (Model valid)
  1 - REJECT (Model miscalibrated)
  2 - INCONCLUSIVE (Insufficient data)
  3 - ERROR (Execution error)

Usage:
  python scripts/risk/run_var_backtest.py \\
    --symbol BTC-EUR \\
    --start 2024-01-01 \\
    --end 2024-12-31 \\
    --confidence 0.99 \\
    --output results.json

  # CI Mode
  python scripts/risk/run_var_backtest.py \\
    --symbol BTC-EUR \\
    --ci-mode \\
    --fail-on-reject
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


def main():
    """Main entry point for VaR backtest CLI."""
    parser = argparse.ArgumentParser(
        description="VaR Backtest Runner with Kupiec POF Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Required arguments
    parser.add_argument(
        "--symbol",
        type=str,
        required=True,
        help="Symbol to backtest (e.g., BTC-EUR)",
    )

    # Date range
    parser.add_argument(
        "--start",
        type=str,
        help="Start date (YYYY-MM-DD). If not provided, uses all available data.",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY-MM-DD). If not provided, uses all available data.",
    )

    # VaR parameters
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.99,
        help="VaR confidence level (default: 0.99 for 99%% VaR)",
    )
    parser.add_argument(
        "--significance",
        type=float,
        default=0.05,
        help="Significance level for test (default: 0.05)",
    )
    parser.add_argument(
        "--min-observations",
        type=int,
        default=250,
        help="Minimum observations for valid test (default: 250)",
    )

    # Output
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for results (json format)",
    )

    # CI mode
    parser.add_argument(
        "--ci-mode",
        action="store_true",
        help="CI mode: minimal output, exit code based on result",
    )
    parser.add_argument(
        "--fail-on-reject",
        action="store_true",
        help="Exit with code 1 if test result is REJECT",
    )
    parser.add_argument(
        "--fail-on-inconclusive",
        action="store_true",
        help="Exit with code 2 if test result is INCONCLUSIVE",
    )

    args = parser.parse_args()

    # Import here to avoid slow startup for --help
    try:
        from src.risk_layer.var_backtest import VaRBacktestRunner
    except ImportError as e:
        print(f"ERROR: Failed to import VaRBacktestRunner: {e}", file=sys.stderr)
        sys.exit(3)

    # Generate synthetic data for demonstration
    # In production, this would load real data from data layer
    try:
        returns, var_estimates = _generate_synthetic_data(
            symbol=args.symbol,
            start_date=args.start,
            end_date=args.end,
            confidence=args.confidence,
        )
    except Exception as e:
        print(f"ERROR: Failed to load data: {e}", file=sys.stderr)
        sys.exit(3)

    # Run backtest
    try:
        runner = VaRBacktestRunner(
            confidence_level=args.confidence,
            significance_level=args.significance,
            min_observations=args.min_observations,
            var_method="historical",
        )

        result = runner.run(
            returns=returns,
            var_estimates=var_estimates,
            symbol=args.symbol,
        )

    except Exception as e:
        print(f"ERROR: Backtest failed: {e}", file=sys.stderr)
        sys.exit(3)

    # Format output
    output_data = _format_output(result)

    # Write to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        if not args.ci_mode:
            print(f"Results written to: {output_path}")

    # Print output (unless in CI mode)
    if not args.ci_mode:
        print("\n" + "=" * 60)
        print("VaR BACKTEST RESULTS")
        print("=" * 60)
        print(f"Symbol:           {result.symbol}")
        print(f"Period:           {result.start_date.date()} - {result.end_date.date()}")
        print(f"Confidence:       {result.var_confidence:.1%}")
        print(f"Observations:     {result.kupiec.n_observations}")
        print(f"Violations:       {result.kupiec.n_violations}")
        print(f"Expected Rate:    {result.kupiec.expected_violation_rate:.2%}")
        print(f"Observed Rate:    {result.kupiec.observed_violation_rate:.2%}")
        print(f"Violation Ratio:  {result.kupiec.violation_ratio:.2f}x")
        print("\nKupiec POF Test:")
        print(f"  LR Statistic:   {result.kupiec.lr_statistic:.4f}")
        print(f"  p-value:        {result.kupiec.p_value:.4f}")
        print(f"  Critical Value: {result.kupiec.critical_value:.4f}")
        print(f"\nRESULT:           {result.kupiec.result.value.upper()}")
        print(f"MODEL VALID:      {result.is_valid}")
        print("=" * 60 + "\n")
    else:
        # CI mode: minimal output
        print(
            f"{result.symbol}: {result.kupiec.result.value.upper()} "
            f"({result.kupiec.n_violations}/{result.kupiec.n_observations} violations)"
        )

    # Exit code based on result
    exit_code = _determine_exit_code(
        result=result,
        fail_on_reject=args.fail_on_reject,
        fail_on_inconclusive=args.fail_on_inconclusive,
    )

    sys.exit(exit_code)


def _generate_synthetic_data(
    symbol: str,
    start_date: str | None,
    end_date: str | None,
    confidence: float,
) -> tuple[pd.Series, pd.Series]:
    """
    Generate synthetic data for demonstration.

    In production, this would load real returns and VaR estimates
    from the data layer.

    Args:
        symbol: Symbol to generate data for
        start_date: Start date (YYYY-MM-DD) or None
        end_date: End date (YYYY-MM-DD) or None
        confidence: VaR confidence level

    Returns:
        Tuple of (returns, var_estimates)
    """
    # Parse dates
    if start_date:
        start = pd.Timestamp(start_date)
    else:
        start = pd.Timestamp("2024-01-01")

    if end_date:
        end = pd.Timestamp(end_date)
    else:
        end = pd.Timestamp("2024-12-31")

    # Generate date range
    dates = pd.date_range(start, end, freq="D")
    n_obs = len(dates)

    # Synthetic returns: mostly small losses/gains + few violations
    expected_violation_rate = 1 - confidence
    n_violations = int(n_obs * expected_violation_rate * 1.2)  # Slightly over-calibrated

    returns_list = [-0.01] * (n_obs - n_violations) + [-0.03] * n_violations
    returns = pd.Series(returns_list, index=dates)

    # Fixed VaR estimate at -2%
    var_estimates = pd.Series([-0.02] * n_obs, index=dates)

    return returns, var_estimates


def _format_output(result) -> dict:
    """
    Format backtest result as JSON-serializable dict.

    Args:
        result: VaRBacktestResult

    Returns:
        Dict with all results
    """
    return {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "test_type": "kupiec_pof",
        },
        "summary": {
            "symbol": result.symbol,
            "period": {
                "start": result.start_date.isoformat(),
                "end": result.end_date.isoformat(),
            },
            "result": result.kupiec.result.value,
            "is_valid": result.is_valid,
        },
        "statistics": {
            "n_observations": result.kupiec.n_observations,
            "n_violations": result.kupiec.n_violations,
            "confidence_level": result.var_confidence,
            "expected_violation_rate": result.kupiec.expected_violation_rate,
            "observed_violation_rate": result.kupiec.observed_violation_rate,
            "violation_ratio": result.kupiec.violation_ratio,
            "lr_statistic": result.kupiec.lr_statistic,
            "p_value": result.kupiec.p_value,
            "critical_value": result.kupiec.critical_value,
            "significance_level": result.kupiec.significance_level,
        },
        "violations": {
            "dates": [d.isoformat() for d in result.violations.violation_dates],
            "count": result.violations.n_violations,
        },
    }


def _determine_exit_code(
    result,
    fail_on_reject: bool,
    fail_on_inconclusive: bool,
) -> int:
    """
    Determine exit code based on result and flags.

    Args:
        result: VaRBacktestResult
        fail_on_reject: Exit with 1 on REJECT
        fail_on_inconclusive: Exit with 2 on INCONCLUSIVE

    Returns:
        Exit code (0, 1, 2, or 3)
    """
    from src.risk_layer.var_backtest import KupiecResult

    if result.kupiec.result == KupiecResult.ACCEPT:
        return 0
    elif result.kupiec.result == KupiecResult.REJECT:
        return 1 if fail_on_reject else 0
    elif result.kupiec.result == KupiecResult.INCONCLUSIVE:
        return 2 if fail_on_inconclusive else 0
    else:
        return 3  # Unknown result


if __name__ == "__main__":
    main()
