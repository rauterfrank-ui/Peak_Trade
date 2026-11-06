"""P29 — Accounting v2 (avg cost + realized PnL)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from src.execution.p26.adapter import FillRecord


class AccountingErrorV2(RuntimeError):
    """Accounting invariant violation."""

    pass


@dataclass(frozen=True)
class PositionCashStateV2:
    """
    Deterministic state container (single-currency cash).
    positions_qty: symbol -> qty (>= 0)
    avg_cost: symbol -> average cost per unit (>= 0, zero iff qty == 0)
    cash: float
    realized_pnl: float (cumulative)
    """

    positions_qty: Dict[str, float]
    avg_cost: Dict[str, float]
    cash: float
    realized_pnl: float

    @staticmethod
    def empty(initial_cash: float = 0.0) -> "PositionCashStateV2":
        return PositionCashStateV2(
            positions_qty={}, avg_cost={}, cash=float(initial_cash), realized_pnl=0.0
        )


def _get_qty_cost(state: PositionCashStateV2, symbol: str) -> Tuple[float, float]:
    qty = float(state.positions_qty.get(symbol, 0.0))
    cost = float(state.avg_cost.get(symbol, 0.0))
    if qty == 0.0 and cost != 0.0:
        cost = 0.0
    return qty, cost


def apply_fills_v2(state: PositionCashStateV2, fills: Iterable[FillRecord]) -> PositionCashStateV2:
    """
    Apply fills in-order, deterministically.
    Conventions:
      - fee always reduces cash
      - BUY: cash -= qty*price + fee ; avg cost updates by weighted average
      - SELL: cash += qty*price - fee ; realized += (price-avg_cost)*qty - fee
      - No shorting: SELL qty must be <= current qty (strict)
    """
    positions = dict(state.positions_qty)
    avg_cost = dict(state.avg_cost)
    cash = float(state.cash)
    realized = float(state.realized_pnl)

    for f in fills:
        symbol = f.symbol
        side = f.side.upper()
        qty = float(f.qty)
        price = float(f.price)
        fee = float(f.fee)

        if qty < 0.0:
            raise AccountingErrorV2(f"negative qty not allowed: {qty}")
        if price < 0.0:
            raise AccountingErrorV2(f"negative price not allowed: {price}")
        if fee < 0.0:
            raise AccountingErrorV2(f"negative fee not allowed: {fee}")

        cur_qty = float(positions.get(symbol, 0.0))
        cur_avg = float(avg_cost.get(symbol, 0.0))
        if cur_qty == 0.0:
            cur_avg = 0.0

        notional = qty * price

        if side == "BUY":
            cash -= notional + fee

            new_qty = cur_qty + qty
            if new_qty <= 0.0:
                new_qty = 0.0
                new_avg = 0.0
            else:
                new_avg = ((cur_qty * cur_avg) + (qty * price)) / new_qty

            positions[symbol] = new_qty
            avg_cost[symbol] = 0.0 if new_qty == 0.0 else new_avg

        elif side == "SELL":
            if qty > cur_qty + 1e-12:
                raise AccountingErrorV2(
                    f"sell qty exceeds position: sell={qty} pos={cur_qty} symbol={symbol}"
                )

            cash += notional - fee
            realized += ((price - cur_avg) * qty) - fee

            new_qty = cur_qty - qty
            if abs(new_qty) <= 1e-12:
                new_qty = 0.0

            positions[symbol] = new_qty
            avg_cost[symbol] = 0.0 if new_qty == 0.0 else cur_avg

        else:
            raise AccountingErrorV2(f"unsupported side: {side}")

        if positions[symbol] < -1e-12:
            raise AccountingErrorV2(
                f"negative position invariant violated: {positions[symbol]} symbol={symbol}"
            )

    positions = {k: float(v) for k, v in positions.items() if abs(float(v)) > 0.0}
    avg_cost = {k: float(avg_cost.get(k, 0.0)) for k in positions}

    return PositionCashStateV2(
        positions_qty=positions, avg_cost=avg_cost, cash=cash, realized_pnl=realized
    )
