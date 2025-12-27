"""
Covariance Estimation for Portfolio Risk
=========================================

Verschiedene Schätzer für Kovarianzmatrizen:
- SAMPLE: Standard-Stichprobenkovarianz
- LEDOIT_WOLF: Ledoit-Wolf Shrinkage (requires sklearn)
- DIAGONAL_SHRINK: Simple diagonal shrinkage ohne sklearn
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Optional sklearn import
try:
    from sklearn.covariance import LedoitWolf

    SKLEARN_AVAILABLE = True
except ImportError:
    LedoitWolf = None
    SKLEARN_AVAILABLE = False
    logger.debug("sklearn not available. Ledoit-Wolf covariance estimation disabled.")


class CovarianceMethod(str, Enum):
    """Methoden für Kovarianzschätzung."""

    SAMPLE = "sample"
    LEDOIT_WOLF = "ledoit_wolf"
    DIAGONAL_SHRINK = "diagonal_shrink"


@dataclass
class CovarianceEstimatorConfig:
    """
    Konfiguration für Kovarianzschätzer.

    Args:
        method: Schätzmethode (sample, ledoit_wolf, diagonal_shrink)
        min_history: Minimale Anzahl von Beobachtungen
        shrinkage_alpha: Shrinkage-Faktor für diagonal_shrink (0=sample, 1=diagonal)
    """

    method: Literal["sample", "ledoit_wolf", "diagonal_shrink"] = "sample"
    min_history: int = 60
    shrinkage_alpha: float = 0.1

    def __post_init__(self):
        if self.min_history < 2:
            raise ValueError("min_history must be at least 2")
        if not (0 <= self.shrinkage_alpha <= 1):
            raise ValueError("shrinkage_alpha must be between 0 and 1")
        if self.method not in ["sample", "ledoit_wolf", "diagonal_shrink"]:
            raise ValueError(
                f"Unknown method: {self.method}. Valid: sample, ledoit_wolf, diagonal_shrink"
            )


class CovarianceEstimator:
    """
    Schätzer für Kovarianzmatrizen mit verschiedenen Methoden.

    Example:
        >>> config = CovarianceEstimatorConfig(method="sample", min_history=60)
        >>> estimator = CovarianceEstimator(config)
        >>> cov = estimator.estimate(returns_df)
    """

    def __init__(self, config: CovarianceEstimatorConfig):
        self.config = config

    def estimate(self, returns_df: pd.DataFrame, validate: bool = True) -> np.ndarray:
        """
        Schätzt die Kovarianzmatrix aus einem Returns DataFrame.

        Args:
            returns_df: DataFrame mit periodischen Returns (Zeilen=Zeit, Spalten=Assets)
            validate: Ob die Matrix auf positive Definitheit geprüft werden soll

        Returns:
            Kovarianzmatrix als np.ndarray (N x N)

        Raises:
            ValueError: Wenn zu wenig Daten, nicht-finite Werte, oder Matrix nicht PD
        """
        clean_returns = returns_df.dropna()

        if len(clean_returns) < self.config.min_history:
            raise ValueError(
                f"Insufficient data: {len(clean_returns)} rows, "
                f"but min_history={self.config.min_history}"
            )

        if not np.all(np.isfinite(clean_returns.values)):
            raise ValueError("Returns contain non-finite values (inf/nan)")

        if self.config.method == "sample":
            cov = self._estimate_sample(clean_returns)
        elif self.config.method == "diagonal_shrink":
            cov = self._estimate_diagonal_shrink(clean_returns)
        elif self.config.method == "ledoit_wolf":
            cov = self._estimate_ledoit_wolf(clean_returns)
        else:
            raise ValueError(f"Unknown method: {self.config.method}")

        if validate:
            self._validate_positive_definite(cov)

        return cov

    def estimate_correlation(self, returns_df: pd.DataFrame) -> np.ndarray:
        """
        Schätzt die Korrelationsmatrix aus einem Returns DataFrame.

        Args:
            returns_df: DataFrame mit periodischen Returns

        Returns:
            Korrelationsmatrix als np.ndarray (N x N)
        """
        cov = self.estimate(returns_df, validate=True)
        std = np.sqrt(np.diag(cov))
        # Avoid division by zero
        std[std == 0] = 1.0
        corr = cov / np.outer(std, std)
        np.fill_diagonal(corr, 1.0)
        return corr

    def _estimate_sample(self, returns_df: pd.DataFrame) -> np.ndarray:
        """Standard sample covariance (ddof=1)."""
        return returns_df.cov(ddof=1).values

    def _estimate_diagonal_shrink(self, returns_df: pd.DataFrame) -> np.ndarray:
        """
        Diagonal shrinkage: cov_shrunk = (1-α)*cov_sample + α*diag(cov_sample)
        """
        cov_sample = self._estimate_sample(returns_df)
        cov_diag = np.diag(np.diag(cov_sample))
        alpha = self.config.shrinkage_alpha
        cov_shrunk = (1 - alpha) * cov_sample + alpha * cov_diag
        return cov_shrunk

    def _estimate_ledoit_wolf(self, returns_df: pd.DataFrame) -> np.ndarray:
        """
        Ledoit-Wolf shrinkage estimator (requires sklearn).
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError(
                "Ledoit-Wolf covariance estimation requires scikit-learn. "
                "Install with: pip install -e '.[risk]' or pip install scikit-learn"
            )

        lw = LedoitWolf()
        cov, _ = lw.fit(returns_df.values).covariance_, lw.shrinkage_
        return cov

    def _validate_positive_definite(self, cov: np.ndarray) -> None:
        """
        Prüft, ob die Kovarianzmatrix positiv definit ist (via Cholesky).

        Raises:
            ValueError: Wenn Matrix nicht positiv definit
        """
        try:
            np.linalg.cholesky(cov)
        except np.linalg.LinAlgError as e:
            raise ValueError(
                f"Covariance matrix is not positive definite. "
                f"This can happen with insufficient data, perfect collinearity, "
                f"or numerical issues. Try increasing min_history or using "
                f"diagonal_shrink method. Original error: {e}"
            ) from e


def build_covariance_estimator_from_config(
    cfg: dict,
) -> CovarianceEstimator:
    """
    Erstellt einen CovarianceEstimator aus einer Config-Dict.

    Args:
        cfg: Dict mit Keys: method, min_history, shrinkage_alpha

    Returns:
        CovarianceEstimator instance
    """
    method = cfg.get("method", "sample")
    min_history = cfg.get("min_history", 60)
    shrinkage_alpha = cfg.get("shrinkage_alpha", 0.1)

    config = CovarianceEstimatorConfig(
        method=method,
        min_history=min_history,
        shrinkage_alpha=shrinkage_alpha,
    )
    return CovarianceEstimator(config)
