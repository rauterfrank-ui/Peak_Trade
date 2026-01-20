"""
Adapter interface for order submission (v0).

NO-LIVE: Adapters in this package must be safe and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol


@dataclass(frozen=True)
class SubmitRequest:
    run_id: str
    correlation_id: str
    order_id: str
    symbol: str
    side: str
    quantity: float
    idempotency_key: str
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SubmitAck:
    order_id: str
    accepted: bool
    venue_order_id: Optional[str] = None
    reason: Optional[str] = None


@dataclass(frozen=True)
class OrderStatus:
    order_id: str
    state: str  # "acked" | "filled" | "canceled" | "failed"
    fill: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class ExecutionAdapter(Protocol):
    def submit(self, req: SubmitRequest) -> SubmitAck: ...

    def cancel(self, *, run_id: str, correlation_id: str, order_id: str) -> None: ...

    def status(self, *, run_id: str, correlation_id: str, order_id: str) -> OrderStatus: ...


class NullExecutionAdapter:
    """
    Safe default: accepts nothing and never creates side effects.
    """

    def submit(self, req: SubmitRequest) -> SubmitAck:
        return SubmitAck(order_id=req.order_id, accepted=False, reason="null_adapter_reject")

    def cancel(self, *, run_id: str, correlation_id: str, order_id: str) -> None:
        return None

    def status(self, *, run_id: str, correlation_id: str, order_id: str) -> OrderStatus:
        return OrderStatus(order_id=order_id, state="failed", error={"code": "null_adapter"})


class InMemoryExecutionAdapter:
    """
    Deterministic in-memory adapter (CI-friendly).

    Behavior:
    - idempotent submit via idempotency_key -> order_id mapping
    - optional transient failures for testing
    - fills can be immediate or delayed by N status polls
    """

    def __init__(
        self,
        *,
        fill_immediately: bool = True,
        fail_first_n_submits: int = 0,
        fill_after_n_polls: int = 0,
    ) -> None:
        self._fill_immediately = bool(fill_immediately)
        self._fail_first_n_submits = int(fail_first_n_submits)
        self._fill_after_n_polls = int(fill_after_n_polls)

        self.submit_calls = 0
        self._idem_to_order_id: dict[str, str] = {}
        self._orders: dict[str, dict[str, Any]] = {}
        self._polls: dict[str, int] = {}

    def submit(self, req: SubmitRequest) -> SubmitAck:
        self.submit_calls += 1

        if req.idempotency_key in self._idem_to_order_id:
            oid = self._idem_to_order_id[req.idempotency_key]
            state = self._orders.get(oid, {}).get("state", "acked")
            accepted = state not in ("failed", "canceled")
            return SubmitAck(order_id=oid, accepted=accepted, venue_order_id=f"mem:{oid}")

        if self.submit_calls <= self._fail_first_n_submits:
            return SubmitAck(order_id=req.order_id, accepted=False, reason="transient_submit_failure")

        self._idem_to_order_id[req.idempotency_key] = req.order_id
        self._orders[req.order_id] = {
            "state": "acked",
            "req": req,
            "fill": None,
            "error": None,
        }
        self._polls[req.order_id] = 0

        if self._fill_immediately and self._fill_after_n_polls == 0:
            self._orders[req.order_id]["state"] = "filled"
            self._orders[req.order_id]["fill"] = {
                "symbol": req.symbol,
                "side": req.side,
                "quantity": req.quantity,
                "price": float(req.meta.get("price", 0.0)),
            }

        return SubmitAck(order_id=req.order_id, accepted=True, venue_order_id=f"mem:{req.order_id}")

    def cancel(self, *, run_id: str, correlation_id: str, order_id: str) -> None:
        if order_id in self._orders and self._orders[order_id]["state"] not in ("filled", "failed"):
            self._orders[order_id]["state"] = "canceled"

    def status(self, *, run_id: str, correlation_id: str, order_id: str) -> OrderStatus:
        if order_id not in self._orders:
            return OrderStatus(order_id=order_id, state="failed", error={"code": "not_found"})

        self._polls[order_id] = self._polls.get(order_id, 0) + 1
        st = self._orders[order_id]["state"]

        if st == "acked" and self._fill_after_n_polls > 0:
            if self._polls[order_id] >= self._fill_after_n_polls:
                self._orders[order_id]["state"] = "filled"
                req: SubmitRequest = self._orders[order_id]["req"]
                self._orders[order_id]["fill"] = {
                    "symbol": req.symbol,
                    "side": req.side,
                    "quantity": req.quantity,
                    "price": float(req.meta.get("price", 0.0)),
                }

        cur = self._orders[order_id]
        return OrderStatus(order_id=order_id, state=cur["state"], fill=cur["fill"], error=cur["error"])
