"""
Tests for Portfolio Analytics (src/risk/portfolio.py)
"""

import pytest
import pandas as pd
import numpy as np

from src.risk.portfolio import (
    compute_position_notional,
    compute_gross_exposure,
    compute_net_exposure,
    compute_weights,
    correlation_matrix,
    portfolio_returns,
)
from src.risk.types import PositionSnapshot


class TestPositionNotional:
    """Tests for compute_position_notional()"""

    def test_long_position(self):
        """Long Position: notional = |units * price|"""
        notional = compute_position_notional(units=0.5, price=50000)
        assert notional == 25000.0

    def test_short_position(self):
        """Short Position: notional ist immer positiv"""
        notional = compute_position_notional(units=-0.3, price=2000)
        assert notional == 600.0

    def test_zero_units(self):
        """Zero units -> notional=0"""
        notional = compute_position_notional(units=0, price=50000)
        assert notional == 0.0


class TestGrossExposure:
    """Tests for compute_gross_exposure()"""

    def test_empty_positions(self):
        """Leere Positionsliste -> Exposure=0"""
        exposure = compute_gross_exposure([])
        assert exposure == 0.0

    def test_single_long_position(self):
        """Single Long Position"""
        pos = PositionSnapshot("BTC/EUR", units=0.5, price=50000)
        exposure = compute_gross_exposure([pos])
        assert exposure == 25000.0

    def test_long_and_short_positions(self):
        """Gross Exposure = Sum(|notional|) für long+short"""
        pos1 = PositionSnapshot("BTC/EUR", units=0.5, price=50000)  # 25000
        pos2 = PositionSnapshot("ETH/EUR", units=-10, price=3000)  # 30000
        exposure = compute_gross_exposure([pos1, pos2])
        assert exposure == 55000.0

    def test_multiple_long_positions(self):
        """Multiple Long Positions"""
        pos1 = PositionSnapshot("BTC/EUR", units=0.5, price=50000)  # 25000
        pos2 = PositionSnapshot("ETH/EUR", units=2, price=3000)  # 6000
        pos3 = PositionSnapshot("SOL/EUR", units=100, price=100)  # 10000
        exposure = compute_gross_exposure([pos1, pos2, pos3])
        assert exposure == 41000.0


class TestNetExposure:
    """Tests for compute_net_exposure()"""

    def test_empty_positions(self):
        """Leere Positionsliste -> Net=0"""
        net = compute_net_exposure([])
        assert net == 0.0

    def test_all_long_positions(self):
        """Nur Long -> Net = Gross"""
        pos1 = PositionSnapshot("BTC/EUR", units=0.5, price=50000)  # 25000
        pos2 = PositionSnapshot("ETH/EUR", units=2, price=3000)  # 6000
        net = compute_net_exposure([pos1, pos2])
        assert net == 31000.0

    def test_all_short_positions(self):
        """Nur Short -> Net negativ"""
        pos1 = PositionSnapshot("BTC/EUR", units=-0.5, price=50000)  # -25000
        pos2 = PositionSnapshot("ETH/EUR", units=-2, price=3000)  # -6000
        net = compute_net_exposure([pos1, pos2])
        assert net == -31000.0

    def test_long_short_mix(self):
        """Long + Short -> Net = Long - Short"""
        pos1 = PositionSnapshot("BTC/EUR", units=0.5, price=50000)  # +25000
        pos2 = PositionSnapshot("ETH/EUR", units=-10, price=3000)  # -30000
        net = compute_net_exposure([pos1, pos2])
        assert net == -5000.0  # net short

    def test_balanced_long_short(self):
        """Balanced long/short -> Net ~0"""
        pos1 = PositionSnapshot("BTC/EUR", units=1, price=10000)  # +10000
        pos2 = PositionSnapshot("ETH/EUR", units=-5, price=2000)  # -10000
        net = compute_net_exposure([pos1, pos2])
        assert abs(net) < 1e-6  # ~0


class TestComputeWeights:
    """Tests for compute_weights()"""

    def test_weights_sum_to_one(self):
        """Weights sollten approx 1.0 summieren (wenn keine Leverage)"""
        pos1 = PositionSnapshot("BTC/EUR", units=0.5, price=50000)  # 25000
        pos2 = PositionSnapshot("ETH/EUR", units=10, price=3000)  # 30000
        # Total = 55000, Equity = 100000 -> weights = 0.25 + 0.30 = 0.55
        weights = compute_weights([pos1, pos2], equity=100000)

        assert weights["BTC/EUR"] == pytest.approx(0.25, abs=1e-6)
        assert weights["ETH/EUR"] == pytest.approx(0.30, abs=1e-6)
        assert sum(weights.values()) == pytest.approx(0.55, abs=1e-6)

    def test_weights_with_leverage(self):
        """Weights können > 1.0 bei Leverage"""
        pos1 = PositionSnapshot("BTC/EUR", units=1, price=50000)  # 50000
        pos2 = PositionSnapshot("ETH/EUR", units=20, price=3000)  # 60000
        # Total = 110000, Equity = 100000 -> sum > 1
        weights = compute_weights([pos1, pos2], equity=100000)

        assert weights["BTC/EUR"] == pytest.approx(0.50, abs=1e-6)
        assert weights["ETH/EUR"] == pytest.approx(0.60, abs=1e-6)
        assert sum(weights.values()) == pytest.approx(1.10, abs=1e-6)

    def test_weights_empty_positions(self):
        """Leere Positionsliste -> leeres Dict"""
        weights = compute_weights([], equity=100000)
        assert weights == {}

    def test_weights_zero_equity_raises(self):
        """Equity <= 0 sollte ValueError werfen"""
        pos = PositionSnapshot("BTC/EUR", units=1, price=50000)
        with pytest.raises(ValueError, match="Equity must be > 0"):
            compute_weights([pos], equity=0)

        with pytest.raises(ValueError, match="Equity must be > 0"):
            compute_weights([pos], equity=-1000)


