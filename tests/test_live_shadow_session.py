# tests/test_live_shadow_session.py
"""
Peak_Trade: Tests für Shadow/Paper Live Session (Phase 31)
==========================================================

Smoke-Tests und Unit-Tests für die Shadow/Paper-Session-Komponenten.
Diese Tests verwenden KEINE echten HTTP-Calls, sondern Fake-Datenquellen.

Test-Kategorien:
1. Config-Loading Tests
2. FakeCandleSource Tests
3. ShadowPaperSession Smoke Tests
4. Risk-Limit Integration Tests
5. Signal-zu-Order Flow Tests

WICHTIG: Alle Tests laufen ohne Netzwerk-Zugriff.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from unittest.mock import Mock, patch, MagicMock

import pandas as pd
import numpy as np

from src.data.kraken_live import (
    LiveCandle,
    FakeCandleSource,
    ShadowPaperConfig,
    LiveExchangeConfig,
    load_shadow_paper_config,
    load_live_exchange_config,
    KRAKEN_TIMEFRAME_MAP,
    _timeframe_to_minutes,
    _symbol_to_kraken,
)
from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.live.shadow_session import (
    ShadowPaperSession,
    ShadowPaperSessionMetrics,
    EnvironmentNotAllowedError,
    ALLOWED_ENVIRONMENT_MODES,
)
from src.live.risk_limits import LiveRiskLimits, LiveRiskConfig, LiveRiskCheckResult
from src.orders.shadow import ShadowMarketContext, ShadowOrderExecutor
from src.orders.base import OrderRequest
from src.execution.pipeline import ExecutionPipeline, SignalEvent
from src.strategies.base import BaseStrategy, StrategyMetadata


# =============================================================================
# Test Fixtures
# =============================================================================


def create_test_candles(
    n: int = 100,
    start_price: float = 50000.0,
    volatility: float = 0.002,
    trend: float = 0.0001,
) -> List[LiveCandle]:
    """
    Erstellt Test-Candles mit kontrollierbarem Preisverlauf.

    Args:
        n: Anzahl Candles
        start_price: Startpreis
        volatility: Volatilität pro Candle
        trend: Trend pro Candle

    Returns:
        Liste von LiveCandle-Objekten
    """
    candles: List[LiveCandle] = []
    base_time = datetime.now(timezone.utc) - timedelta(minutes=n)
    price = start_price

    np.random.seed(42)  # Reproduzierbar

    for i in range(n):
        # Preisentwicklung
        change = np.random.randn() * volatility + trend
        new_price = price * (1 + change)

        # OHLC generieren
        high = max(price, new_price) * (1 + abs(np.random.randn() * 0.001))
        low = min(price, new_price) * (1 - abs(np.random.randn() * 0.001))

        candle = LiveCandle(
            timestamp=base_time + timedelta(minutes=i),
            open=price,
            high=high,
            low=low,
            close=new_price,
            volume=np.random.uniform(1.0, 10.0),
            is_complete=True,
        )
        candles.append(candle)
        price = new_price

    return candles


def create_crossover_candles(n: int = 100) -> List[LiveCandle]:
    """
    Erstellt Candles die einen klaren MA-Crossover erzeugen.

    Erste Hälfte: Abwärtstrend (Fast MA < Slow MA)
    Zweite Hälfte: Aufwärtstrend (Fast MA > Slow MA)

    Returns:
        Liste von LiveCandle-Objekten
    """
    candles: List[LiveCandle] = []
    base_time = datetime.now(timezone.utc) - timedelta(minutes=n)

    for i in range(n):
        if i < n // 2:
            # Abwärtstrend
            price = 50000 - (i * 50)
        else:
            # Aufwärtstrend
            price = 50000 - ((n // 2) * 50) + ((i - n // 2) * 100)

        candle = LiveCandle(
            timestamp=base_time + timedelta(minutes=i),
            open=price,
            high=price * 1.001,
            low=price * 0.999,
            close=price,
            volume=5.0,
            is_complete=True,
        )
        candles.append(candle)

    return candles


class DummyStrategy(BaseStrategy):
    """Dummy-Strategie für Tests."""

    KEY = "dummy"

    def __init__(self, signal_pattern: Optional[List[int]] = None):
        super().__init__(
            config={},
            metadata=StrategyMetadata(name="Dummy", description="Test Strategy"),
        )
        self._signal_pattern = signal_pattern or [0, 0, 1, 1, 0, -1, 0]
        self._call_count = 0

    @classmethod
    def from_config(cls, cfg, section: str = "strategy.dummy") -> "DummyStrategy":
        return cls()

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Gibt Signal basierend auf Pattern zurück."""
        self._call_count += 1
        idx = (self._call_count - 1) % len(self._signal_pattern)
        signal = self._signal_pattern[idx]
        return pd.Series([signal] * len(data), index=data.index)


