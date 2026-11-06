from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .canonical_json import validate_no_floats


def div_toward_zero(n: int, d: int) -> int:
    """
    Deterministic integer division with rounding toward zero.
    """
    if d == 0:
        raise ZeroDivisionError("division by zero")
    q = abs(n) // abs(d)
    return q if (n >= 0) == (d >= 0) else -q


@dataclass
class IntLedgerEngine:
    """
    Minimal deterministic integer LedgerEngine (Slice-3 State Contract).

    IMPORTANT:
    - This engine is used for Slice-3 determinism/regression tests.
    - Production accounting continues to use src.execution.ledger.LedgerEngine.
    """

    base_ccy: str = "USD"
    money_scale: int = 10000
    price_scale: int = 10000
    qty_scale: int = 1

    cash_int: int = 0
    positions: dict[str, dict[str, int]] = field(
        default_factory=dict
    )  # {symbol: {qty_int, avg_price_int}}
    last_price_by_symbol: dict[str, int] = field(default_factory=dict)
    realized_pnl_int: int = 0
    unrealized_pnl_int: int = 0
    fees_paid_int: int = 0
    equity_int: int = 0

    def apply(self, event: Mapping[str, Any]) -> dict[str, Any]:
        validate_no_floats(event)

        et = str(event.get("event_type") or "")
        payload = event.get("payload") or {}
        if not isinstance(payload, Mapping):
            raise ValueError("payload must be mapping")

        if et == "Price":
            sym = str(payload.get("symbol") or "")
            price_int = int(payload["price_int"])
            self.last_price_by_symbol[sym] = price_int
            self._recompute_derived()
            return {"applied": True, "event_type": et, "symbol": sym}

        if et == "Fee":
            fee_int = int(payload["fee_int"])
            self.cash_int -= fee_int
            self.fees_paid_int += fee_int
            self._recompute_derived()
            return {"applied": True, "event_type": et, "fee_int": fee_int}

        if et == "Fill":
            sym = str(payload.get("symbol") or "")
            side = str(payload.get("side") or "").upper()
            qty_int = int(payload["qty_int"])
            price_int = int(payload["price_int"])
            if qty_int < 0:
                raise ValueError("qty_int must be >= 0")

            pos = self.positions.get(sym, {"qty_int": 0, "avg_price_int": 0})
            pre_qty = int(pos["qty_int"])
            pre_avg = int(pos["avg_price_int"])

            if side == "BUY":
                notional = self._price_to_money_int(price_int * qty_int)
                self.cash_int -= notional
                new_qty = pre_qty + qty_int
                new_avg = (
                    0
                    if new_qty == 0
                    else div_toward_zero(pre_avg * pre_qty + price_int * qty_int, new_qty)
                )
                self.positions[sym] = {"qty_int": new_qty, "avg_price_int": new_avg}

            elif side == "SELL":
                notional = self._price_to_money_int(price_int * qty_int)
                self.cash_int += notional
                sell_qty = qty_int
                new_qty = pre_qty - sell_qty

                closed_qty = min(pre_qty, sell_qty) if pre_qty > 0 else 0
                if closed_qty > 0:
                    realized_price_delta = price_int - pre_avg
                    self.realized_pnl_int += self._price_to_money_int(
                        realized_price_delta * closed_qty
                    )

                if new_qty == 0:
                    new_avg = 0
                else:
                    new_avg = pre_avg if (pre_qty > 0 and new_qty > 0) else price_int
                self.positions[sym] = {"qty_int": new_qty, "avg_price_int": new_avg}

            else:
                raise ValueError(f"Unsupported Fill side: {side!r}")

            self._recompute_derived()
            return {
                "applied": True,
                "event_type": et,
                "symbol": sym,
                "qty_int": qty_int,
                "price_int": price_int,
            }

        # Non-economic events are allowed; they don't mutate state.
        return {"applied": False, "event_type": et}

    def _price_to_money_int(self, price_times_qty_int: int) -> int:
        denom = self.price_scale * self.qty_scale
        numer = price_times_qty_int * self.money_scale
        return div_toward_zero(numer, denom)

    def _recompute_derived(self) -> None:
        equity = self.cash_int
        unreal = 0
        for sym in sorted(self.positions.keys()):
            pos = self.positions[sym]
            qty = int(pos["qty_int"])
            avg = int(pos["avg_price_int"])
            last_p = int(self.last_price_by_symbol.get(sym, 0))
            equity += self._price_to_money_int(qty * last_p)
            unreal += self._price_to_money_int((last_p - avg) * qty)
        self.equity_int = equity
        self.unrealized_pnl_int = unreal

    def get_state(self) -> dict[str, Any]:
        return {
            "version": 1,
            "base_ccy": self.base_ccy,
            "money_scale": int(self.money_scale),
            "price_scale": int(self.price_scale),
            "qty_scale": int(self.qty_scale),
            "cash_int": int(self.cash_int),
            "equity_int": int(self.equity_int),
            "positions": {
                sym: {
                    "qty_int": int(self.positions[sym]["qty_int"]),
                    "avg_price_int": int(self.positions[sym]["avg_price_int"]),
                }
                for sym in sorted(self.positions.keys())
            },
            "realized_pnl_int": int(self.realized_pnl_int),
            "unrealized_pnl_int": int(self.unrealized_pnl_int),
            "fees_paid_int": int(self.fees_paid_int),
            "last_price_by_symbol": {
                sym: int(self.last_price_by_symbol[sym])
                for sym in sorted(self.last_price_by_symbol.keys())
            },
        }
