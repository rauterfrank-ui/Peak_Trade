"""
Peak_Trade Risk Layer - Value at Risk (VaR) & CVaR
===================================================
Implementierung von VaR/CVaR-Metriken (Historical + Parametric).

Functions:
- historical_var: Historical Value at Risk
- historical_cvar: Historical Conditional Value at Risk (Expected Shortfall)
- parametric_var: Parametric VaR (Normal-Annahme)
- parametric_cvar: Parametric CVaR (Normal-Annahme)

Conventions:
- returns: pd.Series mit period returns (z.B. daily returns als Dezimalzahl: 0.02 = +2%)
- alpha: Konfidenzniveau (z.B. 0.05 = 5% Tail, 95% VaR)
- Output: VaR/CVaR als POSITIVE Zahl (Loss-Größe)

Example:
    >>> returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
    >>> var_95 = historical_var(returns, alpha=0.05)
    >>> cvar_95 = historical_cvar(returns, alpha=0.05)
    >>> print(f"VaR(95%): {var_95:.2%}, CVaR(95%): {cvar_95:.2%}")
"""

import numpy as np
import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def historical_var(returns: pd.Series, alpha: float = 0.05) -> float:
    """
    Historical Value at Risk: Alpha-Quantil der empirischen Return-Verteilung.

    Args:
        returns: Return-Series (period returns, z.B. daily)
        alpha: Signifikanzniveau (z.B. 0.05 für 95% VaR)

    Returns:
        VaR als positive Zahl (Loss-Größe)

    Notes:
        - Verwendet empirisches Quantil (np.percentile)
        - Bei wenigen Datenpunkten ungenau
        - Nicht-parametrisch, keine Verteilungsannahme

    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        >>> historical_var(returns, alpha=0.05)
        0.02  # 5%-Quantil = -2% Loss -> VaR=2%
    """
    if returns.empty:
        logger.warning("historical_var: Empty returns, returning 0")
        return 0.0

    # Entferne NaNs
    clean_returns = returns.dropna()

    if len(clean_returns) == 0:
        logger.warning("historical_var: All NaN returns, returning 0")
        return 0.0

    # Alpha-Quantil (linke Tail)
    quantile_val = np.percentile(clean_returns, alpha * 100)

    # VaR als positive Loss-Größe
    var = -quantile_val if quantile_val < 0 else 0.0

    return var


def historical_cvar(returns: pd.Series, alpha: float = 0.05) -> float:
    """
    Historical Conditional Value at Risk (Expected Shortfall):
    Mittlerer Loss aller Returns <= VaR-Schwelle.

    Args:
        returns: Return-Series (period returns)
        alpha: Signifikanzniveau (z.B. 0.05 für 95% CVaR)

    Returns:
        CVaR als positive Zahl (durchschnittlicher Loss im Tail)

    Notes:
        - CVaR >= VaR (immer)
        - Kohärentes Risk-Maß (im Gegensatz zu VaR)
        - Berücksichtigt Form des Tails

    Example:
        >>> returns = pd.Series([0.01, -0.02, -0.03, -0.01, 0.02])
        >>> historical_cvar(returns, alpha=0.05)
        0.03  # Mean of worst 5% = -3% -> CVaR=3%
    """
    if returns.empty:
        logger.warning("historical_cvar: Empty returns, returning 0")
        return 0.0

    # Entferne NaNs
    clean_returns = returns.dropna()

    if len(clean_returns) == 0:
        logger.warning("historical_cvar: All NaN returns, returning 0")
        return 0.0

    # VaR-Schwelle berechnen
    var_threshold = -historical_var(returns, alpha)

    # Alle Returns <= VaR-Schwelle (linker Tail)
    tail_returns = clean_returns[clean_returns <= var_threshold]

    if len(tail_returns) == 0:
        # Kein Loss im Tail -> CVaR = VaR
        return historical_var(returns, alpha)

    # Mittlerer Loss im Tail
    cvar = -tail_returns.mean()

    return cvar