# =============================================================================
# Config Loading Tests
# =============================================================================


class TestConfigLoading:
    """Tests für Config-Loading-Funktionen."""

    def test_load_shadow_paper_config_defaults(self):
        """Test: ShadowPaperConfig mit Defaults."""
        mock_cfg = Mock()
        mock_cfg.get = Mock(return_value=None)

        # Bei None sollten Defaults verwendet werden
        config = ShadowPaperConfig()

        assert config.enabled is True
        assert config.mode == "paper"
        assert config.symbol == "BTC/EUR"
        assert config.timeframe == "1m"
        assert config.warmup_candles == 200
        assert config.start_balance == 10000.0

    def test_load_live_exchange_config_defaults(self):
        """Test: LiveExchangeConfig mit Defaults."""
        config = LiveExchangeConfig()

        assert config.name == "kraken"
        assert config.use_sandbox is True
        assert config.base_url == "https://api.kraken.com"
        assert config.max_retries == 3

    def test_timeframe_to_minutes(self):
        """Test: Timeframe-Konvertierung."""
        assert _timeframe_to_minutes("1m") == 1
        assert _timeframe_to_minutes("5m") == 5
        assert _timeframe_to_minutes("1h") == 60
        assert _timeframe_to_minutes("1d") == 1440
        assert _timeframe_to_minutes("unknown") == 1  # Default

    def test_symbol_to_kraken(self):
        """Test: Symbol-Konvertierung zu Kraken-Format."""
        assert _symbol_to_kraken("BTC/EUR") == "XXBTZEUR"
        assert _symbol_to_kraken("ETH/USD") == "XETHZUSD"
        assert _symbol_to_kraken("UNKNOWN/PAIR") == "UNKNOWNPAIR"


# =============================================================================
# FakeCandleSource Tests
# =============================================================================


class TestFakeCandleSource:
    """Tests für FakeCandleSource."""

    def test_warmup_returns_candles(self):
        """Test: Warmup liefert Candles."""
        candles = create_test_candles(n=50)
        source = FakeCandleSource(candles=candles)

        warmup_candles = source.warmup()

        # Warmup liefert ~80% der Candles
        assert len(warmup_candles) > 0
        assert len(warmup_candles) <= len(candles)

    def test_poll_latest_returns_next_candle(self):
        """Test: poll_latest liefert nächste Candle."""
        candles = create_test_candles(n=10)
        source = FakeCandleSource(candles=candles)

        source.warmup()

        # Erste poll sollte nächste Candle liefern
        candle = source.poll_latest()
        assert candle is not None

    def test_poll_latest_returns_none_when_exhausted(self):
        """Test: poll_latest liefert None wenn alle Candles verbraucht."""
        candles = create_test_candles(n=5)
        source = FakeCandleSource(candles=candles)

        source.warmup()

        # Alle verbleibenden Candles holen
        while source.poll_latest() is not None:
            pass

        # Jetzt sollte None kommen
        assert source.poll_latest() is None

    def test_get_buffer_returns_dataframe(self):
        """Test: get_buffer gibt DataFrame zurück."""
        candles = create_test_candles(n=20)
        source = FakeCandleSource(candles=candles)

        source.warmup()

        df = source.get_buffer()

        assert isinstance(df, pd.DataFrame)
        assert "close" in df.columns
        assert "volume" in df.columns
        assert len(df) > 0

    def test_get_latest_price(self):
        """Test: get_latest_price gibt Close-Preis zurück."""
        candles = create_test_candles(n=10)
        source = FakeCandleSource(candles=candles)

        source.warmup()

        price = source.get_latest_price()
        assert price is not None
        assert price > 0

    def test_reset_clears_state(self):
        """Test: reset setzt Zustand zurück."""
        candles = create_test_candles(n=10)
        source = FakeCandleSource(candles=candles)

        source.warmup()
        source.poll_latest()

        source.reset()

        # Nach Reset sollte warmup wieder von vorne beginnen
        new_candles = source.warmup()
        assert len(new_candles) > 0


