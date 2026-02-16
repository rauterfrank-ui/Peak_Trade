"""Coinbase Advanced Trade adapter — v1 (MOCKS ONLY)."""

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
class CoinbaseAdapterConfigV1:
    """
    Mocks-only adapter config.
    DO NOT add secrets here. This adapter must stay offline until explicitly upgraded.
    """

    venue: str = "coinbase_advanced"
    sandbox: bool = False


class CoinbaseExecutionAdapterV1(ExecutionAdapterV1):
    """
    Coinbase Advanced Trade adapter — v1 (MOCKS ONLY).
    All methods must remain deterministic and offline.
    """

    def __init__(self, cfg: Optional[CoinbaseAdapterConfigV1] = None):
        self._cfg = cfg or CoinbaseAdapterConfigV1()
        self._orders: Dict[str, OrderIntentV1] = {}
        self._seq: int = 0

    def capabilities(self) -> AdapterCapabilitiesV1:
        return AdapterCapabilitiesV1(
            name=self._cfg.venue,
            markets=["spot"],
            order_types=["market", "limit"],
            supports_post_only=True,
            supports_reduce_only=False,
            supports_batch_cancel=True,
            supports_cancel_all=True,
            supports_ws_orders=False,
            supports_ws_fills=False,
        )

    def place_order(self, intent: OrderIntentV1) -> OrderResultV1:
        self._seq += 1
        oid = f"mock_cb_{self._cfg.venue}_{self._seq}"
        self._orders[oid] = intent
        return OrderResultV1(
            ok=True,
            adapter=self._cfg.venue,
            order_id=oid,
            client_id=intent.client_id,
            message="mock_order_accepted",
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
