# tests/test_strategies_phase27.py
"""
Peak_Trade Phase 27 Strategy Research Track Tests
=================================================
Tests für die neuen Strategien:
- VolBreakoutStrategy
- MeanReversionChannelStrategy
- RsiReversionStrategy (erweitert)
"""

import numpy as np
import pandas as pd
import pytest

from src.strategies.base import BaseStrategy
from src.strategies.mean_reversion_channel import (
    MeanReversionChannelStrategy,
)
from src.strategies.mean_reversion_channel import (
    generate_signals as mean_reversion_channel_generate_signals,
)
from src.strategies.rsi_reversion import (
    RsiReversionStrategy,
)
from src.strategies.rsi_reversion import (
    generate_signals as rsi_reversion_generate_signals,
)
from src.strategies.vol_breakout import (
    VolBreakoutStrategy,
)
from src.strategies.vol_breakout import (
    generate_signals as vol_breakout_generate_signals,
)

# ============================================================================
# TEST FIXTURES
# ============================================================================


def create_ohlcv_data(n_bars: int = 200, seed: int = 42) -> pd.DataFrame:
    """Erzeugt synthetische OHLCV-Daten für Tests."""
    np.random.seed(seed)

    idx = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
    close = 50000 + np.cumsum(np.random.randn(n_bars) * 100)

    df = pd.DataFrame(index=idx)
    df["close"] = close
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = df[["open", "close"]].max(axis=1) * (1.0 + np.abs(np.random.randn(n_bars)) * 0.002)
    df["low"] = df[["open", "close"]].min(axis=1) * (1.0 - np.abs(np.random.randn(n_bars)) * 0.002)
    df["volume"] = np.random.uniform(100, 500, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


def create_trending_data(n_bars: int = 200, seed: int = 42) -> pd.DataFrame:
    """Erzeugt Daten mit klarem Aufwärtstrend."""
    np.random.seed(seed)

    idx = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
    # Starker Aufwärtstrend mit etwas Noise
    trend = np.linspace(50000, 60000, n_bars)
    noise = np.random.randn(n_bars) * 50
    close = trend + noise

    df = pd.DataFrame(index=idx)
    df["close"] = close
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = df["close"] * 1.002
    df["low"] = df["close"] * 0.998
    df["volume"] = np.random.uniform(100, 500, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


def create_ranging_data(n_bars: int = 200, seed: int = 42) -> pd.DataFrame:
    """Erzeugt Seitwärtsdaten (Ranging Market)."""
    np.random.seed(seed)

    idx = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
    # Oszillierende Bewegung
    close = 50000 + 500 * np.sin(np.linspace(0, 8 * np.pi, n_bars)) + np.random.randn(n_bars) * 100

    df = pd.DataFrame(index=idx)
    df["close"] = close
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = df["close"] * 1.002
    df["low"] = df["close"] * 0.998
    df["volume"] = np.random.uniform(100, 500, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


# ============================================================================
# VOLBREAKOUT STRATEGY TESTS
# ============================================================================


class TestVolBreakoutStrategy:
    """Tests für Volatility Breakout Strategy."""

    def test_vol_breakout_basic_init(self):
        """Test: Basis-Initialisierung."""
        strategy = VolBreakoutStrategy()

        assert strategy is not None
        assert isinstance(strategy, BaseStrategy)
        assert strategy.KEY == "vol_breakout"
        assert strategy.lookback_breakout == 20
        assert strategy.vol_window == 14
        assert strategy.vol_percentile == 50.0
        assert strategy.side == "both"

    def test_vol_breakout_custom_params(self):
        """Test: Initialisierung mit Custom-Parametern."""
        strategy = VolBreakoutStrategy(
            lookback_breakout=30,
            vol_window=20,
            vol_percentile=75.0,
            atr_multiple=2.0,
            side="long",
        )

        assert strategy.lookback_breakout == 30
        assert strategy.vol_window == 20
        assert strategy.vol_percentile == 75.0
        assert strategy.atr_multiple == 2.0
        assert strategy.side == "long"

    def test_vol_breakout_generate_signals(self):
        """Test: Signalgenerierung funktioniert."""
        df = create_ohlcv_data(200)
        strategy = VolBreakoutStrategy()

        signals = strategy.generate_signals(df)

        assert signals is not None
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(df)

        # Signale sollten nur -1, 0, 1 enthalten
        unique_values = set(signals.unique())
        assert unique_values.issubset({-1, 0, 1})

    def test_vol_breakout_long_only(self):
        """Test: Long-Only-Mode generiert keine Short-Signale."""
        df = create_ohlcv_data(200)
        strategy = VolBreakoutStrategy(side="long")

        signals = strategy.generate_signals(df)

        # Keine -1 Signale
        assert -1 not in signals.values

    def test_vol_breakout_short_only(self):
        """Test: Short-Only-Mode generiert keine Long-Signale."""
        df = create_ohlcv_data(200)
        strategy = VolBreakoutStrategy(side="short")

        signals = strategy.generate_signals(df)

        # Keine +1 Signale
        assert 1 not in signals.values

    def test_vol_breakout_validation_errors(self):
        """Test: Validation wirft Fehler bei ungültigen Parametern."""
        with pytest.raises(ValueError, match="lookback_breakout"):
            VolBreakoutStrategy(lookback_breakout=1)

        with pytest.raises(ValueError, match="vol_window"):
            VolBreakoutStrategy(vol_window=0)

        with pytest.raises(ValueError, match="vol_percentile"):
            VolBreakoutStrategy(vol_percentile=150)

        with pytest.raises(ValueError, match="side"):
            VolBreakoutStrategy(side="invalid")

    def test_vol_breakout_insufficient_data(self):
        """Test: Fehler bei zu wenig Daten."""
        df = create_ohlcv_data(20)
        strategy = VolBreakoutStrategy()

        with pytest.raises(ValueError, match="Brauche mind"):
            strategy.generate_signals(df)

    def test_vol_breakout_legacy_api(self):
        """Test: Legacy-API funktioniert."""
        df = create_ohlcv_data(200)
        params = {"lookback_breakout": 20, "vol_window": 14, "side": "both"}

        signals = vol_breakout_generate_signals(df, params)

        assert signals is not None
        assert len(signals) == len(df)

    def test_vol_breakout_metadata(self):
        """Test: Metadata korrekt gesetzt."""
        strategy = VolBreakoutStrategy()

        assert strategy.meta is not None
        assert strategy.meta.name == "Volatility Breakout"
        assert strategy.meta.regime == "breakout"
        assert "breakout" in strategy.meta.tags


# ============================================================================
# MEAN REVERSION CHANNEL STRATEGY TESTS
# ============================================================================


class TestMeanReversionChannelStrategy:
    """Tests für Mean Reversion Channel Strategy."""

    def test_mean_reversion_channel_basic_init(self):
        """Test: Basis-Initialisierung."""
        strategy = MeanReversionChannelStrategy()

        assert strategy is not None
        assert isinstance(strategy, BaseStrategy)
        assert strategy.KEY == "mean_reversion_channel"
        assert strategy.window == 20
        assert strategy.num_std == 2.0
        assert strategy.exit_at_mean is True

    def test_mean_reversion_channel_custom_params(self):
        """Test: Initialisierung mit Custom-Parametern."""
        strategy = MeanReversionChannelStrategy(
            window=30,
            num_std=2.5,
            exit_at_mean=False,
            max_holding_bars=100,
        )

        assert strategy.window == 30
        assert strategy.num_std == 2.5
        assert strategy.exit_at_mean is False
        assert strategy.max_holding_bars == 100

    def test_mean_reversion_channel_generate_signals(self):
        """Test: Signalgenerierung funktioniert."""
        df = create_ranging_data(200)
        strategy = MeanReversionChannelStrategy()

        signals = strategy.generate_signals(df)

        assert signals is not None
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(df)

        # Signale sollten nur -1, 0, 1 enthalten
        unique_values = set(signals.unique())
        assert unique_values.issubset({-1, 0, 1})

    def test_mean_reversion_channel_ranging_market(self):
        """Test: Strategie generiert Signale in Seitwärtsmarkt."""
        df = create_ranging_data(200)
        strategy = MeanReversionChannelStrategy(window=20, num_std=1.5)

        signals = strategy.generate_signals(df)

        # In einem Seitwärtsmarkt sollten sowohl Long als auch Short auftreten
        has_long = 1 in signals.values
        has_short = -1 in signals.values

        # Mindestens eine Richtung sollte Signale haben
        assert has_long or has_short

    def test_mean_reversion_channel_validation_errors(self):
        """Test: Validation wirft Fehler bei ungültigen Parametern."""
        with pytest.raises(ValueError, match="window"):
            MeanReversionChannelStrategy(window=1)

        with pytest.raises(ValueError, match="num_std"):
            MeanReversionChannelStrategy(num_std=0)

        with pytest.raises(ValueError, match="max_holding_bars"):
            MeanReversionChannelStrategy(max_holding_bars=0)

    def test_mean_reversion_channel_insufficient_data(self):
        """Test: Fehler bei zu wenig Daten."""
        df = create_ohlcv_data(20)
        strategy = MeanReversionChannelStrategy()

        with pytest.raises(ValueError, match="Brauche mind"):
            strategy.generate_signals(df)

    def test_mean_reversion_channel_missing_column(self):
        """Test: Fehler wenn Spalte fehlt."""
        df = create_ohlcv_data(100)
        df = df.drop(columns=["close"])
        strategy = MeanReversionChannelStrategy()

        with pytest.raises(ValueError, match="Spalte"):
            strategy.generate_signals(df)

    def test_mean_reversion_channel_legacy_api(self):
        """Test: Legacy-API funktioniert."""
        df = create_ohlcv_data(200)
        params = {"window": 20, "num_std": 2.0, "exit_at_mean": True}

        signals = mean_reversion_channel_generate_signals(df, params)

        assert signals is not None
        assert len(signals) == len(df)

    def test_mean_reversion_channel_metadata(self):
        """Test: Metadata korrekt gesetzt."""
        strategy = MeanReversionChannelStrategy()

        assert strategy.meta is not None
        assert strategy.meta.name == "Mean Reversion Channel"
        assert strategy.meta.regime == "ranging"
        assert "mean_reversion" in strategy.meta.tags


# ============================================================================
# RSI REVERSION STRATEGY TESTS (PHASE 27 ENHANCED)
# ============================================================================


class TestRsiReversionStrategy:
    """Tests für RSI Reversion Strategy (Phase 27 erweitert)."""

    def test_rsi_reversion_basic_init(self):
        """Test: Basis-Initialisierung."""
        strategy = RsiReversionStrategy()

        assert strategy is not None
        assert isinstance(strategy, BaseStrategy)
        assert strategy.KEY == "rsi_reversion"
        assert strategy.rsi_window == 14
        assert strategy.lower == 30.0
        assert strategy.upper == 70.0
        assert strategy.exit_lower == 50.0
        assert strategy.exit_upper == 50.0

    def test_rsi_reversion_custom_params(self):
        """Test: Initialisierung mit Custom-Parametern."""
        strategy = RsiReversionStrategy(
            rsi_window=21,
            lower=25.0,
            upper=75.0,
            exit_lower=45.0,
            exit_upper=55.0,
            use_trend_filter=True,
            trend_ma_window=100,
        )

        assert strategy.rsi_window == 21
        assert strategy.lower == 25.0
        assert strategy.upper == 75.0
        assert strategy.exit_lower == 45.0
        assert strategy.exit_upper == 55.0
        assert strategy.use_trend_filter is True
        assert strategy.trend_ma_window == 100

    def test_rsi_reversion_generate_signals(self):
        """Test: Signalgenerierung funktioniert."""
        df = create_ohlcv_data(200)
        strategy = RsiReversionStrategy()

        signals = strategy.generate_signals(df)

        assert signals is not None
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(df)

        # Signale sollten nur -1, 0, 1 enthalten
        unique_values = set(signals.unique())
        assert unique_values.issubset({-1, 0, 1})

    def test_rsi_reversion_wilder_smoothing(self):
        """Test: Wilder-Smoothing vs. Simple Rolling."""
        df = create_ohlcv_data(200)

        strategy_wilder = RsiReversionStrategy(use_wilder=True)
        strategy_simple = RsiReversionStrategy(use_wilder=False)

        signals_wilder = strategy_wilder.generate_signals(df)
        signals_simple = strategy_simple.generate_signals(df)

        # Beide sollten funktionieren
        assert len(signals_wilder) == len(df)
        assert len(signals_simple) == len(df)

        # Signale können unterschiedlich sein (Wilder ist smoother)
        # Aber beide sollten gültige Signale sein
        for signals in [signals_wilder, signals_simple]:
            assert set(signals.unique()).issubset({-1, 0, 1})

    def test_rsi_reversion_trend_filter(self):
        """Test: Trendfilter funktioniert."""
        df = create_trending_data(200)

        strategy_no_filter = RsiReversionStrategy(use_trend_filter=False)
        strategy_with_filter = RsiReversionStrategy(
            use_trend_filter=True,
            trend_ma_window=50,
        )

        signals_no_filter = strategy_no_filter.generate_signals(df)
        signals_with_filter = strategy_with_filter.generate_signals(df)

        # Beide sollten funktionieren
        assert len(signals_no_filter) == len(df)
        assert len(signals_with_filter) == len(df)

    def test_rsi_reversion_validation_errors(self):
        """Test: Validation wirft Fehler bei ungültigen Parametern."""
        with pytest.raises(ValueError, match="rsi_window"):
            RsiReversionStrategy(rsi_window=1)

        with pytest.raises(ValueError, match="lower.*upper"):
            RsiReversionStrategy(lower=70, upper=30)

        with pytest.raises(ValueError, match="trend_ma_window"):
            RsiReversionStrategy(trend_ma_window=1)

    def test_rsi_reversion_insufficient_data(self):
        """Test: Fehler bei zu wenig Daten."""
        df = create_ohlcv_data(10)
        strategy = RsiReversionStrategy()

        with pytest.raises(ValueError, match="Brauche mind"):
            strategy.generate_signals(df)

    def test_rsi_reversion_legacy_api(self):
        """Test: Legacy-API funktioniert."""
        df = create_ohlcv_data(200)
        params = {
            "rsi_window": 14,
            "lower": 30.0,
            "upper": 70.0,
            "use_wilder": True,
        }

        signals = rsi_reversion_generate_signals(df, params)

        assert signals is not None
        assert len(signals) == len(df)

    def test_rsi_reversion_legacy_api_with_old_param_names(self):
        """Test: Legacy-API mit alten Parameter-Namen."""
        df = create_ohlcv_data(200)
        params = {
            "rsi_period": 14,  # alter Name
            "oversold": 30.0,  # alter Name
            "overbought": 70.0,  # alter Name
        }

        signals = rsi_reversion_generate_signals(df, params)

        assert signals is not None
        assert len(signals) == len(df)

    def test_rsi_reversion_metadata(self):
        """Test: Metadata korrekt gesetzt."""
        strategy = RsiReversionStrategy()

        assert strategy.meta is not None
        assert strategy.meta.name == "RSI Reversion"
        assert strategy.meta.regime == "ranging"
        assert "rsi" in strategy.meta.tags
        assert "mean_reversion" in strategy.meta.tags


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestPhase27Integration:
    """Integrationstests für Phase 27 Strategien."""

    def test_all_strategies_same_api(self):
        """Test: Alle Strategien haben dieselbe API."""
        strategies = [
            VolBreakoutStrategy(),
            MeanReversionChannelStrategy(),
            RsiReversionStrategy(),
        ]

        df = create_ohlcv_data(200)

        for strategy in strategies:
            # Alle müssen BaseStrategy sein
            assert isinstance(strategy, BaseStrategy)

            # Alle müssen KEY haben
            assert hasattr(strategy, "KEY")

            # Alle müssen generate_signals implementieren
            signals = strategy.generate_signals(df)
            assert signals is not None
            assert len(signals) == len(df)

            # Alle müssen meta haben
            assert strategy.meta is not None

    def test_all_strategies_from_config(self):
        """Test: Alle Strategien können aus Config instanziiert werden."""
        strategies = [
            VolBreakoutStrategy(config={"lookback_breakout": 25, "vol_window": 10}),
            MeanReversionChannelStrategy(config={"window": 25, "num_std": 2.5}),
            RsiReversionStrategy(config={"rsi_window": 21, "lower": 25, "upper": 75}),
        ]

        df = create_ohlcv_data(200)

        for strategy in strategies:
            signals = strategy.generate_signals(df)
            assert signals is not None
            assert len(signals) == len(df)

    def test_strategy_signal_consistency(self):
        """Test: Signale sind konsistent bei wiederholten Aufrufen."""
        df = create_ohlcv_data(200)

        strategies = [
            VolBreakoutStrategy(),
            MeanReversionChannelStrategy(),
            RsiReversionStrategy(),
        ]

        for strategy in strategies:
            signals1 = strategy.generate_signals(df)
            signals2 = strategy.generate_signals(df)

            # Identische Signale bei identischen Daten
            pd.testing.assert_series_equal(signals1, signals2)
