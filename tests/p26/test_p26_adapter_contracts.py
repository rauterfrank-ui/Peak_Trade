"""P26 adapter contract tests — determinism and fill bounds."""

import pytest

from src.execution.p24.config import ExecutionModelV2Config
from src.execution.p24.execution_model_v2 import ExecutionModelV2, MarketSnapshot
from src.execution.p26.adapter import ExecutionAdapterV1
from src.execution.p26.types import AdapterOrder


def _snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        ts="0",
        open=100.0,
        high=110.0,
        low=90.0,
        close=105.0,
        volume=1.0,
    )


def test_determinism_same_inputs_same_outputs():
    cfg = ExecutionModelV2Config.from_dict(
        {
            "fee_rate": 0.001,
            "slippage_bps": 5,
        }
    )
    model = ExecutionModelV2(cfg)
    adapter = ExecutionAdapterV1(model=model, cfg=cfg)

    orders = [
        AdapterOrder(id="o1", symbol="BTC/USDT", side="BUY", order_type="MARKET", qty=1.0),
        AdapterOrder(
            id="o2", symbol="BTC/USDT", side="SELL", order_type="LIMIT", qty=2.0, limit_price=106.0
        ),
    ]

    snap = _snapshot()
    out1 = adapter.execute_bar(snapshot=snap, orders=orders)
    out2 = adapter.execute_bar(snapshot=snap, orders=orders)

    assert out1 == out2


@pytest.mark.parametrize("qty", [0.1, 1.0, 5.0])
def test_fill_bounds_never_exceed_order_qty(qty: float):
    cfg = ExecutionModelV2Config.from_dict({"fee_rate": 0.0, "slippage_bps": 0})
    model = ExecutionModelV2(cfg)
    adapter = ExecutionAdapterV1(model=model, cfg=cfg)

    orders = [AdapterOrder(id="o1", symbol="BTC/USDT", side="BUY", order_type="MARKET", qty=qty)]
    fills = adapter.execute_bar(snapshot=_snapshot(), orders=orders)

    filled_total = sum(f.qty for f in fills if f.order_id == "o1")
    assert 0.0 <= filled_total <= qty
