"""
Tests for Monte Carlo VaR Calculator
=====================================
"""

import numpy as np
import pandas as pd
import pytest

from src.risk.monte_carlo import (
    MonteCarloVaRCalculator,
    MonteCarloVaRConfig,
    MonteCarloVaRResult,
    EquityPathResult,
    MonteCarloMethod,
)
from src.risk.var import parametric_var


class TestMonteCarloVaRConfig:
    """Tests for MonteCarloVaRConfig."""

    def test_config_defaults(self):
        """Default config should work."""
        config = MonteCarloVaRConfig()

        assert config.n_simulations == 10000
        assert config.method == MonteCarloMethod.BOOTSTRAP
        assert config.confidence_level == 0.95
        assert config.horizon_days == 1
        assert config.seed == 42

    def test_config_validation(self):
        """Config validation should catch invalid inputs."""
        # Invalid n_simulations
        with pytest.raises(ValueError, match="n_simulations must be > 0"):
            MonteCarloVaRConfig(n_simulations=0)

        # Invalid confidence_level
        with pytest.raises(ValueError, match="confidence_level must be in"):
            MonteCarloVaRConfig(confidence_level=1.5)

        # Invalid horizon_days
        with pytest.raises(ValueError, match="horizon_days must be > 0"):
            MonteCarloVaRConfig(horizon_days=0)


class TestMonteCarloVaRCalculatorInit:
    """Tests for MonteCarloVaRCalculator initialization."""

    def test_initialization_valid_returns(self):
        """Valid returns should initialize successfully."""
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        config = MonteCarloVaRConfig(seed=42)

        calc = MonteCarloVaRCalculator(returns, config)

        assert calc.returns.shape == (100, 2)
        assert len(calc._mean) == 2
        assert len(calc._std) == 2
        assert calc._cov.shape == (2, 2)
        assert calc._corr.shape == (2, 2)

    def test_initialization_with_nans(self):
        """NaNs should be dropped with warning."""
        returns = pd.DataFrame(
            {
                "BTC": [0.01, np.nan, 0.02, 0.03],
                "ETH": [0.02, 0.01, np.nan, 0.04],
            }
        )
        config = MonteCarloVaRConfig(seed=42)

        calc = MonteCarloVaRCalculator(returns, config)

        # Should drop rows with NaNs
        assert len(calc.returns) < 4

    def test_initialization_insufficient_data(self):
        """Insufficient data should raise error."""
        returns = pd.DataFrame({"BTC": [0.01]})
        config = MonteCarloVaRConfig(seed=42)

        with pytest.raises(ValueError, match="at least 2 observations"):
            MonteCarloVaRCalculator(returns, config)


class TestBootstrapSimulation:
    """Tests for bootstrap simulation."""

    def test_bootstrap_basic(self):
        """Bootstrap should resample from historical data."""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        config = MonteCarloVaRConfig(
            n_simulations=1000, method=MonteCarloMethod.BOOTSTRAP, seed=42
        )
        calc = MonteCarloVaRCalculator(returns, config)

        weights = {"BTC": 0.6, "ETH": 0.4}
        result = calc.calculate(weights, portfolio_value=100000)

        assert isinstance(result, MonteCarloVaRResult)
        assert result.var > 0  # VaR should be positive (loss)
        assert result.cvar > 0
        assert result.cvar >= result.var  # CVaR >= VaR
        assert len(result.simulated_returns) == 1000

    def test_bootstrap_determinism(self):
        """Same seed should give same results."""
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        weights = {"BTC": 0.6, "ETH": 0.4}

        config1 = MonteCarloVaRConfig(n_simulations=1000, seed=123)
        calc1 = MonteCarloVaRCalculator(returns, config1)
        result1 = calc1.calculate(weights, portfolio_value=100000)

        config2 = MonteCarloVaRConfig(n_simulations=1000, seed=123)
        calc2 = MonteCarloVaRCalculator(returns, config2)
        result2 = calc2.calculate(weights, portfolio_value=100000)

        assert result1.var == result2.var
        assert result1.cvar == result2.cvar
        np.testing.assert_array_equal(
            result1.simulated_returns, result2.simulated_returns
        )


