# tests/test_exchange_order_executor.py
"""
Peak_Trade: Tests fuer TestnetExchangeOrderExecutor (Phase 35)
==============================================================

Tests fuer den Testnet-Order-Executor mit Mocking.
Prueft Environment-Guards, Risk-Integration und Order-Handling.

WICHTIG: Diese Tests machen KEINE echten API-Calls!
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

from src.orders.base import OrderRequest, OrderFill, OrderExecutionResult
from src.orders.testnet_executor import (
    TestnetExchangeOrderExecutor,
    TestnetExecutionLog,
    EnvironmentNotTestnetError,
    RiskLimitViolationError,
    EXECUTION_MODE_TESTNET_LIVE,
    EXECUTION_MODE_TESTNET_VALIDATED,
)
from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.live.safety import SafetyGuard
from src.live.risk_limits import LiveRiskLimits, LiveRiskConfig, LiveRiskCheckResult


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def testnet_env_config() -> EnvironmentConfig:
    """Erstellt eine Testnet-Environment-Config."""
    return EnvironmentConfig(
        environment=TradingEnvironment.TESTNET,
        enable_live_trading=False,
        testnet_dry_run=False,  # Echte Testnet-Orders erlaubt
        log_all_orders=True,
    )


@pytest.fixture
def paper_env_config() -> EnvironmentConfig:
    """Erstellt eine Paper-Environment-Config (nicht erlaubt fuer Testnet)."""
    return EnvironmentConfig(
        environment=TradingEnvironment.PAPER,
        enable_live_trading=False,
        testnet_dry_run=True,
    )


@pytest.fixture
def live_env_config() -> EnvironmentConfig:
    """Erstellt eine Live-Environment-Config (nicht erlaubt fuer Testnet)."""
    return EnvironmentConfig(
        environment=TradingEnvironment.LIVE,
        enable_live_trading=True,
    )


@pytest.fixture
def safety_guard_testnet(testnet_env_config: EnvironmentConfig) -> SafetyGuard:
    """Erstellt einen SafetyGuard fuer Testnet."""
    return SafetyGuard(env_config=testnet_env_config)


@pytest.fixture
def mock_exchange_client() -> MagicMock:
    """Erstellt einen Mock-Exchange-Client."""
    client = MagicMock()
    client.create_order.return_value = "VALIDATED"  # Default: validate_only
    client.fetch_order_status.return_value = MagicMock(
        txid="TEST123",
        status="closed",
        vol=0.01,
        vol_exec=0.01,
        avg_price=50000.0,
        fee=1.30,
        timestamp=datetime.now(timezone.utc),
    )
    client.fetch_order_as_fill.return_value = OrderFill(
        symbol="BTC/EUR",
        side="buy",
        quantity=0.01,
        price=50000.0,
        timestamp=datetime.now(timezone.utc),
        fee=1.30,
        fee_currency="EUR",
    )
    return client


@pytest.fixture
def mock_risk_limits_allow() -> MagicMock:
    """Erstellt Mock-Risk-Limits die alles erlauben."""
    limits = MagicMock(spec=LiveRiskLimits)
    limits.check_orders.return_value = LiveRiskCheckResult(
        allowed=True,
        reasons=[],
        metrics={"total_notional": 500.0},
    )
    return limits


@pytest.fixture
def mock_risk_limits_block() -> MagicMock:
    """Erstellt Mock-Risk-Limits die alles blockieren."""
    limits = MagicMock(spec=LiveRiskLimits)
    limits.check_orders.return_value = LiveRiskCheckResult(
        allowed=False,
        reasons=["max_order_notional_exceeded", "max_daily_loss_reached"],
        metrics={"total_notional": 5000.0},
    )
    return limits


@pytest.fixture
def sample_order() -> OrderRequest:
    """Erstellt eine Test-Order."""
    return OrderRequest(
        symbol="BTC/EUR",
        side="buy",
        quantity=0.01,
        order_type="market",
        client_id="test_order_001",
    )


@pytest.fixture
def testnet_executor(
    mock_exchange_client: MagicMock,
    safety_guard_testnet: SafetyGuard,
    mock_risk_limits_allow: MagicMock,
    testnet_env_config: EnvironmentConfig,
) -> TestnetExchangeOrderExecutor:
    """Erstellt einen TestnetExchangeOrderExecutor."""
    return TestnetExchangeOrderExecutor(
        exchange_client=mock_exchange_client,
        safety_guard=safety_guard_testnet,
        risk_limits=mock_risk_limits_allow,
        env_config=testnet_env_config,
    )


# =============================================================================
# Environment Guard Tests
# =============================================================================


class TestEnvironmentGuards:
    """Tests fuer Environment-Pruefungen."""

    def test_init_with_testnet_env(
        self,
        mock_exchange_client: MagicMock,
        safety_guard_testnet: SafetyGuard,
        testnet_env_config: EnvironmentConfig,
    ) -> None:
        """Test: Initialisierung im Testnet-Modus erfolgreich."""
        executor = TestnetExchangeOrderExecutor(
            exchange_client=mock_exchange_client,
            safety_guard=safety_guard_testnet,
            env_config=testnet_env_config,
        )

        assert executor.effective_mode == EXECUTION_MODE_TESTNET_LIVE

    def test_init_with_paper_env_fails(
        self,
        mock_exchange_client: MagicMock,
        paper_env_config: EnvironmentConfig,
    ) -> None:
        """Test: Initialisierung im Paper-Modus schlaegt fehl."""
        safety_guard = SafetyGuard(env_config=paper_env_config)

        with pytest.raises(EnvironmentNotTestnetError) as exc_info:
            TestnetExchangeOrderExecutor(
                exchange_client=mock_exchange_client,
                safety_guard=safety_guard,
                env_config=paper_env_config,
            )

        assert "TESTNET" in str(exc_info.value)

    def test_init_with_live_env_fails(
        self,
        mock_exchange_client: MagicMock,
        live_env_config: EnvironmentConfig,
    ) -> None:
        """Test: Initialisierung im Live-Modus schlaegt fehl."""
        safety_guard = SafetyGuard(env_config=live_env_config)

        with pytest.raises(EnvironmentNotTestnetError) as exc_info:
            TestnetExchangeOrderExecutor(
                exchange_client=mock_exchange_client,
                safety_guard=safety_guard,
                env_config=live_env_config,
            )

        assert "TESTNET" in str(exc_info.value)

    def test_dry_run_mode_detection(
        self,
        mock_exchange_client: MagicMock,
        safety_guard_testnet: SafetyGuard,
    ) -> None:
        """Test: testnet_dry_run wird korrekt erkannt."""
        # Mit dry_run=True
        dry_run_config = EnvironmentConfig(
            environment=TradingEnvironment.TESTNET,
            testnet_dry_run=True,
        )
        safety_guard = SafetyGuard(env_config=dry_run_config)

        executor = TestnetExchangeOrderExecutor(
            exchange_client=mock_exchange_client,
            safety_guard=safety_guard,
            env_config=dry_run_config,
        )

        assert executor.effective_mode == EXECUTION_MODE_TESTNET_VALIDATED


# =============================================================================
# Risk Integration Tests
# =============================================================================


class TestRiskIntegration:
    """Tests fuer Risk-Limit-Integration."""

    def test_risk_check_passed(
        self,
        testnet_executor: TestnetExchangeOrderExecutor,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Order wird bei bestandenem Risk-Check ausgefuehrt."""
        result = testnet_executor.execute_order(sample_order, current_price=50000.0)

        assert result.status == "filled"
        assert result.is_filled is True
        assert "VALIDATED" in str(result.metadata.get("exchange_order_id", ""))

    def test_risk_check_blocked(
        self,
        mock_exchange_client: MagicMock,
        safety_guard_testnet: SafetyGuard,
        mock_risk_limits_block: MagicMock,
        testnet_env_config: EnvironmentConfig,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Order wird bei Risk-Verletzung blockiert."""
        executor = TestnetExchangeOrderExecutor(
            exchange_client=mock_exchange_client,
            safety_guard=safety_guard_testnet,
            risk_limits=mock_risk_limits_block,
            env_config=testnet_env_config,
        )

        result = executor.execute_order(sample_order, current_price=50000.0)

        assert result.status == "rejected"
        assert result.is_rejected is True
        assert "risk_limit_violation" in (result.reason or "")
        assert "max_order_notional_exceeded" in (result.reason or "")

        # Exchange-Client sollte NICHT aufgerufen worden sein
        mock_exchange_client.create_order.assert_not_called()

    def test_no_risk_limits(
        self,
        mock_exchange_client: MagicMock,
        safety_guard_testnet: SafetyGuard,
        testnet_env_config: EnvironmentConfig,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Ohne Risk-Limits wird Order trotzdem ausgefuehrt."""
        executor = TestnetExchangeOrderExecutor(
            exchange_client=mock_exchange_client,
            safety_guard=safety_guard_testnet,
            risk_limits=None,  # Keine Risk-Limits
            env_config=testnet_env_config,
        )

        result = executor.execute_order(sample_order, current_price=50000.0)

        assert result.status == "filled"
        mock_exchange_client.create_order.assert_called_once()


# =============================================================================
# Order Execution Tests
# =============================================================================


class TestOrderExecution:
    """Tests fuer Order-Ausfuehrung."""

    def test_execute_single_order_validated(
        self,
        testnet_executor: TestnetExchangeOrderExecutor,
        mock_exchange_client: MagicMock,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Einzelne Order wird im validate_only-Modus ausgefuehrt."""
        mock_exchange_client.create_order.return_value = "VALIDATED"

        result = testnet_executor.execute_order(sample_order, current_price=50000.0)

        assert result.status == "filled"
        assert result.metadata.get("validated_only") is True
        assert result.metadata.get("exchange_order_id") == "VALIDATED"

    def test_execute_single_order_real(
        self,
        mock_exchange_client: MagicMock,
        safety_guard_testnet: SafetyGuard,
        mock_risk_limits_allow: MagicMock,
        testnet_env_config: EnvironmentConfig,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Echte Order mit Transaction-ID."""
        mock_exchange_client.create_order.return_value = "OTEST-REAL-123"
        mock_exchange_client.fetch_order_as_fill.return_value = OrderFill(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            price=50000.0,
            timestamp=datetime.now(timezone.utc),
            fee=1.30,
            fee_currency="EUR",
        )

        executor = TestnetExchangeOrderExecutor(
            exchange_client=mock_exchange_client,
            safety_guard=safety_guard_testnet,
            risk_limits=mock_risk_limits_allow,
            env_config=testnet_env_config,
        )

        result = executor.execute_order(sample_order, current_price=50000.0)

        assert result.status == "filled"
        assert result.metadata.get("exchange_order_id") == "OTEST-REAL-123"
        assert result.metadata.get("validated_only") is False
        assert result.fill is not None
        assert result.fill.quantity == 0.01

    def test_execute_multiple_orders(
        self,
        testnet_executor: TestnetExchangeOrderExecutor,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Mehrere Orders werden ausgefuehrt."""
        orders = [
            sample_order,
            OrderRequest(symbol="ETH/EUR", side="sell", quantity=0.1, order_type="market"),
        ]

        results = testnet_executor.execute_orders(orders, current_price=50000.0)

        assert len(results) == 2
        assert all(r.status == "filled" for r in results)

    def test_execute_orders_batch_risk_block(
        self,
        mock_exchange_client: MagicMock,
        safety_guard_testnet: SafetyGuard,
        mock_risk_limits_block: MagicMock,
        testnet_env_config: EnvironmentConfig,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Batch-Risk-Check blockiert alle Orders."""
        executor = TestnetExchangeOrderExecutor(
            exchange_client=mock_exchange_client,
            safety_guard=safety_guard_testnet,
            risk_limits=mock_risk_limits_block,
            env_config=testnet_env_config,
        )

        orders = [sample_order, sample_order]
        results = executor.execute_orders(orders, current_price=50000.0)

        assert len(results) == 2
        assert all(r.status == "rejected" for r in results)
        assert all("batch_risk_limit_violation" in (r.reason or "") for r in results)


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests fuer Fehlerbehandlung."""

    def test_exchange_error_handling(
        self,
        mock_exchange_client: MagicMock,
        safety_guard_testnet: SafetyGuard,
        mock_risk_limits_allow: MagicMock,
        testnet_env_config: EnvironmentConfig,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Exchange-Fehler werden korrekt behandelt."""
        mock_exchange_client.create_order.side_effect = Exception("API Error")

        executor = TestnetExchangeOrderExecutor(
            exchange_client=mock_exchange_client,
            safety_guard=safety_guard_testnet,
            risk_limits=mock_risk_limits_allow,
            env_config=testnet_env_config,
        )

        result = executor.execute_order(sample_order, current_price=50000.0)

        assert result.status == "rejected"
        assert "exchange_error" in (result.reason or "")
        assert "API Error" in (result.reason or "")


# =============================================================================
# Logging Tests
# =============================================================================


class TestLogging:
    """Tests fuer Execution-Logging."""

    def test_execution_log_created(
        self,
        testnet_executor: TestnetExchangeOrderExecutor,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Execution-Log-Eintraege werden erstellt."""
        testnet_executor.execute_order(sample_order, current_price=50000.0)

        log = testnet_executor.get_execution_log()
        assert len(log) == 1
        assert isinstance(log[0], TestnetExecutionLog)
        assert log[0].request == sample_order

    def test_execution_count(
        self,
        testnet_executor: TestnetExchangeOrderExecutor,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Execution-Count wird korrekt gezaehlt."""
        assert testnet_executor.execution_count == 0

        testnet_executor.execute_order(sample_order, current_price=50000.0)
        assert testnet_executor.execution_count == 1

        testnet_executor.execute_order(sample_order, current_price=50000.0)
        assert testnet_executor.execution_count == 2

    def test_execution_summary(
        self,
        testnet_executor: TestnetExchangeOrderExecutor,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Execution-Summary wird korrekt erstellt."""
        testnet_executor.execute_order(sample_order, current_price=50000.0)

        summary = testnet_executor.get_execution_summary()

        assert summary["total_orders"] == 1
        assert summary["filled_orders"] == 1
        assert summary["rejected_orders"] == 0
        assert summary["environment"] == "testnet"

    def test_reset(
        self,
        testnet_executor: TestnetExchangeOrderExecutor,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Reset setzt Zaehler und Log zurueck."""
        testnet_executor.execute_order(sample_order, current_price=50000.0)
        assert testnet_executor.execution_count == 1

        testnet_executor.reset()

        assert testnet_executor.execution_count == 0
        assert len(testnet_executor.get_execution_log()) == 0


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration-Tests."""

    def test_full_flow_validated(
        self,
        mock_exchange_client: MagicMock,
        testnet_env_config: EnvironmentConfig,
    ) -> None:
        """Test: Vollstaendiger Flow mit validate_only."""
        # Setup
        mock_exchange_client.create_order.return_value = "VALIDATED"

        safety_guard = SafetyGuard(env_config=testnet_env_config)

        # Risk-Limits die alles erlauben
        risk_limits = MagicMock(spec=LiveRiskLimits)
        risk_limits.check_orders.return_value = LiveRiskCheckResult(
            allowed=True, reasons=[], metrics={}
        )

        executor = TestnetExchangeOrderExecutor(
            exchange_client=mock_exchange_client,
            safety_guard=safety_guard,
            risk_limits=risk_limits,
            env_config=testnet_env_config,
        )

        # Order erstellen und ausfuehren
        order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.05,
            order_type="market",
        )

        result = executor.execute_order(order, current_price=50000.0)

        # Assertions
        assert result.status == "filled"
        assert result.metadata["mode"] == EXECUTION_MODE_TESTNET_VALIDATED
        assert executor.execution_count == 1

        # Risk-Check wurde aufgerufen
        risk_limits.check_orders.assert_called_once()

        # Exchange-Client wurde aufgerufen
        mock_exchange_client.create_order.assert_called_once()
