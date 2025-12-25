"""
Tests for Portfolio VaR - Phase 1 Core
=======================================
Deterministic tests for portfolio VaR calculations.
"""

import pytest
import numpy as np
import pandas as pd

from src.risk.portfolio_var import (
    PortfolioVarConfig,
    normalize_symbol,
    align_weights_to_returns,
    estimate_cov,
    portfolio_sigma,
    z_value,
    parametric_var,
    historical_var,
    binom_p_value,
)


class TestNormalizeSymbol:
    """Tests for normalize_symbol()"""

    def test_normalize_symbol_base_slash(self):
        """BTC/EUR -> BTC"""
        assert normalize_symbol("BTC/EUR", mode="base") == "BTC"

    def test_normalize_symbol_base_dash(self):
        """ETH-USD -> ETH"""
        assert normalize_symbol("ETH-USD", mode="base") == "ETH"

    def test_normalize_symbol_base_underscore(self):
        """SOL_USDT -> SOL"""
        assert normalize_symbol("SOL_USDT", mode="base") == "SOL"

    def test_normalize_symbol_base_already_normalized(self):
        """BTC -> BTC"""
        assert normalize_symbol("BTC", mode="base") == "BTC"

    def test_normalize_symbol_raw(self):
        """Raw mode returns unchanged"""
        assert normalize_symbol("BTC/EUR", mode="raw") == "BTC/EUR"

    def test_normalize_symbol_lowercase(self):
        """Handles lowercase and uppercases result"""
        assert normalize_symbol("btc/eur", mode="base") == "BTC"


class TestAlignWeightsToReturns:
    """Tests for align_weights_to_returns()"""

    def test_align_weights_dict_base_mode(self):
        """Dict weights with symbol normalization"""
        returns_cols = ["BTC", "ETH"]
        weights = {"BTC/EUR": 0.6, "ETH/EUR": 0.4}

        w = align_weights_to_returns(weights, returns_cols, symbol_mode="base")

        assert len(w) == 2
        assert w[0] == pytest.approx(0.6)
        assert w[1] == pytest.approx(0.4)

    def test_align_weights_dict_raw_mode(self):
        """Dict weights without normalization"""
        returns_cols = ["BTC/EUR", "ETH/EUR"]
        weights = {"BTC/EUR": 0.5, "ETH/EUR": 0.5}

        w = align_weights_to_returns(weights, returns_cols, symbol_mode="raw")

        assert len(w) == 2
        assert w[0] == pytest.approx(0.5)
        assert w[1] == pytest.approx(0.5)

    def test_align_weights_sequence(self):
        """Sequence weights must match column order"""
        returns_cols = ["BTC", "ETH"]
        weights = [0.7, 0.3]

        w = align_weights_to_returns(weights, returns_cols)

        assert len(w) == 2
        assert w[0] == pytest.approx(0.7)
        assert w[1] == pytest.approx(0.3)

    def test_align_weights_missing_symbol_raises(self):
        """Missing symbol in weights raises ValueError"""
        returns_cols = ["BTC", "ETH", "SOL"]
        weights = {"BTC/EUR": 0.6, "ETH/EUR": 0.4}

        with pytest.raises(ValueError, match="Missing weights"):
            align_weights_to_returns(weights, returns_cols, symbol_mode="base")

    def test_align_weights_sequence_wrong_length_raises(self):
        """Sequence with wrong length raises ValueError"""
        returns_cols = ["BTC", "ETH"]
        weights = [0.5, 0.3, 0.2]  # 3 weights for 2 columns

        with pytest.raises(ValueError, match="length.*must match"):
            align_weights_to_returns(weights, returns_cols)

    def test_align_weights_sum_not_one_raises(self):
        """Weights not summing to ~1.0 raises ValueError"""
        returns_cols = ["BTC", "ETH"]
        weights = {"BTC": 0.5, "ETH": 0.3}  # Sum = 0.8

        with pytest.raises(ValueError, match="sum to ~1.0"):
            align_weights_to_returns(weights, returns_cols)


