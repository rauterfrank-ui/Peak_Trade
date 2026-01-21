"""
BrokerAdapter: wraps a Broker implementation with:
- idempotency (stable keying)
- bounded retries for transient errors

Scope: Finish C1 (mock/fake only, NO-LIVE).
"""

from __future__ import annotations

from typing import Iterable, Sequence

from src.execution.broker.base import Broker, BrokerOrderSnapshot, FillCursor
from src.execution.broker.idempotency import build_idempotency_key
from src.execution.broker.retry import RetryPolicy
from src.execution.contracts import Fill, Order, OrderState


class BrokerAdapter:
    def __init__(self, broker: Broker, retry: RetryPolicy | None = None) -> None:
        self._broker = broker
        self._retry = retry or RetryPolicy()

    def place_order(self, order: Order, idempotency_key: str) -> str:
        stable = build_idempotency_key(order, idempotency_key).value
        return self._retry.run(
            lambda: self._broker.place_order(order=order, idempotency_key=stable)
        )

    def cancel_order(self, broker_order_id: str) -> OrderState:
        return self._retry.run(lambda: self._broker.cancel_order(broker_order_id))

    def query_order(self, broker_order_id: str) -> BrokerOrderSnapshot:
        return self._retry.run(lambda: self._broker.query_order(broker_order_id))

    def list_open_orders(self) -> Sequence[BrokerOrderSnapshot]:
        return self._retry.run(lambda: self._broker.list_open_orders())

    def iter_fills(self, since: FillCursor) -> tuple[FillCursor, Iterable[Fill]]:
        return self._retry.run(lambda: self._broker.iter_fills(since))
