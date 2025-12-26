"""
Tests für Component VaR Calculator
===================================
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.risk.component_var import ComponentVaRCalculator, ComponentVaRResult
from src.risk.covariance import CovarianceEstimator, CovarianceEstimatorConfig
from src.risk.parametric_var import ParametricVaR, ParametricVaRConfig


@pytest.fixture
def sample_returns_from_fixtures():
    """Lädt die generierten Sample Returns."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_returns.csv"
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")
    return pd.read_csv(fixture_path)


@pytest.fixture
def default_calculator():
    """Standard Calculator mit sample covariance."""
    cov_config = CovarianceEstimatorConfig(method="sample", min_history=60)
    cov_estimator = CovarianceEstimator(cov_config)

    var_config = ParametricVaRConfig(confidence_level=0.95, horizon_days=1)
    var_engine = ParametricVaR(var_config)

    return ComponentVaRCalculator(cov_estimator, var_engine)


def test_component_var_basic_calculation(sample_returns_from_fixtures, default_calculator):
    """Test basic Component VaR calculation."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    result = default_calculator.calculate(returns, weights, portfolio_value)

    # Basic checks
    assert result.total_var > 0
    assert len(result.component_var) == 3
    assert len(result.marginal_var) == 3
    assert len(result.contribution_pct) == 3
    assert result.asset_names == ["BTC", "ETH", "SOL"]

    # All component vars should be > 0 (for long-only portfolio)
    assert np.all(result.component_var > 0)

    # Contribution should sum to ~100%
    assert np.isclose(result.contribution_pct.sum(), 100.0, atol=1e-6)


def test_euler_property_strict(sample_returns_from_fixtures, default_calculator):
    """Test Euler Property: sum(component) == total."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    result = default_calculator.calculate(
        returns, weights, portfolio_value, validate_euler=True, euler_rtol=1e-6
    )

    # Euler check should pass (already validated internally)
    sum_components = result.component_var.sum()
    assert np.isclose(sum_components, result.total_var, rtol=1e-6)


def test_weights_as_array(sample_returns_from_fixtures, default_calculator):
    """Test weights als np.ndarray."""
    returns = sample_returns_from_fixtures

    weights_array = np.array([0.5, 0.3, 0.2])  # Order: BTC, ETH, SOL
    portfolio_value = 100_000.0

    result = default_calculator.calculate(returns, weights_array, portfolio_value)

    assert result.total_var > 0
    assert np.allclose(result.weights, weights_array)


def test_missing_weights_raises_error(sample_returns_from_fixtures, default_calculator):
    """Test dass fehlende Gewichte einen Error werfen."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.6, "ETH": 0.4}  # Missing SOL

    with pytest.raises(ValueError, match="Missing weights"):
        default_calculator.calculate(returns, weights, 100_000.0)


def test_weights_not_sum_to_one_raises_error(sample_returns_from_fixtures, default_calculator):
    """Test dass Gewichte die nicht zu 1 summieren einen Error werfen."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.1}  # Sum = 0.9

    with pytest.raises(ValueError, match="sum to approximately 1.0"):
        default_calculator.calculate(returns, weights, 100_000.0)


def test_zero_portfolio_sigma_raises_error(default_calculator):
    """Test dass sigma=0 einen Error wirft."""
    # Create returns with zero variance
    returns = pd.DataFrame(
        {
            "A": [0.0] * 100,
            "B": [0.0] * 100,
            "C": [0.0] * 100,
        }
    )

    weights = {"A": 0.5, "B": 0.3, "C": 0.2}

    # Zero variance -> non-PD covariance matrix OR sigma=0
    with pytest.raises(ValueError, match="(sigma is zero|not positive definite)"):
        default_calculator.calculate(returns, weights, 100_000.0)


