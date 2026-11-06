"""
Generate deterministic sample returns for Component VaR tests.

Creates 3 assets with defined correlations and volatilities:
- BTC: vol=0.03, weight=0.5
- ETH: vol=0.04, weight=0.3, corr(BTC)=0.7
- SOL: vol=0.05, weight=0.2, corr(BTC)=0.5, corr(ETH)=0.6
"""

import numpy as np
import pandas as pd
from pathlib import Path


def generate_sample_returns(
    n_days: int = 252,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generiert deterministische Sample Returns für 3 Assets.

    Args:
        n_days: Anzahl der Tage (default: 252 = 1 year)
        seed: Random seed für Reproduzierbarkeit

    Returns:
        DataFrame mit Spalten [BTC, ETH, SOL] und n_days Zeilen
    """
    np.random.seed(seed)

    # Define target parameters
    means = np.array([0.0005, 0.0003, 0.0002])  # Small positive drift
    vols = np.array([0.03, 0.04, 0.05])  # Daily volatilities

    # Correlation matrix
    corr = np.array(
        [
            [1.0, 0.7, 0.5],
            [0.7, 1.0, 0.6],
            [0.5, 0.6, 1.0],
        ]
    )

    # Convert to covariance
    cov = np.outer(vols, vols) * corr

    # Generate returns via Cholesky decomposition
    L = np.linalg.cholesky(cov)
    z = np.random.randn(n_days, 3)
    returns = means + z @ L.T

    # Create DataFrame
    df = pd.DataFrame(
        returns,
        columns=["BTC", "ETH", "SOL"],
    )

    return df


if __name__ == "__main__":
    output_path = Path(__file__).parent / "sample_returns.csv"
    df = generate_sample_returns()
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} days of returns for {list(df.columns)}")
    print(f"Saved to: {output_path}")
    print(f"\nSummary statistics:")
    print(df.describe())
    print(f"\nCorrelation matrix:")
    print(df.corr())
