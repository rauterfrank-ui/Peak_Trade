"""P112: Execution router smoke (mocks only)."""

from __future__ import annotations

from src.execution.adapters.base_v1 import OrderIntentV1
from src.execution.router import (
    ExecutionRouterContextV1,
    build_execution_router_v1,
)


def test_router_builds_and_places_mock_order() -> None:
    r = build_execution_router_v1(ExecutionRouterContextV1(mode="shadow", adapter_name="mock"))
    out = r.place_order(OrderIntentV1(symbol="BTC/USD", side="buy", qty=0.01, order_type="market"))
    assert out.ok is True
    assert out.adapter == "mock"


def test_router_guard_rejects_live_mode() -> None:
    try:
        build_execution_router_v1(ExecutionRouterContextV1(mode="live", adapter_name="mock"))
        assert False, "expected ValueError"
    except ValueError as e:
        assert "router mode must be one of" in str(e)
