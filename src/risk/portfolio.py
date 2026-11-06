"""
Peak_Trade Risk Layer - Portfolio Analytics
============================================
Portfolio-Level Risk-Funktionen: Exposures, Weights, Correlations.

Functions:
- compute_position_notional: Berechnet Notional einer Position
- compute_gross_exposure: Summe aller |notional|
- compute_net_exposure: Long - Short Exposure
- compute_weights: Portfolio-Weights für jede Position
- correlation_matrix: Korrelationsmatrix aus Returns
- portfolio_returns: Portfolio-Returns aus Weights + Asset-Returns
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional
import logging

from .types import PositionSnapshot

logger = logging.getLogger(__name__)


def compute_position_notional(units: float, price: float) -> float:
    """
    Berechnet Notional einer Position.

    Args:
        units: Anzahl Units (positiv/negativ)
        price: Preis pro Unit

    Returns:
        Absoluter Notional-Wert (immer positiv)

    Example:
        >>> compute_position_notional(0.5, 50000)
        25000.0
        >>> compute_position_notional(-0.3, 2000)  # Short
        600.0
    """
    return abs(units * price)


def compute_gross_exposure(positions: List[PositionSnapshot]) -> float:
    """
    Berechnet Gross Exposure: Summe aller |notional|.

    Args:
        positions: Liste von PositionSnapshots

    Returns:
        Gross Exposure (immer >= 0)

    Example:
        >>> pos1 = PositionSnapshot("BTC/EUR", 0.5, 50000)  # notional=25000
        >>> pos2 = PositionSnapshot("ETH/EUR", -10, 3000)   # notional=30000
        >>> compute_gross_exposure([pos1, pos2])
        55000.0
    """
    if not positions:
        return 0.0
    return sum(abs(pos.notional or 0.0) for pos in positions)


def compute_net_exposure(positions: List[PositionSnapshot]) -> float:
    """
    Berechnet Net Exposure: Long - Short Notionals.

    Args:
        positions: Liste von PositionSnapshots

    Returns:
        Net Exposure (kann positiv/negativ sein)

    Example:
        >>> pos1 = PositionSnapshot("BTC/EUR", 0.5, 50000)   # +25000
        >>> pos2 = PositionSnapshot("ETH/EUR", -10, 3000)    # -30000
        >>> compute_net_exposure([pos1, pos2])
        -5000.0  # net short
    """
    if not positions:
        return 0.0
    return sum(pos.units * pos.price for pos in positions)


def compute_weights(
    positions: List[PositionSnapshot],
    equity: float,
) -> Dict[str, float]:
    """
    Berechnet Portfolio-Weights für jede Position.

    Args:
        positions: Liste von PositionSnapshots
        equity: Gesamtes Eigenkapital

    Returns:
        Dict {symbol: weight} (weight in 0-1, kann >1 bei Leverage)

    Raises:
        ValueError: Wenn equity <= 0

    Example:
        >>> pos1 = PositionSnapshot("BTC/EUR", 0.5, 50000)  # notional=25000
        >>> pos2 = PositionSnapshot("ETH/EUR", 2, 3000)     # notional=6000
        >>> compute_weights([pos1, pos2], equity=100000)
        {'BTC/EUR': 0.25, 'ETH/EUR': 0.06}
    """
    if equity <= 0:
        raise ValueError(f"Equity must be > 0, got {equity}")

    if not positions:
        return {}

    weights = {}
    for pos in positions:
        notional = abs(pos.notional or 0.0)
        weights[pos.symbol] = notional / equity

    return weights


def correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    """
    Berechnet Korrelationsmatrix aus Return-Daten.

    Args:
        returns_df: DataFrame mit Returns (Spalten=Assets, Rows=Time)

    Returns:
        Korrelationsmatrix als DataFrame

    Notes:
        - Verwendet Pearson-Korrelation
        - NaN-Werte werden ignoriert (pairwise deletion)
        - Leere/konstante Spalten führen zu NaN-Korrelationen

    Example:
        >>> returns = pd.DataFrame({
        ...     'BTC': [0.01, -0.02, 0.03],
        ...     'ETH': [0.02, -0.01, 0.02]
        ... })
        >>> corr = correlation_matrix(returns)
        >>> corr.loc['BTC', 'ETH']
        0.98...  # Hoch korreliert
    """
    if returns_df.empty:
        logger.warning("correlation_matrix: Empty DataFrame, returning empty matrix")
        return pd.DataFrame()

    # Pearson-Korrelation, pairwise deletion bei NaNs
    corr = returns_df.corr(method="pearson", min_periods=1)

    return corr


def portfolio_returns(
    returns_df: pd.DataFrame,
    weights: Dict[str, float],
) -> pd.Series:
    """
    Berechnet Portfolio-Returns aus Asset-Returns und Weights.

    Args:
        returns_df: DataFrame mit Returns (Spalten=Assets, Rows=Time)
        weights: Dict {asset: weight}, Summe sollte ~1.0 sein

    Returns:
        Series mit Portfolio-Returns über Zeit

    Notes:
        - Fehlende Assets in returns_df werden ignoriert
        - Weights werden auf verfügbare Assets normiert
        - Leere Returns oder Weights führen zu leerer Series

    Example:
        >>> returns = pd.DataFrame({
        ...     'BTC': [0.01, -0.02, 0.03],
        ...     'ETH': [0.02, -0.01, 0.02]
        ... })
        >>> weights = {'BTC': 0.6, 'ETH': 0.4}
        >>> portfolio_returns(returns, weights)
        0    0.014   # 0.6*0.01 + 0.4*0.02
        1   -0.016   # 0.6*-0.02 + 0.4*-0.01
        2    0.026   # 0.6*0.03 + 0.4*0.02
        dtype: float64
    """
    if returns_df.empty or not weights:
        logger.warning("portfolio_returns: Empty input, returning empty Series")
        return pd.Series(dtype=float)

    # Filtere Weights auf verfügbare Assets
    available_assets = [col for col in returns_df.columns if col in weights]
    if not available_assets:
        logger.warning("portfolio_returns: No matching assets between returns and weights")
        return pd.Series(dtype=float)

    # Extrahiere relevante Returns
    relevant_returns = returns_df[available_assets]

    # Erstelle Weight-Array (normiert auf verfügbare Assets)
    weight_values = np.array([weights[asset] for asset in available_assets])
    total_weight = weight_values.sum()

    if total_weight <= 0:
        logger.warning("portfolio_returns: Total weight <= 0")
        return pd.Series(dtype=float)

    # Normiere Weights
    weight_values = weight_values / total_weight

    # Berechne Portfolio-Returns: (Returns @ Weights)
    portfolio_ret = relevant_returns.dot(weight_values)

    return portfolio_ret