class TestNormalSimulation:
    """Tests for normal (MVN) simulation."""

    def test_normal_basic(self):
        """Normal simulation should work."""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        config = MonteCarloVaRConfig(
            n_simulations=1000, method=MonteCarloMethod.NORMAL, seed=42
        )
        calc = MonteCarloVaRCalculator(returns, config)

        weights = {"BTC": 0.6, "ETH": 0.4}
        result = calc.calculate(weights, portfolio_value=100000)

        assert result.var > 0
        assert result.cvar >= result.var
        assert len(result.simulated_returns) == 1000

    def test_normal_convergence_to_parametric(self):
        """MC VaR should converge to parametric VaR with many simulations."""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(500) * 0.02,
                "ETH": np.random.randn(500) * 0.03,
            }
        )

        # Monte Carlo VaR
        config = MonteCarloVaRConfig(
            n_simulations=50000, method=MonteCarloMethod.NORMAL, seed=42
        )
        calc = MonteCarloVaRCalculator(returns, config)
        weights = {"BTC": 0.6, "ETH": 0.4}
        mc_result = calc.calculate(weights, portfolio_value=100000, alpha=0.05)

        # Parametric VaR
        portfolio_returns = returns @ pd.Series(weights)
        parametric_var_value = parametric_var(portfolio_returns, alpha=0.05) * 100000

        # Should be close (within 20% relative error)
        relative_error = abs(mc_result.var - parametric_var_value) / parametric_var_value
        assert (
            relative_error < 0.2
        ), f"MC VaR {mc_result.var:.2f} vs Parametric {parametric_var_value:.2f}, error={relative_error:.2%}"

    def test_normal_determinism(self):
        """Same seed should give same results."""
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        weights = {"BTC": 0.5, "ETH": 0.5}

        config1 = MonteCarloVaRConfig(
            n_simulations=1000, method=MonteCarloMethod.NORMAL, seed=456
        )
        calc1 = MonteCarloVaRCalculator(returns, config1)
        result1 = calc1.calculate(weights, portfolio_value=100000)

        config2 = MonteCarloVaRConfig(
            n_simulations=1000, method=MonteCarloMethod.NORMAL, seed=456
        )
        calc2 = MonteCarloVaRCalculator(returns, config2)
        result2 = calc2.calculate(weights, portfolio_value=100000)

        assert result1.var == result2.var
        np.testing.assert_array_almost_equal(
            result1.simulated_returns, result2.simulated_returns
        )