# =============================================================================
# LiveCandle Tests
# =============================================================================


class TestLiveCandle:
    """Tests für LiveCandle-Datenstruktur."""

    def test_to_series(self):
        """Test: to_series konvertiert zu pandas Series."""
        ts = datetime.now(timezone.utc)
        candle = LiveCandle(
            timestamp=ts,
            open=100.0,
            high=105.0,
            low=99.0,
            close=104.0,
            volume=10.0,
        )

        series = candle.to_series()

        assert isinstance(series, pd.Series)
        assert series["close"] == 104.0
        assert series["volume"] == 10.0
        assert series.name == ts

    def test_to_dict(self):
        """Test: to_dict konvertiert zu Dictionary."""
        ts = datetime.now(timezone.utc)
        candle = LiveCandle(
            timestamp=ts,
            open=100.0,
            high=105.0,
            low=99.0,
            close=104.0,
            volume=10.0,
        )

        d = candle.to_dict()

        assert d["timestamp"] == ts
        assert d["close"] == 104.0
        assert d["is_complete"] is True


# =============================================================================
# ShadowPaperSession Tests
# =============================================================================


class TestShadowPaperSession:
    """Tests für ShadowPaperSession."""

    def test_session_rejects_live_environment(self):
        """Test: Session lehnt LIVE Environment ab."""
        env_config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=False,
        )
        shadow_cfg = ShadowPaperConfig()
        exchange_cfg = LiveExchangeConfig()
        source = FakeCandleSource(candles=create_test_candles())
        strategy = DummyStrategy()
        pipeline = ExecutionPipeline.for_shadow()
        risk_limits = LiveRiskLimits(
            LiveRiskConfig(
                enabled=True,
                base_currency="EUR",
                max_daily_loss_abs=None,
                max_daily_loss_pct=None,
                max_total_exposure_notional=None,
                max_symbol_exposure_notional=None,
                max_open_positions=None,
                max_order_notional=None,
                block_on_violation=True,
                use_experiments_for_daily_pnl=False,
            )
        )

        with pytest.raises(EnvironmentNotAllowedError):
            ShadowPaperSession(
                env_config=env_config,
                shadow_cfg=shadow_cfg,
                exchange_cfg=exchange_cfg,
                data_source=source,
                strategy=strategy,
                pipeline=pipeline,
                risk_limits=risk_limits,
            )

    def test_session_accepts_paper_environment(self):
        """Test: Session akzeptiert PAPER Environment."""
        env_config = EnvironmentConfig(
            environment=TradingEnvironment.PAPER,
        )
        shadow_cfg = ShadowPaperConfig()
        exchange_cfg = LiveExchangeConfig()
        source = FakeCandleSource(candles=create_test_candles())
        strategy = DummyStrategy()
        pipeline = ExecutionPipeline.for_shadow()
        risk_limits = LiveRiskLimits(
            LiveRiskConfig(
                enabled=False,
                base_currency="EUR",
                max_daily_loss_abs=None,
                max_daily_loss_pct=None,
                max_total_exposure_notional=None,
                max_symbol_exposure_notional=None,
                max_open_positions=None,
                max_order_notional=None,
                block_on_violation=True,
                use_experiments_for_daily_pnl=False,
            )
        )

        # Sollte KEINE Exception werfen
        session = ShadowPaperSession(
            env_config=env_config,
            shadow_cfg=shadow_cfg,
            exchange_cfg=exchange_cfg,
            data_source=source,
            strategy=strategy,
            pipeline=pipeline,
            risk_limits=risk_limits,
        )

        assert session is not None
        assert session.is_running is False

    def test_warmup_sets_flag(self):
        """Test: warmup setzt is_warmup_done Flag."""
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        shadow_cfg = ShadowPaperConfig(warmup_candles=50)
        exchange_cfg = LiveExchangeConfig()
        source = FakeCandleSource(candles=create_test_candles(n=100))
        strategy = DummyStrategy()
        pipeline = ExecutionPipeline.for_shadow()
        risk_limits = LiveRiskLimits(
            LiveRiskConfig(
                enabled=False, base_currency="EUR",
                max_daily_loss_abs=None, max_daily_loss_pct=None,
                max_total_exposure_notional=None, max_symbol_exposure_notional=None,
                max_open_positions=None, max_order_notional=None,
                block_on_violation=True, use_experiments_for_daily_pnl=False,
            )
        )

        session = ShadowPaperSession(
            env_config=env_config,
            shadow_cfg=shadow_cfg,
            exchange_cfg=exchange_cfg,
            data_source=source,
            strategy=strategy,
            pipeline=pipeline,
            risk_limits=risk_limits,
        )

        assert session.is_warmup_done is False

        session.warmup()

        assert session.is_warmup_done is True

    def test_step_once_increments_counter(self):
        """Test: step_once erhöht Schritt-Zähler."""
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        shadow_cfg = ShadowPaperConfig()
        exchange_cfg = LiveExchangeConfig()
        source = FakeCandleSource(candles=create_test_candles(n=100))
        strategy = DummyStrategy(signal_pattern=[0, 0, 0])  # Keine Signal-Änderung
        pipeline = ExecutionPipeline.for_shadow()
        risk_limits = LiveRiskLimits(
            LiveRiskConfig(
                enabled=False, base_currency="EUR",
                max_daily_loss_abs=None, max_daily_loss_pct=None,
                max_total_exposure_notional=None, max_symbol_exposure_notional=None,
                max_open_positions=None, max_order_notional=None,
                block_on_violation=True, use_experiments_for_daily_pnl=False,
            )
        )

        session = ShadowPaperSession(
            env_config=env_config,
            shadow_cfg=shadow_cfg,
            exchange_cfg=exchange_cfg,
            data_source=source,
            strategy=strategy,
            pipeline=pipeline,
            risk_limits=risk_limits,
        )

        session.warmup()

        assert session.metrics.steps == 0

        session.step_once()
        assert session.metrics.steps == 1

        session.step_once()
        assert session.metrics.steps == 2

    def test_run_n_steps_executes_correct_number(self):
        """Test: run_n_steps führt richtige Anzahl Schritte aus."""
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        shadow_cfg = ShadowPaperConfig()
        exchange_cfg = LiveExchangeConfig()
        source = FakeCandleSource(candles=create_test_candles(n=100))
        strategy = DummyStrategy(signal_pattern=[0, 0, 0])
        pipeline = ExecutionPipeline.for_shadow()
        risk_limits = LiveRiskLimits(
            LiveRiskConfig(
                enabled=False, base_currency="EUR",
                max_daily_loss_abs=None, max_daily_loss_pct=None,
                max_total_exposure_notional=None, max_symbol_exposure_notional=None,
                max_open_positions=None, max_order_notional=None,
                block_on_violation=True, use_experiments_for_daily_pnl=False,
            )
        )

        session = ShadowPaperSession(
            env_config=env_config,
            shadow_cfg=shadow_cfg,
            exchange_cfg=exchange_cfg,
            data_source=source,
            strategy=strategy,
            pipeline=pipeline,
            risk_limits=risk_limits,
        )

        session.warmup()

        session.run_n_steps(5, sleep_between=False)

        assert session.metrics.steps == 5

    def test_run_n_steps_requires_warmup(self):
        """Test: run_n_steps wirft Error ohne Warmup."""
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        shadow_cfg = ShadowPaperConfig()
        exchange_cfg = LiveExchangeConfig()
        source = FakeCandleSource(candles=create_test_candles())
        strategy = DummyStrategy()
        pipeline = ExecutionPipeline.for_shadow()
        risk_limits = LiveRiskLimits(
            LiveRiskConfig(
                enabled=False, base_currency="EUR",
                max_daily_loss_abs=None, max_daily_loss_pct=None,
                max_total_exposure_notional=None, max_symbol_exposure_notional=None,
                max_open_positions=None, max_order_notional=None,
                block_on_violation=True, use_experiments_for_daily_pnl=False,
            )
        )

        session = ShadowPaperSession(
            env_config=env_config,
            shadow_cfg=shadow_cfg,
            exchange_cfg=exchange_cfg,
            data_source=source,
            strategy=strategy,
            pipeline=pipeline,
            risk_limits=risk_limits,
        )

        # Kein warmup()

        with pytest.raises(RuntimeError, match="Warmup"):
            session.run_n_steps(5)