class TestEstimateCov:
    """Tests for estimate_cov()"""

    def test_estimate_cov_simple(self):
        """Simple covariance estimation"""
        returns_df = pd.DataFrame({"A": [0.01, -0.01, 0.02], "B": [0.02, -0.02, 0.01]})

        cov = estimate_cov(returns_df)

        assert cov.shape == (2, 2)
        # Diagonal should be positive (variances)
        assert cov[0, 0] > 0
        assert cov[1, 1] > 0
        # Symmetric
        assert cov[0, 1] == pytest.approx(cov[1, 0])

    def test_estimate_cov_insufficient_data_raises(self):
        """Less than 2 rows raises ValueError"""
        returns_df = pd.DataFrame({"A": [0.01], "B": [0.02]})

        with pytest.raises(ValueError, match="at least 2 rows"):
            estimate_cov(returns_df)

    def test_estimate_cov_with_nans(self):
        """NaN rows are dropped"""
        returns_df = pd.DataFrame(
            {"A": [0.01, np.nan, 0.02, 0.01], "B": [0.02, 0.01, np.nan, -0.01]}
        )

        cov = estimate_cov(returns_df)

        assert cov.shape == (2, 2)


class TestPortfolioSigma:
    """Tests for portfolio_sigma()"""

    def test_portfolio_sigma_equal_weights(self):
        """Equal weights, known covariance"""
        # Simple cov matrix
        cov = np.array([[0.04, 0.01], [0.01, 0.09]])
        w = np.array([0.5, 0.5])

        sigma = portfolio_sigma(cov, w)

        # Manual calc: variance = 0.5^2 * 0.04 + 0.5^2 * 0.09 + 2 * 0.5 * 0.5 * 0.01
        #                        = 0.01 + 0.0225 + 0.005 = 0.0375
        # sigma = sqrt(0.0375) ≈ 0.1936
        assert sigma == pytest.approx(0.1936, abs=0.001)

    def test_portfolio_sigma_single_asset(self):
        """Single asset: sigma = sqrt(variance)"""
        cov = np.array([[0.04]])
        w = np.array([1.0])

        sigma = portfolio_sigma(cov, w)

        assert sigma == pytest.approx(0.2, abs=0.0001)  # sqrt(0.04) = 0.2


class TestZValue:
    """Tests for z_value()"""

    def test_z_value_95(self):
        """95% confidence -> z ≈ 1.645"""
        z = z_value(0.95)
        assert abs(z - 1.645) < 0.01

    def test_z_value_99(self):
        """99% confidence -> z ≈ 2.326"""
        z = z_value(0.99)
        assert abs(z - 2.326) < 0.01

    def test_z_value_90(self):
        """90% confidence -> z ≈ 1.282"""
        z = z_value(0.90)
        assert abs(z - 1.282) < 0.01


