"""P28 — Deterministic positions + cash accounting v1."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from src.execution.p26.adapter import FillRecord


@dataclass(frozen=True)
class PositionCashState:
    symbol: str
    position_qty: Decimal
    cash: Decimal


class AccountingError(ValueError):
    """Accounting invariant violation."""

    pass


def apply_fills_v1(
    *,
    symbol: str,
    starting_cash: Decimal,
    starting_position_qty: Decimal,
    fills: Iterable[FillRecord],
    allow_short: bool = False,
) -> PositionCashState:
    """
    Deterministically apply fills to (cash, position) for a single symbol.

    Assumptions:
    - FillRecord.price is the executed price (already includes slippage if modeled).
    - FillRecord.fee is the absolute fee in quote currency (cash).
    - FillRecord.qty is positive.
    - FillRecord.side in {"BUY","SELL"}.
    """
    cash = Decimal(starting_cash)
    pos = Decimal(starting_position_qty)

    for f in fills:
        if f.symbol != symbol:
            raise AccountingError(f"unexpected symbol in fill: {f.symbol} != {symbol}")
        if f.qty <= 0:
            raise AccountingError(f"fill qty must be > 0, got {f.qty}")
        if f.price <= 0:
            raise AccountingError(f"fill price must be > 0, got {f.price}")
        fee = Decimal(str(f.fee))
        notional = Decimal(str(f.qty)) * Decimal(str(f.price))

        if f.side.upper() == "BUY":
            cash -= notional
            cash -= fee
            pos += Decimal(str(f.qty))
        elif f.side.upper() == "SELL":
            if not allow_short and pos < Decimal(str(f.qty)):
                raise AccountingError(
                    f"sell qty exceeds position (no shorting): pos={pos}, sell={f.qty}"
                )
            cash += notional
            cash -= fee
            pos -= Decimal(str(f.qty))
        else:
            raise AccountingError(f"unknown side: {f.side}")

    return PositionCashState(symbol=symbol, position_qty=pos, cash=cash)