def parametric_var(returns: pd.Series, alpha: float = 0.05) -> float:
    """
    Parametric Value at Risk (Normal-Annahme):
    VaR = -mean + z_alpha * std

    Args:
        returns: Return-Series (period returns)
        alpha: Signifikanzniveau (z.B. 0.05 für 95% VaR)

    Returns:
        VaR als positive Zahl (Loss-Größe)

    Notes:
        - Annahme: Returns sind normalverteilt
        - Nutzt scipy für Normal-Quantile (falls verfügbar)
        - Fallback: Standard-Quantile für alpha=0.01, 0.05, 0.10
        - Schnell, aber ungenau bei Fat Tails

    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        >>> parametric_var(returns, alpha=0.05)
        0.051...  # -mean + 1.645*std
    """
    if returns.empty:
        logger.warning("parametric_var: Empty returns, returning 0")
        return 0.0

    # Entferne NaNs
    clean_returns = returns.dropna()

    if len(clean_returns) < 2:
        logger.warning("parametric_var: Insufficient data (n<2), returning 0")
        return 0.0

    mean = clean_returns.mean()
    std = clean_returns.std(ddof=1)

    if std == 0:
        logger.warning("parametric_var: Zero volatility, returning 0")
        return 0.0

    # Z-Score für alpha-Quantil
    z_alpha = _get_normal_quantile(alpha)

    # VaR = -mean + z_alpha * std (z_alpha ist negativ)
    var = -(mean + z_alpha * std)

    return max(var, 0.0)


def parametric_cvar(returns: pd.Series, alpha: float = 0.05) -> float:
    """
    Parametric Conditional Value at Risk (Normal-Annahme):
    CVaR = -mean + std * phi(z_alpha) / alpha

    wobei phi = Dichte der Standardnormalverteilung

    Args:
        returns: Return-Series (period returns)
        alpha: Signifikanzniveau (z.B. 0.05 für 95% CVaR)

    Returns:
        CVaR als positive Zahl (durchschnittlicher Loss im Tail)

    Notes:
        - Annahme: Returns sind normalverteilt
        - CVaR > VaR (bei Normal-Verteilung)
        - Formel: CVaR = -mean + std * phi(z_alpha) / alpha

    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        >>> parametric_cvar(returns, alpha=0.05)
        0.062...  # Höher als parametric_var
    """
    if returns.empty:
        logger.warning("parametric_cvar: Empty returns, returning 0")
        return 0.0

    # Entferne NaNs
    clean_returns = returns.dropna()

    if len(clean_returns) < 2:
        logger.warning("parametric_cvar: Insufficient data (n<2), returning 0")
        return 0.0

    mean = clean_returns.mean()
    std = clean_returns.std(ddof=1)

    if std == 0:
        logger.warning("parametric_cvar: Zero volatility, returning 0")
        return 0.0

    # Z-Score für alpha-Quantil
    z_alpha = _get_normal_quantile(alpha)

    # Phi(z_alpha) = Dichte der Standardnormalverteilung
    phi_z = _normal_pdf(z_alpha)

    # CVaR = -mean + std * phi(z_alpha) / alpha
    # Note: z_alpha ist negativ, phi_z ist positiv, also phi_z/alpha > 0
    # CVaR = std * phi(z_alpha) / alpha - mean
    cvar = (std * phi_z / alpha) - mean

    return max(cvar, 0.0)


def _get_normal_quantile(alpha: float) -> float:
    """
    Berechnet z-Score (Quantil) der Standardnormalverteilung.

    Args:
        alpha: Signifikanzniveau (z.B. 0.05)

    Returns:
        z-Score (negativ für linke Tail)

    Notes:
        - Versucht scipy.stats.norm.ppf
        - Fallback: Lookup-Table für gängige Alphas
    """
    try:
        from scipy.stats import norm

        return norm.ppf(alpha)
    except ImportError:
        # Fallback: Lookup-Table
        lookup = {
            0.01: -2.326,  # 99% VaR
            0.025: -1.96,  # 97.5% VaR
            0.05: -1.645,  # 95% VaR
            0.10: -1.282,  # 90% VaR
        }

        if alpha in lookup:
            return lookup[alpha]

        # Approximation für andere Alphas (grob)
        logger.warning(
            f"parametric_var: scipy nicht verfügbar, alpha={alpha} nicht in Lookup-Table. "
            f"Verwende Näherung für alpha=0.05"
        )
        return -1.645


def _normal_pdf(x: float) -> float:
    """
    Dichtefunktion der Standardnormalverteilung.

    Args:
        x: Wert

    Returns:
        phi(x) = (1/sqrt(2*pi)) * exp(-x^2/2)
    """
    return (1 / np.sqrt(2 * np.pi)) * np.exp(-0.5 * x**2)
