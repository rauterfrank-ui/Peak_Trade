"""
Component VaR (CompVaR) - Parametric Attribution
=================================================

Zerlegung von Portfolio VaR in Asset-Beiträge via Euler Allocation.

WICHTIG: "CompVaR" oder "Component VaR" - NICHT "CVaR" (reserved für Conditional VaR/ES).

Formeln:
--------
Total VaR = z_α * σ_p * sqrt(H) * V

Marginal VaR (i) = (∂VaR/∂w_i) = z_α * (Σ @ w)_i / σ_p * sqrt(H) * V

Component VaR (i) = w_i * Marginal VaR (i)

Euler Property: Σ Component VaR (i) = Total VaR
"""

import logging
from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Union

import numpy as np
import pandas as pd

from .covariance import CovarianceEstimator
from .parametric_var import ParametricVaR, portfolio_sigma_from_cov, z_score

logger = logging.getLogger(__name__)


@dataclass
class ComponentVaRResult:
    """
    Ergebnis einer Component VaR Berechnung.

    Attributes:
        total_var: Gesamt-Portfolio VaR (absolut)
        marginal_var: Marginal VaR pro Asset (absolut)
        component_var: Component VaR pro Asset (absolut)
        contribution_pct: Prozentualer Beitrag jedes Assets zum Total VaR
        weights: Gewichte der Assets (normalisiert)
        asset_names: Namen der Assets (in derselben Reihenfolge)
    """

    total_var: float
    marginal_var: np.ndarray
    component_var: np.ndarray
    contribution_pct: np.ndarray
    weights: np.ndarray
    asset_names: list[str]

    def to_dataframe(self) -> pd.DataFrame:
        """
        Konvertiert das Ergebnis in ein pandas DataFrame.

        Returns:
            DataFrame mit Spalten: asset, weight, marginal_var, component_var, contribution_pct
        """
        return pd.DataFrame(
            {
                "asset": self.asset_names,
                "weight": self.weights,
                "marginal_var": self.marginal_var,
                "component_var": self.component_var,
                "contribution_pct": self.contribution_pct,
            }
        )

    def __str__(self) -> str:
        df = self.to_dataframe()
        return (
            f"Component VaR Analysis\n"
            f"======================\n"
            f"Total VaR: {self.total_var:.2f}\n\n"
            f"{df.to_string(index=False)}\n\n"
            f"Euler Check: sum(component_var) = {self.component_var.sum():.6f} "
            f"(should equal {self.total_var:.6f})"
        )


