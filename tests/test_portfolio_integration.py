# tests/test_portfolio_integration.py
"""
Integration Tests für Portfolio Strategy Layer mit BacktestEngine (Phase 26)
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.portfolio import (
    PortfolioConfig,
    PortfolioContext,
    make_portfolio_strategy,
    EqualWeightPortfolioStrategy,
    FixedWeightsPortfolioStrategy,
    VolTargetPortfolioStrategy,
)


def create_test_ohlcv_data(
    n_bars: int = 100,
    start_price: float = 100.0,
    volatility: float = 0.02,
    trend: float = 0.0001,
    seed: int = 42,
) -> pd.DataFrame:
    """Erstellt synthetische OHLCV-Daten für Tests."""
    np.random.seed(seed)

    dates = pd.date_range(start="2024-01-01", periods=n_bars, freq="1h")
    returns = np.random.normal(trend, volatility, n_bars)
    prices = start_price * np.cumprod(1 + returns)

    df = pd.DataFrame({
        "open": prices * (1 + np.random.uniform(-0.005, 0.005, n_bars)),
        "high": prices * (1 + np.abs(np.random.normal(0, 0.01, n_bars))),
        "low": prices * (1 - np.abs(np.random.normal(0, 0.01, n_bars))),
        "close": prices,
        "volume": np.random.uniform(1000, 10000, n_bars),
    }, index=dates)

    return df


class TestMakePortfolioStrategy:
    """Tests für die Factory-Funktion."""

    def test_make_equal_weight(self):
        """Test: Erstellt EqualWeightPortfolioStrategy."""
        config = PortfolioConfig(enabled=True, name="equal_weight")
        strategy = make_portfolio_strategy(config)

        assert strategy is not None
        assert isinstance(strategy, EqualWeightPortfolioStrategy)

    def test_make_fixed_weights(self):
        """Test: Erstellt FixedWeightsPortfolioStrategy."""
        config = PortfolioConfig(
            enabled=True,
            name="fixed_weights",
            fixed_weights={"BTC/EUR": 0.5, "ETH/EUR": 0.5},
        )
        strategy = make_portfolio_strategy(config)

        assert strategy is not None
        assert isinstance(strategy, FixedWeightsPortfolioStrategy)

    def test_make_vol_target(self):
        """Test: Erstellt VolTargetPortfolioStrategy."""
        config = PortfolioConfig(enabled=True, name="vol_target")
        strategy = make_portfolio_strategy(config)

        assert strategy is not None
        assert isinstance(strategy, VolTargetPortfolioStrategy)

    def test_make_disabled_returns_none(self):
        """Test: Deaktivierte Config → None."""
        config = PortfolioConfig(enabled=False, name="equal_weight")
        strategy = make_portfolio_strategy(config)

        assert strategy is None

    def test_make_unknown_strategy_raises(self):
        """Test: Unbekannte Strategie → ValueError."""
        # Direkt instanziieren um Validierung zu umgehen
        config = PortfolioConfig.__new__(PortfolioConfig)
        config.enabled = True
        config.name = "unknown_strategy"
        config.symbols = None
        config.fixed_weights = None
        config.rebalance_frequency = "1D"
        config.vol_lookback = 20
        config.vol_target = 0.15
        config.max_single_weight = 0.5
        config.min_weight = 0.01
        config.normalize_weights = True

        with pytest.raises(ValueError, match="Unbekannte Portfolio-Strategie"):
            make_portfolio_strategy(config)


class TestPortfolioConfigFromPeakConfig:
    """Tests für Config-Loading."""

    def test_config_from_dict(self):
        """Test: Config aus Dict erstellen."""
        data = {
            "enabled": True,
            "name": "vol_target",
            "symbols": ["BTC/EUR", "ETH/EUR"],
            "vol_lookback": 30,
            "max_single_weight": 0.4,
        }

        config = PortfolioConfig.from_dict(data)

        assert config.enabled is True
        assert config.name == "vol_target"
        assert config.symbols == ["BTC/EUR", "ETH/EUR"]
        assert config.vol_lookback == 30
        assert config.max_single_weight == 0.4

    def test_config_to_dict(self):
        """Test: Config zu Dict konvertieren."""
        config = PortfolioConfig(
            enabled=True,
            name="fixed_weights",
            fixed_weights={"BTC/EUR": 0.6, "ETH/EUR": 0.4},
        )

        data = config.to_dict()

        assert data["enabled"] is True
        assert data["name"] == "fixed_weights"
        assert data["fixed_weights"] == {"BTC/EUR": 0.6, "ETH/EUR": 0.4}


class TestPortfolioContext:
    """Tests für PortfolioContext."""

    def test_context_weight_calculation(self):
        """Test: Automatische Gewichtsberechnung aus Positionen."""
        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR", "ETH/EUR"],
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
            current_positions={"BTC/EUR": 0.1, "ETH/EUR": 1.0},  # 5000 + 3000
            equity=8000.0,
        )

        # Gewichte werden in __post_init__ berechnet
        assert context.current_weights is not None
        assert abs(context.current_weights["BTC/EUR"] - 5000/8000) < 0.001
        assert abs(context.current_weights["ETH/EUR"] - 3000/8000) < 0.001

    def test_context_helper_methods(self):
        """Test: Helper-Methoden."""
        context = PortfolioContext(
            timestamp=pd.Timestamp("2024-01-01"),
            symbols=["BTC/EUR"],
            prices={"BTC/EUR": 50000.0},
            current_positions={"BTC/EUR": 0.1},
            strategy_signals={"BTC/EUR": 1.0},
            equity=5000.0,
        )

        assert context.get_price("BTC/EUR") == 50000.0
        assert context.get_price("ETH/EUR") == 0.0  # Fallback
        assert context.get_position("BTC/EUR") == 0.1
        assert context.get_signal("BTC/EUR") == 1.0
        assert context.get_signal("ETH/EUR") == 0.0  # Fallback


class TestPortfolioStrategyWithData:
    """Integration Tests mit simulierten Daten."""

    def test_equal_weight_with_ohlcv(self):
        """Test: Equal-Weight mit OHLCV-Daten."""
        # Simulierte Daten für 2 Symbole
        btc_data = create_test_ohlcv_data(n_bars=100, start_price=50000, seed=1)
        eth_data = create_test_ohlcv_data(n_bars=100, start_price=3000, seed=2)

        config = PortfolioConfig(enabled=True, name="equal_weight")
        strategy = make_portfolio_strategy(config)

        context = PortfolioContext(
            timestamp=btc_data.index[-1],
            symbols=["BTC/EUR", "ETH/EUR"],
            prices={
                "BTC/EUR": float(btc_data.iloc[-1]["close"]),
                "ETH/EUR": float(eth_data.iloc[-1]["close"]),
            },
            current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0},
            equity=10000.0,
        )

        weights = strategy.generate_target_weights(context)

        assert len(weights) == 2
        assert abs(weights["BTC/EUR"] - 0.5) < 0.01
        assert abs(weights["ETH/EUR"] - 0.5) < 0.01

    def test_vol_target_with_ohlcv(self):
        """Test: Vol-Target mit OHLCV-Daten."""
        # BTC: höhere Volatilität
        btc_data = create_test_ohlcv_data(n_bars=100, volatility=0.03, seed=1)
        # ETH: niedrigere Volatilität
        eth_data = create_test_ohlcv_data(n_bars=100, volatility=0.01, seed=2)

        # Returns berechnen
        btc_returns = btc_data["close"].pct_change().dropna()
        eth_returns = eth_data["close"].pct_change().dropna()
        returns_history = pd.DataFrame({
            "BTC/EUR": btc_returns.values,
            "ETH/EUR": eth_returns.values,
        })

        config = PortfolioConfig(
            enabled=True,
            name="vol_target",
            vol_lookback=20,
        )
        strategy = make_portfolio_strategy(config)

        context = PortfolioContext(
            timestamp=btc_data.index[-1],
            symbols=["BTC/EUR", "ETH/EUR"],
            prices={
                "BTC/EUR": float(btc_data.iloc[-1]["close"]),
                "ETH/EUR": float(eth_data.iloc[-1]["close"]),
            },
            current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0},
            returns_history=returns_history,
            equity=10000.0,
        )

        weights = strategy.generate_target_weights(context)

        # ETH sollte höheres Gewicht haben (niedrigere Vol)
        assert weights["ETH/EUR"] > weights["BTC/EUR"]

    def test_weight_changes_over_time(self):
        """Test: Gewichte ändern sich bei Vol-Target über Zeit."""
        config = PortfolioConfig(enabled=True, name="vol_target", vol_lookback=10)
        strategy = make_portfolio_strategy(config)

        weights_over_time = []

        # Simuliere 50 Bars
        for i in range(20, 50):
            # Dynamische Volatilitäten (BTC wird volatiler)
            btc_vol = 0.02 + 0.001 * i
            eth_vol = 0.02

            returns = pd.DataFrame({
                "BTC/EUR": np.random.normal(0, btc_vol, i),
                "ETH/EUR": np.random.normal(0, eth_vol, i),
            })

            context = PortfolioContext(
                timestamp=pd.Timestamp("2024-01-01") + pd.Timedelta(hours=i),
                symbols=["BTC/EUR", "ETH/EUR"],
                prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
                current_positions={"BTC/EUR": 0.0, "ETH/EUR": 0.0},
                returns_history=returns,
                equity=10000.0,
            )

            weights = strategy.generate_target_weights(context)
            weights_over_time.append(weights.copy())

        # Am Anfang sollten die Gewichte ähnlicher sein als am Ende
        # (weil BTC-Vol steigt)
        first_diff = abs(weights_over_time[0]["BTC/EUR"] - weights_over_time[0]["ETH/EUR"])
        last_diff = abs(weights_over_time[-1]["BTC/EUR"] - weights_over_time[-1]["ETH/EUR"])

        assert last_diff > first_diff  # Gewichte divergieren