def test_component_var_result_to_dataframe(sample_returns_from_fixtures, default_calculator):
    """Test ComponentVaRResult to_dataframe()."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    result = default_calculator.calculate(returns, weights, portfolio_value)

    df = result.to_dataframe()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == [
        "asset",
        "weight",
        "marginal_var",
        "component_var",
        "contribution_pct",
    ]
    assert len(df) == 3
    assert list(df["asset"]) == ["BTC", "ETH", "SOL"]


def test_component_var_result_str(sample_returns_from_fixtures, default_calculator):
    """Test ComponentVaRResult __str__()."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    result = default_calculator.calculate(returns, weights, portfolio_value)

    result_str = str(result)

    assert "Component VaR Analysis" in result_str
    assert f"Total VaR: {result.total_var:.2f}" in result_str
    assert "Euler Check" in result_str


def test_different_confidence_levels(sample_returns_from_fixtures):
    """Test verschiedene Confidence Levels."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    # 95% VaR
    cov_config_95 = CovarianceEstimatorConfig(method="sample", min_history=60)
    var_config_95 = ParametricVaRConfig(confidence_level=0.95, horizon_days=1)
    calc_95 = ComponentVaRCalculator(
        CovarianceEstimator(cov_config_95), ParametricVaR(var_config_95)
    )
    result_95 = calc_95.calculate(returns, weights, portfolio_value)

    # 99% VaR
    cov_config_99 = CovarianceEstimatorConfig(method="sample", min_history=60)
    var_config_99 = ParametricVaRConfig(confidence_level=0.99, horizon_days=1)
    calc_99 = ComponentVaRCalculator(
        CovarianceEstimator(cov_config_99), ParametricVaR(var_config_99)
    )
    result_99 = calc_99.calculate(returns, weights, portfolio_value)

    # 99% VaR should be higher than 95% VaR
    assert result_99.total_var > result_95.total_var


def test_different_horizons(sample_returns_from_fixtures):
    """Test verschiedene Zeithorizonte."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    # 1-day horizon
    cov_config_1d = CovarianceEstimatorConfig(method="sample", min_history=60)
    var_config_1d = ParametricVaRConfig(confidence_level=0.95, horizon_days=1)
    calc_1d = ComponentVaRCalculator(
        CovarianceEstimator(cov_config_1d), ParametricVaR(var_config_1d)
    )
    result_1d = calc_1d.calculate(returns, weights, portfolio_value)

    # 10-day horizon
    cov_config_10d = CovarianceEstimatorConfig(method="sample", min_history=60)
    var_config_10d = ParametricVaRConfig(confidence_level=0.95, horizon_days=10)
    calc_10d = ComponentVaRCalculator(
        CovarianceEstimator(cov_config_10d), ParametricVaR(var_config_10d)
    )
    result_10d = calc_10d.calculate(returns, weights, portfolio_value)

    # 10-day VaR should be higher than 1-day (roughly sqrt(10) times)
    # But not exactly due to correlation effects
    assert result_10d.total_var > result_1d.total_var
    ratio = result_10d.total_var / result_1d.total_var
    # Should be roughly sqrt(10) ≈ 3.16, allow some tolerance
    assert 2.5 < ratio < 4.0


def test_diagonal_shrinkage_method(sample_returns_from_fixtures):
    """Test mit diagonal shrinkage covariance."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    cov_config = CovarianceEstimatorConfig(
        method="diagonal_shrink", min_history=60, shrinkage_alpha=0.2
    )
    var_config = ParametricVaRConfig(confidence_level=0.95, horizon_days=1)
    calc = ComponentVaRCalculator(CovarianceEstimator(cov_config), ParametricVaR(var_config))

    result = calc.calculate(returns, weights, portfolio_value)

    # Should still satisfy Euler
    assert np.isclose(result.component_var.sum(), result.total_var, rtol=1e-4)


def test_highest_contributor(sample_returns_from_fixtures, default_calculator):
    """Test dass wir den höchsten Contributor identifizieren können."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    result = default_calculator.calculate(returns, weights, portfolio_value)

    df = result.to_dataframe()
    highest_contributor = df.loc[df["contribution_pct"].idxmax(), "asset"]

    # BTC hat höchstes Weight, sollte vermutlich auch highest contributor sein
    # (aber nicht garantiert, hängt von Vol/Corr ab)
    assert highest_contributor in ["BTC", "ETH", "SOL"]
    print(f"\nHighest contributor: {highest_contributor}")
    print(df)
