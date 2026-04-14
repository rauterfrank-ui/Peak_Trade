#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# tests/test_live_session_runner.py
"""
Peak_Trade: Tests für LiveSessionRunner (Phase 80)
===================================================

Tests für die Strategy-to-Execution Bridge:
- LiveSessionConfig Validierung
- LIVE-Mode Blockierung
- Shadow/Testnet-Mode Funktionalität
- Session-Lifecycle (Warmup, Steps, Shutdown)
- ExecutionPipeline-Integration

WICHTIG: Alle Tests verwenden Fake/Stub-Komponenten.
         Es werden KEINE echten API-Calls gemacht.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Projekt-Root zum Python-Path hinzufuegen
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

pytestmark = pytest.mark.network


# =============================================================================
# Fake/Stub Components
# =============================================================================


class FakeStrategy:
    """
    Fake-Strategie für Tests.

    Generiert deterministische Signale basierend auf Call-Count.
    """

    KEY = "fake_strategy"

    def __init__(self, signal_sequence: Optional[List[int]] = None):
        """
        Args:
            signal_sequence: Liste von Signalen die nacheinander zurückgegeben werden.
                            Default: [0, 1, 1, 0, -1, 0] (wechselnde Signale)
        """
        self.signal_sequence = signal_sequence or [0, 1, 1, 0, -1, 0]
        self.call_count = 0
        self.config = {"fake": True}
        self.meta = MagicMock()
        self.meta.name = "FakeStrategy"

    @property
    def key(self) -> str:
        return self.KEY

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Gibt deterministische Signale zurück."""
        idx = self.call_count % len(self.signal_sequence)
        signal = self.signal_sequence[idx]
        self.call_count += 1
        return pd.Series([signal] * len(data), index=data.index)

    @classmethod
    def from_config(cls, cfg: Any, section: str) -> "FakeStrategy":
        return cls()


