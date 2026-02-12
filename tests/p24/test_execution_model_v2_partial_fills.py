"""P24 execution model v2 — partial fills unit tests."""

from __future__ import annotations

import copy

from src.execution.p24.config import ExecutionModelV2Config
from src.execution.p24.execution_model_v2 import (
    ExecutionModelV2,
    MarketSnapshot,
    Order,
)


def bar(
    ts: str = "t0",
    o: float = 100,
    h: float = 110,
    l: float = 90,
    c: float = 105,
    v: float = 10_000,
) -> MarketSnapshot:
    return MarketSnapshot(ts=ts, open=o, high=h, low=l, close=c, volume=v)


def test_determinism_same_inputs_same_outputs() -> None:
    cfg = ExecutionModelV2Config.from_dict(
        {
            "fee_rate": 0.001,
            "slippage_bps": 10,
            "partial_fills_v2": {"max_fill_ratio_per_bar": 0.25},
        }
    )
    m = ExecutionModelV2(cfg)
    o1 = Order(order_id="o1", side="BUY", type="MARKET", qty=100)
    o2 = copy.deepcopy(o1)

    fills_a = m.process_bar(bar(), [o1])
    fills_b = m.process_bar(bar(), [o2])

    assert fills_a == fills_b
    assert o1.remaining_qty == o2.remaining_qty


def test_quantity_conservation_market_partial() -> None:
    cfg = ExecutionModelV2Config.from_dict({"partial_fills_v2": {"max_fill_ratio_per_bar": 0.5}})
    m = ExecutionModelV2(cfg)
    o = Order(order_id="o", side="BUY", type="MARKET", qty=10)

    fills = m.process_bar(bar(v=1_000), [o])
    assert len(fills) == 1
    f = fills[0]
    assert f.qty == 5
    assert abs((f.qty + o.remaining_qty) - 10) < 1e-12


def test_fee_applies_only_on_filled_qty() -> None:
    cfg = ExecutionModelV2Config.from_dict(
        {
            "fee_rate": 0.01,
            "partial_fills_v2": {"max_fill_ratio_per_bar": 0.5, "price_rule": "close"},
        }
    )
    m = ExecutionModelV2(cfg)
    o = Order(order_id="o", side="BUY", type="MARKET", qty=10)

    fills = m.process_bar(bar(c=200), [o])
    f = fills[0]
    assert f.qty == 5
    assert f.fee == f.qty * f.price * 0.01


def test_limit_not_filled_when_not_touched() -> None:
    cfg = ExecutionModelV2Config.from_dict({"partial_fills_v2": {"max_fill_ratio_per_bar": 1.0}})
    m = ExecutionModelV2(cfg)
    o = Order(order_id="o", side="BUY", type="LIMIT", qty=10, limit_price=80)
    fills = m.process_bar(bar(), [o])
    assert fills == []
    assert o.remaining_qty == 10


def test_limit_partial_fill_on_touch() -> None:
    cfg = ExecutionModelV2Config.from_dict(
        {"partial_fills_v2": {"max_fill_ratio_per_bar": 0.4, "price_rule": "worst"}}
    )
    m = ExecutionModelV2(cfg)
    o = Order(order_id="o", side="BUY", type="LIMIT", qty=10, limit_price=95)
    fills = m.process_bar(bar(), [o])
    assert len(fills) == 1
    f = fills[0]
    assert f.qty == 4
    assert f.price <= 95
    assert o.remaining_qty == 6


def test_stop_market_triggers_and_fills_same_bar_by_default() -> None:
    cfg = ExecutionModelV2Config.from_dict(
        {
            "partial_fills_v2": {
                "max_fill_ratio_per_bar": 0.5,
                "allow_partial_on_trigger_bar": True,
            }
        }
    )
    m = ExecutionModelV2(cfg)
    o = Order(order_id="o", side="BUY", type="STOP_MARKET", qty=10, stop_price=108)
    fills = m.process_bar(bar(), [o])
    assert len(fills) == 1
    assert o.triggered is True
    assert o.trigger_bar_ts == "t0"
    assert fills[0].qty == 5
    assert o.remaining_qty == 5


def test_stop_market_triggers_but_defers_fill_if_disallowed() -> None:
    cfg = ExecutionModelV2Config.from_dict(
        {
            "partial_fills_v2": {
                "max_fill_ratio_per_bar": 0.5,
                "allow_partial_on_trigger_bar": False,
            }
        }
    )
    m = ExecutionModelV2(cfg)
    o = Order(order_id="o", side="BUY", type="STOP_MARKET", qty=10, stop_price=108)
    fills0 = m.process_bar(bar(ts="t0"), [o])
    assert fills0 == []
    assert o.triggered is True
    assert o.remaining_qty == 10

    fills1 = m.process_bar(bar(ts="t1"), [o])
    assert len(fills1) == 1
    assert fills1[0].qty == 5
    assert o.remaining_qty == 5


def test_min_fill_qty_blocks_small_fills() -> None:
    cfg = ExecutionModelV2Config.from_dict(
        {"partial_fills_v2": {"max_fill_ratio_per_bar": 0.1, "min_fill_qty": 2.0}}
    )
    m = ExecutionModelV2(cfg)
    o = Order(order_id="o", side="BUY", type="MARKET", qty=10)
    fills = m.process_bar(bar(), [o])
    assert fills == []
    assert o.remaining_qty == 10
