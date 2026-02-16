from src.execution.adapters import (
    AdapterCapabilitiesV1,
    MockExecutionAdapterV1,
    OrderIntentV1,
)


def test_mock_adapter_places_and_cancels():
    caps = AdapterCapabilitiesV1(
        name="kraken",
        markets=["spot"],
        order_types=["market", "limit", "stop"],
        supports_post_only=True,
        supports_reduce_only=False,
        supports_batch_cancel=True,
        supports_cancel_all=True,
        supports_ws_orders=False,
        supports_ws_fills=False,
    )
    a = MockExecutionAdapterV1(caps)
    r1 = a.place_order(
        OrderIntentV1(symbol="BTC/USD", side="buy", qty=0.1, order_type="limit", price=1.0)
    )
    assert r1.ok and r1.order_id
    r2 = a.place_order(OrderIntentV1(symbol="BTC/USD", side="sell", qty=0.1, order_type="market"))
    assert r2.ok and r2.order_id
    assert a.cancel_all(symbol="BTC/USD") == 2
