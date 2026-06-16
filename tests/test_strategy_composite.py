# tests/test_strategy_composite.py
"""
Peak_Trade Phase 40 - Composite Strategy Tests
==============================================
Unit-Tests für die Multi-Strategy Composite-Strategie.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

from src.strategies.composite import CompositeStrategy, generate_signals
from src.strategies.rsi_reversion import RsiReversionStrategy
from src.strategies.breakout import BreakoutStrategy
from src.strategies.vol_regime_filter import VolRegimeFilter
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


class MockStrategy(BaseStrategy):
    """Mock-Strategie für Tests mit kontrollierbaren Signalen."""

    KEY = "mock"

    def __init__(self, signals: Optional[pd.Series] = None, name: str = "mock"):
        super().__init__(config={"name": name})
        self._signals = signals
        self._name = name

    @property
    def key(self) -> str:
        return self._name

    @classmethod
    def from_config(cls, cfg, section: str = "strategy.mock"):
        """Dummy from_config für abstrakte Methode."""
        return cls()

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if self._signals is not None:
            return self._signals.reindex(data.index, fill_value=0)
        return pd.Series(0, index=data.index)


# ============================================================================
# COMPOSITE STRATEGY TESTS
# ============================================================================


class TestCompositeStrategy:
    """Tests für Composite Strategy."""

    def test_basic_init(self):
        """Test: Basis-Initialisierung."""
        strategy1 = RsiReversionStrategy()
        strategy2 = BreakoutStrategy()

        composite = CompositeStrategy(strategies=[strategy1, strategy2])

        assert composite is not None
        assert isinstance(composite, BaseStrategy)
        assert composite.KEY == "composite"
        assert len(composite.strategies) == 2
        assert len(composite.weights) == 2
        # Equal weights
        assert abs(composite.weights[0] - 0.5) < 0.01
        assert abs(composite.weights[1] - 0.5) < 0.01

    def test_init_with_tuples(self):
        """Test: Initialisierung mit (strategy, weight) Tupeln."""
        strategy1 = RsiReversionStrategy()
        strategy2 = BreakoutStrategy()

        composite = CompositeStrategy(
            strategies=[
                (strategy1, 0.6),
                (strategy2, 0.4),
            ]
        )

        assert len(composite.strategies) == 2
        assert abs(composite.weights[0] - 0.6) < 0.01
        assert abs(composite.weights[1] - 0.4) < 0.01

    def test_init_with_separate_weights(self):
        """Test: Initialisierung mit separater Weights-Liste."""
        strategy1 = RsiReversionStrategy()
        strategy2 = BreakoutStrategy()

        composite = CompositeStrategy(
            strategies=[strategy1, strategy2],
            weights=[0.7, 0.3],
        )

        assert abs(composite.weights[0] - 0.7) < 0.01
        assert abs(composite.weights[1] - 0.3) < 0.01

    def test_weights_normalization(self):
        """Test: Gewichte werden auf 1.0 normalisiert."""
        strategy1 = RsiReversionStrategy()
        strategy2 = BreakoutStrategy()

        composite = CompositeStrategy(
            strategies=[strategy1, strategy2],
            weights=[1.0, 1.0],  # Summe = 2.0
        )

        # Sollte normalisiert werden
        assert abs(sum(composite.weights) - 1.0) < 0.01

    def test_generate_signals_weighted(self):
        """Test: Weighted Aggregation funktioniert."""
        df = create_ohlcv_data(200)

        # Mock-Strategien mit bekannten Signalen
        signals1 = pd.Series(1, index=df.index)  # Immer Long
        signals2 = pd.Series(-1, index=df.index)  # Immer Short

        mock1 = MockStrategy(signals=signals1, name="mock1")
        mock2 = MockStrategy(signals=signals2, name="mock2")

        composite = CompositeStrategy(
            strategies=[mock1, mock2],
            weights=[0.6, 0.4],  # 0.6 * 1 + 0.4 * (-1) = 0.2
            aggregation="weighted",
            signal_threshold=0.3,
        )

        result = composite.generate_signals(df)

        # Weighted avg = 0.2, threshold = 0.3 → flat (0)
        assert (result == 0).all(), "Weighted avg 0.2 < threshold 0.3 → sollte flat sein"

    def test_generate_signals_voting(self):
        """Test: Voting Aggregation funktioniert."""
        df = create_ohlcv_data(200)

        # 3 Strategien: 2 Long, 1 Short → Mehrheit Long
        signals1 = pd.Series(1, index=df.index)
        signals2 = pd.Series(1, index=df.index)
        signals3 = pd.Series(-1, index=df.index)

        mock1 = MockStrategy(signals=signals1, name="mock1")
        mock2 = MockStrategy(signals=signals2, name="mock2")
        mock3 = MockStrategy(signals=signals3, name="mock3")

        composite = CompositeStrategy(
            strategies=[mock1, mock2, mock3],
            aggregation="voting",
        )

        result = composite.generate_signals(df)

        # Mehrheit Long → sollte 1 sein
        assert (result == 1).all(), "Mehrheit Long → Signal sollte 1 sein"

    def test_generate_signals_unanimous(self):
        """Test: Unanimous Aggregation funktioniert."""
        df = create_ohlcv_data(200)

        # Alle Long
        signals1 = pd.Series(1, index=df.index)
        signals2 = pd.Series(1, index=df.index)

        mock1 = MockStrategy(signals=signals1, name="mock1")
        mock2 = MockStrategy(signals=signals2, name="mock2")

        composite = CompositeStrategy(
            strategies=[mock1, mock2],
            aggregation="unanimous",
        )

        result = composite.generate_signals(df)

        # Alle übereinstimmend → sollte 1 sein
        assert (result == 1).all()

    def test_generate_signals_unanimous_no_consensus(self):
        """Test: Unanimous ohne Konsens gibt 0."""
        df = create_ohlcv_data(200)

        signals1 = pd.Series(1, index=df.index)
        signals2 = pd.Series(-1, index=df.index)

        mock1 = MockStrategy(signals=signals1, name="mock1")
        mock2 = MockStrategy(signals=signals2, name="mock2")

        composite = CompositeStrategy(
            strategies=[mock1, mock2],
            aggregation="unanimous",
        )

        result = composite.generate_signals(df)

        # Kein Konsens → sollte 0 sein
        assert (result == 0).all()

    def test_add_strategy(self):
        """Test: Strategie hinzufügen funktioniert."""
        strategy1 = RsiReversionStrategy()

        composite = CompositeStrategy(strategies=[strategy1])
        assert len(composite.strategies) == 1

        strategy2 = BreakoutStrategy()
        composite.add_strategy(strategy2)

        assert len(composite.strategies) == 2
        # Equal weights nach add
        assert abs(composite.weights[0] - 0.5) < 0.01
        assert abs(composite.weights[1] - 0.5) < 0.01

    def test_with_filter_strategy(self):
        """Test: Filter-Strategie funktioniert."""
        df = create_ohlcv_data(200)

        # Trading-Strategie immer Long
        signals_trading = pd.Series(1, index=df.index)
        mock_trading = MockStrategy(signals=signals_trading, name="trading")

        # Filter blockiert alles (immer 0)
        signals_filter = pd.Series(0, index=df.index)
        mock_filter = MockStrategy(signals=signals_filter, name="filter")

        composite = CompositeStrategy(
            strategies=[mock_trading],
            filter_strategy=mock_filter,
        )

        result = composite.generate_signals(df)

        # Filter blockiert alles → sollte 0 sein
        assert (result == 0).all()

    def test_with_real_strategies(self):
        """Test: Mit echten Strategien."""
        df = create_ohlcv_data(200)

        strategy1 = RsiReversionStrategy(rsi_window=14)
        strategy2 = BreakoutStrategy(lookback_breakout=15)

        composite = CompositeStrategy(
            strategies=[strategy1, strategy2],
            aggregation="weighted",
            signal_threshold=0.3,
        )

        result = composite.generate_signals(df)

        assert result is not None
        assert len(result) == len(df)
        assert set(result.unique()).issubset({-1, 0, 1})

    def test_validation_errors(self):
        """Test: Validation wirft Fehler."""
        strategy = RsiReversionStrategy()

        with pytest.raises(ValueError, match="aggregation"):
            CompositeStrategy(
                strategies=[strategy],
                aggregation="invalid",
            )

        with pytest.raises(ValueError, match="signal_threshold"):
            CompositeStrategy(
                strategies=[strategy],
                signal_threshold=1.5,
            )

    def test_no_strategies_error(self):
        """Test: Fehler wenn keine Strategien."""
        composite = CompositeStrategy(strategies=[])

        df = create_ohlcv_data(200)

        with pytest.raises(ValueError, match="Keine Strategien"):
            composite.generate_signals(df)

    def test_get_component_signals(self):
        """Test: Komponenten-Signale abrufen."""
        df = create_ohlcv_data(200)

        strategy1 = RsiReversionStrategy(rsi_window=14)
        strategy2 = BreakoutStrategy(lookback_breakout=15)

        composite = CompositeStrategy(
            strategies=[strategy1, strategy2],
        )

        component_signals = composite.get_component_signals(df)

        assert len(component_signals) == 2
        assert "rsi_reversion" in component_signals
        assert "breakout" in component_signals

        for name, signals in component_signals.items():
            assert len(signals) == len(df)

    def test_metadata(self):
        """Test: Metadata korrekt gesetzt."""
        strategy = RsiReversionStrategy()
        composite = CompositeStrategy(strategies=[strategy])

        assert composite.meta is not None
        assert composite.meta.name == "Composite Strategy"
        assert "composite" in composite.meta.tags

    def test_signal_consistency(self):
        """Test: Signale sind konsistent."""
        df = create_ohlcv_data(200)

        strategy1 = RsiReversionStrategy(rsi_window=14)
        strategy2 = BreakoutStrategy(lookback_breakout=15)

        composite = CompositeStrategy(
            strategies=[strategy1, strategy2],
            aggregation="weighted",
        )

        signals1 = composite.generate_signals(df)
        signals2 = composite.generate_signals(df)

        pd.testing.assert_series_equal(signals1, signals2)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestCompositeIntegration:
    """Integrationstests für Composite Strategy."""

    def test_with_vol_filter(self):
        """Test: Composite mit Vol-Regime-Filter."""
        df = create_ohlcv_data(200)

        rsi_strategy = RsiReversionStrategy(rsi_window=14)
        breakout_strategy = BreakoutStrategy(lookback_breakout=15)
        vol_filter = VolRegimeFilter(
            vol_window=14,
            vol_percentile_low=25,
            vol_percentile_high=75,
        )

        composite = CompositeStrategy(
            strategies=[rsi_strategy, breakout_strategy],
            filter_strategy=vol_filter,
            aggregation="voting",
        )

        result = composite.generate_signals(df)

        assert result is not None
        assert len(result) == len(df)

    def test_three_strategy_portfolio(self):
        """Test: Portfolio mit drei Strategien."""
        df = create_ohlcv_data(200)

        strategies = [
            (RsiReversionStrategy(rsi_window=14), 0.4),
            (BreakoutStrategy(lookback_breakout=15), 0.3),
            (BreakoutStrategy(lookback_breakout=20, side="long"), 0.3),
        ]

        composite = CompositeStrategy(
            strategies=strategies,
            aggregation="weighted",
            signal_threshold=0.25,
        )

        result = composite.generate_signals(df)

        assert result is not None
        assert len(result) == len(df)
        assert set(result.unique()).issubset({-1, 0, 1})

    def test_realistic_scenario(self):
        """Test: Realistisches Szenario."""
        df = create_ohlcv_data(500, seed=123)

        composite = CompositeStrategy(
            strategies=[
                RsiReversionStrategy(rsi_window=14, lower=25, upper=75),
                BreakoutStrategy(lookback_breakout=20, stop_loss_pct=0.02),
            ],
            weights=[0.5, 0.5],
            aggregation="weighted",
            signal_threshold=0.3,
        )

        result = composite.generate_signals(df)

        # Prüfe sinnvolle Signal-Verteilung
        signal_counts = result.value_counts()
        assert len(signal_counts) >= 1


# ============================================================================
# CompositeStrategy.from_config load_strategy() MIGRATION (offline, fail-closed)
# ============================================================================


class TestCompositeStrategyFromConfigLoadStrategyMigration:
    """Offline guards for canonical CompositeStrategy.from_config binding migration."""

    TARGET_MODULE = Path(__file__).resolve().parent.parent / "src/strategies/composite.py"
    FORBIDDEN_NAMES = ("create_strategy_from_config",)

    def _read_source(self) -> str:
        return self.TARGET_MODULE.read_text(encoding="utf-8")

    def _minimal_cfg(self, **composite_overrides: object):
        from unittest.mock import MagicMock

        raw: dict = {
            "environment": {"mode": "backtest"},
            "strategy": {
                "composite": {
                    "components": ["rsi_reversion", "breakout"],
                    "weights": [0.6, 0.4],
                    "aggregation": "weighted",
                    "signal_threshold": 0.3,
                },
                "rsi_reversion": {"rsi_window": 14, "lower": 30.0, "upper": 70.0},
                "breakout": {"lookback_breakout": 15, "side": "long"},
            },
        }
        composite_section = raw["strategy"]["composite"]
        composite_section.update(composite_overrides)

        cfg = MagicMock()

        def _get(path: str, default=None):
            node = raw
            for part in path.split("."):
                if not isinstance(node, dict) or part not in node:
                    return default
                node = node[part]
            return node

        cfg.get.side_effect = _get
        return cfg

    def test_source_uses_load_strategy(self) -> None:
        source = self._read_source()
        assert "load_strategy" in source

    def test_source_has_no_create_strategy_from_config(self) -> None:
        source = self._read_source()
        for forbidden in self.FORBIDDEN_NAMES:
            assert forbidden not in source

    def test_from_config_calls_load_strategy_per_component(self) -> None:
        from unittest.mock import patch

        calls: list[str] = []
        original = __import__("src.strategies", fromlist=["load_strategy"]).load_strategy

        def _track(key: str):
            calls.append(key)
            return original(key)

        cfg = self._minimal_cfg()
        with patch("src.strategies.load_strategy", side_effect=_track):
            composite = CompositeStrategy.from_config(cfg)

        assert calls == ["rsi_reversion", "breakout"]
        assert len(composite.strategies) == 2
        assert composite.strategies[0].KEY == "rsi_reversion"
        assert composite.strategies[1].KEY == "breakout"

    def test_from_config_preserves_component_order_weights_and_params(self) -> None:
        cfg = self._minimal_cfg(
            components=["breakout", "rsi_reversion"],
            weights=[0.7, 0.3],
            aggregation="voting",
            signal_threshold=0.25,
        )
        composite = CompositeStrategy.from_config(cfg)

        assert [s.KEY for s in composite.strategies] == ["breakout", "rsi_reversion"]
        assert composite.weights == [0.7, 0.3]
        assert composite.aggregation == "voting"
        assert composite.signal_threshold == 0.25
        assert composite.strategies[0].config["lookback_breakout"] == 15
        assert composite.strategies[1].config["rsi_window"] == 14

    def test_from_config_returns_composite_strategy_instance(self) -> None:
        composite = CompositeStrategy.from_config(self._minimal_cfg())
        assert isinstance(composite, CompositeStrategy)
        assert isinstance(composite, BaseStrategy)
        assert composite.KEY == "composite"

    def test_from_config_fresh_instances_no_shared_state(self) -> None:
        cfg = self._minimal_cfg()
        first = CompositeStrategy.from_config(cfg)
        second = CompositeStrategy.from_config(cfg)

        assert first.strategies[0] is not second.strategies[0]
        assert first.strategies[1] is not second.strategies[1]
        first.strategies[0].config["rsi_window"] = 99
        assert second.strategies[0].config["rsi_window"] == 14

    def test_from_config_unknown_component_fail_closed(self) -> None:
        cfg = self._minimal_cfg(
            components=["rsi_reversion", "invalid_strategy_key_xyz"],
            weights=None,
        )
        composite = CompositeStrategy.from_config(cfg)

        assert len(composite.strategies) == 1
        assert composite.strategies[0].KEY == "rsi_reversion"

    def test_from_config_filter_uses_load_strategy_binding(self) -> None:
        from unittest.mock import patch

        calls: list[str] = []
        original = __import__("src.strategies", fromlist=["load_strategy"]).load_strategy

        def _track(key: str):
            calls.append(key)
            return original(key)

        cfg = self._minimal_cfg(filter="vol_regime_filter")
        cfg.get.side_effect = lambda path, default=None: {
            "strategy.composite.components": ["rsi_reversion", "breakout"],
            "strategy.composite.weights": [0.6, 0.4],
            "strategy.composite.aggregation": "weighted",
            "strategy.composite.signal_threshold": 0.3,
            "strategy.composite.filter": "vol_regime_filter",
            "strategy.rsi_reversion.rsi_window": 14,
            "strategy.rsi_reversion.lower": 30.0,
            "strategy.rsi_reversion.upper": 70.0,
            "strategy.breakout.lookback_breakout": 15,
            "strategy.breakout.side": "long",
            "strategy.vol_regime_filter.vol_window": 14,
            "strategy.vol_regime_filter.vol_percentile_low": 25,
            "strategy.vol_regime_filter.vol_percentile_high": 75,
        }.get(path, default)

        with patch("src.strategies.load_strategy", side_effect=_track):
            composite = CompositeStrategy.from_config(cfg)

        assert "vol_regime_filter" in calls
        assert composite.filter_strategy is not None
        assert composite.filter_strategy.KEY == "vol_regime_filter"

    def test_nested_composite_component_preserves_existing_contract(self) -> None:
        cfg = self._minimal_cfg(components=["rsi_reversion", "composite"], weights=None)
        composite = CompositeStrategy.from_config(cfg)

        assert len(composite.strategies) == 2
        assert composite.strategies[0].KEY == "rsi_reversion"
        assert composite.strategies[1].KEY == "composite"
        assert isinstance(composite.strategies[1], CompositeStrategy)