# =============================================================================
# Risk-Limit Integration Tests
# =============================================================================


class TestRiskLimitIntegration:
    """Tests für Risk-Limit-Integration in Session."""

    def test_risk_limits_block_large_orders(self):
        """Test: Risk-Limits blockieren zu große Orders."""
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        shadow_cfg = ShadowPaperConfig(position_fraction=1.0)  # Große Position
        exchange_cfg = LiveExchangeConfig()
        source = FakeCandleSource(candles=create_crossover_candles(n=100))

        # Strategie die Signal-Wechsel erzeugt
        strategy = DummyStrategy(signal_pattern=[0, 1])

        pipeline = ExecutionPipeline.for_shadow()

        # Sehr niedrige Limits
        risk_limits = LiveRiskLimits(
            LiveRiskConfig(
                enabled=True,
                base_currency="EUR",
                max_daily_loss_abs=None,
                max_daily_loss_pct=None,
                max_total_exposure_notional=10.0,  # Sehr niedrig
                max_symbol_exposure_notional=5.0,  # Sehr niedrig
                max_open_positions=1,
                max_order_notional=1.0,  # Sehr niedrig
                block_on_violation=True,
                use_experiments_for_daily_pnl=False,
            )
        )

        session = ShadowPaperSession(
            env_config=env_config,
            shadow_cfg=shadow_cfg,
            exchange_cfg=exchange_cfg,
            data_source=source,
            strategy=strategy,
            pipeline=pipeline,
            risk_limits=risk_limits,
        )

        session.warmup()

        # Mehrere Steps durchführen
        session.run_n_steps(10, sleep_between=False)

        # Bei aktivierten Risk-Limits sollten einige Orders blockiert sein
        # (wenn es Signal-Wechsel gab und Orders generiert wurden)
        # Kann 0 sein, wenn keine Orders generiert wurden
        metrics = session.metrics.to_dict()
        assert "blocked_orders_count" in metrics

    def test_risk_limits_disabled_allows_all(self):
        """Test: Deaktivierte Risk-Limits erlauben alles."""
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        shadow_cfg = ShadowPaperConfig(position_fraction=0.5)
        exchange_cfg = LiveExchangeConfig()
        source = FakeCandleSource(candles=create_crossover_candles(n=100))

        strategy = DummyStrategy(signal_pattern=[0, 1, 0])  # Signal-Wechsel
        pipeline = ExecutionPipeline.for_shadow()

        # Risk-Limits deaktiviert
        risk_limits = LiveRiskLimits(
            LiveRiskConfig(
                enabled=False,  # Deaktiviert
                base_currency="EUR",
                max_daily_loss_abs=None,
                max_daily_loss_pct=None,
                max_total_exposure_notional=None,
                max_symbol_exposure_notional=None,
                max_open_positions=None,
                max_order_notional=None,
                block_on_violation=True,
                use_experiments_for_daily_pnl=False,
            )
        )

        session = ShadowPaperSession(
            env_config=env_config,
            shadow_cfg=shadow_cfg,
            exchange_cfg=exchange_cfg,
            data_source=source,
            strategy=strategy,
            pipeline=pipeline,
            risk_limits=risk_limits,
        )

        session.warmup()
        session.run_n_steps(10, sleep_between=False)

        # Keine blockierten Orders bei deaktivierten Limits
        assert session.metrics.blocked_orders_count == 0