class TestParametricVar:
    """Tests for parametric_var()"""

    def test_parametric_var_matches_known_small_example(self):
        """Deterministic test with known covariance"""
        # Create deterministic returns
        np.random.seed(42)
        returns_df = pd.DataFrame(
            {"BTC": [0.02, -0.01, 0.03, -0.02, 0.01], "ETH": [0.01, -0.02, 0.02, -0.01, 0.03]}
        )

        weights = {"BTC": 0.5, "ETH": 0.5}

        var = parametric_var(returns_df, weights, confidence=0.95, horizon_days=1, use_mean=False)

        # VaR should be positive
        assert var > 0

        # Manual verification (approximate)
        # Compute cov + sigma manually
        cov = estimate_cov(returns_df)
        w = np.array([0.5, 0.5])
        sigma = portfolio_sigma(cov, w)
        z = z_value(0.95)
        expected_var = z * sigma

        assert var == pytest.approx(expected_var, rel=0.01)

    def test_parametric_var_with_mean(self):
        """VaR with mean drift (use_mean=True)"""
        returns_df = pd.DataFrame(
            {
                "BTC": [0.01, 0.02, 0.01, 0.02, 0.01],  # Positive mean
                "ETH": [0.01, 0.02, 0.01, 0.02, 0.01],
            }
        )

        weights = {"BTC": 0.5, "ETH": 0.5}

        var_with_mean = parametric_var(
            returns_df, weights, confidence=0.99, horizon_days=1, use_mean=True
        )
        var_without_mean = parametric_var(
            returns_df, weights, confidence=0.99, horizon_days=1, use_mean=False
        )

        # With positive mean, VaR with mean should be lower (less conservative)
        assert var_with_mean < var_without_mean

    def test_parametric_var_horizon_scaling(self):
        """VaR scales with sqrt(horizon)"""
        returns_df = pd.DataFrame(
            {"BTC": [0.01, -0.01, 0.02, -0.02], "ETH": [0.02, -0.01, 0.01, -0.02]}
        )

        weights = {"BTC": 0.6, "ETH": 0.4}

        var_1day = parametric_var(returns_df, weights, confidence=0.95, horizon_days=1)
        var_4days = parametric_var(returns_df, weights, confidence=0.95, horizon_days=4)

        # VaR(4 days) ≈ VaR(1 day) * sqrt(4) = VaR(1 day) * 2
        assert var_4days == pytest.approx(var_1day * 2, rel=0.01)

    def test_parametric_var_symbol_mode_base(self):
        """Symbol normalization works in parametric VaR"""
        returns_df = pd.DataFrame({"BTC": [0.01, -0.01, 0.02], "ETH": [0.02, -0.02, 0.01]})

        weights = {"BTC/EUR": 0.6, "ETH/USD": 0.4}

        var = parametric_var(returns_df, weights, confidence=0.95, symbol_mode="base")

        assert var > 0


class TestHistoricalVar:
    """Tests for historical_var()"""

    def test_historical_var_quantile_behavior(self):
        """Historical VaR matches expected quantile"""
        # Construct returns with known quantile
        # 100 returns, 5% tail = 5 worst returns
        np.random.seed(123)
        btc_returns = np.random.normal(0.01, 0.02, 100)
        eth_returns = np.random.normal(0.01, 0.03, 100)

        returns_df = pd.DataFrame({"BTC": btc_returns, "ETH": eth_returns})

        weights = [0.5, 0.5]

        var = historical_var(returns_df, weights, confidence=0.95, horizon_days=1)

        # VaR should be positive
        assert var > 0

        # Manual verification: compute portfolio returns and check quantile
        portfolio_returns = returns_df @ np.array(weights)
        quantile_val = portfolio_returns.quantile(1 - 0.95)  # 5th percentile
        expected_var = -quantile_val

        assert var == pytest.approx(expected_var, abs=1e-10)

    def test_historical_var_horizon_days_aggregation(self):
        """Historical VaR with horizon_days > 1"""
        returns_df = pd.DataFrame(
            {
                "BTC": [0.01, -0.01, 0.02, -0.02, 0.01, 0.01],
                "ETH": [0.02, -0.02, 0.01, -0.01, 0.02, 0.01],
            }
        )

        weights = {"BTC": 0.5, "ETH": 0.5}

        var = historical_var(returns_df, weights, confidence=0.90, horizon_days=2)

        # Should be positive
        assert var > 0

    def test_historical_var_insufficient_data_raises(self):
        """Historical VaR with insufficient data raises ValueError"""
        returns_df = pd.DataFrame({"BTC": [0.01], "ETH": [0.02]})

        weights = [0.5, 0.5]

        with pytest.raises(ValueError, match="at least 2 rows"):
            historical_var(returns_df, weights, confidence=0.95, horizon_days=1)

    def test_historical_var_symbol_mode_base(self):
        """Symbol normalization works in historical VaR"""
        returns_df = pd.DataFrame(
            {"BTC": [0.01, -0.01, 0.02, -0.02], "ETH": [0.02, -0.02, 0.01, -0.01]}
        )

        weights = {"BTC/EUR": 0.7, "ETH/EUR": 0.3}

        var = historical_var(returns_df, weights, confidence=0.90, symbol_mode="base")

        assert var > 0


