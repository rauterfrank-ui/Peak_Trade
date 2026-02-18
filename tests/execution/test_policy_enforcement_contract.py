"""
Execution-level contract tests for policy enforcement (Phase D.2).

When PT_POLICY_ENFORCE_V0=1:
- policy NO_TRADE => submit_order returns rejected with policy_blocked
- policy ALLOW => submit_order proceeds (no block)

When PT_POLICY_ENFORCE_V0=0 (default): policy block never occurs.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.execution import ExecutionPipeline, ExecutionStatus, OrderIntent
from src.orders.paper import PaperMarketContext, PaperOrderExecutor


def _make_paper_pipeline():
    """Minimal paper pipeline for contract tests."""
    env_config = EnvironmentConfig(environment=TradingEnvironment.PAPER)
    executor = PaperOrderExecutor(PaperMarketContext(prices={"BTC/EUR": 50000.0}))
    return ExecutionPipeline(
        executor=executor,
        env_config=env_config,
    )


def _make_intent():
    """OrderIntent with current_price (required for policy v1)."""
    return OrderIntent(
        symbol="BTC/EUR",
        side="buy",
        quantity=0.01,
        current_price=50000.0,
    )


def test_policy_enforce_off_allows_no_trade(monkeypatch):
    """
    PT_POLICY_ENFORCE_V0=0 (default): policy NO_TRADE does not block.
    Enforcer is off, so submit_order proceeds despite policy saying NO_TRADE.
    """
    monkeypatch.delenv("PT_POLICY_ENFORCE_V0", raising=False)
    pipeline = _make_paper_pipeline()
    intent = _make_intent()

    result = pipeline.submit_order(intent)

    # With enforce OFF, policy NO_TRADE is ignored; order proceeds
    assert result.rejected is False
    assert result.status == ExecutionStatus.SUCCESS


def test_policy_enforce_on_blocks_no_trade(monkeypatch):
    """
    PT_POLICY_ENFORCE_V0=1 + policy NO_TRADE => submit_order returns rejected
    with policy_blocked. Default policy v1 yields NO_TRADE (edge=0, costs=18).
    """
    monkeypatch.setenv("PT_POLICY_ENFORCE_V0", "1")
    pipeline = _make_paper_pipeline()
    intent = _make_intent()

    result = pipeline.submit_order(intent)

    assert result.rejected is True
    assert "policy_blocked" in (result.reason or "")
    assert result.status == ExecutionStatus.BLOCKED_BY_SAFETY
    assert len(result.executed_orders) == 0


def test_policy_enforce_on_allows_when_policy_allow(monkeypatch):
    """
    PT_POLICY_ENFORCE_V0=1 + policy ALLOW => submit_order proceeds.
    Patch decision context to yield ALLOW (edge > costs + buffer).
    """
    monkeypatch.setenv("PT_POLICY_ENFORCE_V0", "1")

    def _mock_build_decision_context_v1(*, intent, env, is_testnet, current_price, **kwargs):
        from src.observability.nowcast.decision_context_v1 import build_decision_context_v1

        ctx = build_decision_context_v1(
            intent=intent,
            env=env,
            is_testnet=is_testnet,
            current_price=current_price,
            **{k: v for k, v in kwargs.items() if k in ("source", "ts", "cost_model")},
        )
        # Override to yield ALLOW: edge=25 > costs=0 + 1 buffer
        ctx["forecast"] = ctx.get("forecast") or {}
        ctx["forecast"]["mu_bp"] = 25.0
        ctx["costs"] = {"fees_bp": 0.0, "slippage_bp": 0.0, "impact_bp": 0.0, "latency_bp": 0.0}
        return ctx

    with patch(
        "src.execution.pipeline.build_decision_context_v1",
        side_effect=_mock_build_decision_context_v1,
    ):
        pipeline = _make_paper_pipeline()
        intent = _make_intent()
        result = pipeline.submit_order(intent)

    assert result.rejected is False
    assert result.status == ExecutionStatus.SUCCESS
    assert len(result.executed_orders) == 1