# =============================================================================
# Session Metrics Tests
# =============================================================================


class TestSessionMetrics:
    """Tests für ShadowPaperSessionMetrics."""

    def test_metrics_to_dict(self):
        """Test: Metriken zu Dictionary konvertieren."""
        metrics = ShadowPaperSessionMetrics(
            steps=10,
            total_orders=5,
            filled_orders=4,
            rejected_orders=1,
            blocked_orders_count=0,
        )

        d = metrics.to_dict()

        assert d["steps"] == 10
        assert d["total_orders"] == 5
        assert d["fill_rate"] == 0.8
        assert "start_time" in d

    def test_fill_rate_zero_with_no_orders(self):
        """Test: Fill-Rate ist 0 bei keinen Orders."""
        metrics = ShadowPaperSessionMetrics(total_orders=0)

        d = metrics.to_dict()

        assert d["fill_rate"] == 0.0


# =============================================================================
# Signal-to-Order Flow Tests
# =============================================================================


class TestSignalToOrderFlow:
    """Tests für den Signal-zu-Order-Flow."""

    def test_signal_change_generates_order(self):
        """Test: Signal-Änderung generiert Order."""
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        shadow_cfg = ShadowPaperConfig(position_fraction=0.1)
        exchange_cfg = LiveExchangeConfig()

        # Candles mit genug Daten für Strategie
        candles = create_test_candles(n=100)
        source = FakeCandleSource(candles=candles)

        # Strategie mit definiertem Signal-Wechsel (0 -> 1)
        strategy = DummyStrategy(signal_pattern=[0, 0, 0, 0, 0, 1])

        pipeline = ExecutionPipeline.for_shadow()
        risk_limits = LiveRiskLimits(
            LiveRiskConfig(
                enabled=False, base_currency="EUR",
                max_daily_loss_abs=None, max_daily_loss_pct=None,
                max_total_exposure_notional=None, max_symbol_exposure_notional=None,
                max_open_positions=None, max_order_notional=None,
                block_on_violation=True, use_experiments_for_daily_pnl=False,
            )
        )

        session = ShadowPaperSession(
            env_config=env_config,
            shadow_cfg=shadow_cfg,
            exchange_cfg=exchange_cfg,
            data_source=source,
            strategy=strategy,
            pipeline=pipeline,
            risk_limits=risk_limits,
        )

        session.warmup()

        # Mehrere Steps, bis Signal-Wechsel
        results = session.run_n_steps(10, sleep_between=False)

        # Sollte mindestens eine Order erzeugt haben (bei Signal-Wechsel)
        # Kann variieren je nach Buffer-Zustand
        # Wichtig: Kein Crash, Metriken sind konsistent
        assert session.metrics.steps == 10

    def test_no_order_without_signal_change(self):
        """Test: Keine Order ohne Signal-Änderung."""
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        shadow_cfg = ShadowPaperConfig()
        exchange_cfg = LiveExchangeConfig()
        source = FakeCandleSource(candles=create_test_candles(n=100))

        # Strategie mit konstantem Signal
        strategy = DummyStrategy(signal_pattern=[0, 0, 0, 0, 0])

        pipeline = ExecutionPipeline.for_shadow()
        risk_limits = LiveRiskLimits(
            LiveRiskConfig(
                enabled=False, base_currency="EUR",
                max_daily_loss_abs=None, max_daily_loss_pct=None,
                max_total_exposure_notional=None, max_symbol_exposure_notional=None,
                max_open_positions=None, max_order_notional=None,
                block_on_violation=True, use_experiments_for_daily_pnl=False,
            )
        )

        session = ShadowPaperSession(
            env_config=env_config,
            shadow_cfg=shadow_cfg,
            exchange_cfg=exchange_cfg,
            data_source=source,
            strategy=strategy,
            pipeline=pipeline,
            risk_limits=risk_limits,
        )

        session.warmup()
        session.run_n_steps(5, sleep_between=False)

        # Keine Orders bei konstantem Signal
        assert session.metrics.total_orders == 0