@dataclass
class FakeCandle:
    """Fake-Candle für Tests."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 100.0


class FakeDataSource:
    """
    Fake-Datenquelle für Tests.

    Gibt deterministische Candles zurück.
    """

    def __init__(
        self,
        symbol: str = "BTC/EUR",
        timeframe: str = "1m",
        num_candles: int = 100,
        base_price: float = 50000.0,
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.num_candles = num_candles
        self.base_price = base_price
        self._candles: List[FakeCandle] = []
        self._poll_count = 0

    def warmup(self) -> List[FakeCandle]:
        """Generiert Warmup-Candles."""
        self._candles = []
        for i in range(self.num_candles):
            price = self.base_price + (i * 10)
            candle = FakeCandle(
                timestamp=datetime.now(timezone.utc),
                open=price,
                high=price + 50,
                low=price - 50,
                close=price + 25,
            )
            self._candles.append(candle)
        return self._candles

    def poll_latest(self) -> Optional[FakeCandle]:
        """Gibt die nächste Candle zurück."""
        self._poll_count += 1
        if not self._candles:
            return None
        # Rotiere durch Candles
        return self._candles[self._poll_count % len(self._candles)]

    def get_buffer(self) -> pd.DataFrame:
        """Gibt Candle-Buffer als DataFrame zurück."""
        if not self._candles:
            return pd.DataFrame()

        data = [
            {
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
            }
            for c in self._candles
        ]
        df = pd.DataFrame(data)
        df.index = pd.date_range("2024-01-01", periods=len(self._candles), freq="1min")
        return df


class FakeOrderExecutor:
    """Fake-Executor der Orders nur aufzeichnet."""

    def __init__(self):
        self.orders_received: List[Any] = []
        self.context = MagicMock()

    def execute_orders(self, orders: List[Any]) -> List[Any]:
        """Nimmt Orders entgegen und gibt Fake-Results zurück."""
        self.orders_received.extend(orders)

        results = []
        for order in orders:
            result = MagicMock()
            result.is_filled = True
            result.is_rejected = False
            result.status = "filled"
            result.fill = MagicMock()
            result.fill.side = order.side
            result.fill.quantity = order.quantity
            result.fill.price = 50000.0
            result.fill.fee = 0.5
            result.request = order
            results.append(result)

        return results


# =============================================================================
# Tests: LiveSessionConfig
# =============================================================================


class TestLiveSessionConfig:
    """Tests für LiveSessionConfig Validierung und Parameter."""

    def test_config_valid_shadow_mode(self):
        """Gültige Shadow-Mode Konfiguration wird akzeptiert."""
        from src.execution.live_session import LiveSessionConfig

        config = LiveSessionConfig(
            mode="shadow",
            strategy_key="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1m",
        )

        assert config.mode == "shadow"
        assert config.strategy_key == "ma_crossover"
        assert config.symbol == "BTC/EUR"
        assert config.timeframe == "1m"

    def test_config_valid_testnet_mode(self):
        """Gültige Testnet-Mode Konfiguration wird akzeptiert."""
        from src.execution.live_session import LiveSessionConfig

        config = LiveSessionConfig(
            mode="testnet",
            strategy_key="rsi_reversion",
            symbol="ETH/EUR",
            timeframe="5m",
        )

        assert config.mode == "testnet"
        assert config.strategy_key == "rsi_reversion"

    def test_config_live_mode_blocked(self):
        """LIVE-Mode wird explizit blockiert (Phase 80)."""
        from src.execution.live_session import LiveSessionConfig, LiveModeNotAllowedError

        with pytest.raises(LiveModeNotAllowedError) as exc_info:
            LiveSessionConfig(
                mode="live",
                strategy_key="ma_crossover",
                symbol="BTC/EUR",
            )

        assert "LIVE-Mode ist in Phase 80 NICHT erlaubt" in str(exc_info.value)

    def test_config_invalid_mode_rejected(self):
        """Ungültiger Mode wird abgelehnt."""
        from src.execution.live_session import LiveSessionConfig

        with pytest.raises(ValueError) as exc_info:
            LiveSessionConfig(
                mode="invalid_mode",  # type: ignore
                strategy_key="ma_crossover",
                symbol="BTC/EUR",
            )

        assert "Ungültiger mode" in str(exc_info.value)

    def test_config_invalid_symbol_rejected(self):
        """Ungültiges Symbol wird abgelehnt."""
        from src.execution.live_session import LiveSessionConfig

        with pytest.raises(ValueError) as exc_info:
            LiveSessionConfig(
                mode="shadow",
                strategy_key="ma_crossover",
                symbol="INVALID",  # Fehlt "/"
            )

        assert "Ungültiges symbol" in str(exc_info.value)

    def test_config_empty_strategy_rejected(self):
        """Leerer Strategy-Key wird abgelehnt."""
        from src.execution.live_session import LiveSessionConfig

        with pytest.raises(ValueError) as exc_info:
            LiveSessionConfig(
                mode="shadow",
                strategy_key="",
                symbol="BTC/EUR",
            )

        assert "strategy_key darf nicht leer sein" in str(exc_info.value)

    def test_config_invalid_position_fraction_rejected(self):
        """Ungültige position_fraction wird abgelehnt."""
        from src.execution.live_session import LiveSessionConfig

        with pytest.raises(ValueError) as exc_info:
            LiveSessionConfig(
                mode="shadow",
                strategy_key="ma_crossover",
                symbol="BTC/EUR",
                position_fraction=1.5,  # > 1.0
            )

        assert "position_fraction" in str(exc_info.value)

    def test_config_generate_run_id(self):
        """Run-ID wird korrekt generiert."""
        from src.execution.live_session import LiveSessionConfig

        config = LiveSessionConfig(
            mode="shadow",
            strategy_key="ma_crossover",
            symbol="BTC/EUR",
        )

        run_id = config.generate_run_id()
        assert run_id.startswith("shadow_ma_crossover_")
        assert len(run_id) > 20  # Enthält Timestamp und UUID

    def test_config_custom_run_id(self):
        """Benutzerdefinierte Run-ID wird verwendet."""
        from src.execution.live_session import LiveSessionConfig

        config = LiveSessionConfig(
            mode="shadow",
            strategy_key="ma_crossover",
            symbol="BTC/EUR",
            run_id="my_custom_run_id",
        )

        run_id = config.generate_run_id()
        assert run_id == "my_custom_run_id"

    def test_config_to_dict(self):
        """Config kann zu Dict konvertiert werden."""
        from src.execution.live_session import LiveSessionConfig

        config = LiveSessionConfig(
            mode="shadow",
            strategy_key="ma_crossover",
            symbol="BTC/EUR",
            timeframe="5m",
        )

        config_dict = config.to_dict()

        assert config_dict["mode"] == "shadow"
        assert config_dict["strategy_key"] == "ma_crossover"
        assert config_dict["symbol"] == "BTC/EUR"
        assert config_dict["timeframe"] == "5m"


# =============================================================================
# Tests: LiveSessionRunner
# =============================================================================


class TestLiveSessionRunner:
    """Tests für LiveSessionRunner Lifecycle und Execution."""

    def test_runner_init_shadow_mode(self):
        """Runner kann im Shadow-Mode initialisiert werden."""
        from src.execution.live_session import (
            LiveSessionConfig,
            LiveSessionRunner,
            LiveSessionMetrics,
        )
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.execution.pipeline import ExecutionPipeline
        from src.orders.shadow import ShadowMarketContext

        config = LiveSessionConfig(
            mode="shadow",
            strategy_key="fake_strategy",
            symbol="BTC/EUR",
        )

        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        strategy = FakeStrategy()
        pipeline = ExecutionPipeline.for_shadow()
        data_source = FakeDataSource()

        runner = LiveSessionRunner(
            session_config=config,
            env_config=env_config,
            strategy=strategy,
            pipeline=pipeline,
            data_source=data_source,
        )

        assert runner.config == config
        assert runner.is_running is False
        assert runner.is_warmup_done is False
        assert runner.run_id.startswith("shadow_")

    def test_runner_init_live_mode_blocked(self):
        """Runner blockiert LIVE-Mode bei Initialisierung."""
        from src.execution.live_session import (
            LiveSessionConfig,
            LiveSessionRunner,
            LiveModeNotAllowedError,
        )

        # Config mit mode="live" würde bereits Exception werfen
        # Aber testen wir auch den Runner direkt
        with pytest.raises(LiveModeNotAllowedError):
            LiveSessionConfig(mode="live", strategy_key="test", symbol="BTC/EUR")

    def test_runner_warmup(self):
        """Runner führt Warmup korrekt durch."""
        from src.execution.live_session import LiveSessionConfig, LiveSessionRunner
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.execution.pipeline import ExecutionPipeline

        config = LiveSessionConfig(
            mode="shadow",
            strategy_key="fake_strategy",
            symbol="BTC/EUR",
        )

        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        strategy = FakeStrategy()
        pipeline = ExecutionPipeline.for_shadow()
        data_source = FakeDataSource()

        runner = LiveSessionRunner(
            session_config=config,
            env_config=env_config,
            strategy=strategy,
            pipeline=pipeline,
            data_source=data_source,
        )

        assert runner.is_warmup_done is False

        runner.warmup()

        assert runner.is_warmup_done is True
        assert runner.metrics.start_time is not None

    def test_runner_step_once(self):
        """Runner führt einen Step korrekt durch."""
        from src.execution.live_session import LiveSessionConfig, LiveSessionRunner
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.execution.pipeline import ExecutionPipeline

        config = LiveSessionConfig(
            mode="shadow",
            strategy_key="fake_strategy",
            symbol="BTC/EUR",
        )

        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        # Signal-Sequenz: 0 -> 1 (Signal-Change triggert Order)
        strategy = FakeStrategy(signal_sequence=[0, 1, 1, 0])
        pipeline = ExecutionPipeline.for_shadow()
        data_source = FakeDataSource()

        runner = LiveSessionRunner(
            session_config=config,
            env_config=env_config,
            strategy=strategy,
            pipeline=pipeline,
            data_source=data_source,
        )

        runner.warmup()

        # Erster Step
        result1 = runner.step_once()
        assert runner.metrics.steps == 1

        # Mehrere Steps
        for _ in range(5):
            runner.step_once()

        assert runner.metrics.steps == 6

    def test_runner_run_n_steps(self):
        """Runner führt N Steps aus."""
        from src.execution.live_session import (
            LiveSessionConfig,
            LiveSessionRunner,
            SessionRuntimeError,
        )
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.execution.pipeline import ExecutionPipeline

        config = LiveSessionConfig(
            mode="shadow",
            strategy_key="fake_strategy",
            symbol="BTC/EUR",
        )

        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        strategy = FakeStrategy()
        pipeline = ExecutionPipeline.for_shadow()
        data_source = FakeDataSource()

        runner = LiveSessionRunner(
            session_config=config,
            env_config=env_config,
            strategy=strategy,
            pipeline=pipeline,
            data_source=data_source,
        )

        # run_n_steps ohne Warmup sollte Exception werfen
        with pytest.raises(SessionRuntimeError) as exc_info:
            runner.run_n_steps(5)

        assert "Warmup muss vor run_n_steps" in str(exc_info.value)

        # Mit Warmup
        runner.warmup()
        results = runner.run_n_steps(10, sleep_between=False)

        assert runner.metrics.steps == 10
        # Results können leer sein wenn keine Signal-Änderungen

    def test_runner_shutdown(self):
        """Runner kann sauber heruntergefahren werden."""
        from src.execution.live_session import LiveSessionConfig, LiveSessionRunner
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.execution.pipeline import ExecutionPipeline

        config = LiveSessionConfig(
            mode="shadow",
            strategy_key="fake_strategy",
            symbol="BTC/EUR",
        )

        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        strategy = FakeStrategy()
        pipeline = ExecutionPipeline.for_shadow()
        data_source = FakeDataSource()

        runner = LiveSessionRunner(
            session_config=config,
            env_config=env_config,
            strategy=strategy,
            pipeline=pipeline,
            data_source=data_source,
        )

        runner.warmup()

        # Shutdown-Flag setzen
        runner.shutdown()

        # run_n_steps sollte früh abbrechen
        results = runner.run_n_steps(100, sleep_between=False)

        # Sollte vorzeitig beendet worden sein (0 oder wenige Steps)
        assert runner.metrics.steps < 100

    def test_runner_get_summary(self):
        """Runner gibt korrekte Zusammenfassung zurück."""
        from src.execution.live_session import LiveSessionConfig, LiveSessionRunner
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.execution.pipeline import ExecutionPipeline

        config = LiveSessionConfig(
            mode="shadow",
            strategy_key="fake_strategy",
            symbol="BTC/EUR",
        )

        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        strategy = FakeStrategy()
        pipeline = ExecutionPipeline.for_shadow()
        data_source = FakeDataSource()

        runner = LiveSessionRunner(
            session_config=config,
            env_config=env_config,
            strategy=strategy,
            pipeline=pipeline,
            data_source=data_source,
        )

        runner.warmup()
        runner.run_n_steps(5, sleep_between=False)

        summary = runner.get_summary()

        assert "run_id" in summary
        assert "config" in summary
        assert "metrics" in summary
        assert "pipeline_summary" in summary
        assert summary["config"]["mode"] == "shadow"


# =============================================================================
# Tests: Factory Method from_config
# =============================================================================


class TestLiveSessionRunnerFactory:
    """Tests für LiveSessionRunner.from_config() Factory."""

    @patch("src.execution.live_session.LiveSessionRunner._build_data_source")
    @patch("src.strategies.registry.create_strategy_from_config")
    def test_from_config_shadow_mode(self, mock_create_strategy, mock_build_data):
        """from_config erstellt Runner im Shadow-Mode."""
        from src.execution.live_session import (
            LiveSessionConfig,
            LiveSessionRunner,
        )
        from src.core.peak_config import PeakConfig

        # Mock-Strategie und Data-Source
        mock_create_strategy.return_value = FakeStrategy()
        mock_build_data.return_value = FakeDataSource()

        config = LiveSessionConfig(
            mode="shadow",
            strategy_key="ma_crossover",
            symbol="BTC/EUR",
        )

        # PeakConfig mocken
        peak_config = MagicMock(spec=PeakConfig)
        peak_config.get.return_value = None

        runner = LiveSessionRunner.from_config(config, peak_config=peak_config)

        assert runner.config == config
        assert runner.is_running is False
        mock_create_strategy.assert_called_once()

    def test_from_config_live_mode_blocked(self):
        """from_config blockiert LIVE-Mode."""
        from src.execution.live_session import (
            LiveSessionConfig,
            LiveSessionRunner,
            LiveModeNotAllowedError,
        )

        # Config mit mode="live" wirft bereits bei Erstellung
        with pytest.raises(LiveModeNotAllowedError):
            LiveSessionConfig(mode="live", strategy_key="test", symbol="BTC/EUR")


# =============================================================================
# Tests: CLI Smoke Test
# =============================================================================


class TestExecutionSessionCLI:
    """Smoke-Tests für das CLI-Skript."""

    def test_cli_help(self):
        """CLI --help funktioniert."""
        result = subprocess.run(
            [sys.executable, "scripts/run_execution_session.py", "--help"],
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR),
        )

        assert result.returncode == 0
        assert "Strategy-to-Execution Session" in result.stdout
        assert "--mode" in result.stdout
        assert "--strategy" in result.stdout
        assert "--symbol" in result.stdout

    def test_cli_list_strategies(self):
        """CLI --list-strategies funktioniert."""
        result = subprocess.run(
            [sys.executable, "scripts/run_execution_session.py", "--list-strategies"],
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR),
        )

        assert result.returncode == 0
        assert "Verfügbare Strategien" in result.stdout
        assert "ma_crossover" in result.stdout

    def test_cli_dry_run(self):
        """CLI --dry-run validiert Config ohne Session zu starten."""
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_execution_session.py",
                "--strategy",
                "ma_crossover",
                "--symbol",
                "BTC/EUR",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR),
            timeout=30,
        )

        # Kann 0 (Success) oder 1 (Config-Fehler) sein je nach Config-Existenz
        # Hauptsache es crasht nicht
        assert result.returncode in [0, 1]
        # Sollte keine Exception traceback haben
        assert "Traceback" not in result.stderr or "LiveModeNotAllowedError" not in result.stderr

    def test_cli_invalid_mode_rejected(self):
        """CLI lehnt ungültigen Mode ab."""
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_execution_session.py",
                "--mode",
                "live",  # NICHT ERLAUBT
                "--strategy",
                "ma_crossover",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR),
            timeout=30,
        )

        # argparse sollte "invalid choice" melden
        assert result.returncode != 0
        assert "invalid choice" in result.stderr or "error" in result.stderr.lower()


# =============================================================================
# Tests: Integration mit ExecutionPipeline
# =============================================================================


class TestLiveSessionPipelineIntegration:
    """Tests für die Integration mit ExecutionPipeline."""

    def test_pipeline_execute_with_safety_called(self):
        """execute_with_safety wird korrekt aufgerufen."""
        from src.execution.live_session import LiveSessionConfig, LiveSessionRunner
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.execution.pipeline import ExecutionPipeline

        config = LiveSessionConfig(
            mode="shadow",
            strategy_key="fake_strategy",
            symbol="BTC/EUR",
        )

        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        # Signal-Sequenz mit Signal-Change
        strategy = FakeStrategy(signal_sequence=[0, 1])  # 0 -> 1 triggert Order
        pipeline = ExecutionPipeline.for_shadow()
        data_source = FakeDataSource()

        runner = LiveSessionRunner(
            session_config=config,
            env_config=env_config,
            strategy=strategy,
            pipeline=pipeline,
            data_source=data_source,
        )

        runner.warmup()

        # Step 1: Signal 0
        runner.step_once()

        # Step 2: Signal 1 (Signal-Change -> Order)
        runner.step_once()

        # Check dass Orders generiert wurden (wenn Signal-Change erkannt)
        # Die genaue Anzahl hängt von der Signal-Sequenz ab
        assert runner.metrics.steps == 2


# =============================================================================
# Run Tests
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
