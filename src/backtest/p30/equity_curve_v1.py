"""P30 — Equity curve v1 (deterministic backtest reporting primitive)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from src.backtest.p29.accounting_v2 import PositionCashStateV2, apply_fills_v2
from src.execution.p26.adapter import FillRecord


@dataclass(frozen=True)
class EquityRowV1:
    idx: int
    price: float
    cash: float
    qty: float
    position_value: float
    realized_pnl: float
    unrealized_pnl: float
    fees: float
    equity: float


def equity_curve_v1(
    prices: Sequence[float],
    fills_by_idx: Sequence[Sequence[FillRecord]],
    *,
    initial_cash: float = 0.0,
    symbol: str = "MOCK",
) -> list[EquityRowV1]:
    """
    Deterministic fold over bars:
    - apply fills at idx
    - mark-to-market using prices[idx]
    Notes:
    - single-asset v1; multi-asset requires portfolio state (future phase).
    """
    if len(prices) != len(fills_by_idx):
        raise ValueError("prices and fills_by_idx must have same length")

    st = PositionCashStateV2.empty(initial_cash)
    out: list[EquityRowV1] = []

    for i, px in enumerate(prices):
        fills = list(fills_by_idx[i])
        if fills:
            st = apply_fills_v2(st, fills)

        qty = float(st.positions_qty.get(symbol, 0.0))
        cash = float(st.cash)
        avg_cost = float(st.avg_cost.get(symbol, 0.0))
        if qty == 0.0:
            avg_cost = 0.0
        pos_val = qty * float(px)
        unreal = (float(px) - avg_cost) * qty
        fees = float(sum(float(f.fee) for f in fills)) if fills else 0.0
        eq = cash + pos_val

        out.append(
            EquityRowV1(
                idx=i,
                price=float(px),
                cash=cash,
                qty=qty,
                position_value=pos_val,
                realized_pnl=float(st.realized_pnl),
                unrealized_pnl=unreal,
                fees=fees,
                equity=eq,
            )
        )

    return out
