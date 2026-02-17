"""P114: Router wiring smoke (mocks only)."""

from __future__ import annotations

import pytest

from src.execution.adapters.base_v1 import OrderIntentV1
from src.execution.router.router_v1 import (
    ExecutionRouterContextV1,
    build_execution_router_v1,
)


def test_router_builds_and_has_adapter_name() -> None:
    ctx = ExecutionRouterContextV1(mode="shadow", dry_run=True, adapter_name="mock")
    router = build_execution_router_v1(ctx)
    rep = router.status()
    assert rep["ok"] is True
    assert rep["adapter"]["name"] == "mock"


def test_router_place_order_ok_in_dry_run() -> None:
    ctx = ExecutionRouterContextV1(mode="shadow", dry_run=True, adapter_name="coinbase")
    router = build_execution_router_v1(ctx)
    intent = OrderIntentV1(
        symbol="BTC-USD",
        side="buy",
        order_type="market",
        qty=0.01,
        client_id="test-client",
    )
    res = router.place_order(intent)
    assert res.ok is True
    # Adapter name from capabilities (e.g. coinbase_advanced, okx, bybit_v1, mock)
    assert res.adapter and len(res.adapter) > 0


def test_router_rejects_live_mode() -> None:
    with pytest.raises(ValueError):
        _ = build_execution_router_v1(
            ExecutionRouterContextV1(mode="live", dry_run=True, adapter_name="mock")
        )
