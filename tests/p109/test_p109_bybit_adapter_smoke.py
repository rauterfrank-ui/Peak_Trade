"""P109 Bybit adapter smoke tests (mocks only)."""

from src.execution.adapters.base_v1 import OrderIntentV1
from src.execution.adapters.providers.bybit_v1 import BybitExecutionAdapterV1


def test_p109_bybit_adapter_smoke_place_order_and_caps():
    a = BybitExecutionAdapterV1()
    caps = a.capabilities()
    assert caps.name == "bybit_v1"
    assert "spot" in caps.markets
    assert "perp" in caps.markets
    assert caps.supports_batch_cancel is True

    r = a.place_order(
        OrderIntentV1(
            symbol="BTC/USDT",
            side="buy",
            qty=1.0,
            order_type="market",
            client_id="c1",
        )
    )
    assert r.ok is True
    assert r.adapter == "bybit_v1"
    assert r.order_id and "bybit_mock" in r.order_id
    assert r.client_id == "c1"

    r2 = a.place_order(OrderIntentV1(symbol="BTC/USDT", side="sell", qty=0.5, order_type="market"))
    assert r2.ok and r2.order_id
    assert a.batch_cancel([r.order_id, r2.order_id]) == 2
    assert a.cancel_all() == 0