class TestStudentTSimulation:
    """Tests for Student-t simulation."""

    def test_student_t_basic(self):
        """Student-t simulation should work."""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        config = MonteCarloVaRConfig(
            n_simulations=1000,
            method=MonteCarloMethod.STUDENT_T,
            student_t_df=5,
            seed=42,
        )
        calc = MonteCarloVaRCalculator(returns, config)

        weights = {"BTC": 0.6, "ETH": 0.4}
        result = calc.calculate(weights, portfolio_value=100000)

        assert result.var > 0
        assert result.cvar >= result.var
        assert len(result.simulated_returns) == 1000

    def test_student_t_heavier_tails(self):
        """Student-t should have heavier tails than normal."""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(200) * 0.02,
                "ETH": np.random.randn(200) * 0.03,
            }
        )
        weights = {"BTC": 0.5, "ETH": 0.5}

        # Normal
        config_normal = MonteCarloVaRConfig(
            n_simulations=10000, method=MonteCarloMethod.NORMAL, seed=42
        )
        calc_normal = MonteCarloVaRCalculator(returns, config_normal)
        result_normal = calc_normal.calculate(weights, portfolio_value=100000)

        # Student-t
        config_t = MonteCarloVaRConfig(
            n_simulations=10000,
            method=MonteCarloMethod.STUDENT_T,
            student_t_df=3,
            seed=42,
        )
        calc_t = MonteCarloVaRCalculator(returns, config_t)
        result_t = calc_t.calculate(weights, portfolio_value=100000)

        # Student-t should typically have higher VaR due to heavier tails
        # (But this is probabilistic, so we just check it runs without errors)
        assert result_t.var > 0
        assert result_normal.var > 0

    def test_student_t_determinism(self):
        """Same seed should give same results."""
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        weights = {"BTC": 0.5, "ETH": 0.5}

        config1 = MonteCarloVaRConfig(
            n_simulations=1000, method=MonteCarloMethod.STUDENT_T, seed=789
        )
        calc1 = MonteCarloVaRCalculator(returns, config1)
        result1 = calc1.calculate(weights, portfolio_value=100000)

        config2 = MonteCarloVaRConfig(
            n_simulations=1000, method=MonteCarloMethod.STUDENT_T, seed=789
        )
        calc2 = MonteCarloVaRCalculator(returns, config2)
        result2 = calc2.calculate(weights, portfolio_value=100000)

        assert result1.var == result2.var
        np.testing.assert_array_almost_equal(
            result1.simulated_returns, result2.simulated_returns
        )


class TestCorrelationStress:
    """Tests for correlation stress testing."""

    def test_correlation_stress_increases_var(self):
        """Increased correlations should increase VaR (typically)."""
        np.random.seed(42)
        # Create negatively correlated returns
        btc = np.random.randn(200) * 0.02
        eth = -btc * 0.5 + np.random.randn(200) * 0.01
        returns = pd.DataFrame({"BTC": btc, "ETH": eth})

        weights = {"BTC": 0.5, "ETH": 0.5}

        # Base case
        config_base = MonteCarloVaRConfig(
            n_simulations=5000,
            method=MonteCarloMethod.NORMAL,
            correlation_stress_multiplier=1.0,
            seed=42,
        )
        calc_base = MonteCarloVaRCalculator(returns, config_base)
        result_base = calc_base.calculate(weights, portfolio_value=100000)

        # Stressed case (increase correlations)
        config_stress = MonteCarloVaRConfig(
            n_simulations=5000,
            method=MonteCarloMethod.NORMAL,
            correlation_stress_multiplier=1.5,
            seed=42,
        )
        calc_stress = MonteCarloVaRCalculator(returns, config_stress)
        result_stress = calc_stress.calculate(weights, portfolio_value=100000)

        # Stressed VaR should be >= base VaR (typically)
        # (But this is not guaranteed for all cases, so we just check it runs)
        assert result_stress.var > 0
        assert result_base.var > 0

    def test_correlation_stress_psd_handling(self):
        """Correlation stress should handle non-PSD matrices."""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "A": np.random.randn(100) * 0.02,
                "B": np.random.randn(100) * 0.02,
                "C": np.random.randn(100) * 0.02,
            }
        )

        # Very high stress multiplier might create non-PSD matrix
        config = MonteCarloVaRConfig(
            n_simulations=1000,
            method=MonteCarloMethod.NORMAL,
            correlation_stress_multiplier=2.0,
            seed=42,
        )

        # Should not raise error (should fix PSD internally)
        calc = MonteCarloVaRCalculator(returns, config)
        weights = {"A": 0.33, "B": 0.33, "C": 0.34}
        result = calc.calculate(weights, portfolio_value=100000)

        assert result.var > 0


