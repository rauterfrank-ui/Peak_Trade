#!/usr/bin/env python3
"""
Component VaR Report Generator Script
======================================

Generates HTML, JSON, and CSV reports for Component VaR analysis.

Usage:
    python scripts/run_component_var_report.py --returns data.csv --weights BTC=0.6,ETH=0.3,SOL=0.1
    python scripts/run_component_var_report.py --use-fixtures --alpha 0.95 --horizon 1
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.reporting.component_var_report import (
    ComponentVaRReportData,
    ComponentVaRReportGenerator,
    run_sanity_checks,
)
from src.risk.component_var import ComponentVaRCalculator
from src.risk.covariance import CovarianceEstimator, CovarianceEstimatorConfig
from src.risk.parametric_var import ParametricVaR, ParametricVaRConfig, z_score

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_weights(weights_str: str) -> Dict[str, float]:
    """
    Parse weights string like 'BTC=0.6,ETH=0.3,SOL=0.1'.

    Args:
        weights_str: Weights string

    Returns:
        Dictionary mapping symbol to weight
    """
    weights = {}
    for pair in weights_str.split(","):
        symbol, weight = pair.split("=")
        weights[symbol.strip()] = float(weight.strip())
    return weights


def load_fixture_data() -> pd.DataFrame:
    """Load fixture returns data for testing."""
    fixture_path = Path(__file__).parent.parent / "tests/risk/fixtures/sample_returns.csv"

    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {fixture_path}")

    df = pd.read_csv(fixture_path, index_col=0, parse_dates=True)
    logger.info(f"Loaded fixture data: {df.shape[0]} rows, {df.shape[1]} assets")
    return df


def load_returns_data(filepath: Path, lookback: Optional[int] = None) -> pd.DataFrame:
    """
    Load returns data from CSV.

    Args:
        filepath: Path to CSV file
        lookback: Optional lookback window (most recent N rows)

    Returns:
        DataFrame with returns
    """
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)

    if lookback:
        df = df.tail(lookback)

    logger.info(f"Loaded returns data: {df.shape[0]} rows, {df.shape[1]} assets")
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Generate Component VaR Report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--returns", type=Path, help="Path to returns CSV file (columns=assets, index=dates)"
    )
    input_group.add_argument(
        "--use-fixtures", action="store_true", help="Use fixture data for testing"
    )

    # Weights
    parser.add_argument(
        "--weights",
        type=str,
        help="Asset weights as 'SYMBOL=WEIGHT,...' (e.g., 'BTC=0.6,ETH=0.3,SOL=0.1'). If not provided, uses equal weights.",
    )

    # VaR parameters
    parser.add_argument(
        "--alpha", type=float, default=0.95, help="Confidence level (default: 0.95)"
    )
    parser.add_argument("--horizon", type=int, default=1, help="Horizon in days (default: 1)")
    parser.add_argument("--lookback", type=int, help="Lookback window in days (optional)")
    parser.add_argument(
        "--portfolio-value",
        type=float,
        default=1_000_000.0,
        help="Portfolio value in USD (default: 1,000,000)",
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: results/risk/component_var/<run_id>)",
    )
    parser.add_argument("--run-id", type=str, help="Run ID (default: auto-generated timestamp)")

    args = parser.parse_args()

    # Load returns data
    if args.use_fixtures:
        returns_df = load_fixture_data()
    else:
        returns_df = load_returns_data(args.returns, lookback=args.lookback)

    asset_symbols = list(returns_df.columns)

    # Parse or create weights
    if args.weights:
        weights_dict = parse_weights(args.weights)
        # Ensure all symbols in returns are covered
        weights_array = np.array([weights_dict.get(sym, 0.0) for sym in asset_symbols])
    else:
        # Equal weights
        weights_array = np.ones(len(asset_symbols)) / len(asset_symbols)
        logger.info("Using equal weights for all assets")

    # Normalize weights
    weights_array = weights_array / weights_array.sum()

    # Setup Component VaR calculator
    cov_config = CovarianceEstimatorConfig(method="sample", min_history=30)
    cov_estimator = CovarianceEstimator(cov_config)

    var_config = ParametricVaRConfig(confidence_level=args.alpha, horizon_days=args.horizon)
    var_engine = ParametricVaR(var_config)

    calculator = ComponentVaRCalculator(cov_estimator, var_engine)

    # Calculate Component VaR
    logger.info(f"Calculating Component VaR (α={args.alpha}, H={args.horizon})...")
    result = calculator.calculate(
        returns_df=returns_df,
        weights=weights_array,
        portfolio_value=args.portfolio_value,
        validate_euler=True,
    )

    # Run sanity checks
    sanity_checks = run_sanity_checks(
        weights=result.weights,
        component_var=result.component_var,
        total_var=result.total_var,
        asset_symbols=asset_symbols,
    )

    # Generate run ID
    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")

    # Set output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = Path("results/risk/component_var") / run_id

    # Prepare report data
    report_data = ComponentVaRReportData(
        run_id=run_id,
        timestamp=datetime.now().isoformat(),
        total_var=float(result.total_var),
        portfolio_value=args.portfolio_value,
        confidence=args.alpha,
        horizon=args.horizon,
        lookback_days=args.lookback or len(returns_df),
        asset_symbols=asset_symbols,
        weights=result.weights.tolist(),
        component_var=result.component_var.tolist(),
        contribution_pct=result.contribution_pct.tolist(),
        marginal_var=result.marginal_var.tolist(),
        sanity_checks=sanity_checks,
        metadata={
            "num_assets": len(asset_symbols),
            "data_rows": len(returns_df),
            "z_score": float(z_score(args.alpha)),
        },
    )

    # Generate reports
    generator = ComponentVaRReportGenerator(output_dir)
    outputs = generator.generate_reports(report_data)

    # Summary
    print("\n" + "=" * 80)
    print("Component VaR Report Generated")
    print("=" * 80)
    print(f"Run ID:         {run_id}")
    print(f"Output Dir:     {output_dir}")
    print(f"Total VaR:      ${result.total_var:,.2f}")
    print(f"Portfolio:      ${args.portfolio_value:,.2f}")
    print(f"Confidence:     {args.alpha * 100:.1f}%")
    print(f"Horizon:        {args.horizon} day(s)")
    print(f"Assets:         {len(asset_symbols)}")
    print(f"\nSanity Checks:  {'✅ PASS' if sanity_checks['all_pass'] else '⚠️  WARNINGS'}")
    print("\nGenerated Files:")
    for fmt, path in outputs.items():
        print(f"  - {fmt.upper():6s}: {path}")
    print("=" * 80)

    # Return appropriate exit code
    sys.exit(0 if sanity_checks["all_pass"] else 1)


if __name__ == "__main__":
    main()