class TestCorrelationMatrix:
    """Tests for correlation_matrix()"""

    def test_correlation_diagonal_is_one(self):
        """Diagonal sollte 1.0 sein (Korrelation mit sich selbst)"""
        returns = pd.DataFrame({"BTC": [0.01, -0.02, 0.03], "ETH": [0.02, -0.01, 0.02]})
        corr = correlation_matrix(returns)

        assert corr.loc["BTC", "BTC"] == pytest.approx(1.0, abs=1e-6)
        assert corr.loc["ETH", "ETH"] == pytest.approx(1.0, abs=1e-6)

    def test_correlation_symmetric(self):
        """Korrelationsmatrix sollte symmetrisch sein"""
        returns = pd.DataFrame({"BTC": [0.01, -0.02, 0.03], "ETH": [0.02, -0.01, 0.02]})
        corr = correlation_matrix(returns)

        assert corr.loc["BTC", "ETH"] == pytest.approx(corr.loc["ETH", "BTC"], abs=1e-6)

    def test_correlation_range(self):
        """Korrelation sollte in [-1, 1] liegen"""
        np.random.seed(42)
        returns = pd.DataFrame(
            {
                "A": np.random.normal(0, 0.02, 100),
                "B": np.random.normal(0, 0.03, 100),
                "C": np.random.normal(0, 0.01, 100),
            }
        )
        corr = correlation_matrix(returns)

        for col in corr.columns:
            for row in corr.index:
                assert -1.0 <= corr.loc[row, col] <= 1.0

    def test_correlation_empty_dataframe(self):
        """Leeres DataFrame -> leere Matrix"""
        returns = pd.DataFrame()
        corr = correlation_matrix(returns)
        assert corr.empty

    def test_correlation_perfectly_correlated(self):
        """Perfekt korrelierte Assets -> corr = 1.0"""
        returns = pd.DataFrame({"A": [0.01, -0.02, 0.03], "B": [0.01, -0.02, 0.03]})
        corr = correlation_matrix(returns)

        assert corr.loc["A", "B"] == pytest.approx(1.0, abs=1e-6)


class TestPortfolioReturns:
    """Tests for portfolio_returns()"""

    def test_portfolio_returns_equal_weights(self):
        """Portfolio Returns mit gleichen Weights"""
        returns = pd.DataFrame({"BTC": [0.01, -0.02, 0.03], "ETH": [0.02, -0.01, 0.02]})
        weights = {"BTC": 0.5, "ETH": 0.5}

        port_ret = portfolio_returns(returns, weights)

        # Expected: 0.5*BTC + 0.5*ETH
        expected = pd.Series([0.015, -0.015, 0.025])
        pd.testing.assert_series_equal(port_ret, expected, check_names=False)

    def test_portfolio_returns_unequal_weights(self):
        """Portfolio Returns mit ungleichen Weights"""
        returns = pd.DataFrame({"BTC": [0.01, -0.02], "ETH": [0.02, -0.01]})
        weights = {"BTC": 0.6, "ETH": 0.4}

        port_ret = portfolio_returns(returns, weights)

        # Expected: 0.6*BTC + 0.4*ETH
        expected = pd.Series([0.6 * 0.01 + 0.4 * 0.02, 0.6 * (-0.02) + 0.4 * (-0.01)])
        pd.testing.assert_series_equal(port_ret, expected, check_names=False)

    def test_portfolio_returns_empty_inputs(self):
        """Leere Inputs -> leere Series"""
        returns = pd.DataFrame()
        weights = {}
        port_ret = portfolio_returns(returns, weights)
        assert port_ret.empty

    def test_portfolio_returns_missing_asset(self):
        """Fehlende Assets in weights werden ignoriert"""
        returns = pd.DataFrame({"BTC": [0.01, -0.02], "ETH": [0.02, -0.01]})
        weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}  # SOL nicht in returns

        port_ret = portfolio_returns(returns, weights)

        # Normiert auf BTC+ETH: 0.5/(0.5+0.3)*BTC + 0.3/(0.5+0.3)*ETH
        # = 0.625*BTC + 0.375*ETH
        expected = pd.Series([0.625 * 0.01 + 0.375 * 0.02, 0.625 * (-0.02) + 0.375 * (-0.01)])
        pd.testing.assert_series_equal(port_ret, expected, check_names=False, atol=1e-6)

    def test_portfolio_returns_weights_sum_not_one(self):
        """Weights werden normiert, auch wenn Sum != 1"""
        returns = pd.DataFrame({"BTC": [0.01], "ETH": [0.02]})
        weights = {"BTC": 2.0, "ETH": 3.0}  # Sum = 5.0

        port_ret = portfolio_returns(returns, weights)

        # Normiert: 2/5*BTC + 3/5*ETH = 0.4*0.01 + 0.6*0.02 = 0.016
        expected = pd.Series([0.016])
        pd.testing.assert_series_equal(port_ret, expected, check_names=False)

