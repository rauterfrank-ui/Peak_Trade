#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# tests/test_execution_pipeline.py
"""
Peak_Trade: Tests für ExecutionPipeline Phase 16A
=================================================

Tests für die neue execute_with_safety() Methode:
- Environment-Check (LIVE-Mode blockiert)
- SafetyGuard-Integration
- Risk-Check-Integration (LiveRiskLimits)
- Run-Logging-Integration
- Executor-Ausfuehrung

WICHTIG: Keine echten Orders - alles Paper/Sandbox.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

import pytest

# Projekt-Root zum Python-Path hinzufuegen
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# ============================================================================
# Fake-Komponenten für Tests
# ============================================================================


@dataclass
class FakeLiveRiskCheckResult:
    """Fake LiveRiskCheckResult für Tests."""

    allowed: bool
    reasons: List[str]
    metrics: dict


class FakeSafetyGuard:
    """Fake SafetyGuard für Tests."""

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
    """Fake LiveRiskLimits für Tests."""

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
    """Fake LiveRunLogger für Tests."""

    def __init__(self):
        self.events: List[dict] = []
        self.called = False

    def log_event(self, event) -> None:
        """Fake log_event."""
        self.called = True
        self.events.append(event)


# ============================================================================
# Tests für execute_with_safety()
# ============================================================================


class TestExecutionPipelineWithSafety:
    """Tests für execute_with_safety() Methode."""

    def test_execution_pipeline_blocks_live_mode(self):
        """execute_with_safety() blockiert LIVE-Mode hart (Phase 16A)."""
        from src.execution import ExecutionPipeline
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor
        from src.orders.base import OrderRequest

        # LIVE-Mode Environment
        env_config = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        safety_guard = FakeSafetyGuard(allow_orders=True)
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
            safety_guard=safety_guard,
        )

        order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01)
        result = pipeline.execute_with_safety([order])

        # Executor sollte NICHT aufgerufen worden sein
        assert result.rejected is True
        assert len(result.executed_orders) == 0
        assert result.reason == "live_mode_not_supported_in_phase_16a"

    def test_execution_pipeline_runs_safety_and_blocks_on_violation(self):
        """execute_with_safety() blockiert bei SafetyGuard-Verletzung."""
        from src.execution import ExecutionPipeline
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.live.safety import SafetyBlockedError
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor
        from src.orders.base import OrderRequest

        # PAPER-Mode, aber SafetyGuard blockiert
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        safety_guard = FakeSafetyGuard(
            allow_orders=False,
            raise_exception=SafetyBlockedError("Test blockiert"),
        )
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
            safety_guard=safety_guard,
        )

        order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01)
        result = pipeline.execute_with_safety([order])

        # Executor sollte NICHT aufgerufen worden sein
        assert result.rejected is True
        assert len(result.executed_orders) == 0
        assert "safety_guard_blocked" in result.reason
        assert safety_guard.called is True

    def test_execution_pipeline_executes_orders_when_safe(self):
        """execute_with_safety() fuehrt Orders aus wenn alle Checks passieren."""
        from src.execution import ExecutionPipeline
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor
        from src.orders.base import OrderRequest

        # PAPER-Mode, SafetyGuard erlaubt
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

        # Executor sollte aufgerufen worden sein
        assert result.rejected is False
        assert len(result.executed_orders) == 1
        assert result.executed_orders[0].status == "filled"
        assert safety_guard.called is True

    def test_execution_pipeline_blocks_on_risk_violation(self):
        """execute_with_safety() blockiert bei Risk-Limit-Verletzung."""
        from src.execution import ExecutionPipeline
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor
        from src.orders.base import OrderRequest

        # PAPER-Mode, SafetyGuard erlaubt, aber Risk-Limits blockieren
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        safety_guard = FakeSafetyGuard(allow_orders=True)
        risk_limits = FakeRiskLimits(allow_orders=False)
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
            safety_guard=safety_guard,
            risk_limits=risk_limits,
        )

        order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01)
        result = pipeline.execute_with_safety([order], context={"current_price": 50000.0})

        # Executor sollte NICHT aufgerufen worden sein
        assert result.rejected is True
        assert len(result.executed_orders) == 0
        assert "risk_limits_violated" in result.reason
        assert risk_limits.called is True
        assert result.risk_check is not None
        assert result.risk_check.allowed is False

    def test_execution_pipeline_logs_events_when_logger_configured(self):
        """execute_with_safety() loggt Events wenn Run-Logger konfiguriert."""
        from src.execution import ExecutionPipeline
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor
        from src.orders.base import OrderRequest

        # PAPER-Mode, alle Checks passieren, Logger konfiguriert
        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        safety_guard = FakeSafetyGuard(allow_orders=True)
        fake_logger = FakeRunLogger()
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
            safety_guard=safety_guard,
            run_logger=fake_logger,
        )

        order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01)
        result = pipeline.execute_with_safety([order])

        # Logger sollte aufgerufen worden sein
        assert result.rejected is False
        assert fake_logger.called is True
        assert len(fake_logger.events) > 0

    def test_execution_pipeline_handles_empty_orders(self):
        """execute_with_safety() handhabt leere Order-Liste."""
        from src.execution import ExecutionPipeline
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor

        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))
        pipeline = ExecutionPipeline(executor=executor)

        result = pipeline.execute_with_safety([])

        assert result.rejected is False
        assert len(result.executed_orders) == 0

    def test_execution_pipeline_works_without_safety_components(self):
        """execute_with_safety() funktioniert auch ohne Safety-Komponenten."""
        from src.execution import ExecutionPipeline
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor
        from src.orders.base import OrderRequest

        # Pipeline ohne Safety-Komponenten
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))
        pipeline = ExecutionPipeline(executor=executor)

        order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01)
        result = pipeline.execute_with_safety([order])

        # Sollte trotzdem funktionieren (keine Safety-Checks = alles erlaubt)
        assert result.rejected is False
        assert len(result.executed_orders) == 1

    def test_execution_pipeline_converts_orders_for_risk_check(self):
        """execute_with_safety() konvertiert OrderRequest zu LiveOrderRequest für Risk-Check."""
        from src.execution import ExecutionPipeline
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor
        from src.orders.base import OrderRequest

        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        safety_guard = FakeSafetyGuard(allow_orders=True)
        risk_limits = FakeRiskLimits(allow_orders=True)
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))

        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
            safety_guard=safety_guard,
            risk_limits=risk_limits,
        )

        order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            metadata={"strategy_key": "test_strategy"},
        )
        result = pipeline.execute_with_safety([order], context={"current_price": 50000.0})

        # Risk-Check sollte aufgerufen worden sein
        assert risk_limits.called is True
        assert risk_limits.last_orders is not None
        assert len(risk_limits.last_orders) == 1
        # LiveOrderRequest sollte korrekte Felder haben
        live_order = risk_limits.last_orders[0]
        assert live_order.symbol == "BTC/EUR"
        assert live_order.side == "BUY"
        assert live_order.quantity == 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
