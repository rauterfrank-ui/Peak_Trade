"""
Peak_Trade Portfolio VaR - Phase 1 Core
========================================
Portfolio-level Value at Risk (parametric + historical).

Phase 1: Core library only, no live-trading integration.

Features:
- Parametric VaR (Normal distribution, covariance-based)
- Historical VaR (empirical quantile)
- Symbol normalization (BTC/EUR -> BTC)
- Config builder for PeakConfig integration
- SciPy optional (fallback to statistics.NormalDist)

Usage:
    >>> from src.core.config import load_config
    >>> from src.risk.portfolio_var import build_portfolio_var_config_from_config, parametric_var
    >>>
    >>> cfg = load_config()
    >>> var_config = build_portfolio_var_config_from_config(cfg)
    >>>
    >>> # Compute VaR
    >>> returns_df = ...  # DataFrame with columns ["BTC", "ETH"]
    >>> weights = {"BTC/EUR": 0.6, "ETH/EUR": 0.4}
    >>> var = parametric_var(returns_df, weights, confidence=0.99, horizon_days=1)
    >>> print(f"VaR(99%): {var:.2%}")
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, Literal, Mapping, Sequence, Union
import math

import numpy as np
import pandas as pd

# Optional SciPy imports
try:
    from scipy.stats import norm as scipy_norm
    from scipy.stats import binomtest as scipy_binomtest

    SCIPY_AVAILABLE = True
except ImportError:
    scipy_norm = None
    scipy_binomtest = None
    SCIPY_AVAILABLE = False

# Fallback for z-value: statistics.NormalDist (Python 3.8+)
from statistics import NormalDist


@dataclass
class PortfolioVarConfig:
    """
    Configuration for Portfolio VaR calculations.

    Attributes:
        enabled: Enable portfolio VaR calculations
        method: VaR method ("parametric" or "historical")
        confidence: Confidence level (e.g. 0.99 for 99% VaR)
        horizon_days: Risk horizon in days (default: 1)
        lookback_bars: Number of bars for historical data (default: 500)
        symbol_mode: Symbol normalization mode ("base" or "raw")
        use_mean: Include mean return in parametric VaR (default: False, more conservative)
    """

    enabled: bool = True
    method: Literal["parametric", "historical"] = "parametric"
    confidence: float = 0.99
    horizon_days: int = 1
    lookback_bars: int = 500
    symbol_mode: Literal["base", "raw"] = "base"
    use_mean: bool = False

    def __post_init__(self) -> None:
        """Validate config."""
        if not 0 < self.confidence < 1:
            raise ValueError(f"confidence must be in (0,1), got {self.confidence}")
        if self.horizon_days <= 0:
            raise ValueError(f"horizon_days must be > 0, got {self.horizon_days}")
        if self.lookback_bars < 2:
            raise ValueError(f"lookback_bars must be >= 2, got {self.lookback_bars}")


def build_portfolio_var_config_from_config(cfg: Any) -> PortfolioVarConfig:
    """
    Build PortfolioVarConfig from PeakConfig.

    Args:
        cfg: PeakConfig instance (with .get("a.b.c", default) method)

    Returns:
        PortfolioVarConfig instance

    Expected config structure (config.toml):

        [risk.portfolio_var]
        enabled = true
        method = "parametric"  # or "historical"
        confidence = 0.99
        horizon_days = 1
        lookback_bars = 500
        symbol_mode = "base"  # or "raw"
        use_mean = false

    Example:
        >>> from src.core.config import load_config
        >>> cfg = load_config()
        >>> var_config = build_portfolio_var_config_from_config(cfg)
    """
    return PortfolioVarConfig(
        enabled=bool(cfg.get("risk.portfolio_var.enabled", True)),
        method=str(cfg.get("risk.portfolio_var.method", "parametric")),
        confidence=float(cfg.get("risk.portfolio_var.confidence", 0.99)),
        horizon_days=int(cfg.get("risk.portfolio_var.horizon_days", 1)),
        lookback_bars=int(cfg.get("risk.portfolio_var.lookback_bars", 500)),
        symbol_mode=str(cfg.get("risk.portfolio_var.symbol_mode", "base")),
        use_mean=bool(cfg.get("risk.portfolio_var.use_mean", False)),
    )


def normalize_symbol(symbol: str, mode: Literal["base", "raw"] = "base") -> str:
    """
    Normalize symbol for returns DataFrame keying.

    Args:
        symbol: Raw symbol (e.g. "BTC/EUR", "ETH-USD", "SOL_USDT")
        mode: Normalization mode
            - "base": Extract base asset (BTC/EUR -> BTC)
            - "raw": Return unchanged

    Returns:
        Normalized symbol

    Examples:
        >>> normalize_symbol("BTC/EUR", mode="base")
        'BTC'
        >>> normalize_symbol("ETH-USD", mode="base")
        'ETH'
        >>> normalize_symbol("SOL_USDT", mode="base")
        'SOL'
        >>> normalize_symbol("BTC", mode="base")
        'BTC'
        >>> normalize_symbol("BTC/EUR", mode="raw")
        'BTC/EUR'
    """
    if mode == "raw":
        return symbol

    # mode == "base": Extract base asset
    # Split on common separators: / - _
    parts = re.split(r"[/_-]", symbol)
    return parts[0].upper()


def align_weights_to_returns(
    weights: Union[Mapping[str, float], Sequence[float]],
    returns_cols: Sequence[str],
    symbol_mode: Literal["base", "raw"] = "base",
) -> np.ndarray:
    """
    Align weights to returns DataFrame columns.

    Args:
        weights: Portfolio weights (dict or sequence)
            - If dict: keys are symbols (will be normalized), values are weights
            - If sequence: must match returns_cols order exactly
        returns_cols: Column names from returns DataFrame
        symbol_mode: Symbol normalization mode

    Returns:
        NumPy array of weights aligned to returns_cols

    Raises:
        ValueError: If weights don't sum to ~1.0 or if symbols are missing

    Examples:
        >>> returns_cols = ["BTC", "ETH"]
        >>> weights = {"BTC/EUR": 0.6, "ETH/EUR": 0.4}
        >>> w = align_weights_to_returns(weights, returns_cols, symbol_mode="base")
        >>> w
        array([0.6, 0.4])

        >>> weights = [0.5, 0.5]
        >>> w = align_weights_to_returns(weights, returns_cols)
        >>> w
        array([0.5, 0.5])
    """
    if isinstance(weights, Mapping):
        # Normalize symbols in weights
        normalized_weights = {}
        for symbol, weight in weights.items():
            norm_symbol = normalize_symbol(symbol, mode=symbol_mode)
            normalized_weights[norm_symbol] = weight

        # Build weight array aligned to returns_cols
        w = []
        missing = []
        for col in returns_cols:
            if col in normalized_weights:
                w.append(normalized_weights[col])
            else:
                missing.append(col)

        if missing:
            raise ValueError(
                f"Missing weights for returns columns: {missing}. "
                f"Available normalized weights: {list(normalized_weights.keys())}"
            )

        w = np.array(w)
    else:
        # Sequence: must match length
        w = np.array(weights)
        if len(w) != len(returns_cols):
            raise ValueError(
                f"Weights sequence length ({len(w)}) must match "
                f"returns columns ({len(returns_cols)})"
            )

    # Validate sum ~= 1.0
    weight_sum = w.sum()
    if not (0.99 <= weight_sum <= 1.01):
        raise ValueError(
            f"Weights must sum to ~1.0, got {weight_sum:.4f}. "
            f"Please normalize weights before calling VaR functions."
        )

    return w


def estimate_cov(returns_df: pd.DataFrame) -> np.ndarray:
    """
    Estimate covariance matrix from returns DataFrame.

    Args:
        returns_df: DataFrame with returns (rows=time, columns=assets)

    Returns:
        Covariance matrix as NumPy array

    Notes:
        - Uses sample covariance (ddof=1)
        - Drops NaN rows before calculation
        - Minimum 2 rows required

    Example:
        >>> returns_df = pd.DataFrame({"BTC": [0.01, -0.02], "ETH": [0.02, -0.01]})
        >>> cov = estimate_cov(returns_df)
        >>> cov.shape
        (2, 2)
    """
    clean_df = returns_df.dropna()

    if len(clean_df) < 2:
        raise ValueError(f"Need at least 2 rows for covariance estimation, got {len(clean_df)}")

    return clean_df.cov().values


def portfolio_sigma(cov: np.ndarray, w: np.ndarray) -> float:
    """
    Compute portfolio standard deviation.

    Args:
        cov: Covariance matrix (n x n)
        w: Weight vector (n,)

    Returns:
        Portfolio standard deviation (sigma_portfolio)

    Formula:
        sigma_p = sqrt(w^T * Σ * w)

    Example:
        >>> cov = np.array([[0.04, 0.01], [0.01, 0.09]])
        >>> w = np.array([0.5, 0.5])
        >>> sigma = portfolio_sigma(cov, w)
        >>> sigma
        0.158...
    """
    variance = w @ cov @ w
    return np.sqrt(variance)


def z_value(confidence: float) -> float:
    """
    Compute z-value (inverse CDF) for Normal distribution.

    Args:
        confidence: Confidence level (e.g. 0.99)

    Returns:
        z-value (positive for upper tail)

    Notes:
        - Uses scipy.stats.norm if available
        - Falls back to statistics.NormalDist

    Examples:
        >>> z = z_value(0.95)
        >>> abs(z - 1.645) < 0.01
        True
        >>> z = z_value(0.99)
        >>> abs(z - 2.326) < 0.01
        True
    """
    if SCIPY_AVAILABLE and scipy_norm is not None:
        return scipy_norm.ppf(confidence)
    else:
        # Fallback to statistics.NormalDist
        return NormalDist().inv_cdf(confidence)


def parametric_var(
    returns_df: pd.DataFrame,
    weights: Union[Mapping[str, float], Sequence[float]],
    confidence: float = 0.99,
    horizon_days: int = 1,
    symbol_mode: Literal["base", "raw"] = "base",
    use_mean: bool = False,
) -> float:
    """
    Compute parametric Value at Risk (Normal distribution, covariance-based).

    Args:
        returns_df: DataFrame with asset returns (rows=time, columns=assets)
        weights: Portfolio weights (dict or sequence)
        confidence: Confidence level (e.g. 0.99 for 99% VaR)
        horizon_days: Risk horizon in days
        symbol_mode: Symbol normalization mode ("base" or "raw")
        use_mean: Include mean return in VaR calculation (default: False, more conservative)

    Returns:
        VaR as positive float (in return units, e.g. 0.023 = 2.3%)

    Formula (use_mean=False):
        VaR = z_α * σ_portfolio * sqrt(horizon)

    Formula (use_mean=True):
        VaR = -(μ_portfolio * horizon - z_α * σ_portfolio * sqrt(horizon))

    Notes:
        - Assumes Normal distribution (multivariate)
        - More accurate for short horizons and stable markets
        - use_mean=False is more conservative (ignores positive drift)

    Example:
        >>> returns_df = pd.DataFrame({"BTC": [0.01, -0.02, 0.03], "ETH": [0.02, -0.01, 0.02]})
        >>> weights = {"BTC": 0.5, "ETH": 0.5}
        >>> var = parametric_var(returns_df, weights, confidence=0.95, horizon_days=1)
        >>> var > 0
        True
    """
    # 1. Align weights
    w = align_weights_to_returns(weights, returns_df.columns, symbol_mode=symbol_mode)

    # 2. Estimate covariance
    cov = estimate_cov(returns_df)

    # 3. Portfolio sigma
    sigma_p = portfolio_sigma(cov, w)

    # 4. Z-value for confidence
    z = z_value(confidence)

    # 5. Compute VaR
    horizon_factor = np.sqrt(horizon_days)

    if use_mean:
        # Include mean drift (can reduce VaR if positive returns)
        clean_returns = returns_df.dropna()
        portfolio_returns = clean_returns @ w
        mu_p = portfolio_returns.mean()

        # VaR = -(μ * h - z * σ * sqrt(h))
        var = -(mu_p * horizon_days - z * sigma_p * horizon_factor)
    else:
        # Conservative: ignore mean (assumes μ=0)
        var = z * sigma_p * horizon_factor

    return max(var, 0.0)


def historical_var(
    returns_df: pd.DataFrame,
    weights: Union[Mapping[str, float], Sequence[float]],
    confidence: float = 0.99,
    horizon_days: int = 1,
    symbol_mode: Literal["base", "raw"] = "base",
) -> float:
    """
    Compute historical Value at Risk (empirical quantile).

    Args:
        returns_df: DataFrame with asset returns (rows=time, columns=assets)
        weights: Portfolio weights (dict or sequence)
        confidence: Confidence level (e.g. 0.99 for 99% VaR)
        horizon_days: Risk horizon in days
        symbol_mode: Symbol normalization mode ("base" or "raw")

    Returns:
        VaR as positive float (in return units)

    Formula:
        VaR = -quantile(portfolio_returns, 1 - confidence)

    For horizon_days > 1:
        - Compute rolling compounded returns over horizon
        - Take quantile of aggregated returns

    Notes:
        - Non-parametric, no distribution assumption
        - Requires sufficient historical data (>= 100 bars recommended)

    Example:
        >>> returns_df = pd.DataFrame({"BTC": [0.01, -0.02, 0.03, -0.01], "ETH": [0.02, -0.01, 0.02, 0.01]})
        >>> weights = {"BTC": 0.5, "ETH": 0.5}
        >>> var = historical_var(returns_df, weights, confidence=0.95, horizon_days=1)
        >>> var > 0
        True
    """
    # 1. Align weights
    w = align_weights_to_returns(weights, returns_df.columns, symbol_mode=symbol_mode)

    # 2. Compute portfolio returns
    clean_returns = returns_df.dropna()
    if len(clean_returns) < 2:
        raise ValueError(f"Need at least 2 rows for historical VaR, got {len(clean_returns)}")

    portfolio_returns = clean_returns @ w

    # 3. Handle horizon
    if horizon_days == 1:
        # Simple case: use returns directly
        agg_returns = portfolio_returns
    else:
        # Rolling compounded returns over horizon
        # (1+r_1) * (1+r_2) * ... * (1+r_h) - 1
        rolling_prod = (
            (1 + portfolio_returns).rolling(window=horizon_days).apply(lambda x: x.prod(), raw=True)
        )
        agg_returns = rolling_prod - 1
        agg_returns = agg_returns.dropna()

        if len(agg_returns) < 2:
            raise ValueError(
                f"Insufficient data for horizon_days={horizon_days}. "
                f"Need at least {horizon_days + 1} bars."
            )

    # 4. Compute quantile
    # VaR is the loss at confidence level (lower tail)
    # quantile at (1 - confidence) is the loss threshold
    quantile_val = agg_returns.quantile(1 - confidence)

    # 5. VaR as positive number (negate loss)
    var = -quantile_val

    return max(var, 0.0)


def binom_p_value(
    k: int,
    n: int,
    p: float,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
) -> float:
    """
    Compute p-value for binomial test.

    Args:
        k: Number of successes
        n: Number of trials
        p: Hypothesized probability of success
        alternative: Alternative hypothesis ("two-sided", "greater", "less")

    Returns:
        p-value (float in [0, 1])

    Notes:
        - Uses scipy.stats.binomtest if available
        - Falls back to exact binomial calculation
        - Useful for backtesting VaR models (Kupiec test)

    Example:
        >>> p_val = binom_p_value(k=50, n=100, p=0.5, alternative="two-sided")
        >>> 0.9 < p_val < 1.0  # Near 1.0 (no evidence against H0)
        True
    """
    if SCIPY_AVAILABLE and scipy_binomtest is not None:
        # Use scipy.stats.binomtest (modern, not deprecated)
        result = scipy_binomtest(k, n, p, alternative=alternative)
        return result.pvalue

    # Fallback: exact binomial p-value calculation
    return _binom_p_value_fallback(k, n, p, alternative)


def _binom_p_value_fallback(k: int, n: int, p: float, alternative: str = "two-sided") -> float:
    """
    Fallback implementation for binomial p-value (no scipy).

    Uses exact binomial PMF calculation.
    """

    def binom_pmf(k_val: int, n_val: int, p_val: float) -> float:
        """Binomial PMF: P(X = k)"""
        if k_val < 0 or k_val > n_val:
            return 0.0
        return math.comb(n_val, k_val) * (p_val**k_val) * ((1 - p_val) ** (n_val - k_val))

    if alternative == "two-sided":
        # Two-sided: sum all outcomes with pmf <= pmf(k)
        pmf_k = binom_pmf(k, n, p)
        p_value = sum(binom_pmf(i, n, p) for i in range(n + 1) if binom_pmf(i, n, p) <= pmf_k)
    elif alternative == "greater":
        # P(X >= k)
        p_value = sum(binom_pmf(i, n, p) for i in range(k, n + 1))
    elif alternative == "less":
        # P(X <= k)
        p_value = sum(binom_pmf(i, n, p) for i in range(0, k + 1))
    else:
        raise ValueError(f"Invalid alternative: {alternative}")

    return min(max(p_value, 0.0), 1.0)  # Clamp to [0, 1]
