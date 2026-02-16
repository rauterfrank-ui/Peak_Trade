"""P107 Coinbase adapter smoke tests (mocks only)."""

from src.execution.adapters.base_v1 import OrderIntentV1
from src.execution.adapters.providers.coinbase_v1 import CoinbaseExecutionAdapterV1


def test_coinbase_adapter_is_offline_and_deterministic():
    a = CoinbaseExecutionAdapterV1()
    caps = a.capabilities()
    assert caps.name == "coinbase_advanced"
    assert "spot" in caps.markets
    assert caps.supports_post_only
    assert caps.supports_batch_cancel

    intent = OrderIntentV1(
        symbol="BTC-USD",
        side="buy",
        qty=0.01,
        order_type="limit",
        price=30000.0,
        client_id="t1",
        post_only=True,
    )
    r1 = a.place_order(intent)
    r2 = a.place_order(OrderIntentV1(symbol="BTC-USD", side="sell", qty=0.01, order_type="market"))
    assert r1.ok and r2.ok
    assert r1.order_id and r2.order_id
    assert a.cancel_all(symbol="BTC-USD") == 2
