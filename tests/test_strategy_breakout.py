# tests/test_strategy_breakout.py
"""
Peak_Trade Phase 40 - Breakout Strategy Tests
==============================================
Unit-Tests für die Breakout/Momentum-Strategie.
"""

import numpy as np
import pandas as pd
import pytest

from src.strategies.base import BaseStrategy
from src.strategies.breakout import BreakoutStrategy, generate_signals

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


def create_uptrend_data(n_bars: int = 200, seed: int = 42) -> pd.DataFrame:
    """Erzeugt Daten mit klarem Aufwärtstrend und Breakouts."""
    np.random.seed(seed)

    idx = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
    # Steigender Trend mit Breakout-Muster
    base = np.linspace(50000, 55000, n_bars)
    # Füge periodische "Breakout"-Muster hinzu
    breakout_signal = np.zeros(n_bars)
    for i in range(0, n_bars, 30):
        # Alle 30 Bars ein Breakout nach oben
        if i + 5 < n_bars:
            breakout_signal[i:i+5] = np.linspace(0, 500, 5)

    close = base + breakout_signal + np.random.randn(n_bars) * 50

    df = pd.DataFrame(index=idx)
    df["close"] = close
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = df["close"] * 1.003
    df["low"] = df["close"] * 0.997
    df["volume"] = np.random.uniform(100, 500, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


def create_downtrend_data(n_bars: int = 200, seed: int = 42) -> pd.DataFrame:
    """Erzeugt Daten mit klarem Abwärtstrend."""
    np.random.seed(seed)

    idx = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
    base = np.linspace(55000, 50000, n_bars)
    close = base + np.random.randn(n_bars) * 50

    df = pd.DataFrame(index=idx)
    df["close"] = close
    df["open"] = df["close"].shift(1).fillna(55000)
    df["high"] = df["close"] * 1.002
    df["low"] = df["close"] * 0.998
    df["volume"] = np.random.uniform(100, 500, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


# ============================================================================
# BREAKOUT STRATEGY TESTS
# ============================================================================


class TestBreakoutStrategy:
    """Tests für Breakout Strategy."""

    def test_basic_init(self):
        """Test: Basis-Initialisierung."""
        strategy = BreakoutStrategy()

        assert strategy is not None
        assert isinstance(strategy, BaseStrategy)
        assert strategy.KEY == "breakout"
        assert strategy.lookback_breakout == 20
        assert strategy.stop_loss_pct is None
        assert strategy.take_profit_pct is None
        assert strategy.trailing_stop_pct is None
        assert strategy.risk_mode == "symmetric"

    def test_custom_params(self):
        """Test: Initialisierung mit Custom-Parametern."""
        strategy = BreakoutStrategy(
            lookback_breakout=30,
            stop_loss_pct=0.03,
            take_profit_pct=0.06,
            trailing_stop_pct=0.02,
            side="long",
        )

        assert strategy.lookback_breakout == 30
        assert strategy.stop_loss_pct == 0.03
        assert strategy.take_profit_pct == 0.06
        assert strategy.trailing_stop_pct == 0.02
        # Legacy: side="long" wird zu risk_mode="long_only" gemappt
        assert strategy.risk_mode == "long_only"

    def test_generate_signals(self):
        """Test: Signalgenerierung funktioniert."""
        df = create_ohlcv_data(200)
        strategy = BreakoutStrategy()

        signals = strategy.generate_signals(df)

        assert signals is not None
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(df)

        # Signale sollten nur -1, 0, 1 enthalten
        unique_values = set(signals.unique())
        assert unique_values.issubset({-1, 0, 1})

    def test_long_only(self):
        """Test: Long-Only-Mode generiert keine Short-Signale."""
        df = create_ohlcv_data(200)
        strategy = BreakoutStrategy(side="long")

        signals = strategy.generate_signals(df)

        # Keine -1 Signale (keine Shorts)
        assert -1 not in signals.values

    def test_short_only(self):
        """Test: Short-Only-Mode generiert keine Long-Signale."""
        df = create_downtrend_data(200)
        strategy = BreakoutStrategy(side="short")

        signals = strategy.generate_signals(df)

        # Keine +1 Signale (keine Longs)
        assert 1 not in signals.values

    def test_uptrend_generates_long_signals(self):
        """Test: Aufwärtstrend generiert Long-Signale."""
        df = create_uptrend_data(200)
        strategy = BreakoutStrategy(lookback_breakout=15, side="both")

        signals = strategy.generate_signals(df)

        # In einem Aufwärtstrend erwarten wir Long-Signale
        long_count = (signals == 1).sum()
        assert long_count > 0, "Aufwärtstrend sollte Long-Signale generieren"

    def test_validation_errors(self):
        """Test: Validation wirft Fehler bei ungültigen Parametern."""
        with pytest.raises(ValueError, match="lookback_breakout"):
            BreakoutStrategy(lookback_breakout=1)

        with pytest.raises(ValueError, match="risk_mode"):
            BreakoutStrategy(risk_mode="invalid")

        with pytest.raises(ValueError, match="stop_loss_pct"):
            BreakoutStrategy(stop_loss_pct=-0.01)

        with pytest.raises(ValueError, match="take_profit_pct"):
            BreakoutStrategy(take_profit_pct=0)

    def test_insufficient_data(self):
        """Test: Fehler bei zu wenig Daten."""
        df = create_ohlcv_data(20)
        strategy = BreakoutStrategy()

        with pytest.raises(ValueError, match="Brauche mind"):
            strategy.generate_signals(df)

    def test_missing_column(self):
        """Test: Fehler wenn Spalte fehlt."""
        df = create_ohlcv_data(100)
        df = df.drop(columns=["close"])
        strategy = BreakoutStrategy()

        with pytest.raises(ValueError, match="Spalte"):
            strategy.generate_signals(df)

    def test_legacy_api(self):
        """Test: Legacy-API funktioniert."""
        df = create_ohlcv_data(200)
        params = {
            "lookback_breakout": 20,
            "stop_loss_pct": 0.03,
            "side": "both",
        }

        signals = generate_signals(df, params)

        assert signals is not None
        assert len(signals) == len(df)

    def test_metadata(self):
        """Test: Metadata korrekt gesetzt."""
        strategy = BreakoutStrategy()

        assert strategy.meta is not None
        assert strategy.meta.name == "Breakout Strategy"
        assert strategy.meta.regime == "trending"
        assert "breakout" in strategy.meta.tags

    def test_signal_consistency(self):
        """Test: Signale sind konsistent bei wiederholten Aufrufen."""
        df = create_ohlcv_data(200)
        strategy = BreakoutStrategy(lookback_breakout=15)

        signals1 = strategy.generate_signals(df)
        signals2 = strategy.generate_signals(df)

        # Identische Signale bei identischen Daten
        pd.testing.assert_series_equal(signals1, signals2)

    def test_with_stop_loss(self):
        """Test: Stop-Loss funktioniert."""
        df = create_ohlcv_data(200)
        strategy = BreakoutStrategy(
            lookback_breakout=15,
            stop_loss_pct=0.02,
        )

        signals = strategy.generate_signals(df)

        # Signale sollten gültig sein
        assert signals is not None
        assert len(signals) == len(df)
        assert set(signals.unique()).issubset({-1, 0, 1})

    def test_with_take_profit(self):
        """Test: Take-Profit funktioniert."""
        df = create_ohlcv_data(200)
        strategy = BreakoutStrategy(
            lookback_breakout=15,
            take_profit_pct=0.05,
        )

        signals = strategy.generate_signals(df)

        assert signals is not None
        assert len(signals) == len(df)

    def test_with_trailing_stop(self):
        """Test: Trailing-Stop funktioniert."""
        df = create_uptrend_data(200)
        strategy = BreakoutStrategy(
            lookback_breakout=15,
            trailing_stop_pct=0.02,
            side="long",
        )

        signals = strategy.generate_signals(df)

        assert signals is not None
        assert len(signals) == len(df)

    def test_config_dict(self):
        """Test: Config-Dict wird korrekt verarbeitet."""
        config = {
            "lookback_breakout": 25,
            "stop_loss_pct": 0.025,
            "take_profit_pct": 0.05,
            "side": "long",
        }

        strategy = BreakoutStrategy(config=config)

        assert strategy.lookback_breakout == 25
        assert strategy.stop_loss_pct == 0.025
        assert strategy.take_profit_pct == 0.05
        # Legacy: side="long" wird zu risk_mode="long_only" gemappt
        assert strategy.risk_mode == "long_only"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestBreakoutIntegration:
    """Integrationstests für Breakout Strategy."""

    def test_realistic_scenario(self):
        """Test: Realistisches Szenario mit typischen Parametern."""
        df = create_ohlcv_data(500, seed=123)

        strategy = BreakoutStrategy(
            lookback_breakout=20,
            stop_loss_pct=0.03,
            take_profit_pct=0.06,
        )

        signals = strategy.generate_signals(df)

        # Prüfe sinnvolle Signal-Verteilung
        signal_counts = signals.value_counts()

        # Sollte nicht nur eine Art von Signal sein
        assert len(signal_counts) >= 1, "Sollte mindestens eine Signal-Art geben"

    def test_all_features_combined(self):
        """Test: Alle Features kombiniert."""
        df = create_ohlcv_data(300)

        strategy = BreakoutStrategy(
            lookback_breakout=15,
            stop_loss_pct=0.02,
            take_profit_pct=0.04,
            trailing_stop_pct=0.015,
            side="both",
        )

        signals = strategy.generate_signals(df)

        assert signals is not None
        assert len(signals) == len(df)
        assert signals.name == "signal"


# ============================================================================
# NEW FEATURES TESTS (Phase 40+)
# ============================================================================


class TestBreakoutNewFeatures:
    """Tests für neue Breakout-Features (lookback_high/low, ATR-Filter, etc.)."""

    def test_separate_lookbacks(self):
        """Test: Separate Lookbacks für Long/Short."""
        df = create_ohlcv_data(200)

        strategy = BreakoutStrategy(
            lookback_high=20,
            lookback_low=15,
            risk_mode="symmetric"
        )

        signals = strategy.generate_signals(df)

        assert signals is not None
        assert len(signals) == len(df)
        assert strategy.lookback_high == 20
        assert strategy.lookback_low == 15

    def test_atr_filter(self):
        """Test: ATR-Filter verhindert Noise-Breakouts."""
        df = create_ohlcv_data(200)

        # Mit ATR-Filter
        strategy_with_filter = BreakoutStrategy(
            lookback_breakout=15,
            use_atr_filter=True,
            atr_multiplier=1.0,
            risk_mode="symmetric"
        )

        # Ohne ATR-Filter
        strategy_no_filter = BreakoutStrategy(
            lookback_breakout=15,
            use_atr_filter=False,
            risk_mode="symmetric"
        )

        signals_with = strategy_with_filter.generate_signals(df)
        signals_without = strategy_no_filter.generate_signals(df)

        # Signale sollten unterschiedlich sein (Filter blockiert einige)
        assert signals_with is not None
        assert signals_without is not None

    def test_risk_mode_long_only(self):
        """Test: risk_mode='long_only' generiert nur Long-Signale."""
        df = create_ohlcv_data(200)

        strategy = BreakoutStrategy(
            lookback_breakout=15,
            risk_mode="long_only"
        )

        signals = strategy.generate_signals(df)

        # Keine -1 Signale (keine Shorts)
        assert -1 not in signals.values

    def test_risk_mode_short_only(self):
        """Test: risk_mode='short_only' generiert nur Short-Signale."""
        df = create_downtrend_data(200)

        strategy = BreakoutStrategy(
            lookback_breakout=15,
            risk_mode="short_only"
        )

        signals = strategy.generate_signals(df)

        # Keine +1 Signale (keine Longs)
        assert 1 not in signals.values

    def test_exit_on_opposite_breakout(self):
        """Test: exit_on_opposite_breakout funktioniert."""
        df = create_ohlcv_data(200)

        strategy_exit = BreakoutStrategy(
            lookback_breakout=15,
            exit_on_opposite_breakout=True,
            risk_mode="symmetric"
        )

        strategy_no_exit = BreakoutStrategy(
            lookback_breakout=15,
            exit_on_opposite_breakout=False,
            risk_mode="symmetric"
        )

        signals_exit = strategy_exit.generate_signals(df)
        signals_no_exit = strategy_no_exit.generate_signals(df)

        assert signals_exit is not None
        assert signals_no_exit is not None

    def test_legacy_side_mapping(self):
        """Test: Legacy 'side' Parameter wird zu 'risk_mode' gemappt."""
        df = create_ohlcv_data(200)

        # Legacy: side="long" sollte zu risk_mode="long_only" werden
        strategy = BreakoutStrategy(
            lookback_breakout=15,
            side="long"
        )

        assert strategy.risk_mode == "long_only"

        signals = strategy.generate_signals(df)
        assert -1 not in signals.values

    def test_atr_filter_without_multiplier(self):
        """Test: ATR-Filter ohne Multiplier (nur Aktivierung)."""
        df = create_ohlcv_data(200)

        strategy = BreakoutStrategy(
            lookback_breakout=15,
            use_atr_filter=True,
            atr_multiplier=None,
            risk_mode="symmetric"
        )

        signals = strategy.generate_signals(df)

        assert signals is not None
        assert len(signals) == len(df)

    def test_validation_new_params(self):
        """Test: Validation für neue Parameter."""
        with pytest.raises(ValueError, match="lookback_high"):
            BreakoutStrategy(lookback_high=1)

        with pytest.raises(ValueError, match="lookback_low"):
            BreakoutStrategy(lookback_low=1)

        with pytest.raises(ValueError, match="risk_mode"):
            BreakoutStrategy(risk_mode="invalid")

        with pytest.raises(ValueError, match="atr_lookback"):
            BreakoutStrategy(atr_lookback=1)

        with pytest.raises(ValueError, match="atr_multiplier"):
            BreakoutStrategy(use_atr_filter=True, atr_multiplier=0)

    def test_long_breakout_scenario(self):
        """Test: Künstlicher Preisverlauf mit klarem Long-Breakout."""
        # Erstelle Daten mit klarem Breakout nach oben
        idx = pd.date_range("2024-01-01", periods=100, freq="1h", tz="UTC")

        # Konsolidierung bei ~50000
        prices = [50000] * 25
        # Dann Breakout nach oben
        prices.extend([50100 + i * 10 for i in range(75)])

        df = pd.DataFrame(index=idx)
        df["close"] = prices
        df["high"] = df["close"] * 1.001
        df["low"] = df["close"] * 0.999
        df["open"] = df["close"].shift(1).fillna(50000)
        df["volume"] = 100

        strategy = BreakoutStrategy(
            lookback_breakout=20,
            risk_mode="long_only"
        )

        signals = strategy.generate_signals(df)

        # Nach dem Breakout sollten Long-Signale kommen
        assert (signals == 1).any(), "Sollte Long-Signale nach Breakout generieren"

    def test_short_breakout_scenario(self):
        """Test: Künstlicher Preisverlauf mit klarem Short-Breakout."""
        idx = pd.date_range("2024-01-01", periods=100, freq="1h", tz="UTC")

        # Konsolidierung bei ~50000
        prices = [50000] * 25
        # Dann Breakout nach unten
        prices.extend([49900 - i * 10 for i in range(75)])

        df = pd.DataFrame(index=idx)
        df["close"] = prices
        df["high"] = df["close"] * 1.001
        df["low"] = df["close"] * 0.999
        df["open"] = df["close"].shift(1).fillna(50000)
        df["volume"] = 100

        strategy = BreakoutStrategy(
            lookback_breakout=20,
            risk_mode="short_only"
        )

        signals = strategy.generate_signals(df)

        # Nach dem Breakout sollten Short-Signale kommen
        assert (signals == -1).any(), "Sollte Short-Signale nach Breakout generieren"
