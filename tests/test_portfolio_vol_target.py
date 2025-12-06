# tests/test_portfolio_vol_target.py
"""
Tests für VolTargetPortfolioStrategy (Phase 26)
"""

import pytest
import pandas as pd
import numpy as np

from src.portfolio import (
    VolTargetPortfolioStrategy,
    PortfolioConfig,
    PortfolioContext,
)


@pytest.fixture
def vol_target_config():
    """Config für Vol-Target-Strategie."""
    return PortfolioConfig(
        enabled=True,
        name="vol_target",
        vol_lookback=20,
        vol_target=0.15,
        max_single_weight=0.6,
        min_weight=0.01,
        normalize_weights=True,
    )


def create_returns_history(symbols: list, n_bars: int, vols: dict) -> pd.DataFrame:
    """Erstellt synthetische Returns mit gegebenen Volatilitäten."""
    np.random.seed(42)
    returns = {}
    for symbol in symbols:
        vol = vols.get(symbol, 0.02)
        returns[symbol] = np.random.normal(0, vol, n_bars)
    return pd.DataFrame(returns)


class TestVolTargetPortfolioStrategy:
    """Tests für Vol-Target-Strategie."""

    def test_vol_target_inverse_weighting(self, vol_target_config):
        """Test: Niedrigere Vol → höheres Gewicht."""
        # Erstelle Returns: BTC hat höhere Vol als ETH
        vols = {"BTC/EUR": 0.03, "ETH/EUR": 0.01}  # BTC 3x so volatil
        returns_history = create_returns_history(
            ["BTC/EUR", "ETH/EUR"],
            n_bars=50,
            vols=vols,
        )

        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR", "ETH/EUR"],
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
            current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0},
            returns_history=returns_history,
            equity=10000.0,
        )

        strategy = VolTargetPortfolioStrategy(vol_target_config)
        weights = strategy.generate_target_weights(context)

        # ETH sollte höheres Gewicht haben (niedrigere Vol)
        assert weights["ETH/EUR"] > weights["BTC/EUR"]

        # Summe sollte 1.0 sein
        assert abs(sum(weights.values()) - 1.0) < 0.001

    def test_vol_target_equal_vol_equal_weights(self, vol_target_config):
        """Test: Gleiche Vol → gleiche Gewichte."""
        # Bei gleichen Volatilitäten aus Context sollten Gewichte gleich sein
        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR", "ETH/EUR"],
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
            current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0},
            volatilities={"BTC/EUR": 0.20, "ETH/EUR": 0.20},  # Exakt gleiche Vol
            equity=10000.0,
        )

        strategy = VolTargetPortfolioStrategy(vol_target_config)
        weights = strategy.generate_target_weights(context)

        # Gewichte sollten exakt gleich sein
        assert abs(weights["BTC/EUR"] - weights["ETH/EUR"]) < 0.001

    def test_vol_target_no_returns_fallback(self, vol_target_config):
        """Test: Ohne Returns → Fallback auf Equal-Weight."""
        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR", "ETH/EUR"],
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
            current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0},
            returns_history=None,  # Keine Returns verfügbar
            equity=10000.0,
        )

        strategy = VolTargetPortfolioStrategy(vol_target_config)
        weights = strategy.generate_target_weights(context)

        # Fallback auf Equal-Weight → je 50%
        assert abs(weights["BTC/EUR"] - 0.5) < 0.01
        assert abs(weights["ETH/EUR"] - 0.5) < 0.01

    def test_vol_target_insufficient_returns_fallback(self, vol_target_config):
        """Test: Zu wenig Returns → Fallback auf Equal-Weight."""
        # Nur 10 Returns, aber vol_lookback=20
        returns_history = create_returns_history(
            ["BTC/EUR", "ETH/EUR"],
            n_bars=10,  # < vol_lookback
            vols={"BTC/EUR": 0.02, "ETH/EUR": 0.02},
        )

        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR", "ETH/EUR"],
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
            current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0},
            returns_history=returns_history,
            equity=10000.0,
        )

        strategy = VolTargetPortfolioStrategy(vol_target_config)
        weights = strategy.generate_target_weights(context)

        # Fallback auf Equal-Weight
        assert abs(weights["BTC/EUR"] - 0.5) < 0.01
        assert abs(weights["ETH/EUR"] - 0.5) < 0.01

    def test_vol_target_volatilities_from_context(self, vol_target_config):
        """Test: Volatilitäten aus Context verwenden."""
        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR", "ETH/EUR"],
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
            current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0},
            volatilities={"BTC/EUR": 0.30, "ETH/EUR": 0.15},  # BTC 2x so volatil
            equity=10000.0,
        )

        strategy = VolTargetPortfolioStrategy(vol_target_config)
        weights = strategy.generate_target_weights(context)

        # ETH sollte höheres Gewicht haben
        assert weights["ETH/EUR"] > weights["BTC/EUR"]

    def test_vol_target_three_symbols(self, vol_target_config):
        """Test: 3 Symbole mit unterschiedlicher Vol."""
        vols = {
            "BTC/EUR": 0.03,  # Höchste Vol
            "ETH/EUR": 0.02,  # Mittlere Vol
            "LTC/EUR": 0.01,  # Niedrigste Vol
        }
        returns_history = create_returns_history(
            ["BTC/EUR", "ETH/EUR", "LTC/EUR"],
            n_bars=50,
            vols=vols,
        )

        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR", "ETH/EUR", "LTC/EUR"],
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0, "LTC/EUR": 100.0},
            current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0, "LTC/EUR": 0.0},
            returns_history=returns_history,
            equity=10000.0,
        )

        strategy = VolTargetPortfolioStrategy(vol_target_config)
        weights = strategy.generate_target_weights(context)

        # Reihenfolge: LTC > ETH > BTC (nach Gewicht)
        assert weights["LTC/EUR"] > weights["ETH/EUR"]
        assert weights["ETH/EUR"] > weights["BTC/EUR"]

    def test_compute_portfolio_vol(self, vol_target_config):
        """Test: Portfolio-Volatilitäts-Berechnung."""
        strategy = VolTargetPortfolioStrategy(vol_target_config)

        weights = {"BTC/EUR": 0.5, "ETH/EUR": 0.5}
        volatilities = {"BTC/EUR": 0.20, "ETH/EUR": 0.10}

        # Ohne Korrelationsmatrix (Annahme: unkorreliert)
        portfolio_vol = strategy.compute_portfolio_vol(weights, volatilities)

        # Erwartete Vol (unkorreliert): sqrt(0.5^2 * 0.2^2 + 0.5^2 * 0.1^2)
        expected = np.sqrt(0.25 * 0.04 + 0.25 * 0.01)
        assert abs(portfolio_vol - expected) < 0.01
