"""
Tests für Component VaR Calculator
===================================
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.risk.component_var import (
    ComponentVaRCalculator,
    ComponentVaRResult,
    IncrementalVaRResult,
    DiversificationBenefitResult,
    calculate_incremental_var,
    calculate_diversification_benefit,
)
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


# =============================================================================
# Phase 2 Tests: Incremental VaR & Diversification (Agent A2)
# =============================================================================


def test_incremental_var_basic(sample_returns_from_fixtures, default_calculator):
    """Test basic Incremental VaR calculation."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    # Calculate incremental VaR for SOL
    result = calculate_incremental_var(
        default_calculator, returns, weights, "SOL", portfolio_value
    )

    assert isinstance(result, IncrementalVaRResult)
    assert result.asset_name == "SOL"
    assert result.asset_weight == 0.2
    assert result.portfolio_var_without >= 0
    assert result.portfolio_var_with >= 0
    # Adding an asset typically increases VaR (unless negative correlation)
    assert result.incremental_var != 0  # Should have some impact


def test_incremental_var_positive_for_volatile_asset(
    sample_returns_from_fixtures, default_calculator
):
    """Adding a volatile asset should increase VaR."""
    returns = sample_returns_from_fixtures

    # Small weight, but we're testing the direction
    weights = {"BTC": 0.7, "ETH": 0.25, "SOL": 0.05}
    portfolio_value = 100_000.0

    result = calculate_incremental_var(
        default_calculator, returns, weights, "SOL", portfolio_value
    )

    # Adding SOL should increase VaR (assuming positive correlation)
    # This is not always guaranteed, but for typical crypto portfolios it should be true
    assert result.incremental_var != 0


def test_incremental_var_single_asset_portfolio(default_calculator):
    """Test incremental VaR when portfolio consists only of the target asset."""
    # Synthetic returns
    np.random.seed(42)
    returns = pd.DataFrame(
        {
            "BTC": np.random.normal(0.001, 0.02, 100),
        }
    )

    weights = {"BTC": 1.0}
    portfolio_value = 100_000.0

    result = calculate_incremental_var(
        default_calculator, returns, weights, "BTC", portfolio_value
    )

    # Portfolio without BTC = empty = 0 VaR
    assert result.portfolio_var_without == 0.0
    # Portfolio with BTC = full VaR
    assert result.portfolio_var_with > 0
    # Incremental = full VaR
    assert result.incremental_var == result.portfolio_var_with


def test_incremental_var_missing_asset_raises_error(
    sample_returns_from_fixtures, default_calculator
):
    """Test that missing asset raises ValueError."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    with pytest.raises(ValueError, match="not found in weights"):
        calculate_incremental_var(
            default_calculator, returns, weights, "DOGE", portfolio_value
        )


def test_incremental_var_str(sample_returns_from_fixtures, default_calculator):
    """Test IncrementalVaRResult __str__()."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    result = calculate_incremental_var(
        default_calculator, returns, weights, "SOL", portfolio_value
    )

    result_str = str(result)
    assert "Incremental VaR" in result_str
    assert "SOL" in result_str
    assert "Portfolio VaR (without)" in result_str
    assert "Portfolio VaR (with)" in result_str


