"""P26 ExecutionAdapterV1 — bridges backtest orders to P24 ExecutionModelV2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from src.execution.p24.config import ExecutionModelV2Config
from src.execution.p24.execution_model_v2 import (
    ExecutionModelV2,
    Fill as P24Fill,
    MarketSnapshot as P24MarketSnapshot,
    Order as P24Order,
)
from src.execution.p26.types import AdapterOrder


@dataclass(frozen=True)
class FillRecord:
    order_id: str
    symbol: str
    side: str
    qty: float
    price: float
    fee: float


def _to_p24_order(ao: AdapterOrder) -> P24Order:
    return P24Order(
        order_id=ao.id,
        side=ao.side,
        type=ao.order_type,
        qty=ao.qty,
        limit_price=ao.limit_price,
        stop_price=ao.stop_price,
    )


def _to_fill_record(f: P24Fill, symbol: str, side: str) -> FillRecord:
    return FillRecord(
        order_id=f.order_id, symbol=symbol, side=side, qty=f.qty, price=f.price, fee=f.fee
    )


class ExecutionAdapterV1:
    """
    Bridges backtest orders to deterministic execution model.
    """

    def __init__(self, model: ExecutionModelV2, cfg: ExecutionModelV2Config) -> None:
        self._model = model
        self._cfg = cfg

    def execute_bar(
        self,
        *,
        snapshot: P24MarketSnapshot,
        orders: Sequence[AdapterOrder],
    ) -> List[FillRecord]:
        if not orders:
            return []
        order_map = {ao.id: (ao.symbol, ao.side) for ao in orders}
        p24_orders = [_to_p24_order(ao) for ao in orders]
        fills = self._model.process_bar(snapshot, p24_orders)
        return [
            _to_fill_record(f, order_map[f.order_id][0], order_map[f.order_id][1]) for f in fills
        ]
