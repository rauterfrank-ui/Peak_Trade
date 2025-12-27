# tests/test_run_testnet_session.py
"""
Peak_Trade: Smoke-Tests fuer run_testnet_session (Phase 35)
===========================================================

Smoke-Tests fuer das Testnet-Session-CLI-Script.
Prueft, dass das Script korrekt konfiguriert werden kann
und keine unerwarteten Fehler auftreten.

WICHTIG: Diese Tests machen KEINE echten API-Calls!
"""

from __future__ import annotations

import pytest
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, Mock, patch

# Projekt-Root zum Path hinzufuegen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_testnet_session import (
    TestnetSession,
    TestnetSessionConfig,
    TestnetSessionMetrics,
    build_testnet_session,
    create_strategy,
    load_testnet_session_config,
    setup_logging,
)
from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.core.peak_config import PeakConfig
from src.live.safety import SafetyGuard
from src.live.risk_limits import LiveRiskLimits, LiveRiskCheckResult
from src.orders.testnet_executor import (
    TestnetExchangeOrderExecutor,
    EnvironmentNotTestnetError,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def testnet_config_dict() -> Dict[str, Any]:
    """Erstellt ein Test-Config-Dict fuer Testnet-Session."""
    return {
        "environment": {
            "mode": "testnet",
            "enable_live_trading": False,
            "testnet_dry_run": True,
        },
        "testnet_session": {
            "enabled": True,
            "symbol": "BTC/EUR",
            "timeframe": "1m",
            "poll_interval_seconds": 60.0,
            "warmup_candles": 200,
            "start_balance": 10000.0,
            "position_fraction": 0.1,
            "fee_rate": 0.0026,
            "slippage_bps": 5.0,
        },
        "exchange": {
            "kraken_testnet": {
                "enabled": True,
                "base_url": "https://api.kraken.com",
                "api_key_env_var": "KRAKEN_TESTNET_API_KEY",
                "api_secret_env_var": "KRAKEN_TESTNET_API_SECRET",
                "validate_only": True,
                "timeout_seconds": 30.0,
                "max_retries": 3,
                "rate_limit_ms": 1000,
            },
        },
        "live_risk": {
            "enabled": True,
            "max_order_notional": 1000.0,
            "max_total_exposure_notional": 5000.0,
            "block_on_violation": True,
        },
        "shadow_paper_logging": {
            "enabled": True,
            "base_dir": "test_runs",
            "flush_interval_steps": 50,
            "format": "parquet",
        },
        "strategy": {
            "ma_crossover": {
                "fast_period": 10,
                "slow_period": 30,
                "stop_pct": 0.02,
            },
        },
    }


@pytest.fixture
def testnet_peak_config(testnet_config_dict: Dict[str, Any]) -> PeakConfig:
    """Erstellt eine PeakConfig fuer Testnet."""
    return PeakConfig(raw=testnet_config_dict)


@pytest.fixture
def paper_config_dict(testnet_config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Config mit Paper-Environment (nicht erlaubt fuer Testnet)."""
    config = testnet_config_dict.copy()
    config["environment"] = {"mode": "paper"}
    return config


@pytest.fixture
def mock_exchange_client() -> MagicMock:
    """Mock-Exchange-Client."""
    client = MagicMock()
    client.has_credentials = True
    client.create_order.return_value = "VALIDATED"
    client.fetch_ticker.return_value = {
        "symbol": "BTC/EUR",
        "last": 50000.0,
        "bid": 49990.0,
        "ask": 50010.0,
    }
    return client


# =============================================================================
# Config Tests
# =============================================================================


class TestConfigLoading:
    """Tests fuer Config-Loading."""

    def test_load_testnet_session_config(
        self,
        testnet_peak_config: PeakConfig,
    ) -> None:
        """Test: TestnetSessionConfig wird korrekt geladen."""
        config = load_testnet_session_config(testnet_peak_config)

        assert config.symbol == "BTC/EUR"
        assert config.timeframe == "1m"
        assert config.poll_interval_seconds == 60.0
        assert config.warmup_candles == 200
        assert config.start_balance == 10000.0
        assert config.position_fraction == 0.1

    def test_config_defaults(self) -> None:
        """Test: Defaults werden bei fehlenden Werten verwendet."""
        empty_config = PeakConfig(raw={})
        config = load_testnet_session_config(empty_config)

        # Defaults sollten gesetzt sein
        assert config.symbol == "BTC/EUR"
        assert config.timeframe == "1m"


class TestSessionConfig:
    """Tests fuer TestnetSessionConfig Dataclass."""

    def test_session_config_dataclass(self) -> None:
        """Test: TestnetSessionConfig hat korrekte Werte."""
        config = TestnetSessionConfig(
            symbol="ETH/USD",
            timeframe="5m",
            poll_interval_seconds=30.0,
            warmup_candles=100,
            start_balance=5000.0,
            position_fraction=0.2,
        )

        assert config.symbol == "ETH/USD"
        assert config.timeframe == "5m"
        assert config.poll_interval_seconds == 30.0
        assert config.start_balance == 5000.0


# =============================================================================
# Session Metrics Tests
# =============================================================================


class TestSessionMetrics:
    """Tests fuer TestnetSessionMetrics."""

    def test_metrics_default_values(self) -> None:
        """Test: Default-Werte sind korrekt."""
        metrics = TestnetSessionMetrics()

        assert metrics.steps == 0
        assert metrics.total_orders == 0
        assert metrics.filled_orders == 0
        assert metrics.current_position == 0.0

    def test_metrics_to_dict(self) -> None:
        """Test: Metriken werden korrekt zu Dict konvertiert."""
        metrics = TestnetSessionMetrics(
            steps=10,
            total_orders=5,
            filled_orders=4,
            rejected_orders=1,
            current_position=0.05,
        )

        result = metrics.to_dict()

        assert result["steps"] == 10
        assert result["total_orders"] == 5
        assert result["filled_orders"] == 4
        assert result["fill_rate"] == 0.8  # 4/5


# =============================================================================
# Strategy Factory Tests
# =============================================================================


class TestStrategyFactory:
    """Tests fuer Strategy-Factory."""

    def test_create_ma_crossover_strategy(
        self,
        testnet_peak_config: PeakConfig,
    ) -> None:
        """Test: MA-Crossover-Strategie wird korrekt erstellt."""
        strategy = create_strategy("ma_crossover", testnet_peak_config)

        assert strategy is not None
        assert hasattr(strategy, "key")

    def test_unknown_strategy_raises(
        self,
        testnet_peak_config: PeakConfig,
    ) -> None:
        """Test: Unbekannte Strategie wirft ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_strategy("unknown_strategy", testnet_peak_config)

        assert "Unbekannte Strategie" in str(exc_info.value)


# =============================================================================
# Session Builder Tests
# =============================================================================


class TestSessionBuilder:
    """Tests fuer build_testnet_session."""

    @patch("scripts.run_testnet_session.create_kraken_testnet_client_from_config")
    def test_build_session_testnet_env(
        self,
        mock_create_client: MagicMock,
        mock_exchange_client: MagicMock,
        testnet_peak_config: PeakConfig,
    ) -> None:
        """Test: Session wird im Testnet-Modus erfolgreich gebaut."""
        mock_create_client.return_value = mock_exchange_client

        session = build_testnet_session(
            cfg=testnet_peak_config,
            strategy_name="ma_crossover",
            enable_logging=False,  # Logging deaktivieren fuer Test
        )

        assert session is not None
        assert isinstance(session, TestnetSession)

    @patch("scripts.run_testnet_session.create_kraken_testnet_client_from_config")
    def test_build_session_paper_env_fails(
        self,
        mock_create_client: MagicMock,
        mock_exchange_client: MagicMock,
        paper_config_dict: Dict[str, Any],
    ) -> None:
        """Test: Session im Paper-Modus schlaegt fehl."""
        mock_create_client.return_value = mock_exchange_client
        cfg = PeakConfig(raw=paper_config_dict)

        with pytest.raises(EnvironmentNotTestnetError):
            build_testnet_session(
                cfg=cfg,
                strategy_name="ma_crossover",
                enable_logging=False,
            )

    @patch("scripts.run_testnet_session.create_kraken_testnet_client_from_config")
    def test_build_session_with_overrides(
        self,
        mock_create_client: MagicMock,
        mock_exchange_client: MagicMock,
        testnet_peak_config: PeakConfig,
    ) -> None:
        """Test: Overrides werden korrekt angewendet."""
        mock_create_client.return_value = mock_exchange_client

        session = build_testnet_session(
            cfg=testnet_peak_config,
            strategy_name="ma_crossover",
            symbol_override="ETH/EUR",
            timeframe_override="5m",
            enable_logging=False,
        )

        assert session._session_config.symbol == "ETH/EUR"
        assert session._session_config.timeframe == "5m"


# =============================================================================
# TestnetSession Tests
# =============================================================================


class TestTestnetSession:
    """Tests fuer TestnetSession-Klasse."""

    @pytest.fixture
    def mock_session(
        self,
        mock_exchange_client: MagicMock,
    ) -> TestnetSession:
        """Erstellt eine Mock-TestnetSession."""
        env_config = EnvironmentConfig(
            environment=TradingEnvironment.TESTNET,
            testnet_dry_run=True,
        )
        session_config = TestnetSessionConfig()
        safety_guard = SafetyGuard(env_config=env_config)

        # Mock Risk-Limits
        risk_limits = MagicMock(spec=LiveRiskLimits)
        risk_limits.check_orders.return_value = LiveRiskCheckResult(
            allowed=True, reasons=[], metrics={}
        )

        # Mock Executor
        executor = MagicMock(spec=TestnetExchangeOrderExecutor)
        executor.effective_mode = "testnet_validated"
        executor.get_execution_summary.return_value = {
            "total_orders": 0,
            "filled_orders": 0,
            "mode": "testnet_validated",
        }

        # Mock Strategy
        strategy = MagicMock()
        strategy.key = "ma_crossover"

        return TestnetSession(
            env_config=env_config,
            session_config=session_config,
            exchange_client=mock_exchange_client,
            executor=executor,
            strategy=strategy,
            risk_limits=risk_limits,
            run_logger=None,
        )

    def test_session_initialization(self, mock_session: TestnetSession) -> None:
        """Test: Session wird korrekt initialisiert."""
        assert mock_session.is_running is False
        assert mock_session.metrics.steps == 0

    def test_session_warmup(self, mock_session: TestnetSession) -> None:
        """Test: Warmup funktioniert."""
        mock_session.warmup()

        assert mock_session.metrics.start_time is not None
        mock_session._client.fetch_ticker.assert_called_once()

    def test_session_step_once(self, mock_session: TestnetSession) -> None:
        """Test: step_once fuehrt einen Schritt aus."""
        # Warmup zuerst
        mock_session.warmup()

        # Fuege Preis-Buffer hinzu (fuer Signal-Generierung)
        for i in range(25):
            mock_session._price_buffer.append(
                {
                    "timestamp": None,
                    "close": 50000.0 + i * 10,
                }
            )

        result = mock_session.step_once()

        assert mock_session.metrics.steps == 1

    def test_session_get_execution_summary(self, mock_session: TestnetSession) -> None:
        """Test: Execution-Summary wird korrekt erstellt."""
        summary = mock_session.get_execution_summary()

        assert "session_metrics" in summary
        assert "executor_summary" in summary
        assert "config" in summary

    def test_session_env_not_testnet_fails(self) -> None:
        """Test: Session mit Paper-Env schlaegt fehl."""
        paper_config = EnvironmentConfig(
            environment=TradingEnvironment.PAPER,
        )

        with pytest.raises(EnvironmentNotTestnetError):
            TestnetSession(
                env_config=paper_config,
                session_config=TestnetSessionConfig(),
                exchange_client=MagicMock(),
                executor=MagicMock(),
                strategy=MagicMock(),
                risk_limits=MagicMock(),
            )


# =============================================================================
# Logging Tests
# =============================================================================


class TestLogging:
    """Tests fuer Logging-Setup."""

    def test_setup_logging(self) -> None:
        """Test: Logging wird korrekt konfiguriert."""
        logger = setup_logging("INFO")

        assert logger is not None
        assert logger.name == "testnet_session"


# =============================================================================
# CLI Integration Tests
# =============================================================================


class TestCLIIntegration:
    """Integration-Tests fuer CLI."""

    @patch("scripts.run_testnet_session.create_kraken_testnet_client_from_config")
    @patch("scripts.run_testnet_session.load_config")
    def test_main_dry_run(
        self,
        mock_load_config: MagicMock,
        mock_create_client: MagicMock,
        testnet_config_dict: Dict[str, Any],
        mock_exchange_client: MagicMock,
    ) -> None:
        """Test: CLI dry-run funktioniert."""
        mock_load_config.return_value = PeakConfig(raw=testnet_config_dict)
        mock_create_client.return_value = mock_exchange_client

        # Importiere main nach Patches
        from scripts.run_testnet_session import main

        with patch("sys.argv", ["run_testnet_session.py", "--dry-run"]):
            with patch("pathlib.Path.exists", return_value=True):
                result = main()

        assert result == 0  # Success

    @patch("scripts.run_testnet_session.load_config")
    def test_main_config_not_found(
        self,
        mock_load_config: MagicMock,
    ) -> None:
        """Test: CLI mit nicht gefundener Config schlaegt fehl."""
        from scripts.run_testnet_session import main

        with patch("sys.argv", ["run_testnet_session.py", "--config", "nonexistent.toml"]):
            with patch("pathlib.Path.exists", return_value=False):
                result = main()

        assert result == 1  # Error
