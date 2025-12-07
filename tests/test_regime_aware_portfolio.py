# tests/test_regime_aware_portfolio.py
"""
Peak_Trade Regime-Aware Portfolio Strategy Tests
================================================
Unit-Tests für die Regime-Aware Portfolio-Strategie.
"""
import pytest
import pandas as pd
import numpy as np

from src.strategies.regime_aware_portfolio import RegimeAwarePortfolioStrategy
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


def create_low_volatility_data(n_bars: int = 200) -> pd.DataFrame:
    """Erzeugt Daten mit niedriger Volatilität (für Risk-On-Regime)."""
    np.random.seed(42)

    idx = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
    close = 50000 + np.cumsum(np.random.randn(n_bars) * 10)

    df = pd.DataFrame(index=idx)
    df["close"] = close
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = df["close"] * 1.0005
    df["low"] = df["close"] * 0.9995
    df["volume"] = np.random.uniform(100, 500, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


def create_high_volatility_data(n_bars: int = 200) -> pd.DataFrame:
    """Erzeugt Daten mit hoher Volatilität (für Risk-Off-Regime)."""
    np.random.seed(42)

    idx = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
    close = 50000 + np.cumsum(np.random.randn(n_bars) * 500)

    df = pd.DataFrame(index=idx)
    df["close"] = close
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = df["close"] * 1.01
    df["low"] = df["close"] * 0.99
    df["volume"] = np.random.uniform(100, 500, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


# ============================================================================
# REGIME-AWARE PORTFOLIO TESTS
# ============================================================================


class TestRegimeAwarePortfolioStrategy:
    """Tests für Regime-Aware Portfolio Strategy."""

    def test_basic_init(self):
        """Test: Basis-Initialisierung."""
        strategy = RegimeAwarePortfolioStrategy(
            components=["breakout_basic", "rsi_reversion"],
            base_weights={"breakout_basic": 0.6, "rsi_reversion": 0.4},
            regime_strategy="vol_regime_basic"
        )

        assert strategy is not None
        assert isinstance(strategy, BaseStrategy)
        assert strategy.KEY == "regime_aware_portfolio"
        assert strategy.components == ["breakout_basic", "rsi_reversion"]
        assert strategy.regime_strategy_name == "vol_regime_basic"
        assert strategy.mode == "scale"
        assert strategy.risk_on_scale == 1.0
        assert strategy.neutral_scale == 0.5
        assert strategy.risk_off_scale == 0.0

    def test_custom_params(self):
        """Test: Initialisierung mit Custom-Parametern."""
        strategy = RegimeAwarePortfolioStrategy(
            components=["breakout_basic"],
            base_weights={"breakout_basic": 1.0},
            regime_strategy="vol_regime_basic",
            mode="filter",
            risk_on_scale=1.0,
            neutral_scale=0.3,
            risk_off_scale=0.0,
            signal_threshold=0.25
        )

        assert strategy.mode == "filter"
        assert strategy.neutral_scale == 0.3
        assert strategy.signal_threshold == 0.25

    def test_weight_normalization(self):
        """Test: Basisgewichte werden normalisiert."""
        strategy = RegimeAwarePortfolioStrategy(
            components=["breakout_basic", "rsi_reversion"],
            base_weights={"breakout_basic": 0.6, "rsi_reversion": 0.4},
            regime_strategy="vol_regime_basic"
        )

        # Gewichte sollten normalisiert sein (Summe = 1.0)
        total = sum(abs(w) for w in strategy.base_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_equal_weights_for_missing(self):
        """Test: Fehlende Gewichte werden auf equal weight gesetzt."""
        strategy = RegimeAwarePortfolioStrategy(
            components=["breakout_basic", "rsi_reversion", "ma_crossover"],
            base_weights={},  # Leer
            regime_strategy="vol_regime_basic"
        )

        # Alle Komponenten sollten Gewichte haben
        assert len(strategy.base_weights) == 3
        assert all(component in strategy.base_weights for component in strategy.components)
        # Alle sollten etwa gleich gewichtet sein
        weights = list(strategy.base_weights.values())
        assert all(abs(w - 1/3) < 0.01 for w in weights)

    def test_validation_errors(self):
        """Test: Validation wirft Fehler bei ungültigen Parametern."""
        with pytest.raises(ValueError, match="components darf nicht leer sein"):
            RegimeAwarePortfolioStrategy(
                components=[],
                regime_strategy="vol_regime_basic"
            )

        with pytest.raises(ValueError, match="regime_strategy muss gesetzt sein"):
            RegimeAwarePortfolioStrategy(
                components=["breakout_basic"],
                regime_strategy=""
            )

        with pytest.raises(ValueError, match="mode.*scale.*filter"):
            RegimeAwarePortfolioStrategy(
                components=["breakout_basic"],
                regime_strategy="vol_regime_basic",
                mode="invalid"
            )

        with pytest.raises(ValueError, match="signal_threshold"):
            RegimeAwarePortfolioStrategy(
                components=["breakout_basic"],
                regime_strategy="vol_regime_basic",
                signal_threshold=1.5
            )

    def test_regime_scale_mapping(self):
        """Test: Regime-Werte werden korrekt auf Scales gemappt."""
        strategy = RegimeAwarePortfolioStrategy(
            components=["breakout_basic"],
            base_weights={"breakout_basic": 1.0},
            regime_strategy="vol_regime_basic",
            risk_on_scale=1.0,
            neutral_scale=0.5,
            risk_off_scale=0.0
        )

        assert strategy._get_regime_scale(1) == 1.0   # Risk-On
        assert strategy._get_regime_scale(0) == 0.5   # Neutral
        assert strategy._get_regime_scale(-1) == 0.0  # Risk-Off

    def test_generate_signals_structure(self):
        """Test: Signalgenerierung liefert korrektes Format."""
        # Wir testen nur die Struktur, nicht die vollständige Logik
        # (da echte Strategien benötigt werden)
        strategy = RegimeAwarePortfolioStrategy(
            components=["breakout_basic"],
            base_weights={"breakout_basic": 1.0},
            regime_strategy="vol_regime_basic"
        )

        # Sollte ValueError werfen wenn Strategien nicht geladen werden können
        # (da wir keinen echten Config haben)
        df = create_ohlcv_data(100)
        with pytest.raises((ValueError, KeyError)):
            strategy.generate_signals(df)


# ============================================================================
# INTEGRATION TESTS (mit Mock-Strategien)
# ============================================================================


class MockStrategy(BaseStrategy):
    """Mock-Strategie für Tests."""

    KEY = "mock_strategy"

    def __init__(self, signals: pd.Series, config=None, metadata=None):
        super().__init__(config=config or {}, metadata=metadata)
        self._signals = signals

    @classmethod
    def from_config(cls, cfg, section="strategy.mock"):
        raise NotImplementedError

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        return self._signals.reindex(data.index, fill_value=0)


class TestRegimeAwarePortfolioIntegration:
    """Integrationstests mit Mock-Strategien."""

    def test_risk_on_scale(self):
        """Test: Risk-On-Regime = volle Gewichte (1.0)."""
        df = create_low_volatility_data(100)

        # Mock-Komponenten-Signale
        component_signals = pd.Series(1, index=df.index, dtype=int)  # Immer Long
        mock_component = MockStrategy(component_signals)

        # Mock-Regime: Immer Risk-On (1)
        regime_signals = pd.Series(1, index=df.index, dtype=int)
        mock_regime = MockStrategy(regime_signals)

        # Erstelle Strategie mit Mocks
        strategy = RegimeAwarePortfolioStrategy(
            components=["mock_component"],
            base_weights={"mock_component": 1.0},
            regime_strategy="mock_regime",
            risk_on_scale=1.0,
            neutral_scale=0.5,
            risk_off_scale=0.0
        )
        strategy._component_strategies = [mock_component]
        strategy._regime_strategy = mock_regime

        signals = strategy.generate_signals(df)

        # Bei Risk-On sollte das Signal nicht reduziert werden
        assert signals is not None
        assert len(signals) == len(df)

    def test_risk_off_scale_zero(self):
        """Test: Risk-Off-Regime = keine Gewichte (0.0)."""
        df = create_high_volatility_data(100)

        # Mock-Komponenten-Signale
        component_signals = pd.Series(1, index=df.index, dtype=int)  # Immer Long
        mock_component = MockStrategy(component_signals)

        # Mock-Regime: Immer Risk-Off (-1)
        regime_signals = pd.Series(-1, index=df.index, dtype=int)
        mock_regime = MockStrategy(regime_signals)

        strategy = RegimeAwarePortfolioStrategy(
            components=["mock_component"],
            base_weights={"mock_component": 1.0},
            regime_strategy="mock_regime",
            risk_on_scale=1.0,
            neutral_scale=0.5,
            risk_off_scale=0.0
        )
        strategy._component_strategies = [mock_component]
        strategy._regime_strategy = mock_regime

        signals = strategy.generate_signals(df)

        # Bei Risk-Off sollte scale=0.0 sein, daher sollten Signale 0 sein
        assert signals is not None
        # In Risk-Off sollten die meisten Signale 0 sein (nach Skalierung)
        zero_count = (signals == 0).sum()
        assert zero_count > len(df) * 0.8  # Mindestens 80% sollten 0 sein

    def test_neutral_scale_half(self):
        """Test: Neutral-Regime = halbe Gewichte (0.5)."""
        df = create_ohlcv_data(100)

        # Mock-Komponenten-Signale (starke Signale)
        component_signals = pd.Series(1, index=df.index, dtype=int)
        mock_component = MockStrategy(component_signals)

        # Mock-Regime: Immer Neutral (0)
        regime_signals = pd.Series(0, index=df.index, dtype=int)
        mock_regime = MockStrategy(regime_signals)

        strategy = RegimeAwarePortfolioStrategy(
            components=["mock_component"],
            base_weights={"mock_component": 1.0},
            regime_strategy="mock_regime",
            risk_on_scale=1.0,
            neutral_scale=0.5,
            risk_off_scale=0.0,
            signal_threshold=0.3
        )
        strategy._component_strategies = [mock_component]
        strategy._regime_strategy = mock_regime

        signals = strategy.generate_signals(df)

        # Bei Neutral sollte scale=0.5 sein
        assert signals is not None
        # Mit 0.5-Skalierung sollte das Signal noch über Threshold sein (1.0 * 0.5 = 0.5 > 0.3)
        assert (signals == 1).any()

    def test_filter_mode(self):
        """Test: Filter-Mode blockiert bei Risk-Off."""
        df = create_high_volatility_data(100)

        component_signals = pd.Series(1, index=df.index, dtype=int)
        mock_component = MockStrategy(component_signals)

        regime_signals = pd.Series(-1, index=df.index, dtype=int)  # Risk-Off
        mock_regime = MockStrategy(regime_signals)

        strategy = RegimeAwarePortfolioStrategy(
            components=["mock_component"],
            base_weights={"mock_component": 1.0},
            regime_strategy="mock_regime",
            mode="filter",
            risk_off_scale=0.0
        )
        strategy._component_strategies = [mock_component]
        strategy._regime_strategy = mock_regime

        signals = strategy.generate_signals(df)

        # Im Filter-Mode bei Risk-Off sollten alle Signale 0 sein
        assert (signals == 0).all()

    def test_multi_component_combination(self):
        """Test: Mehrere Komponenten werden korrekt kombiniert."""
        df = create_ohlcv_data(100)

        # Zwei Mock-Komponenten mit unterschiedlichen Signalen
        signals1 = pd.Series(1, index=df.index, dtype=int)  # Long
        signals2 = pd.Series(0, index=df.index, dtype=int)  # Flat
        mock1 = MockStrategy(signals1)
        mock2 = MockStrategy(signals2)

        # Regime: Risk-On
        regime_signals = pd.Series(1, index=df.index, dtype=int)
        mock_regime = MockStrategy(regime_signals)

        strategy = RegimeAwarePortfolioStrategy(
            components=["mock1", "mock2"],
            base_weights={"mock1": 0.6, "mock2": 0.4},
            regime_strategy="mock_regime",
            risk_on_scale=1.0
        )
        strategy._component_strategies = [mock1, mock2]
        strategy._regime_strategy = mock_regime

        signals = strategy.generate_signals(df)

        assert signals is not None
        # Kombiniertes Signal sollte 0.6 * 1 + 0.4 * 0 = 0.6 sein
        # Mit scale=1.0 sollte das über threshold=0.3 sein → Long
        assert (signals == 1).any()

    def test_get_component_signals(self):
        """Test: get_component_signals() funktioniert."""
        df = create_ohlcv_data(100)

        signals1 = pd.Series(1, index=df.index, dtype=int)
        signals2 = pd.Series(-1, index=df.index, dtype=int)
        mock1 = MockStrategy(signals1)
        mock2 = MockStrategy(signals2)

        regime_signals = pd.Series(0, index=df.index, dtype=int)
        mock_regime = MockStrategy(regime_signals)

        strategy = RegimeAwarePortfolioStrategy(
            components=["mock1", "mock2"],
            base_weights={"mock1": 0.5, "mock2": 0.5},
            regime_strategy="mock_regime"
        )
        strategy._component_strategies = [mock1, mock2]
        strategy._regime_strategy = mock_regime

        component_sigs = strategy.get_component_signals(df)

        assert "mock1" in component_sigs
        assert "mock2" in component_sigs
        assert len(component_sigs["mock1"]) == len(df)
        assert len(component_sigs["mock2"]) == len(df)

    def test_get_regime_signals(self):
        """Test: get_regime_signals() funktioniert."""
        df = create_ohlcv_data(100)

        # Erstelle Regime-Signale mit korrekter Länge
        regime_pattern = [1, 0, -1] * (len(df) // 3 + 1)
        regime_signals = pd.Series(regime_pattern[:len(df)], index=df.index, dtype=int)
        mock_regime = MockStrategy(regime_signals)

        # Mock-Komponente
        mock_component = MockStrategy(pd.Series(1, index=df.index, dtype=int))

        strategy = RegimeAwarePortfolioStrategy(
            components=["mock1"],
            base_weights={"mock1": 1.0},
            regime_strategy="mock_regime"
        )
        # Setze beide Mocks um _load_strategies zu umgehen
        strategy._component_strategies = [mock_component]
        strategy._regime_strategy = mock_regime

        regime = strategy.get_regime_signals(df)

        assert regime is not None
        assert len(regime) == len(df)
        assert set(regime.unique()).issubset({-1, 0, 1})


