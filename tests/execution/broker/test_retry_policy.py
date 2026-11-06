from __future__ import annotations

from decimal import Decimal

import pytest

from src.execution.broker.adapter import BrokerAdapter
from src.execution.broker.base import BrokerOrderSnapshot, FillCursor
from src.execution.broker.errors import InvalidOrderError, TransientBrokerError
from src.execution.broker.retry import RetryConfig, RetryPolicy
from src.execution.contracts import Order, OrderSide, OrderState, OrderType


class FlakyPlaceOrderBroker:
    def __init__(self, fail_times: int) -> None:
        self._remaining = fail_times
        self.calls = 0

    def place_order(self, order: Order, idempotency_key: str) -> str:
        self.calls += 1
        if self._remaining > 0:
            self._remaining -= 1
            raise TransientBrokerError("temporary")
        return "ok_0001"

    # Unused in this test, but required by adapter surface
    def cancel_order(self, broker_order_id: str) -> OrderState:  # pragma: no cover
        raise AssertionError("not used")

    def query_order(self, broker_order_id: str) -> BrokerOrderSnapshot:  # pragma: no cover
        raise AssertionError("not used")

    def list_open_orders(self):  # pragma: no cover
        raise AssertionError("not used")

    def iter_fills(self, since: FillCursor):  # pragma: no cover
        raise AssertionError("not used")


class AlwaysInvalidBroker:
    def __init__(self) -> None:
        self.calls = 0

    def place_order(self, order: Order, idempotency_key: str) -> str:
        self.calls += 1
        raise InvalidOrderError("bad order")

    def cancel_order(self, broker_order_id: str) -> OrderState:  # pragma: no cover
        raise AssertionError("not used")

    def query_order(self, broker_order_id: str) -> BrokerOrderSnapshot:  # pragma: no cover
        raise AssertionError("not used")

    def list_open_orders(self):  # pragma: no cover
        raise AssertionError("not used")

    def iter_fills(self, since: FillCursor):  # pragma: no cover
        raise AssertionError("not used")


def test_retry_policy_is_bounded_and_no_real_sleeps() -> None:
    delays: list[float] = []

    retry = RetryPolicy(
        config=RetryConfig(max_retries=3, initial_delay_s=0.0, max_delay_s=0.0),
        sleep=lambda s: delays.append(s),
    )
    broker = FlakyPlaceOrderBroker(fail_times=2)
    adapter = BrokerAdapter(broker, retry=retry)

    order = Order(
        client_order_id="c1_retry_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("1"),
        price=Decimal("50000"),
        state=OrderState.CREATED,
    )

    broker_order_id = adapter.place_order(order, idempotency_key="idem-retry")
    assert broker_order_id == "ok_0001"
    assert broker.calls == 3  # 2 fails + 1 success
    assert delays == [0.0, 0.0]


def test_retry_policy_does_not_retry_permanent_errors() -> None:
    delays: list[float] = []
    retry = RetryPolicy(
        config=RetryConfig(max_retries=10, initial_delay_s=0.0, max_delay_s=0.0),
        sleep=lambda s: delays.append(s),
    )
    broker = AlwaysInvalidBroker()
    adapter = BrokerAdapter(broker, retry=retry)

    order = Order(
        client_order_id="c1_retry_002",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("1"),
        state=OrderState.CREATED,
    )

    with pytest.raises(InvalidOrderError):
        adapter.place_order(order, idempotency_key="idem-retry-perm")

    assert broker.calls == 1
    assert delays == []