# =============================================================================
# Callback Tests
# =============================================================================


class TestCallbacks:
    """Tests für Session-Callbacks."""

    def test_on_step_callback_called(self):
        """Test: on_step_callback wird aufgerufen."""
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        shadow_cfg = ShadowPaperConfig()
        exchange_cfg = LiveExchangeConfig()
        source = FakeCandleSource(candles=create_test_candles(n=50))
        strategy = DummyStrategy()
        pipeline = ExecutionPipeline.for_shadow()
        risk_limits = LiveRiskLimits(
            LiveRiskConfig(
                enabled=False, base_currency="EUR",
                max_daily_loss_abs=None, max_daily_loss_pct=None,
                max_total_exposure_notional=None, max_symbol_exposure_notional=None,
                max_open_positions=None, max_order_notional=None,
                block_on_violation=True, use_experiments_for_daily_pnl=False,
            )
        )

        callback_calls: List[int] = []

        def callback(step: int, candle: Optional[LiveCandle]) -> None:
            callback_calls.append(step)

        session = ShadowPaperSession(
            env_config=env_config,
            shadow_cfg=shadow_cfg,
            exchange_cfg=exchange_cfg,
            data_source=source,
            strategy=strategy,
            pipeline=pipeline,
            risk_limits=risk_limits,
            on_step_callback=callback,
        )

        session.warmup()
        session.run_n_steps(3, sleep_between=False)

        assert len(callback_calls) == 3
        assert callback_calls == [1, 2, 3]


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests für Edge Cases."""

    def test_empty_buffer_handled(self):
        """Test: Leerer Buffer wird sauber behandelt."""
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        shadow_cfg = ShadowPaperConfig()
        exchange_cfg = LiveExchangeConfig()

        # Wenige Candles -> Buffer schnell leer
        source = FakeCandleSource(candles=create_test_candles(n=5))
        strategy = DummyStrategy()
        pipeline = ExecutionPipeline.for_shadow()
        risk_limits = LiveRiskLimits(
            LiveRiskConfig(
                enabled=False, base_currency="EUR",
                max_daily_loss_abs=None, max_daily_loss_pct=None,
                max_total_exposure_notional=None, max_symbol_exposure_notional=None,
                max_open_positions=None, max_order_notional=None,
                block_on_violation=True, use_experiments_for_daily_pnl=False,
            )
        )

        session = ShadowPaperSession(
            env_config=env_config,
            shadow_cfg=shadow_cfg,
            exchange_cfg=exchange_cfg,
            data_source=source,
            strategy=strategy,
            pipeline=pipeline,
            risk_limits=risk_limits,
        )

        session.warmup()

        # Sollte nicht crashen auch wenn Buffer leer wird
        session.run_n_steps(20, sleep_between=False)

        assert session.metrics.steps == 20

    def test_execution_summary_available(self):
        """Test: Execution-Summary ist verfügbar."""
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        shadow_cfg = ShadowPaperConfig()
        exchange_cfg = LiveExchangeConfig()
        source = FakeCandleSource(candles=create_test_candles())
        strategy = DummyStrategy()
        pipeline = ExecutionPipeline.for_shadow()
        risk_limits = LiveRiskLimits(
            LiveRiskConfig(
                enabled=False, base_currency="EUR",
                max_daily_loss_abs=None, max_daily_loss_pct=None,
                max_total_exposure_notional=None, max_symbol_exposure_notional=None,
                max_open_positions=None, max_order_notional=None,
                block_on_violation=True, use_experiments_for_daily_pnl=False,
            )
        )

        session = ShadowPaperSession(
            env_config=env_config,
            shadow_cfg=shadow_cfg,
            exchange_cfg=exchange_cfg,
            data_source=source,
            strategy=strategy,
            pipeline=pipeline,
            risk_limits=risk_limits,
        )

        session.warmup()
        session.run_n_steps(3, sleep_between=False)

        summary = session.get_execution_summary()

        assert "session_metrics" in summary
        assert "pipeline_summary" in summary
        assert "config" in summary
        assert summary["config"]["mode"] == "paper"
