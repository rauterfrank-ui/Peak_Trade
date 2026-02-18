#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# tests/test_execution_pipeline_governance.py
"""
Peak_Trade: Tests fuer ExecutionPipeline Phase 16A V2 (Governance-aware)
========================================================================

Tests fuer die Governance-Integration:
- env="live" → Governance-Exception, kein Executor-Aufruf
- env="paper"/"shadow"/"testnet" + Risk ok → Executor wird aufgerufen
- Risk-Fail → keine Ausfuehrung, Result markiert als blocked_by_risk
- Governance-Modul wird wirklich genutzt (get_governance_status("live_order_execution"))
- OrderIntent und submit_order() API

WICHTIG: Keine echten Orders - alles Paper/Sandbox.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from unittest.mock import patch, MagicMock

import pytest

# Projekt-Root zum Python-Path hinzufuegen
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# ============================================================================
# Fake-Komponenten fuer Tests
# ============================================================================


@dataclass
class FakeLiveRiskCheckResult:
    """Fake LiveRiskCheckResult fuer Tests."""

    allowed: bool
    reasons: List[str]
    metrics: dict


class FakeSafetyGuard:
    """Fake SafetyGuard fuer Tests."""

    def __init__(self, allow_orders: bool = True, raise_exception: Optional[Exception] = None):
        self.allow_orders = allow_orders
        self.raise_exception = raise_exception
        self.called = False

    def ensure_may_place_order(
        self, *, is_testnet: bool = False, context: Optional[dict] = None
    ) -> None:
        """Fake ensure_may_place_order."""
        self.called = True
        if self.raise_exception:
            raise self.raise_exception
        if not self.allow_orders:
            from src.live.safety import SafetyBlockedError

            raise SafetyBlockedError("Fake SafetyGuard blockiert Orders")


class FakeRiskLimits:
    """Fake LiveRiskLimits fuer Tests."""

    def __init__(self, allow_orders: bool = True):
        self.allow_orders = allow_orders
        self.called = False
        self.last_orders = None

    def check_orders(self, orders, *, current_date=None) -> FakeLiveRiskCheckResult:
        """Fake check_orders."""
        self.called = True
        self.last_orders = orders
        if self.allow_orders:
            return FakeLiveRiskCheckResult(
                allowed=True,
                reasons=[],
                metrics={"total_notional": 100.0},
            )
        else:
            return FakeLiveRiskCheckResult(
                allowed=False,
                reasons=["fake_risk_limit_violation"],
                metrics={"total_notional": 100.0},
            )


class FakeRunLogger:
    """Fake LiveRunLogger fuer Tests."""

    def __init__(self):
        self.events: List[dict] = []
        self.called = False

    def log_event(self, event) -> None:
        """Fake log_event."""
        self.called = True
        self.events.append(event)


# ============================================================================
# Tests fuer Governance-Integration (Phase 16A V2)
# ============================================================================


class TestExecutionPipelineGovernance:
    """Tests fuer Governance-Integration in ExecutionPipeline."""

    def test_live_env_raises_governance_exception(self):
        """
        env="live" → GovernanceViolationError/LiveExecutionLockedError wird geworfen.

        Akzeptanzkriterium: Bei env="live" wird eine Exception geworfen,
        keine Orders werden ausgefuehrt.
        """
        from src.execution import ExecutionPipeline, OrderIntent, LiveExecutionLockedError
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor

        # LIVE-Mode Environment
        env_config = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
        )

        intent = OrderIntent(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            current_price=50000.0,
        )

        # submit_order() mit raise_on_governance_violation=True sollte Exception werfen
        with pytest.raises(LiveExecutionLockedError) as exc_info:
            pipeline.submit_order(intent, raise_on_governance_violation=True)

        assert (
            "governance" in str(exc_info.value).lower() or "locked" in str(exc_info.value).lower()
        )

    def test_live_env_returns_blocked_result_without_raise(self):
        """
        env="live" + raise_on_governance_violation=False → ExecutionResult mit status=BLOCKED_BY_GOVERNANCE.
        """
        from src.execution import ExecutionPipeline, OrderIntent, ExecutionStatus
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor

        # LIVE-Mode Environment
        env_config = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
        )

        intent = OrderIntent(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            current_price=50000.0,
        )

        # Mit raise_on_governance_violation=False sollte Result zurueckgegeben werden
        result = pipeline.submit_order(intent, raise_on_governance_violation=False)

        assert result.rejected is True
        assert result.status == ExecutionStatus.BLOCKED_BY_GOVERNANCE
        assert result.is_blocked_by_governance is True
        assert result.governance_status == "locked"
        assert result.environment == "live"
        assert len(result.executed_orders) == 0

    def test_governance_module_is_actually_called(self):
        """
        Governance-Modul wird wirklich aufgerufen (get_governance_status("live_order_execution")).
        """
        from src.execution import ExecutionPipeline, OrderIntent
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor

        # LIVE-Mode Environment
        env_config = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
        )

        intent = OrderIntent(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            current_price=50000.0,
        )

        # Patche get_governance_status um Aufruf zu verifizieren
        with patch("src.execution.pipeline.get_governance_status") as mock_governance:
            mock_governance.return_value = "locked"

            result = pipeline.submit_order(intent, raise_on_governance_violation=False)

            # Verify get_governance_status wurde mit dem richtigen Key aufgerufen
            mock_governance.assert_called_with("live_order_execution")

    def test_paper_env_executes_orders(self):
        """
        env="paper" + Risk ok → Executor wird aufgerufen, Orders werden ausgefuehrt.
        """
        from src.execution import ExecutionPipeline, OrderIntent, ExecutionStatus
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor

        # PAPER-Mode Environment
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        safety_guard = FakeSafetyGuard(allow_orders=True)
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
            safety_guard=safety_guard,
        )

        intent = OrderIntent(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            strategy_key="test_strategy",
            current_price=50000.0,
        )

        result = pipeline.submit_order(intent)

        assert result.rejected is False
        assert result.status == ExecutionStatus.SUCCESS
        assert result.is_success is True
        assert result.environment == "paper"
        assert len(result.executed_orders) == 1
        assert result.executed_orders[0].status == "filled"
        # Governance-Status sollte "locked" sein (fuer live_order_execution)
        assert result.governance_status == "locked"

    def test_shadow_env_executes_orders(self):
        """
        env="shadow" + Risk ok → ShadowOrderExecutor wird aufgerufen.
        """
        from src.execution import ExecutionPipeline, OrderIntent, ExecutionStatus
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.shadow import ShadowOrderExecutor, ShadowMarketContext

        # PAPER-Mode mit Shadow-Executor
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        safety_guard = FakeSafetyGuard(allow_orders=True)
        shadow_ctx = ShadowMarketContext(prices={"BTC/EUR": 50000.0})
        executor = ShadowOrderExecutor(market_context=shadow_ctx)

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
            safety_guard=safety_guard,
        )

        intent = OrderIntent(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            current_price=50000.0,
        )

        result = pipeline.submit_order(intent)

        assert result.rejected is False
        assert result.status == ExecutionStatus.SUCCESS
        assert result.environment == "shadow"  # Erkannt durch Executor-Typ
        assert len(result.executed_orders) == 1
        assert result.executed_orders[0].metadata.get("shadow") is True

    def test_testnet_env_executes_orders(self):
        """
        env="testnet" + Risk ok → Orders werden im Testnet-Modus ausgefuehrt.
        """
        from src.execution import ExecutionPipeline, OrderIntent, ExecutionStatus
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor

        # TESTNET-Mode Environment
        env_config = EnvironmentConfig(
            environment=TradingEnvironment.TESTNET,
            testnet_dry_run=True,  # Dry-Run fuer Tests
        )
        safety_guard = FakeSafetyGuard(allow_orders=True)
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
            safety_guard=safety_guard,
        )

        intent = OrderIntent(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            current_price=50000.0,
        )

        result = pipeline.submit_order(intent)

        assert result.rejected is False
        assert result.status == ExecutionStatus.SUCCESS
        assert result.environment == "testnet"
        assert len(result.executed_orders) == 1

    def test_risk_fail_blocks_execution(self):
        """
        Risk-Check fehlgeschlagen → keine Ausfuehrung, Result markiert als blocked_by_risk.
        """
        from src.execution import ExecutionPipeline, OrderIntent, ExecutionStatus
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor

        # PAPER-Mode, aber Risk-Limits blockieren
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        safety_guard = FakeSafetyGuard(allow_orders=True)
        risk_limits = FakeRiskLimits(allow_orders=False)  # Risk blockiert
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
            safety_guard=safety_guard,
            risk_limits=risk_limits,
        )

        intent = OrderIntent(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            current_price=50000.0,
        )

        result = pipeline.submit_order(intent)

        assert result.rejected is True
        assert result.status == ExecutionStatus.BLOCKED_BY_RISK
        assert result.is_blocked_by_risk is True
        assert len(result.executed_orders) == 0
        assert risk_limits.called is True
        assert "risk_limits" in result.reason

    def test_no_executor_call_when_live_blocked(self):
        """
        Bei env="live" wird der Executor NICHT aufgerufen.
        """
        from src.execution import ExecutionPipeline, OrderIntent
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor
        from unittest.mock import MagicMock

        # LIVE-Mode Environment
        env_config = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))

        # Mock den Executor um Aufruf zu pruefen
        executor.execute_orders = MagicMock(return_value=[])

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
        )

        intent = OrderIntent(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            current_price=50000.0,
        )

        result = pipeline.submit_order(intent, raise_on_governance_violation=False)

        # Executor sollte NICHT aufgerufen worden sein
        executor.execute_orders.assert_not_called()
        assert result.rejected is True

    def test_order_intent_to_order_request_conversion(self):
        """
        OrderIntent wird korrekt zu OrderRequest konvertiert.
        """
        from src.execution import OrderIntent

        intent = OrderIntent(
            symbol="ETH/EUR",
            side="sell",
            quantity=0.5,
            order_type="limit",
            limit_price=3000.0,
            strategy_key="momentum_strategy",
            current_price=3100.0,
            metadata={"extra_info": "test"},
        )

        order = intent.to_order_request(client_id="test_001")

        assert order.symbol == "ETH/EUR"
        assert order.side == "sell"
        assert order.quantity == 0.5
        assert order.order_type == "limit"
        assert order.limit_price == 3000.0
        assert order.client_id == "test_001"
        assert order.metadata.get("strategy_key") == "momentum_strategy"
        assert order.metadata.get("current_price") == 3100.0
        assert order.metadata.get("extra_info") == "test"

    def test_governance_status_in_result(self):
        """
        ExecutionResult enthaelt governance_status.
        """
        from src.execution import ExecutionPipeline, OrderIntent
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor

        # PAPER-Mode
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        safety_guard = FakeSafetyGuard(allow_orders=True)
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
            safety_guard=safety_guard,
        )

        intent = OrderIntent(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            current_price=50000.0,
        )

        result = pipeline.submit_order(intent)

        # Governance-Status sollte gesetzt sein
        assert result.governance_status is not None
        # live_order_execution ist "locked"
        assert result.governance_status == "locked"

    def test_invalid_quantity_returns_error(self):
        """
        Ungueltiger OrderIntent (quantity <= 0) liefert INVALID-Result.
        """
        from src.execution import ExecutionPipeline, OrderIntent, ExecutionStatus
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor

        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))
        pipeline = ExecutionPipeline(executor=executor)

        intent = OrderIntent(
            symbol="BTC/EUR",
            side="buy",
            quantity=0,  # Ungueltig!
            current_price=50000.0,
        )

        result = pipeline.submit_order(intent)

        assert result.rejected is True
        assert result.status == ExecutionStatus.INVALID
        assert "quantity" in result.reason.lower()


class TestExecuteWithSafetyGovernance:
    """Tests fuer execute_with_safety() mit Governance-Integration."""

    def test_execute_with_safety_includes_governance_check(self):
        """
        execute_with_safety() prueft auch Governance (Phase 16A V2).
        """
        from src.execution import ExecutionPipeline, ExecutionStatus
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor
        from src.orders.base import OrderRequest

        # LIVE-Mode Environment
        env_config = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
        )

        order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01)
        result = pipeline.execute_with_safety([order])

        # Sollte durch Governance blockiert werden
        assert result.rejected is True
        assert result.status == ExecutionStatus.BLOCKED_BY_GOVERNANCE
        assert result.governance_status == "locked"

    def test_execute_with_safety_returns_environment(self):
        """
        execute_with_safety() setzt environment im Result.
        """
        from src.execution import ExecutionPipeline, ExecutionStatus
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor
        from src.orders.base import OrderRequest

        # PAPER-Mode Environment
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        safety_guard = FakeSafetyGuard(allow_orders=True)
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
            safety_guard=safety_guard,
        )

        order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01)
        result = pipeline.execute_with_safety([order])

        assert result.environment == "paper"
        assert result.status == ExecutionStatus.SUCCESS


class TestExecutionPipelineExceptions:
    """Tests fuer ExecutionPipeline-Exceptions."""

    def test_live_execution_locked_error_attributes(self):
        """LiveExecutionLockedError hat korrekte Attribute."""
        from src.execution import LiveExecutionLockedError

        error = LiveExecutionLockedError()

        assert error.feature_key == "live_order_execution"
        assert error.status == "locked"
        assert "governance" in error.message.lower() or "locked" in error.message.lower()

    def test_governance_violation_error_custom_message(self):
        """GovernanceViolationError akzeptiert custom message."""
        from src.execution import GovernanceViolationError

        error = GovernanceViolationError(
            message="Custom governance error",
            feature_key="custom_feature",
            status="unknown",
        )

        assert error.feature_key == "custom_feature"
        assert error.status == "unknown"
        assert error.message == "Custom governance error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
