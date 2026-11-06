#!/usr/bin/env python3
"""
Component VaR Demo Script
=========================

Demonstrates Component VaR calculation using sample fixtures.

Usage:
    python scripts/risk/demo_component_var.py
    # or with uv:
    uv run python scripts/risk/demo_component_var.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd

from src.risk.component_var import ComponentVaRCalculator
from src.risk.covariance import CovarianceEstimator, CovarianceEstimatorConfig
from src.risk.parametric_var import ParametricVaR, ParametricVaRConfig


def main():
    print("=" * 70)
    print("Component VaR Demo")
    print("=" * 70)

    # 1) Load sample returns
    fixture_path = (
        Path(__file__).parent.parent.parent / "tests" / "risk" / "fixtures" / "sample_returns.csv"
    )

    if not fixture_path.exists():
        print(f"ERROR: Fixture not found: {fixture_path}")
        print("Run: python tests/risk/fixtures/generate_sample_returns.py")
        return

    returns_df = pd.read_csv(fixture_path)
    print(f"\n✓ Loaded {len(returns_df)} days of returns for: {list(returns_df.columns)}")

    # 2) Configure covariance estimator
    cov_config = CovarianceEstimatorConfig(
        method="sample",  # Try: "diagonal_shrink" or "ledoit_wolf"
        min_history=60,
        shrinkage_alpha=0.1,
    )
    cov_estimator = CovarianceEstimator(cov_config)
    print(f"✓ Covariance method: {cov_config.method}")

    # 3) Configure VaR engine
    var_config = ParametricVaRConfig(
        confidence_level=0.95,
        horizon_days=1,
    )
    var_engine = ParametricVaR(var_config)
    print(
        f"✓ VaR config: {var_config.confidence_level * 100:.0f}% confidence, {var_config.horizon_days}-day horizon"
    )

    # 4) Create calculator
    calculator = ComponentVaRCalculator(cov_estimator, var_engine)

    # 5) Define portfolio
    weights = {
        "BTC": 0.5,
        "ETH": 0.3,
        "SOL": 0.2,
    }
    portfolio_value = 100_000.0  # EUR

    print(f"\n✓ Portfolio: {portfolio_value:,.0f} EUR")
    for asset, weight in weights.items():
        print(f"  - {asset}: {weight * 100:.1f}%")

    # 6) Calculate Component VaR
    print("\n" + "=" * 70)
    print("Calculating Component VaR...")
    print("=" * 70)

    result = calculator.calculate(
        returns_df=returns_df,
        weights=weights,
        portfolio_value=portfolio_value,
        validate_euler=True,
        euler_rtol=1e-6,
    )

    # 7) Display results
    print(f"\n{result}")

    # 8) Identify highest contributor
    df = result.to_dataframe()
    highest = df.loc[df["contribution_pct"].idxmax()]

    print("\n" + "=" * 70)
    print("Highest Risk Contributor")
    print("=" * 70)
    print(f"Asset:        {highest['asset']}")
    print(f"Weight:       {highest['weight'] * 100:.1f}%")
    print(f"Contribution: {highest['contribution_pct']:.1f}%")
    print(f"CompVaR:      {highest['component_var']:,.2f} EUR")

    print("\n" + "=" * 70)
    print("Interpretation")
    print("=" * 70)
    print(
        f"With {var_config.confidence_level * 100:.0f}% confidence, the portfolio is not expected to"
    )
    print(
        f"lose more than {result.total_var:,.2f} EUR over the next {var_config.horizon_days} day(s)."
    )
    print(f"\n{highest['asset']} contributes {highest['contribution_pct']:.1f}% of this risk.")

    print("\n✓ Demo complete!")


if __name__ == "__main__":
    main()