class TestBinomPValue:
    """Tests for binom_p_value()"""

    def test_binom_p_value_reasonable(self):
        """Binomial test with k=50, n=100, p=0.5 should have high p-value"""
        p_val = binom_p_value(k=50, n=100, p=0.5, alternative="two-sided")

        # Expected: p-value close to 1.0 (no evidence against H0)
        assert 0.9 < p_val <= 1.0

    def test_binom_p_value_extreme(self):
        """Binomial test with extreme k should have low p-value"""
        p_val = binom_p_value(k=95, n=100, p=0.5, alternative="two-sided")

        # Expected: p-value very small (strong evidence against H0)
        assert p_val < 0.01

    def test_binom_p_value_greater(self):
        """Binomial test with alternative='greater'"""
        p_val = binom_p_value(k=60, n=100, p=0.5, alternative="greater")

        # P(X >= 60) should be relatively small
        assert 0 < p_val < 0.1

    def test_binom_p_value_less(self):
        """Binomial test with alternative='less'"""
        p_val = binom_p_value(k=40, n=100, p=0.5, alternative="less")

        # P(X <= 40) should be relatively small
        assert 0 < p_val < 0.1

    def test_binom_p_value_in_range(self):
        """P-value should always be in [0, 1]"""
        for k in [0, 10, 50, 90, 100]:
            p_val = binom_p_value(k=k, n=100, p=0.5, alternative="two-sided")
            assert 0 <= p_val <= 1


class TestPortfolioVarConfig:
    """Tests for PortfolioVarConfig dataclass"""

    def test_config_defaults(self):
        """Default config values"""
        config = PortfolioVarConfig()

        assert config.enabled is True
        assert config.method == "parametric"
        assert config.confidence == 0.99
        assert config.horizon_days == 1
        assert config.lookback_bars == 500
        assert config.symbol_mode == "base"
        assert config.use_mean is False

    def test_config_invalid_confidence_raises(self):
        """Invalid confidence raises ValueError"""
        with pytest.raises(ValueError, match="confidence must be in"):
            PortfolioVarConfig(confidence=1.5)

        with pytest.raises(ValueError, match="confidence must be in"):
            PortfolioVarConfig(confidence=0.0)

    def test_config_invalid_horizon_raises(self):
        """Invalid horizon_days raises ValueError"""
        with pytest.raises(ValueError, match="horizon_days must be"):
            PortfolioVarConfig(horizon_days=0)

    def test_config_invalid_lookback_raises(self):
        """Invalid lookback_bars raises ValueError"""
        with pytest.raises(ValueError, match="lookback_bars must be"):
            PortfolioVarConfig(lookback_bars=1)


class TestEdgeCases:
    """Edge cases and error handling"""

    def test_parametric_var_with_nans(self):
        """Parametric VaR handles NaN rows"""
        returns_df = pd.DataFrame(
            {"BTC": [0.01, np.nan, 0.02, -0.01], "ETH": [0.02, 0.01, np.nan, -0.02]}
        )

        weights = [0.5, 0.5]

        var = parametric_var(returns_df, weights, confidence=0.95)

        # Should work (drops NaN rows)
        assert var > 0

    def test_historical_var_all_positive_returns(self):
        """Historical VaR with all positive returns"""
        returns_df = pd.DataFrame({"BTC": [0.01, 0.02, 0.03], "ETH": [0.01, 0.02, 0.03]})

        weights = [0.5, 0.5]

        var = historical_var(returns_df, weights, confidence=0.95)

        # VaR should be 0 or very small (no losses)
        assert var >= 0
        assert var < 0.01  # Should be close to 0
