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
        self.last_context: Optional[dict] = None

    def ensure_may_place_order(
        self, *, is_testnet: bool = False, context: Optional[dict] = None
    ) -> None:
        """Fake ensure_may_place_order."""
        self.called = True
        self.last_context = context
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


class FakeRejectingExecutor:
    """Executor that returns rejected results (simulates missing API credentials / exchange reject)."""

    def execute_orders(self, orders) -> List:
        from src.orders.base import OrderExecutionResult

        return [
            OrderExecutionResult(
                status="rejected",
                request=o,
                fill=None,
                reason="missing_api_credentials",
            )
            for o in orders
        ]


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

    def test_execute_with_safety_maps_recon_pipeline_to_recon_for_safety(self):
        """recon_pipeline wird zu recon gemappt, damit SafetyGuard Runbook-B lesen kann."""
        from src.execution import ExecutionPipeline
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor
        from src.orders.base import OrderRequest

        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        safety_guard = FakeSafetyGuard(allow_orders=True)
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))
        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
            safety_guard=safety_guard,
        )
        order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01)
        recon_pipeline = {
            "expected_positions": {"epoch": 1, "positions": {"BTC/EUR": 0.05}},
        }
        pipeline.execute_with_safety(
            [order],
            context={"current_price": 50000.0, "recon_pipeline": recon_pipeline},
        )
        assert safety_guard.last_context is not None
        assert safety_guard.last_context["recon"] is recon_pipeline

    def test_execute_with_safety_does_not_overwrite_explicit_recon(self):
        """Explizites recon hat Vorrang vor recon_pipeline."""
        from src.execution import ExecutionPipeline
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.paper import PaperMarketContext, PaperOrderExecutor
        from src.orders.base import OrderRequest

        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        safety_guard = FakeSafetyGuard(allow_orders=True)
        executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))
        pipeline = ExecutionPipeline(
            executor=executor,
            env_config=env_config,
            safety_guard=safety_guard,
        )
        order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01)
        recon = {"expected_positions": {"epoch": 2, "positions": {"BTC/EUR": 0.1}}}
        other = {"expected_positions": {"epoch": 99, "positions": {"BTC/EUR": 0.0}}}
        pipeline.execute_with_safety(
            [order],
            context={"recon": recon, "recon_pipeline": other},
        )
        assert safety_guard.last_context is not None
        assert safety_guard.last_context["recon"] is recon

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

    def test_execute_with_safety_emits_order_submit_and_reject_when_executor_rejects(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Regression: execute_with_safety emits order_submit/order_reject for executor-rejected path (Trial 5 gap fix)."""
        import json

        from src.execution import ExecutionPipeline
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.orders.base import OrderRequest

        monkeypatch.chdir(tmp_path)
        (tmp_path / "out").mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("PT_EXEC_EVENTS_ENABLED", "true")
        monkeypatch.setenv(
            "PT_EXEC_EVENTS_JSONL_PATH", "out/ops/execution_events/execution_events.jsonl"
        )

        env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        pipeline = ExecutionPipeline(
            executor=FakeRejectingExecutor(),
            env_config=env_config,
            safety_guard=FakeSafetyGuard(allow_orders=True),
        )

        order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            client_id="trial5_test_001",
        )
        result = pipeline.execute_with_safety([order])

        assert result.rejected is False
        assert len(result.executed_orders) == 1
        assert result.executed_orders[0].status == "rejected"

        p = tmp_path / "out/ops/execution_events/execution_events.jsonl"
        assert p.exists(), "Execution events JSONL should exist when PT_EXEC_EVENTS_ENABLED=true"
        lines = p.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) >= 2, "Expected order_submit + order_reject events"

        events = [json.loads(ln) for ln in lines]
        types = [e["event_type"] for e in events]
        assert "order_submit" in types, "order_submit must be emitted before executor call"
        assert "order_reject" in types, (
            "order_reject must be emitted when executor returns rejected"
        )

        submit = next(e for e in events if e["event_type"] == "order_submit")
        assert submit["symbol"] == "BTC/EUR"
        assert submit["client_order_id"] == "trial5_test_001"

        reject = next(e for e in events if e["event_type"] == "order_reject")
        assert reject["symbol"] == "BTC/EUR"
        assert "missing_api_credentials" in (reject.get("msg") or "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
