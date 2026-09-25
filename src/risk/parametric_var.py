"""
Parametric VaR Engine
=====================

Berechnet Parametric VaR aus Kovarianzmatrix und Gewichten.
Verwendet für Component VaR Attribution.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Optional scipy import
try:
    from scipy.stats import norm as scipy_norm

    SCIPY_AVAILABLE = True
except ImportError:
    scipy_norm = None
    SCIPY_AVAILABLE = False
    logger.debug("scipy not available. Using statistics.NormalDist fallback.")

# Fallback for z-score
try:
    from statistics import NormalDist

    NORMALDIST_AVAILABLE = True
except ImportError:
    NormalDist = None
    NORMALDIST_AVAILABLE = False


@dataclass
class ParametricVaRConfig:
    """
    Konfiguration für Parametric VaR Berechnung.

    Args:
        confidence_level: Konfidenzniveau (z.B. 0.95 für 95% VaR)
        horizon_days: Zeithorizont in Tagen
    """

    confidence_level: float = 0.95
    horizon_days: int = 1

    def __post_init__(self):
        if not (0 < self.confidence_level < 1):
            raise ValueError("confidence_level must be between 0 and 1 (exclusive)")
        if self.horizon_days <= 0:
            raise ValueError("horizon_days must be positive")


def z_score(confidence_level: float) -> float:
    """
    Berechnet den z-Wert (inverse CDF) für ein gegebenes Konfidenzniveau.

    Nutzt scipy.stats.norm wenn verfügbar, sonst statistics.NormalDist.

    Args:
        confidence_level: Konfidenzniveau (z.B. 0.95)

    Returns:
        z-Wert (z.B. 1.645 für 95%)

    Raises:
        ImportError: Wenn weder scipy noch statistics.NormalDist verfügbar
    """
    if SCIPY_AVAILABLE:
        return scipy_norm.ppf(confidence_level)
    elif NORMALDIST_AVAILABLE:
        return NormalDist().inv_cdf(confidence_level)
    else:
        raise ImportError(
            "Neither scipy (scipy.stats.norm) nor statistics.NormalDist "
            "are available for z-score calculation. Please install scipy "
            "or use Python 3.8+."
        )


def portfolio_sigma_from_cov(cov: np.ndarray, w: np.ndarray) -> float:
    """
    Berechnet Portfolio-Standardabweichung aus Kovarianzmatrix und Gewichten.

    Formula: σ_p = sqrt(w^T * Σ * w)

    Args:
        cov: Kovarianzmatrix (N x N)
        w: Gewichtsvektor (N,)

    Returns:
        Portfolio-Standardabweichung (scalar)
    """
    return float(np.sqrt(w.T @ cov @ w))


class ParametricVaR:
    """
    Parametric VaR Engine basierend auf Kovarianzmatrix.

    Example:
        >>> config = ParametricVaRConfig(confidence_level=0.95, horizon_days=1)
        >>> var_engine = ParametricVaR(config)
        >>> var_abs = var_engine.calculate_from_cov(cov, weights, portfolio_value)
    """

    def __init__(self, config: ParametricVaRConfig):
        self.config = config

    def calculate_from_cov(
        self,
        cov: np.ndarray,
        weights_array: np.ndarray,
        portfolio_value: float,
    ) -> float:
        """
        Berechnet Parametric VaR aus Kovarianzmatrix.

        Formula: VaR = z_α * σ_p * sqrt(H) * V

        Args:
            cov: Kovarianzmatrix (N x N)
            weights_array: Gewichtsvektor (N,), normalisiert auf sum=1
            portfolio_value: Portfolio-Wert (z.B. 100000 EUR)

        Returns:
            VaR als positive Zahl (absolute Währungseinheiten)

        Raises:
            ValueError: Wenn sigma=0 oder portfolio_value<=0
        """
        if portfolio_value <= 0:
            raise ValueError("portfolio_value must be positive")

        sigma = portfolio_sigma_from_cov(cov, weights_array)

        if sigma == 0:
            raise ValueError(
                "Portfolio sigma is zero. This typically means all assets "
                "have zero variance or weights are zero."
            )

        z = z_score(self.config.confidence_level)
        horizon_scale = np.sqrt(self.config.horizon_days)

        var_value = z * sigma * horizon_scale * portfolio_value

        return float(max(0.0, var_value))


def build_parametric_var_from_config(cfg: dict) -> ParametricVaR:
    """
    Erstellt einen ParametricVaR Engine aus einer Config-Dict.

    Args:
        cfg: Dict mit Keys: confidence_level, horizon_days

    Returns:
        ParametricVaR instance
    """
    confidence_level = cfg.get("confidence_level", 0.95)
    horizon_days = cfg.get("horizon_days", 1)

    config = ParametricVaRConfig(
        confidence_level=confidence_level,
        horizon_days=horizon_days,
    )
    return ParametricVaR(config)
