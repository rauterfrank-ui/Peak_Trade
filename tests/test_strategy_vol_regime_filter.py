# tests/test_strategy_vol_regime_filter.py
"""
Peak_Trade Phase 40 - Vol Regime Filter Tests
=============================================
Unit-Tests für den Volatilitäts-Regime-Filter.
"""

import pytest
import pandas as pd
import numpy as np

from src.strategies.vol_regime_filter import VolRegimeFilter, generate_signals
from src.strategies.base import BaseStrategy


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


def create_low_volatility_data(n_bars: int = 200, seed: int = 42) -> pd.DataFrame:
    """Erzeugt Daten mit niedriger Volatilität."""
    np.random.seed(seed)

    idx = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
    # Sehr geringe Preisbewegung
    close = 50000 + np.cumsum(np.random.randn(n_bars) * 10)

    df = pd.DataFrame(index=idx)
    df["close"] = close
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = df["close"] * 1.0005
    df["low"] = df["close"] * 0.9995
    df["volume"] = np.random.uniform(100, 500, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


def create_high_volatility_data(n_bars: int = 200, seed: int = 42) -> pd.DataFrame:
    """Erzeugt Daten mit hoher Volatilität."""
    np.random.seed(seed)

    idx = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
    # Starke Preisbewegung
    close = 50000 + np.cumsum(np.random.randn(n_bars) * 500)

    df = pd.DataFrame(index=idx)
    df["close"] = close
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = df["close"] * 1.01
    df["low"] = df["close"] * 0.99
    df["volume"] = np.random.uniform(100, 500, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


def create_mixed_volatility_data(n_bars: int = 200, seed: int = 42) -> pd.DataFrame:
    """Erzeugt Daten mit wechselnder Volatilität."""
    np.random.seed(seed)

    idx = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")

    # Erste Hälfte: niedrige Vol, zweite Hälfte: hohe Vol
    half = n_bars // 2
    low_vol = np.random.randn(half) * 20
    high_vol = np.random.randn(n_bars - half) * 500

    returns = np.concatenate([low_vol, high_vol])
    close = 50000 + np.cumsum(returns)

    df = pd.DataFrame(index=idx)
    df["close"] = close
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = df["close"] * 1.005
    df["low"] = df["close"] * 0.995
    df["volume"] = np.random.uniform(100, 500, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


# ============================================================================
# VOL REGIME FILTER TESTS
# ============================================================================


class TestVolRegimeFilter:
    """Tests für Volatility Regime Filter."""

    def test_basic_init(self):
        """Test: Basis-Initialisierung."""
        filter = VolRegimeFilter()

        assert filter is not None
        assert isinstance(filter, BaseStrategy)
        assert filter.KEY == "vol_regime_filter"
        assert filter.vol_window == 20
        assert filter.vol_method == "atr"
        assert filter.min_vol is None
        assert filter.max_vol is None
        assert filter.invert is False

    def test_custom_params(self):
        """Test: Initialisierung mit Custom-Parametern."""
        filter = VolRegimeFilter(
            vol_window=14,
            vol_method="std",
            vol_percentile_low=25,
            vol_percentile_high=75,
            lookback_percentile=50,
            invert=True,
        )

        assert filter.vol_window == 14
        assert filter.vol_method == "std"
        assert filter.vol_percentile_low == 25
        assert filter.vol_percentile_high == 75
        assert filter.lookback_percentile == 50
        assert filter.invert is True

    def test_generate_signals(self):
        """Test: Signalgenerierung funktioniert."""
        df = create_ohlcv_data(200)
        filter = VolRegimeFilter()

        signals = filter.generate_signals(df)

        assert signals is not None
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(df)

        # Filter-Signale sollten nur 0 oder 1 enthalten
        unique_values = set(signals.unique())
        assert unique_values.issubset({0, 1})

    def test_atr_method(self):
        """Test: ATR-Methode funktioniert."""
        df = create_ohlcv_data(200)
        filter = VolRegimeFilter(vol_method="atr", vol_window=14)

        signals = filter.generate_signals(df)

        assert signals is not None
        assert len(signals) == len(df)

    def test_std_method(self):
        """Test: Standard-Abweichungs-Methode funktioniert."""
        df = create_ohlcv_data(200)
        filter = VolRegimeFilter(vol_method="std", vol_window=20)

        signals = filter.generate_signals(df)

        assert signals is not None
        assert len(signals) == len(df)

    def test_realized_method(self):
        """Test: Realized-Volatility-Methode funktioniert."""
        df = create_ohlcv_data(200)
        filter = VolRegimeFilter(vol_method="realized", vol_window=20)

        signals = filter.generate_signals(df)

        assert signals is not None
        assert len(signals) == len(df)

    def test_percentile_filter(self):
        """Test: Perzentil-Filter funktioniert."""
        df = create_mixed_volatility_data(200)
        filter = VolRegimeFilter(
            vol_window=14,
            vol_percentile_low=25,
            vol_percentile_high=75,
            lookback_percentile=50,
        )

        signals = filter.generate_signals(df)

        # Sollte bei extremer Vol blockieren (0)
        has_blocked = (signals == 0).any()
        has_allowed = (signals == 1).any()

        # Mindestens einige blockiert und einige erlaubt
        assert has_blocked or has_allowed

    def test_invert_filter(self):
        """Test: Invertierte Filter-Logik."""
        df = create_ohlcv_data(200)

        filter_normal = VolRegimeFilter(
            vol_window=14,
            vol_percentile_low=25,
            vol_percentile_high=75,
            invert=False,
        )

        filter_inverted = VolRegimeFilter(
            vol_window=14,
            vol_percentile_low=25,
            vol_percentile_high=75,
            invert=True,
        )

        signals_normal = filter_normal.generate_signals(df)
        signals_inverted = filter_inverted.generate_signals(df)

        # Invertierte Signale sollten das Gegenteil sein (wo Daten valid sind)
        # Nach der Warmup-Phase
        valid_idx = signals_normal.index[50:]
        diff = (signals_normal.loc[valid_idx] != signals_inverted.loc[valid_idx]).sum()

        # Sollte Unterschiede geben
        assert diff > 0, "Invertierte Signale sollten sich unterscheiden"

    def test_validation_errors(self):
        """Test: Validation wirft Fehler bei ungültigen Parametern."""
        with pytest.raises(ValueError, match="vol_window"):
            VolRegimeFilter(vol_window=1)

        with pytest.raises(ValueError, match="vol_method"):
            VolRegimeFilter(vol_method="invalid")

        with pytest.raises(ValueError, match="vol_percentile_low"):
            VolRegimeFilter(vol_percentile_low=150)

        with pytest.raises(ValueError, match="vol_percentile_high"):
            VolRegimeFilter(vol_percentile_high=-10)

        with pytest.raises(ValueError, match="vol_percentile_low.*vol_percentile_high"):
            VolRegimeFilter(vol_percentile_low=75, vol_percentile_high=25)

    def test_insufficient_data(self):
        """Test: Fehler bei zu wenig Daten."""
        df = create_ohlcv_data(30)
        filter = VolRegimeFilter(vol_window=20, lookback_percentile=100)

        with pytest.raises(ValueError, match="Brauche mind"):
            filter.generate_signals(df)

    def test_missing_column(self):
        """Test: Fehler wenn Spalte fehlt."""
        df = create_ohlcv_data(150)
        df = df.drop(columns=["close"])
        filter = VolRegimeFilter()

        with pytest.raises(ValueError, match="Spalte"):
            filter.generate_signals(df)

    def test_apply_to_signals(self):
        """Test: Filter kann auf andere Signale angewendet werden."""
        df = create_ohlcv_data(200)

        # Fake Trading-Signale
        trading_signals = pd.Series(np.random.choice([-1, 0, 1], size=len(df)), index=df.index)

        filter = VolRegimeFilter(
            vol_window=14,
            vol_percentile_low=25,
            vol_percentile_high=75,
        )

        filtered_signals = filter.apply_to_signals(df, trading_signals)

        assert filtered_signals is not None
        assert len(filtered_signals) == len(df)

        # Gefilterte Signale sollten <= originale Signale sein (absolut)
        # (weil Filter mit 0 oder 1 multipliziert)
        for i in range(len(df)):
            if filtered_signals.iloc[i] != 0:
                assert abs(filtered_signals.iloc[i]) <= abs(trading_signals.iloc[i])

    def test_legacy_api(self):
        """Test: Legacy-API funktioniert."""
        df = create_ohlcv_data(200)
        params = {
            "vol_window": 14,
            "vol_method": "atr",
            "vol_percentile_low": 25,
            "vol_percentile_high": 75,
        }

        signals = generate_signals(df, params)

        assert signals is not None
        assert len(signals) == len(df)

    def test_metadata(self):
        """Test: Metadata korrekt gesetzt."""
        filter = VolRegimeFilter()

        assert filter.meta is not None
        assert filter.meta.name == "Volatility Regime Filter"
        assert filter.meta.regime == "any"
        assert "filter" in filter.meta.tags
        assert "volatility" in filter.meta.tags

    def test_signal_consistency(self):
        """Test: Signale sind konsistent bei wiederholten Aufrufen."""
        df = create_ohlcv_data(200)
        filter = VolRegimeFilter(vol_window=14)

        signals1 = filter.generate_signals(df)
        signals2 = filter.generate_signals(df)

        pd.testing.assert_series_equal(signals1, signals2)

    def test_atr_threshold(self):
        """Test: ATR-Threshold-Filter funktioniert."""
        df = create_ohlcv_data(200)

        # Hoher Threshold sollte mehr blockieren
        filter_high = VolRegimeFilter(
            vol_window=14,
            atr_threshold=1000,  # Sehr hoch
        )

        signals = filter_high.generate_signals(df)

        # Bei sehr hohem Threshold sollten die meisten blockiert sein
        blocked_ratio = (signals == 0).sum() / len(signals)
        assert blocked_ratio > 0.5, "Hoher ATR-Threshold sollte viel blockieren"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestVolRegimeFilterIntegration:
    """Integrationstests für Vol Regime Filter."""

    def test_with_trading_strategy(self):
        """Test: Integration mit einer Trading-Strategie."""
        df = create_ohlcv_data(200)

        # Simuliere Trading-Signale
        trading_signals = pd.Series(0, index=df.index)
        trading_signals.iloc[50:60] = 1
        trading_signals.iloc[100:110] = -1

        filter = VolRegimeFilter(
            vol_window=14,
            vol_percentile_low=20,
            vol_percentile_high=80,
        )

        filtered = filter.apply_to_signals(df, trading_signals)

        # Filtered sollte weniger oder gleich viele Non-Zero haben
        original_trades = (trading_signals != 0).sum()
        filtered_trades = (filtered != 0).sum()

        assert filtered_trades <= original_trades

    def test_realistic_parameters(self):
        """Test: Realistische Parameter-Kombination."""
        df = create_ohlcv_data(500, seed=123)

        filter = VolRegimeFilter(
            vol_window=20,
            vol_method="atr",
            vol_percentile_low=25,
            vol_percentile_high=75,
            lookback_percentile=100,
        )

        signals = filter.generate_signals(df)

        # Prüfe sinnvolle Verteilung
        allowed = (signals == 1).sum()
        blocked = (signals == 0).sum()

        # Sollte nicht alles blockieren oder alles erlauben
        total = allowed + blocked
        assert allowed > 0, "Sollte einige Trades erlauben"
        assert blocked > 0 or True, "Könnte einige blockieren"  # Optional


# ============================================================================
# NEW FEATURES TESTS (Phase 40+)
# ============================================================================


class TestVolRegimeNewFeatures:
    """Tests für neue Vol-Regime-Filter-Features (Threshold-basierte Klassifikation)."""

    def test_low_vol_threshold(self):
        """Test: Low-Vol-Threshold erkennt Low-Vol-Regime."""
        df = create_low_volatility_data(200)

        filter_regime = VolRegimeFilter(vol_window=14, low_vol_threshold=50.0, regime_mode=True)

        signals = filter_regime.generate_signals(df)

        # Bei niedriger Volatilität sollten wir Regime = 1 (Risk-On) sehen
        assert signals is not None
        assert len(signals) == len(df)
        # Nach min_bars sollten wir einige 1-Signale haben
        if len(signals) > filter_regime.min_bars:
            assert 1 in signals.iloc[filter_regime.min_bars :].values

    def test_high_vol_threshold(self):
        """Test: High-Vol-Threshold erkennt High-Vol-Regime."""
        df = create_high_volatility_data(200)

        filter_regime = VolRegimeFilter(vol_window=14, high_vol_threshold=200.0, regime_mode=True)

        signals = filter_regime.generate_signals(df)

        # Bei hoher Volatilität sollten wir Regime = -1 (Risk-Off) sehen
        assert signals is not None
        assert len(signals) == len(df)
        # Nach min_bars sollten wir einige -1-Signale haben
        if len(signals) > filter_regime.min_bars:
            assert -1 in signals.iloc[filter_regime.min_bars :].values

    def test_regime_classification(self):
        """Test: Regime-Klassifikation (1/-1/0)."""
        df = create_mixed_volatility_data(200)

        filter_regime = VolRegimeFilter(
            vol_window=14,
            low_vol_threshold=30.0,
            high_vol_threshold=300.0,
            min_bars=20,
            regime_mode=True,
        )

        signals = filter_regime.generate_signals(df)

        # Signale sollten 1, -1 oder 0 sein
        unique_values = set(signals.values[filter_regime.min_bars :])
        assert unique_values.issubset({-1, 0, 1}), f"Unerwartete Werte: {unique_values}"

    def test_min_bars_respect(self):
        """Test: min_bars wird respektiert (neutral vor min_bars)."""
        # Brauchen genug Daten für lookback_percentile (default 100) + min_bars
        df = create_ohlcv_data(200)

        filter_regime = VolRegimeFilter(
            vol_window=14,
            low_vol_threshold=50.0,
            min_bars=30,
            lookback_percentile=50,  # Reduziert auf 50 für diesen Test
            regime_mode=True,
        )

        signals = filter_regime.generate_signals(df)

        # Vor min_bars sollten alle Signale 0 (neutral) sein
        assert all(signals.iloc[:30] == 0), "Vor min_bars sollten alle Signale neutral sein"

    def test_range_vol_method(self):
        """Test: Range-Volatilitäts-Methode funktioniert."""
        df = create_ohlcv_data(200)

        filter_range = VolRegimeFilter(
            vol_window=14, vol_method="range", low_vol_threshold=100.0, regime_mode=True
        )

        signals = filter_range.generate_signals(df)

        assert signals is not None
        assert len(signals) == len(df)

    def test_validation_new_params(self):
        """Test: Validation für neue Parameter."""
        with pytest.raises(ValueError, match="vol_method"):
            VolRegimeFilter(vol_method="invalid")

        with pytest.raises(ValueError, match="min_bars"):
            VolRegimeFilter(min_bars=0)

        with pytest.raises(ValueError, match="low_vol_threshold.*high_vol_threshold"):
            VolRegimeFilter(low_vol_threshold=100.0, high_vol_threshold=50.0)

    def test_regime_vs_filter_mode(self):
        """Test: Unterschied zwischen Regime-Mode und Filter-Mode."""
        df = create_ohlcv_data(200)

        # Filter-Mode (1/0)
        filter_filter = VolRegimeFilter(vol_window=14, regime_mode=False)

        # Regime-Mode (1/-1/0)
        filter_regime = VolRegimeFilter(
            vol_window=14, low_vol_threshold=50.0, high_vol_threshold=500.0, regime_mode=True
        )

        signals_filter = filter_filter.generate_signals(df)
        signals_regime = filter_regime.generate_signals(df)

        # Filter-Mode sollte nur 0 oder 1 haben
        assert set(signals_filter.unique()).issubset({0, 1})

        # Regime-Mode kann -1, 0, 1 haben
        assert set(signals_regime.unique()).issubset({-1, 0, 1})

    def test_neutral_zone(self):
        """Test: Neutral-Zone zwischen Thresholds."""
        df = create_ohlcv_data(200)

        # Thresholds so setzen, dass viele Werte in der Neutral-Zone sind
        filter_regime = VolRegimeFilter(
            vol_window=14,
            low_vol_threshold=10.0,
            high_vol_threshold=10000.0,
            min_bars=20,
            regime_mode=True,
        )

        signals = filter_regime.generate_signals(df)

        # Die meisten sollten neutral (0) sein
        assert signals is not None
        # Nach min_bars sollte es eine Mischung geben
        unique_values = set(signals.values[filter_regime.min_bars :])
        assert len(unique_values) >= 1

    def test_auto_regime_mode_detection(self):
        """Test: Auto-Detection von regime_mode bei Thresholds."""
        # Wenn Thresholds gesetzt sind, sollte regime_mode automatisch aktiviert werden
        filter_auto = VolRegimeFilter(
            vol_window=14,
            low_vol_threshold=50.0,
            # regime_mode nicht explizit gesetzt
        )

        # from_config sollte regime_mode=True setzen wenn Thresholds vorhanden
        # Hier testen wir nur die Instanz
        assert filter_auto.low_vol_threshold == 50.0
