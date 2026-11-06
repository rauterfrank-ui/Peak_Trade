from __future__ import annotations

from decimal import Decimal

import pytest

from src.execution.broker.adapter import BrokerAdapter
from src.execution.broker.errors import InvalidOrderError
from src.execution.broker.fake_broker import FakeBroker
from src.execution.contracts import Order, OrderSide, OrderState, OrderType


def test_adapter_contract_happy_path_place_query_list_cancel() -> None:
    broker = FakeBroker()
    adapter = BrokerAdapter(broker)

    order = Order(
        client_order_id="c1_order_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("1"),
        price=Decimal("50000"),
        state=OrderState.CREATED,
    )

    broker_order_id = adapter.place_order(order, idempotency_key="idem-1")
    assert broker_order_id.startswith("fake_")

    snap = adapter.query_order(broker_order_id)
    assert snap.client_order_id == "c1_order_001"
    assert snap.broker_order_id == broker_order_id
    assert snap.state == OrderState.ACKNOWLEDGED

    open_orders = adapter.list_open_orders()
    assert [o.broker_order_id for o in open_orders] == [broker_order_id]

    state = adapter.cancel_order(broker_order_id)
    assert state == OrderState.CANCELLED

    open_orders_after = adapter.list_open_orders()
    assert open_orders_after == []


def test_adapter_contract_reject_path_invalid_order() -> None:
    broker = FakeBroker()
    adapter = BrokerAdapter(broker)

    invalid = Order(
        client_order_id="c1_order_invalid",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("0"),
        state=OrderState.CREATED,
    )

    with pytest.raises(InvalidOrderError):
        adapter.place_order(invalid, idempotency_key="idem-invalid")