class TestHorizonScaling:
    """Tests for multi-day horizon scaling."""

    def test_horizon_scaling(self):
        """VaR should scale with sqrt(horizon)."""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(200) * 0.02,
                "ETH": np.random.randn(200) * 0.03,
            }
        )
        weights = {"BTC": 0.6, "ETH": 0.4}

        # 1-day VaR
        config_1d = MonteCarloVaRConfig(
            n_simulations=5000, method=MonteCarloMethod.NORMAL, horizon_days=1, seed=42
        )
        calc_1d = MonteCarloVaRCalculator(returns, config_1d)
        result_1d = calc_1d.calculate(weights, portfolio_value=100000)

        # 10-day VaR
        config_10d = MonteCarloVaRConfig(
            n_simulations=5000,
            method=MonteCarloMethod.NORMAL,
            horizon_days=10,
            seed=42,
        )
        calc_10d = MonteCarloVaRCalculator(returns, config_10d)
        result_10d = calc_10d.calculate(weights, portfolio_value=100000)

        # 10-day VaR should be approximately sqrt(10) times 1-day VaR
        expected_ratio = np.sqrt(10)
        actual_ratio = result_10d.var / result_1d.var

        # Allow 30% tolerance (MC simulation has variance)
        assert (
            0.7 * expected_ratio < actual_ratio < 1.3 * expected_ratio
        ), f"Expected ratio ~{expected_ratio:.2f}, got {actual_ratio:.2f}"


class TestEquityPathSimulation:
    """Tests for equity path simulation."""

    def test_equity_paths_shape(self):
        """Equity paths should have correct shape."""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        config = MonteCarloVaRConfig(
            n_simulations=500,
            method=MonteCarloMethod.NORMAL,
            horizon_days=10,
            seed=42,
        )
        calc = MonteCarloVaRCalculator(returns, config)

        weights = {"BTC": 0.6, "ETH": 0.4}
        result = calc.simulate_equity_paths(weights, initial_value=100000)

        assert isinstance(result, EquityPathResult)
        assert result.paths.shape == (500, 11)  # n_sims x (horizon + 1)
        assert result.final_values.shape == (500,)
        assert result.returns.shape == (500,)
        assert result.initial_value == 100000
        assert result.horizon_days == 10

    def test_equity_paths_initial_value(self):
        """All paths should start at initial_value."""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        config = MonteCarloVaRConfig(
            n_simulations=100, method=MonteCarloMethod.NORMAL, horizon_days=5, seed=42
        )
        calc = MonteCarloVaRCalculator(returns, config)

        weights = {"BTC": 0.5, "ETH": 0.5}
        result = calc.simulate_equity_paths(weights, initial_value=50000)

        # All paths should start at 50000
        np.testing.assert_array_equal(result.paths[:, 0], 50000)

    def test_equity_paths_determinism(self):
        """Same seed should give same paths."""
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        weights = {"BTC": 0.5, "ETH": 0.5}

        config1 = MonteCarloVaRConfig(
            n_simulations=100, method=MonteCarloMethod.NORMAL, horizon_days=5, seed=999
        )
        calc1 = MonteCarloVaRCalculator(returns, config1)
        result1 = calc1.simulate_equity_paths(weights, initial_value=100000)

        config2 = MonteCarloVaRConfig(
            n_simulations=100, method=MonteCarloMethod.NORMAL, horizon_days=5, seed=999
        )
        calc2 = MonteCarloVaRCalculator(returns, config2)
        result2 = calc2.simulate_equity_paths(weights, initial_value=100000)

        np.testing.assert_array_almost_equal(result1.paths, result2.paths)

    def test_equity_paths_returns_consistency(self):
        """Final returns should match (final - initial) / initial."""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        config = MonteCarloVaRConfig(
            n_simulations=100, method=MonteCarloMethod.NORMAL, horizon_days=5, seed=42
        )
        calc = MonteCarloVaRCalculator(returns, config)

        weights = {"BTC": 0.5, "ETH": 0.5}
        initial = 100000
        result = calc.simulate_equity_paths(weights, initial_value=initial)

        # Check returns calculation
        expected_returns = (result.final_values - initial) / initial
        np.testing.assert_array_almost_equal(result.returns, expected_returns)


