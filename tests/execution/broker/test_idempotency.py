from __future__ import annotations

from decimal import Decimal

from src.execution.broker.adapter import BrokerAdapter
from src.execution.broker.fake_broker import FakeBroker
from src.execution.broker.idempotency import build_idempotency_key
from src.execution.contracts import Order, OrderSide, OrderState, OrderType


def test_build_idempotency_key_is_stable() -> None:
    order = Order(
        client_order_id="c1_idem_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("1"),
        price=Decimal("50000"),
        state=OrderState.CREATED,
    )

    k1 = build_idempotency_key(order, "idem-a").value
    k2 = build_idempotency_key(order, "idem-a").value
    k3 = build_idempotency_key(order, "idem-b").value

    assert k1 == k2
    assert k1 != k3


def test_adapter_idempotency_prevents_duplicate_side_effects() -> None:
    broker = FakeBroker()
    adapter = BrokerAdapter(broker)

    order = Order(
        client_order_id="c1_idem_002",
        symbol="BTC-EUR",
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        quantity=Decimal("2"),
        price=Decimal("60000"),
        state=OrderState.CREATED,
    )

    before = broker.placed_orders_count
    oid1 = adapter.place_order(order, idempotency_key="idem-dup")
    mid = broker.placed_orders_count
    oid2 = adapter.place_order(order, idempotency_key="idem-dup")
    after = broker.placed_orders_count

    assert oid1 == oid2
    assert mid == before + 1
    assert after == mid