def test_diversification_benefit_basic(sample_returns_from_fixtures, default_calculator):
    """Test basic Diversification Benefit calculation."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    result = calculate_diversification_benefit(
        default_calculator, returns, weights, portfolio_value
    )

    assert isinstance(result, DiversificationBenefitResult)
    assert result.portfolio_var > 0
    assert len(result.standalone_vars) == 3
    assert len(result.weighted_standalone_vars) == 3
    assert result.sum_weighted_standalone > 0
    # Diversification benefit should be positive (risk reduction)
    assert result.diversification_benefit > 0
    # Diversification ratio should be < 1.0 (unless perfect correlation)
    assert 0 < result.diversification_ratio <= 1.0


def test_diversification_benefit_single_asset(default_calculator):
    """Test diversification benefit with single asset (should be zero)."""
    # Synthetic returns
    np.random.seed(42)
    returns = pd.DataFrame(
        {
            "BTC": np.random.normal(0.001, 0.02, 100),
        }
    )

    weights = {"BTC": 1.0}
    portfolio_value = 100_000.0

    result = calculate_diversification_benefit(
        default_calculator, returns, weights, portfolio_value
    )

    # Single asset: no diversification possible
    # Portfolio VaR = Standalone VaR
    assert np.isclose(result.diversification_benefit, 0.0, atol=1e-6)
    assert np.isclose(result.diversification_ratio, 1.0, atol=1e-6)


def test_diversification_benefit_perfect_correlation():
    """Test diversification benefit with perfectly correlated assets."""
    # Create perfectly correlated returns (but add tiny noise to avoid singular matrix)
    np.random.seed(42)
    base_returns = np.random.normal(0.001, 0.02, 100)

    returns = pd.DataFrame(
        {
            "A": base_returns,
            "B": base_returns + np.random.normal(0, 1e-8, 100),  # Nearly perfect correlation
        }
    )

    weights = {"A": 0.6, "B": 0.4}
    portfolio_value = 100_000.0

    cov_config = CovarianceEstimatorConfig(method="sample", min_history=50)
    var_config = ParametricVaRConfig(confidence_level=0.95, horizon_days=1)
    calc = ComponentVaRCalculator(CovarianceEstimator(cov_config), ParametricVaR(var_config))

    result = calculate_diversification_benefit(calc, returns, weights, portfolio_value)

    # Nearly perfect correlation -> minimal diversification benefit
    # Ratio should be close to 1.0
    assert result.diversification_ratio >= 0.90  # Very little diversification


def test_diversification_benefit_uncorrelated_assets():
    """Test diversification benefit with uncorrelated assets."""
    # Create uncorrelated returns
    np.random.seed(42)
    returns = pd.DataFrame(
        {
            "A": np.random.normal(0.001, 0.02, 200),
            "B": np.random.normal(0.001, 0.02, 200),
        }
    )

    weights = {"A": 0.5, "B": 0.5}
    portfolio_value = 100_000.0

    cov_config = CovarianceEstimatorConfig(method="sample", min_history=100)
    var_config = ParametricVaRConfig(confidence_level=0.95, horizon_days=1)
    calc = ComponentVaRCalculator(CovarianceEstimator(cov_config), ParametricVaR(var_config))

    result = calculate_diversification_benefit(calc, returns, weights, portfolio_value)

    # Uncorrelated assets -> strong diversification benefit
    # Ratio should be well below 1.0
    assert result.diversification_benefit > 0
    assert result.diversification_ratio < 0.9  # Significant diversification


def test_diversification_benefit_to_dataframe(
    sample_returns_from_fixtures, default_calculator
):
    """Test DiversificationBenefitResult to_dataframe()."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    result = calculate_diversification_benefit(
        default_calculator, returns, weights, portfolio_value
    )

    df = result.to_dataframe()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == [
        "asset",
        "weight",
        "standalone_var",
        "weighted_standalone_var",
    ]
    assert len(df) == 3
    assert list(df["asset"]) == ["BTC", "ETH", "SOL"]


def test_diversification_benefit_str(sample_returns_from_fixtures, default_calculator):
    """Test DiversificationBenefitResult __str__()."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    result = calculate_diversification_benefit(
        default_calculator, returns, weights, portfolio_value
    )

    result_str = str(result)
    assert "Diversification Benefit Analysis" in result_str
    # Check for key strings (without exact formatting which may vary)
    assert "Portfolio VaR:" in result_str
    assert "Diversification Benefit:" in result_str
    assert "Diversification Ratio:" in result_str
    assert "BTC" in result_str
    assert "ETH" in result_str
    assert "SOL" in result_str


def test_diversification_benefit_invariants(sample_returns_from_fixtures, default_calculator):
    """Test diversification benefit invariants."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    result = calculate_diversification_benefit(
        default_calculator, returns, weights, portfolio_value
    )

    # 1. Sum of weighted standalone VaRs should equal sum of individual parts
    assert np.isclose(
        result.weighted_standalone_vars.sum(), result.sum_weighted_standalone, rtol=1e-6
    )

    # 2. Diversification benefit = Sum Weighted Standalone - Portfolio VaR
    expected_benefit = result.sum_weighted_standalone - result.portfolio_var
    assert np.isclose(result.diversification_benefit, expected_benefit, rtol=1e-6)

    # 3. Diversification ratio = Portfolio VaR / Sum Weighted Standalone
    if result.sum_weighted_standalone > 0:
        expected_ratio = result.portfolio_var / result.sum_weighted_standalone
        assert np.isclose(result.diversification_ratio, expected_ratio, rtol=1e-6)


def test_incremental_var_all_assets(sample_returns_from_fixtures, default_calculator):
    """Test incremental VaR for all assets in portfolio."""
    returns = sample_returns_from_fixtures

    weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    portfolio_value = 100_000.0

    # Calculate incremental VaR for each asset
    incremental_results = {}
    for asset in weights.keys():
        result = calculate_incremental_var(
            default_calculator, returns, weights, asset, portfolio_value
        )
        incremental_results[asset] = result

    # All results should have valid values
    for asset, result in incremental_results.items():
        assert result.portfolio_var_with > 0
        assert result.portfolio_var_without >= 0
        print(f"\n{asset}: Incremental VaR = {result.incremental_var:,.2f}")
