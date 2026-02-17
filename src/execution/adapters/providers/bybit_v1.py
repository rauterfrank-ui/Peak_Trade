"""Bybit adapter — v1 (MOCKS ONLY)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from src.execution.adapters.base_v1 import (
    AdapterCapabilitiesV1,
    ExecutionAdapterV1,
    OrderIntentV1,
    OrderResultV1,
)


@dataclass(frozen=True)
class BybitAdapterConfigV1:
    """Mocks-only: keep config minimal and non-sensitive."""

    environment: str = "paper"  # paper/shadow only (no live)
    account_tag: str = "mock"


class BybitExecutionAdapterV1(ExecutionAdapterV1):
    """
    Bybit adapter (mocks only).
    No network calls. No API keys. Deterministic outputs.
    """

    def __init__(self, cfg: Optional[BybitAdapterConfigV1] = None):
        self._cfg = cfg or BybitAdapterConfigV1()
        self._orders: Dict[str, OrderIntentV1] = {}
        self._seq: int = 0

    def capabilities(self) -> AdapterCapabilitiesV1:
        return AdapterCapabilitiesV1(
            name="bybit_v1",
            markets=["spot", "perp"],
            order_types=["market", "limit"],
            supports_post_only=True,
            supports_reduce_only=True,
            supports_batch_cancel=True,
            supports_cancel_all=True,
            supports_ws_orders=False,
            supports_ws_fills=False,
        )

    def place_order(self, intent: OrderIntentV1) -> OrderResultV1:
        self._seq += 1
        order_id = f"bybit_mock_{self._seq}"
        self._orders[order_id] = intent
        return OrderResultV1(
            ok=True,
            adapter="bybit_v1",
            order_id=order_id,
            client_id=intent.client_id,
            message="mock_ok",
        )

    def cancel_all(self, symbol: Optional[str] = None) -> int:
        if symbol is None:
            n = len(self._orders)
            self._orders.clear()
            return n
        to_del = [oid for oid, it in self._orders.items() if it.symbol == symbol]
        for oid in to_del:
            del self._orders[oid]
        return len(to_del)

    def batch_cancel(self, order_ids: List[str]) -> int:
        n = 0
        for oid in order_ids:
            if oid in self._orders:
                del self._orders[oid]
                n += 1
        return n
