"""P27 contract tests — determinism, fill bounds, accounting hooks."""

from __future__ import annotations

import pytest

from src.backtest.p27.execution_integration import (
    P27ExecutionWiringConfig,
    build_p26_adapter,
    execute_bar_via_p26,
)
from src.execution.p24.config import ExecutionModelV2Config
from src.execution.p24.execution_model_v2 import MarketSnapshot
from src.execution.p26.types import AdapterOrder


def _mk_cfg() -> P27ExecutionWiringConfig:
    return P27ExecutionWiringConfig(
        enabled=True,
        execution_mode="p26_v1",
        p24_config=ExecutionModelV2Config.from_dict({"fee_rate": 0.001, "slippage_bps": 5}),
    )


def _snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        ts="0",
        open=100.0,
        high=110.0,
        low=90.0,
        close=105.0,
        volume=1_000.0,
    )


def test_determinism_same_inputs_same_fills() -> None:
    cfg = _mk_cfg()
    adapter = build_p26_adapter(cfg)

    bar = _snapshot()
    orders = [
        AdapterOrder(id="o1", symbol="BTC/USDT", side="BUY", order_type="MARKET", qty=1.0),
        AdapterOrder(
            id="o2",
            symbol="BTC/USDT",
            side="SELL",
            order_type="LIMIT",
            qty=0.5,
            limit_price=108.0,
        ),
    ]

    fills_a = execute_bar_via_p26(adapter, bar, orders)
    fills_b = execute_bar_via_p26(adapter, bar, orders)
    assert fills_a == fills_b


def test_fill_bounds() -> None:
    cfg = _mk_cfg()
    adapter = build_p26_adapter(cfg)

    bar = _snapshot()
    orders = [
        AdapterOrder(id="o1", symbol="BTC/USDT", side="BUY", order_type="MARKET", qty=1.0),
        AdapterOrder(
            id="o2",
            symbol="BTC/USDT",
            side="SELL",
            order_type="STOP_MARKET",
            qty=2.0,
            stop_price=95.0,
        ),
    ]
    fills = execute_bar_via_p26(adapter, bar, orders)

    order_qty = {o.id: o.qty for o in orders}
    for f in fills:
        assert f.qty >= 0
        filled_total = sum(x.qty for x in fills if x.order_id == f.order_id)
        assert filled_total <= order_qty.get(f.order_id, float("inf"))


@pytest.mark.parametrize("qty", [0.1, 1.0, 5.0])
def test_fill_bounds_parametrized(qty: float) -> None:
    """Placeholder: per-order fill qty never exceeds order qty."""
    cfg = P27ExecutionWiringConfig(
        enabled=True,
        execution_mode="p26_v1",
        p24_config=ExecutionModelV2Config.from_dict({"fee_rate": 0.0, "slippage_bps": 0}),
    )
    adapter = build_p26_adapter(cfg)

    orders = [AdapterOrder(id="o1", symbol="BTC/USDT", side="BUY", order_type="MARKET", qty=qty)]
    fills = execute_bar_via_p26(adapter, _snapshot(), orders)

    filled_total = sum(f.qty for f in fills if f.order_id == "o1")
    assert 0.0 <= filled_total <= qty
