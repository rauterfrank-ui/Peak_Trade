# tests/test_testnet_orchestrator_smoke.py
"""
Tests für src/live/testnet_orchestrator.py (Phase 64)
=====================================================

Smoke-Tests für Testnet-Orchestrator v1.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Pfad-Setup
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.peak_config import PeakConfig
from src.live.testnet_orchestrator import (
    TestnetOrchestrator,
    RunState,
    RunInfo,
    RunNotFoundError,
    ReadinessCheckFailedError,
    InvalidModeError,
    OrchestratorError,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def test_config() -> PeakConfig:
    """Erstellt eine Test-Config für Shadow-Mode."""
    return PeakConfig(raw={
        "environment": {
            "mode": "paper",
            "enable_live_trading": False,
            "require_confirm_token": True,
            "confirm_token": "",
            "testnet_dry_run": True,
            "log_all_orders": True,
        },
        "general": {
            "base_currency": "EUR",
            "starting_capital": 10000.0,
        },
        "shadow": {
            "enabled": True,
            "run_type": "shadow_run",
            "fee_rate": 0.0005,
            "slippage_bps": 0.0,
            "base_currency": "EUR",
            "log_all_orders": True,
        },
        "live_risk": {
            "enabled": True,
            "base_currency": "EUR",
            "max_order_notional": 1000.0,
            "max_symbol_exposure_notional": 2000.0,
            "max_total_exposure_notional": 5000.0,
            "max_open_positions": 5,
            "max_daily_loss_abs": 500.0,
            "max_daily_loss_pct": 5.0,
            "block_on_violation": True,
            "use_experiments_for_daily_pnl": True,
        },
        "strategy": {
            "ma_crossover": {
                "fast_window": 10,
                "slow_window": 30,
                "price_col": "close",
            },
        },
    })


@pytest.fixture
def testnet_test_config() -> PeakConfig:
    """Erstellt eine Test-Config für Testnet-Mode."""
    return PeakConfig(raw={
        "environment": {
            "mode": "testnet",
            "enable_live_trading": False,
            "require_confirm_token": True,
            "confirm_token": "",
            "testnet_dry_run": True,
            "log_all_orders": True,
        },
        "general": {
            "base_currency": "EUR",
            "starting_capital": 10000.0,
        },
        "shadow": {
            "enabled": True,
            "run_type": "shadow_run",
            "fee_rate": 0.0005,
            "slippage_bps": 0.0,
            "base_currency": "EUR",
            "log_all_orders": True,
        },
        "live_risk": {
            "enabled": True,
            "base_currency": "EUR",
            "max_order_notional": 1000.0,
            "max_symbol_exposure_notional": 2000.0,
            "max_total_exposure_notional": 5000.0,
            "max_open_positions": 5,
            "max_daily_loss_abs": 500.0,
            "max_daily_loss_pct": 5.0,
            "block_on_violation": True,
            "use_experiments_for_daily_pnl": True,
        },
        "strategy": {
            "ma_crossover": {
                "fast_window": 10,
                "slow_window": 30,
                "price_col": "close",
            },
        },
    })


@pytest.fixture
def orchestrator(test_config: PeakConfig) -> TestnetOrchestrator:
    """Erstellt einen Testnet-Orchestrator."""
    return TestnetOrchestrator(config=test_config)


# =============================================================================
# Readiness-Check Tests
# =============================================================================


def test_readiness_check_shadow_mode(test_config: PeakConfig) -> None:
    """Test: Readiness-Check für Shadow-Mode."""
    orchestrator = TestnetOrchestrator(config=test_config)
    
    # Sollte keine Exception werfen
    orchestrator._ensure_readiness("shadow")


def test_readiness_check_testnet_mode(testnet_test_config: PeakConfig) -> None:
    """Test: Readiness-Check für Testnet-Mode."""
    orchestrator = TestnetOrchestrator(config=testnet_test_config)
    
    # Sollte keine Exception werfen
    orchestrator._ensure_readiness("testnet")


def test_readiness_check_invalid_mode(test_config: PeakConfig) -> None:
    """Test: Readiness-Check mit ungültigem Mode."""
    orchestrator = TestnetOrchestrator(config=test_config)
    
    with pytest.raises(InvalidModeError, match="Ungültiger Mode"):
        orchestrator._ensure_readiness("live")


def test_readiness_check_wrong_environment(testnet_test_config: PeakConfig) -> None:
    """Test: Readiness-Check mit falschem Environment."""
    # Config mit Paper-Mode, aber Testnet-Check
    orchestrator = TestnetOrchestrator(config=testnet_test_config)
    
    # Ändere Environment zu Paper
    testnet_test_config.raw["environment"]["mode"] = "paper"
    
    with pytest.raises(ReadinessCheckFailedError, match="Testnet-Runs erfordern"):
        orchestrator._ensure_readiness("testnet")


# =============================================================================
# Shadow-Run Tests
# =============================================================================


@patch("src.live.shadow_session.ShadowPaperSession")
@patch("src.strategies.registry.create_strategy_from_config")
@patch("src.data.kraken_live.create_kraken_source_from_config")
def test_start_shadow_run_smoke(
    mock_data_source: MagicMock,
    mock_strategy: MagicMock,
    mock_session_class: MagicMock,
    orchestrator: TestnetOrchestrator,
) -> None:
    """Test: Shadow-Run starten (Smoke-Test)."""
    # Mock Session
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    # Mock Strategy
    mock_strategy_instance = MagicMock()
    mock_strategy_instance.key = "ma_crossover"
    mock_strategy.return_value = mock_strategy_instance

    # Mock Data Source
    mock_data_source.return_value = MagicMock()

    # Mock Run-Logger
    with patch("src.live.run_logging.create_run_logger_from_config") as mock_logger:
        mock_logger_instance = MagicMock()
        mock_logger_instance.run_dir = Path("/tmp/test_run")
        mock_logger.return_value = mock_logger_instance

        # Starte Run
        run_id = orchestrator.start_shadow_run(
            strategy_name="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1m",
            notes="Test-Run",
        )

        # Prüfe, dass Run-ID zurückgegeben wird
        assert run_id is not None
        assert run_id.startswith("shadow_")

        # Prüfe, dass Run registriert ist
        status = orchestrator.get_status(run_id=run_id)
        assert isinstance(status, RunInfo)
        assert status.run_id == run_id
        assert status.mode == "shadow"
        assert status.strategy_name == "ma_crossover"
        assert status.symbol == "BTC/EUR"
        assert status.timeframe == "1m"
        assert status.notes == "Test-Run"


def test_start_shadow_run_with_invalid_strategy(orchestrator: TestnetOrchestrator) -> None:
    """Test: Shadow-Run mit ungültiger Strategie."""
    with patch("src.strategies.registry.create_strategy_from_config") as mock_strategy:
        mock_strategy.side_effect = KeyError("Strategy 'invalid' not found")

        with patch("src.live.run_logging.create_run_logger_from_config") as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger_instance.run_dir = Path("/tmp/test_run")
            mock_logger.return_value = mock_logger_instance

            with pytest.raises(OrchestratorError, match="Fehler beim Starten"):
                orchestrator.start_shadow_run(
                    strategy_name="invalid",
                    symbol="BTC/EUR",
                    timeframe="1m",
                )


# =============================================================================
# Testnet-Run Tests
# =============================================================================


@patch("src.live.shadow_session.ShadowPaperSession")
@patch("src.strategies.registry.create_strategy_from_config")
@patch("src.data.kraken_live.create_kraken_source_from_config")
def test_start_testnet_run_smoke(
    mock_data_source: MagicMock,
    mock_strategy: MagicMock,
    mock_session_class: MagicMock,
    testnet_test_config: PeakConfig,
) -> None:
    """Test: Testnet-Run starten (Smoke-Test)."""
    orchestrator = TestnetOrchestrator(config=testnet_test_config)

    # Mock Session
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    # Mock Strategy
    mock_strategy_instance = MagicMock()
    mock_strategy_instance.key = "ma_crossover"
    mock_strategy.return_value = mock_strategy_instance

    # Mock Data Source
    mock_data_source.return_value = MagicMock()

    # Mock Run-Logger
    with patch("src.live.run_logging.create_run_logger_from_config") as mock_logger:
        mock_logger_instance = MagicMock()
        mock_logger_instance.run_dir = Path("/tmp/test_run")
        mock_logger.return_value = mock_logger_instance

        # Starte Run
        run_id = orchestrator.start_testnet_run(
            strategy_name="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1m",
            notes="Test-Run",
        )

        # Prüfe, dass Run-ID zurückgegeben wird
        assert run_id is not None
        assert run_id.startswith("testnet_")

        # Prüfe, dass Run registriert ist
        status = orchestrator.get_status(run_id=run_id)
        assert isinstance(status, RunInfo)
        assert status.run_id == run_id
        assert status.mode == "testnet"


# =============================================================================
# Status & Stop Tests
# =============================================================================


def test_get_status_all_runs(orchestrator: TestnetOrchestrator) -> None:
    """Test: Status aller Runs."""
    status = orchestrator.get_status()
    
    assert isinstance(status, list)
    # Initial sollte keine Runs vorhanden sein
    assert len(status) == 0


def test_get_status_run_not_found(orchestrator: TestnetOrchestrator) -> None:
    """Test: Status mit nicht existierender Run-ID."""
    with pytest.raises(RunNotFoundError, match="Run-ID nicht gefunden"):
        orchestrator.get_status(run_id="nonexistent_run_id")


@patch("src.live.shadow_session.ShadowPaperSession")
@patch("src.strategies.registry.create_strategy_from_config")
@patch("src.data.kraken_live.create_kraken_source_from_config")
def test_stop_run(
    mock_data_source: MagicMock,
    mock_strategy: MagicMock,
    mock_session_class: MagicMock,
    orchestrator: TestnetOrchestrator,
) -> None:
    """Test: Run stoppen."""
    # Mock Session
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    # Mock Strategy
    mock_strategy_instance = MagicMock()
    mock_strategy_instance.key = "ma_crossover"
    mock_strategy.return_value = mock_strategy_instance

    # Mock Data Source
    mock_data_source.return_value = MagicMock()

    # Mock Run-Logger
    with patch("src.live.run_logging.create_run_logger_from_config") as mock_logger:
        mock_logger_instance = MagicMock()
        mock_logger_instance.run_dir = Path("/tmp/test_run")
        mock_logger.return_value = mock_logger_instance

        # Starte Run
        run_id = orchestrator.start_shadow_run(
            strategy_name="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1m",
        )

        # Warte kurz, damit Run initialisiert wird
        time.sleep(0.1)

        # Stoppe Run
        orchestrator.stop_run(run_id)

        # Prüfe Status
        status = orchestrator.get_status(run_id=run_id)
        assert status.state in (RunState.STOPPED, RunState.STOPPING)


def test_stop_run_not_found(orchestrator: TestnetOrchestrator) -> None:
    """Test: Stoppen eines nicht existierenden Runs."""
    with pytest.raises(RunNotFoundError, match="Run-ID nicht gefunden"):
        orchestrator.stop_run("nonexistent_run_id")


# =============================================================================
# Event-Tailing Tests
# =============================================================================


@patch("src.live.shadow_session.ShadowPaperSession")
@patch("src.strategies.registry.create_strategy_from_config")
@patch("src.data.kraken_live.create_kraken_source_from_config")
def test_tail_events(
    mock_data_source: MagicMock,
    mock_strategy: MagicMock,
    mock_session_class: MagicMock,
    orchestrator: TestnetOrchestrator,
) -> None:
    """Test: Events tailen."""
    # Mock Session
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    # Mock Strategy
    mock_strategy_instance = MagicMock()
    mock_strategy_instance.key = "ma_crossover"
    mock_strategy.return_value = mock_strategy_instance

    # Mock Data Source
    mock_data_source.return_value = MagicMock()

    # Mock Run-Logger
    with patch("src.live.run_logging.create_run_logger_from_config") as mock_logger:
        mock_logger_instance = MagicMock()
        mock_logger_instance.run_dir = Path("/tmp/test_run")
        mock_logger.return_value = mock_logger_instance

        # Starte Run
        run_id = orchestrator.start_shadow_run(
            strategy_name="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1m",
        )

        # Mock load_run_events
        with patch("src.live.run_logging.load_run_events") as mock_load:
            import pandas as pd

            mock_load.return_value = pd.DataFrame(
                [
                    {"step": 1, "ts_event": "2025-12-07T12:00:00", "signal": 1, "equity": 10000.0},
                    {"step": 2, "ts_event": "2025-12-07T12:01:00", "signal": 0, "equity": 10050.0},
                ]
            )

            events = orchestrator.tail_events(run_id=run_id, limit=10)

            assert isinstance(events, list)
            assert len(events) == 2


def test_tail_events_run_not_found(orchestrator: TestnetOrchestrator) -> None:
    """Test: Events tailen mit nicht existierender Run-ID."""
    with pytest.raises(RunNotFoundError, match="Run-ID nicht gefunden"):
        orchestrator.tail_events(run_id="nonexistent_run_id", limit=10)

