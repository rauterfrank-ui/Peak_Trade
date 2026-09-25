"""
Monte Carlo VaR Calculator
===========================

Provides Monte Carlo simulation-based VaR/CVaR calculations.

Agent A4 Implementation: Full Monte Carlo VaR with equity path simulation.

Methods:
--------
- Bootstrap: Resampling from historical returns
- Normal: Assume normal distribution + draw from MVN
- Student-t: Student-t distributed shocks with correlation

Features:
---------
- Deterministic RNG (numpy default_rng with seed)
- Equity path simulation over horizon_days
- Correlation stress testing (increase correlations, ensure PSD)
- Percentile analysis

References:
-----------
- Jorion, P. (2007). Value at Risk (3rd ed.). McGraw-Hill.
- Glasserman, P. (2003). Monte Carlo Methods in Financial Engineering. Springer.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Epsilon for numerical stability
EPS = 1e-12


class MonteCarloMethod(str, Enum):
    """Monte Carlo simulation method."""

    BOOTSTRAP = "bootstrap"
    NORMAL = "normal"
    STUDENT_T = "student_t"


class CopulaType(str, Enum):
    """Copula type for dependence modeling."""

    GAUSSIAN = "gaussian"
    T = "t"


@dataclass
class MonteCarloVaRConfig:
    """
    Configuration for Monte Carlo VaR.

    Attributes:
        n_simulations: Number of Monte Carlo paths (default: 10000)
        method: Simulation method (bootstrap, normal, student_t)
        confidence_level: VaR confidence level (default: 0.95 = 95% VaR)
        horizon_days: Risk horizon in days (default: 1)
        seed: Random seed for reproducibility (default: 42)
        student_t_df: Degrees of freedom for student-t (default: 5)
        correlation_stress_multiplier: Multiplier for correlation stress (default: 1.0 = no stress)
    """

    n_simulations: int = 10000
    method: MonteCarloMethod = MonteCarloMethod.BOOTSTRAP
    confidence_level: float = 0.95
    horizon_days: int = 1
    seed: int = 42
    student_t_df: int = 5
    correlation_stress_multiplier: float = 1.0

    def __post_init__(self):
        """Validate configuration."""
        if self.n_simulations <= 0:
            raise ValueError(f"n_simulations must be > 0, got {self.n_simulations}")
        if not 0 < self.confidence_level < 1:
            raise ValueError(f"confidence_level must be in (0, 1), got {self.confidence_level}")
        if self.horizon_days <= 0:
            raise ValueError(f"horizon_days must be > 0, got {self.horizon_days}")
        if self.student_t_df <= 0:
            raise ValueError(f"student_t_df must be > 0, got {self.student_t_df}")


@dataclass
class MonteCarloVaRResult:
    """
    Result of Monte Carlo VaR calculation.

    Attributes:
        var: Value at Risk (absolute, in currency units)
        cvar: Conditional VaR / Expected Shortfall (absolute)
        simulated_returns: Simulated portfolio returns (n_simulations,)
        percentile_index: Index of VaR percentile in sorted returns
        percentiles: Dictionary of common percentiles (1%, 5%, 50%, 95%, 99%)
        simulation_metadata: Additional metadata (method, seed, etc.)
    """

    var: float
    cvar: float
    simulated_returns: np.ndarray
    percentile_index: int
    percentiles: Dict[str, float] = field(default_factory=dict)
    simulation_metadata: Dict[str, any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"<MonteCarloVaRResult("
            f"VaR={self.var:,.2f}, "
            f"CVaR={self.cvar:,.2f}, "
            f"n_sims={len(self.simulated_returns)})>"
        )


@dataclass
class EquityPathResult:
    """
    Result of equity path simulation.

    Attributes:
        paths: Simulated equity paths (n_simulations, horizon_days+1)
        final_values: Final equity values at horizon (n_simulations,)
        returns: Returns over horizon (n_simulations,)
        initial_value: Initial portfolio value
        horizon_days: Simulation horizon in days
    """

    paths: np.ndarray
    final_values: np.ndarray
    returns: np.ndarray
    initial_value: float
    horizon_days: int


class MonteCarloVaRCalculator:
    """
    Monte Carlo VaR Calculator.

    Agent A4 Implementation: Full Monte Carlo VaR with multiple distributions.

    Usage:
    ------
    >>> config = MonteCarloVaRConfig(n_simulations=10000, method="normal", seed=42)
    >>> calc = MonteCarloVaRCalculator(returns_df, config)
    >>> result = calc.calculate(weights={"BTC-EUR": 0.6, "ETH-EUR": 0.4}, portfolio_value=100000)
    >>> print(f"MC VaR: {result.var:,.2f}")
    """

    def __init__(self, returns: pd.DataFrame, config: MonteCarloVaRConfig):
        """
        Initialize Monte Carlo VaR Calculator.

        Args:
            returns: Historical returns DataFrame (assets as columns)
            config: Monte Carlo configuration

        Raises:
            ValueError: If returns contain NaNs or have insufficient data
        """
        self.returns = returns.copy()
        self.config = config
        self._rng = np.random.default_rng(config.seed)

        # Validate returns
        if self.returns.isnull().any().any():
            logger.warning("Returns contain NaNs. Dropping NaN rows.")
            self.returns = self.returns.dropna()

        if len(self.returns) < 2:
            raise ValueError(
                f"Need at least 2 observations for MC simulation, got {len(self.returns)}"
            )

        # Pre-compute statistics
        self._mean = self.returns.mean().values
        self._std = self.returns.std().values
        self._cov = self.returns.cov().values
        self._corr = self.returns.corr().values

        # Apply correlation stress if needed
        if abs(config.correlation_stress_multiplier - 1.0) > EPS:
            self._apply_correlation_stress()

        logger.info(
            f"MonteCarloVaRCalculator initialized: "
            f"method={config.method.value}, n_sims={config.n_simulations}, "
            f"assets={len(self.returns.columns)}, obs={len(self.returns)}"
        )

    def _apply_correlation_stress(self):
        """Apply correlation stress: increase correlations, ensure PSD."""
        multiplier = self.config.correlation_stress_multiplier
        n = len(self._corr)

        # Stress correlations (keep diagonal = 1)
        stressed_corr = self._corr.copy()
        for i in range(n):
            for j in range(n):
                if i != j:
                    stressed_corr[i, j] = np.clip(self._corr[i, j] * multiplier, -1.0, 1.0)

        # Ensure PSD by adding jitter to diagonal if needed
        stressed_corr = self._ensure_psd(stressed_corr)

        # Convert back to covariance
        std_matrix = np.outer(self._std, self._std)
        self._cov = stressed_corr * std_matrix
        self._corr = stressed_corr

        logger.info(
            f"Applied correlation stress: multiplier={multiplier:.2f}, "
            f"avg_corr={np.mean(stressed_corr[np.triu_indices_from(stressed_corr, k=1)]):.4f}"
        )

    def _ensure_psd(self, corr: np.ndarray, max_iterations: int = 10) -> np.ndarray:
        """
        Ensure correlation matrix is positive semi-definite.

        Args:
            corr: Correlation matrix
            max_iterations: Maximum iterations for fixing

        Returns:
            PSD correlation matrix
        """
        for iteration in range(max_iterations):
            try:
                # Try Cholesky decomposition
                np.linalg.cholesky(corr)
                return corr  # Success!
            except np.linalg.LinAlgError:
                # Not PSD, add small jitter to diagonal
                jitter = 1e-6 * (2**iteration)  # Exponential increase
                corr_fixed = corr.copy()
                np.fill_diagonal(corr_fixed, 1.0 + jitter)
                corr = corr_fixed

        # If still failing, use eigenvalue clipping
        eigenvalues, eigenvectors = np.linalg.eigh(corr)
        eigenvalues = np.maximum(eigenvalues, 1e-8)  # Clip to positive
        corr = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T

        # Re-normalize to correlation matrix
        d = np.sqrt(np.diag(corr))
        corr = corr / np.outer(d, d)
        np.fill_diagonal(corr, 1.0)

        return corr

    def calculate(
        self,
        weights: Dict[str, float],
        portfolio_value: float,
        alpha: Optional[float] = None,
    ) -> MonteCarloVaRResult:
        """
        Calculate Monte Carlo VaR/CVaR.

        Args:
            weights: Asset weights (must sum to 1.0)
            portfolio_value: Portfolio value (in currency units)
            alpha: VaR significance level (default: 1 - config.confidence_level)

        Returns:
            MonteCarloVaRResult with VaR, CVaR, and simulated returns

        Raises:
            ValueError: If weights don't match returns columns or don't sum to ~1
        """
        # Validate weights
        if set(weights.keys()) != set(self.returns.columns):
            raise ValueError(
                f"Weight keys {set(weights.keys())} don't match returns columns {set(self.returns.columns)}"
            )

        weights_sum = sum(weights.values())
        if abs(weights_sum - 1.0) > 1e-3:
            raise ValueError(
                f"Weights must sum to 1.0, got {weights_sum:.6f}. Difference: {abs(weights_sum - 1.0):.6f}"
            )

        # Convert weights to numpy array (aligned with returns columns)
        weights_array = np.array([weights[col] for col in self.returns.columns])

        # Determine alpha
        if alpha is None:
            alpha = 1.0 - self.config.confidence_level

        # Simulate returns
        if self.config.method == MonteCarloMethod.BOOTSTRAP:
            simulated_returns = self._simulate_bootstrap(weights_array, self.config.n_simulations)
        elif self.config.method == MonteCarloMethod.NORMAL:
            simulated_returns = self._simulate_normal(weights_array, self.config.n_simulations)
        elif self.config.method == MonteCarloMethod.STUDENT_T:
            simulated_returns = self._simulate_student_t(weights_array, self.config.n_simulations)
        else:
            raise ValueError(f"Unknown method: {self.config.method}")

        # Adjust for horizon (scaling by sqrt(horizon))
        if self.config.horizon_days > 1:
            simulated_returns = simulated_returns * np.sqrt(self.config.horizon_days)

        # Calculate VaR (as positive loss)
        losses = -simulated_returns  # Convert returns to losses
        sorted_losses = np.sort(losses)
        percentile_index = int(np.ceil(len(sorted_losses) * (1 - alpha))) - 1
        percentile_index = max(0, min(percentile_index, len(sorted_losses) - 1))
        var_loss = sorted_losses[percentile_index]
        var = var_loss * portfolio_value

        # Calculate CVaR (Expected Shortfall)
        tail_losses = sorted_losses[percentile_index:]
        cvar_loss = np.mean(tail_losses)
        cvar = cvar_loss * portfolio_value

        # Calculate common percentiles (as returns, not losses)
        percentiles = {
            "p01": float(np.percentile(simulated_returns, 1)),
            "p05": float(np.percentile(simulated_returns, 5)),
            "p50": float(np.percentile(simulated_returns, 50)),
            "p95": float(np.percentile(simulated_returns, 95)),
            "p99": float(np.percentile(simulated_returns, 99)),
        }

        # Metadata
        metadata = {
            "method": self.config.method.value,
            "n_simulations": self.config.n_simulations,
            "horizon_days": self.config.horizon_days,
            "seed": self.config.seed,
            "alpha": alpha,
            "confidence_level": self.config.confidence_level,
        }

        return MonteCarloVaRResult(
            var=var,
            cvar=cvar,
            simulated_returns=simulated_returns,
            percentile_index=percentile_index,
            percentiles=percentiles,
            simulation_metadata=metadata,
        )

    def simulate_equity_paths(
        self, weights: Dict[str, float], initial_value: float
    ) -> EquityPathResult:
        """
        Simulate equity paths over horizon_days.

        Args:
            weights: Asset weights (must sum to 1.0)
            initial_value: Initial portfolio value

        Returns:
            EquityPathResult with paths, final values, and returns

        Example:
            >>> result = calc.simulate_equity_paths(weights={"BTC": 0.5, "ETH": 0.5}, initial_value=100000)
            >>> result.paths.shape  # (n_simulations, horizon_days+1)
            >>> result.final_values.shape  # (n_simulations,)
        """
        # Validate weights
        if set(weights.keys()) != set(self.returns.columns):
            raise ValueError("Weight keys don't match returns columns")

        weights_array = np.array([weights[col] for col in self.returns.columns])

        n_sims = self.config.n_simulations
        horizon = self.config.horizon_days

        # Initialize paths: (n_sims, horizon+1)
        paths = np.zeros((n_sims, horizon + 1))
        paths[:, 0] = initial_value

        # Simulate daily returns
        for t in range(1, horizon + 1):
            # Generate daily portfolio returns
            if self.config.method == MonteCarloMethod.BOOTSTRAP:
                daily_returns = self._simulate_bootstrap(weights_array, n_sims)
            elif self.config.method == MonteCarloMethod.NORMAL:
                daily_returns = self._simulate_normal(weights_array, n_sims)
            elif self.config.method == MonteCarloMethod.STUDENT_T:
                daily_returns = self._simulate_student_t(weights_array, n_sims)
            else:
                raise ValueError(f"Unknown method: {self.config.method}")

            # Update paths
            paths[:, t] = paths[:, t - 1] * (1 + daily_returns)

        # Calculate final values and returns
        final_values = paths[:, -1]
        returns = (final_values - initial_value) / initial_value

        return EquityPathResult(
            paths=paths,
            final_values=final_values,
            returns=returns,
            initial_value=initial_value,
            horizon_days=horizon,
        )

    def _simulate_bootstrap(self, weights: np.ndarray, n_sims: int) -> np.ndarray:
        """
        Bootstrap resampling method.

        Args:
            weights: Asset weights (numpy array)
            n_sims: Number of simulations

        Returns:
            Simulated portfolio returns (n_sims,)
        """
        # Sample rows (with replacement) from historical returns
        n_obs = len(self.returns)
        sample_indices = self._rng.integers(0, n_obs, size=n_sims)

        # Get sampled returns
        sampled_asset_returns = self.returns.values[sample_indices]  # (n_sims, n_assets)

        # Compute portfolio returns
        portfolio_returns = sampled_asset_returns @ weights

        return portfolio_returns

    def _simulate_normal(self, weights: np.ndarray, n_sims: int) -> np.ndarray:
        """
        Normal (MVN) simulation.

        Args:
            weights: Asset weights (numpy array)
            n_sims: Number of simulations

        Returns:
            Simulated portfolio returns (n_sims,)
        """
        # Sample from multivariate normal
        asset_returns = self._rng.multivariate_normal(
            mean=self._mean, cov=self._cov, size=n_sims
        )  # (n_sims, n_assets)

        # Compute portfolio returns
        portfolio_returns = asset_returns @ weights

        return portfolio_returns

    def _simulate_student_t(self, weights: np.ndarray, n_sims: int) -> np.ndarray:
        """
        Student-t simulation with correlation.

        Args:
            weights: Asset weights (numpy array)
            n_sims: Number of simulations

        Returns:
            Simulated portfolio returns (n_sims,)
        """
        n_assets = len(weights)
        df = self.config.student_t_df

        # Generate standard t shocks
        t_shocks = self._rng.standard_t(df, size=(n_sims, n_assets))

        # Apply correlation via Cholesky
        try:
            L = np.linalg.cholesky(self._corr)
        except np.linalg.LinAlgError:
            # Fallback: use eigenvalue decomposition
            eigenvalues, eigenvectors = np.linalg.eigh(self._corr)
            eigenvalues = np.maximum(eigenvalues, 1e-8)
            L = eigenvectors @ np.diag(np.sqrt(eigenvalues))

        correlated_shocks = t_shocks @ L.T  # (n_sims, n_assets)

        # Scale by standard deviations
        asset_returns = self._mean + correlated_shocks * self._std

        # Compute portfolio returns
        portfolio_returns = asset_returns @ weights

        return portfolio_returns

    def __repr__(self) -> str:
        return (
            f"<MonteCarloVaRCalculator("
            f"method={self.config.method.value}, "
            f"n_sims={self.config.n_simulations}, "
            f"assets={len(self.returns.columns)})>"
        )


def build_monte_carlo_var_from_config(
    returns: pd.DataFrame, cfg: any, section: str = "risk.monte_carlo"
) -> Optional[MonteCarloVaRCalculator]:
    """
    Factory function to build MonteCarloVaRCalculator from config.

    Args:
        returns: Historical returns DataFrame
        cfg: Config object (PeakConfig or dict)
        section: Config section for Monte Carlo VaR

    Returns:
        MonteCarloVaRCalculator if enabled, else None

    Example Config (config.toml):
    ------------------------------
    [risk.monte_carlo]
    enabled = true
    n_simulations = 10000
    method = "normal"
    confidence_level = 0.95
    horizon_days = 1
    seed = 42
    student_t_df = 5
    correlation_stress_multiplier = 1.0
    """
    # Config accessor
    if hasattr(cfg, "get"):
        get_fn = cfg.get
    elif isinstance(cfg, dict):

        def get_fn(path, default=None):
            keys = path.split(".")
            node = cfg
            for key in keys:
                if isinstance(node, dict) and key in node:
                    node = node[key]
                else:
                    return default
            return node

    else:
        raise TypeError(f"Unsupported config type: {type(cfg)}")

    # Check if Monte Carlo VaR is enabled
    enabled = bool(get_fn(f"{section}.enabled", False))
    if not enabled:
        logger.info("Monte Carlo VaR disabled in config")
        return None

    # Load config parameters
    n_sims = int(get_fn(f"{section}.n_simulations", 10000))
    method_str = str(get_fn(f"{section}.method", "bootstrap")).lower()
    confidence = float(get_fn(f"{section}.confidence_level", 0.95))
    horizon = int(get_fn(f"{section}.horizon_days", 1))
    seed = int(get_fn(f"{section}.seed", 42))
    student_t_df = int(get_fn(f"{section}.student_t_df", 5))
    correlation_stress = float(get_fn(f"{section}.correlation_stress_multiplier", 1.0))

    # Parse method enum
    try:
        method = MonteCarloMethod(method_str)
    except ValueError:
        logger.warning(f"Invalid MC method '{method_str}', defaulting to bootstrap")
        method = MonteCarloMethod.BOOTSTRAP

    # Build config
    mc_config = MonteCarloVaRConfig(
        n_simulations=n_sims,
        method=method,
        confidence_level=confidence,
        horizon_days=horizon,
        seed=seed,
        student_t_df=student_t_df,
        correlation_stress_multiplier=correlation_stress,
    )

    # Build calculator
    calculator = MonteCarloVaRCalculator(returns, mc_config)
    logger.info(f"Built Monte Carlo VaR Calculator: {mc_config}")

    return calculator