class ComponentVaRCalculator:
    """
    Calculator für Component VaR (parametric) mit Euler Validation.

    Example:
        >>> from src.risk.covariance import CovarianceEstimator, CovarianceEstimatorConfig
        >>> from src.risk.parametric_var import ParametricVaR, ParametricVaRConfig
        >>>
        >>> cov_config = CovarianceEstimatorConfig(method="sample", min_history=60)
        >>> cov_estimator = CovarianceEstimator(cov_config)
        >>>
        >>> var_config = ParametricVaRConfig(confidence_level=0.95, horizon_days=1)
        >>> var_engine = ParametricVaR(var_config)
        >>>
        >>> calculator = ComponentVaRCalculator(cov_estimator, var_engine)
        >>> result = calculator.calculate(returns_df, weights_dict, portfolio_value)
        >>> print(result)
    """

    def __init__(
        self,
        cov_estimator: CovarianceEstimator,
        var_engine: ParametricVaR,
    ):
        self.cov_estimator = cov_estimator
        self.var_engine = var_engine

    def calculate(
        self,
        returns_df: pd.DataFrame,
        weights: Union[Mapping[str, float], np.ndarray],
        portfolio_value: float,
        validate_euler: bool = True,
        euler_rtol: float = 1e-6,
    ) -> ComponentVaRResult:
        """
        Berechnet Component VaR für ein Portfolio.

        Args:
            returns_df: DataFrame mit periodischen Returns (Zeilen=Zeit, Spalten=Assets)
            weights: Gewichte als Dict (asset -> weight) oder np.ndarray
            portfolio_value: Portfolio-Wert (z.B. 100000 EUR)
            validate_euler: Ob Euler-Property validiert werden soll
            euler_rtol: Relative Toleranz für Euler-Check

        Returns:
            ComponentVaRResult mit allen Metriken

        Raises:
            ValueError: Wenn Gewichte nicht sum=1, sigma=0, oder Euler-Check fehlschlägt
        """
        # 1) Align weights to returns columns
        asset_names = list(returns_df.columns)
        w = self._align_weights(weights, asset_names)

        # 2) Estimate covariance
        cov = self.cov_estimator.estimate(returns_df, validate=True)

        # 3) Calculate portfolio sigma
        sigma = portfolio_sigma_from_cov(cov, w)

        if sigma == 0:
            raise ValueError(
                "Portfolio sigma is zero. Cannot compute Component VaR. "
                "This typically means all assets have zero variance."
            )

        # 4) Calculate Total VaR (using same cov as component calculation)
        z = z_score(self.var_engine.config.confidence_level)
        horizon_scale = np.sqrt(self.var_engine.config.horizon_days)
        total_var = z * sigma * horizon_scale * portfolio_value

        # 5) Calculate Marginal VaR
        # Marginal VaR (i) = z * (Σ @ w)_i / σ_p * sqrt(H) * V
        cov_with_portfolio = cov @ w  # (N,)
        marginal_var_abs = (z * cov_with_portfolio / sigma) * horizon_scale * portfolio_value

        # 6) Calculate Component VaR
        # Component VaR (i) = w_i * Marginal VaR (i)
        component_var_abs = w * marginal_var_abs

        # 7) Calculate Contribution %
        if total_var > 0:
            contribution_pct = (component_var_abs / total_var) * 100.0
        else:
            contribution_pct = np.zeros_like(component_var_abs)

        # 8) Euler Validation
        if validate_euler:
            sum_components = np.sum(component_var_abs)
            if not np.isclose(sum_components, total_var, rtol=euler_rtol):
                raise ValueError(
                    f"Euler property violated: sum(component_var) = {sum_components:.6f}, "
                    f"but total_var = {total_var:.6f}. "
                    f"Relative error: {abs(sum_components - total_var) / total_var:.2e}. "
                    f"This should not happen for parametric VaR from covariance. "
                    f"Check for numerical issues or inconsistent inputs."
                )

        return ComponentVaRResult(
            total_var=float(total_var),
            marginal_var=marginal_var_abs,
            component_var=component_var_abs,
            contribution_pct=contribution_pct,
            weights=w,
            asset_names=asset_names,
        )

    def _align_weights(
        self,
        weights: Union[Mapping[str, float], np.ndarray],
        asset_names: list[str],
    ) -> np.ndarray:
        """
        Richtet Gewichte an Asset-Namen aus und validiert.

        Args:
            weights: Gewichte als Dict oder np.ndarray
            asset_names: Liste der Asset-Namen (Spalten von returns_df)

        Returns:
            Gewichtsvektor als np.ndarray (N,)

        Raises:
            ValueError: Wenn Gewichte nicht sum≈1 oder fehlende Assets
        """
        if isinstance(weights, Mapping):
            w = np.zeros(len(asset_names))
            missing = []
            for i, asset in enumerate(asset_names):
                if asset in weights:
                    w[i] = weights[asset]
                else:
                    missing.append(asset)

            if missing:
                raise ValueError(
                    f"Missing weights for assets: {', '.join(missing)}. "
                    f"Provided weights: {list(weights.keys())}, "
                    f"Required assets: {asset_names}"
                )
        elif isinstance(weights, np.ndarray):
            if len(weights) != len(asset_names):
                raise ValueError(
                    f"Length of weights array ({len(weights)}) must match "
                    f"number of assets ({len(asset_names)})"
                )
            w = weights
        else:
            raise TypeError("weights must be a Mapping[str, float] or np.ndarray")

        # Validate sum ≈ 1
        weight_sum = np.sum(w)
        if not np.isclose(weight_sum, 1.0, atol=1e-6):
            raise ValueError(f"Weights must sum to approximately 1.0, but got {weight_sum:.6f}")

        return w


def build_component_var_calculator_from_config(
    cfg: dict,
) -> ComponentVaRCalculator:
    """
    Erstellt einen ComponentVaRCalculator aus einer Config-Dict.

    Args:
        cfg: Dict mit nested Sections:
             - covariance: {method, min_history, shrinkage_alpha}
             - var: {confidence_level, horizon_days}

    Returns:
        ComponentVaRCalculator instance
    """
    from .covariance import build_covariance_estimator_from_config
    from .parametric_var import build_parametric_var_from_config

    cov_cfg = cfg.get("covariance", {})
    var_cfg = cfg.get("var", {})

    cov_estimator = build_covariance_estimator_from_config(cov_cfg)
    var_engine = build_parametric_var_from_config(var_cfg)

    return ComponentVaRCalculator(cov_estimator, var_engine)