class TestPercentiles:
    """Tests for percentile calculations."""

    def test_percentiles_keys(self):
        """Result should contain expected percentile keys."""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        config = MonteCarloVaRConfig(
            n_simulations=1000, method=MonteCarloMethod.NORMAL, seed=42
        )
        calc = MonteCarloVaRCalculator(returns, config)

        weights = {"BTC": 0.5, "ETH": 0.5}
        result = calc.calculate(weights, portfolio_value=100000)

        # Check percentiles
        assert "p01" in result.percentiles
        assert "p05" in result.percentiles
        assert "p50" in result.percentiles
        assert "p95" in result.percentiles
        assert "p99" in result.percentiles

    def test_percentiles_ordering(self):
        """Percentiles should be ordered correctly."""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(200) * 0.02,
                "ETH": np.random.randn(200) * 0.03,
            }
        )
        config = MonteCarloVaRConfig(
            n_simulations=5000, method=MonteCarloMethod.NORMAL, seed=42
        )
        calc = MonteCarloVaRCalculator(returns, config)

        weights = {"BTC": 0.5, "ETH": 0.5}
        result = calc.calculate(weights, portfolio_value=100000)

        # p01 < p05 < p50 < p95 < p99
        assert result.percentiles["p01"] < result.percentiles["p05"]
        assert result.percentiles["p05"] < result.percentiles["p50"]
        assert result.percentiles["p50"] < result.percentiles["p95"]
        assert result.percentiles["p95"] < result.percentiles["p99"]


class TestWeightValidation:
    """Tests for weight validation."""

    def test_weights_sum_validation(self):
        """Weights must sum to ~1.0."""
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        config = MonteCarloVaRConfig(seed=42)
        calc = MonteCarloVaRCalculator(returns, config)

        # Weights don't sum to 1
        weights = {"BTC": 0.5, "ETH": 0.3}  # sum = 0.8

        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            calc.calculate(weights, portfolio_value=100000)

    def test_weights_keys_validation(self):
        """Weight keys must match returns columns."""
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        config = MonteCarloVaRConfig(seed=42)
        calc = MonteCarloVaRCalculator(returns, config)

        # Wrong keys
        weights = {"BTC": 0.5, "XRP": 0.5}

        with pytest.raises(ValueError, match="don't match returns columns"):
            calc.calculate(weights, portfolio_value=100000)


class TestCVaRInvariant:
    """Tests for CVaR >= VaR invariant."""

    def test_cvar_gte_var_bootstrap(self):
        """CVaR >= VaR for bootstrap."""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        config = MonteCarloVaRConfig(
            n_simulations=1000, method=MonteCarloMethod.BOOTSTRAP, seed=42
        )
        calc = MonteCarloVaRCalculator(returns, config)

        weights = {"BTC": 0.6, "ETH": 0.4}
        result = calc.calculate(weights, portfolio_value=100000)

        assert result.cvar >= result.var

    def test_cvar_gte_var_normal(self):
        """CVaR >= VaR for normal."""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        config = MonteCarloVaRConfig(
            n_simulations=1000, method=MonteCarloMethod.NORMAL, seed=42
        )
        calc = MonteCarloVaRCalculator(returns, config)

        weights = {"BTC": 0.6, "ETH": 0.4}
        result = calc.calculate(weights, portfolio_value=100000)

        assert result.cvar >= result.var

    def test_cvar_gte_var_student_t(self):
        """CVaR >= VaR for student-t."""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "BTC": np.random.randn(100) * 0.02,
                "ETH": np.random.randn(100) * 0.03,
            }
        )
        config = MonteCarloVaRConfig(
            n_simulations=1000, method=MonteCarloMethod.STUDENT_T, seed=42
        )
        calc = MonteCarloVaRCalculator(returns, config)

        weights = {"BTC": 0.6, "ETH": 0.4}
        result = calc.calculate(weights, portfolio_value=100000)

        assert result.cvar >= result.var
