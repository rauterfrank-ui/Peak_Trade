from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

from .models import (
    AccountState,
    DecimalPolicy,
    FillEvent,
    LedgerEntry,
    LedgerEvent,
    LedgerSnapshot,
    MarkEvent,
    PositionLot,
    PositionState,
)


def _is_float_present(obj: Any) -> bool:
    if isinstance(obj, float):
        return True
    if isinstance(obj, Mapping):
        return any(_is_float_present(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return any(_is_float_present(v) for v in obj)
    return False


def _sign(x: Decimal) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


@dataclass
class LedgerEngine:
    """
    EXEC_SLICE2 FIFO-lot ledger engine.

    Determinism contract:
    - Caller provides (ts_utc, seq); engine enforces non-decreasing ordering.
    - Decimal everywhere (floats forbidden).
    - Quantization centralized in DecimalPolicy and applied on ingestion & arithmetic.
    """

    base_ccy: str = "USD"
    decimal_policy: DecimalPolicy = field(default_factory=DecimalPolicy.default)

    _account: AccountState = field(default_factory=AccountState, init=False)
    _last_key: Optional[Tuple[str, int]] = field(default=None, init=False)

    def __init__(self, base_ccy: str = "USD", decimal_policy: Optional[DecimalPolicy] = None, *, quote_currency: Optional[str] = None):
        # Back-compat alias: quote_currency behaves like base_ccy.
        self.base_ccy = str(quote_currency or base_ccy)
        self.decimal_policy = decimal_policy or DecimalPolicy.default()
        self._account = AccountState()
        self._last_key = None

    @property
    def account(self) -> AccountState:
        return self._account

    def open_cash(self, *, amount: Decimal, ccy: Optional[str] = None) -> List[LedgerEntry]:
        """
        Deterministically seed cash (offline-only).
        """
        ccy_s = str(ccy or self.base_ccy)
        amt_q = self.decimal_policy.quantize_money(amount)
        cur = self._account.cash_by_ccy.get(ccy_s, Decimal("0"))
        self._account.cash_by_ccy[ccy_s] = self.decimal_policy.quantize_money(cur + amt_q)
        return [
            LedgerEntry(
                ts_utc="1970-01-01T00:00:00Z",
                seq=0,
                kind="OPEN_CASH",
                instrument=None,
                fields={"ccy": ccy_s, "amount": amt_q},
            )
        ]

    def apply(self, event: LedgerEvent) -> List[LedgerEntry]:
        if _is_float_present(event):
            raise TypeError("float forbidden for deterministic accounting")

        if isinstance(event, FillEvent):
            return self._apply_fill(event)
        if isinstance(event, MarkEvent):
            return self._apply_mark(event)
        raise TypeError(f"Unsupported event type: {type(event)!r}")

    def snapshot(self, ts_utc_last: str, seq_last: int) -> LedgerSnapshot:
        # Compute unrealized + equity deterministically (base_ccy only for now).
        pol = self.decimal_policy
        unreal = Decimal("0")
        position_value = Decimal("0")

        for inst in sorted(self._account.positions.keys()):
            pos = self._account.positions[inst]
            if pos.last_mark_price is None:
                continue
            mark = pol.quantize_price(pos.last_mark_price)
            for lot in pos.lots:
                qty = pol.quantize_qty(lot.qty_signed)
                if qty == 0:
                    continue
                qty_abs = qty.copy_abs()
                if qty > 0:
                    unreal += pol.quantize_money((mark - lot.price) * qty_abs)
                else:
                    unreal += pol.quantize_money((lot.price - mark) * qty_abs)
                position_value += pol.quantize_money(mark * qty)

        cash = pol.quantize_money(self._account.cash_by_ccy.get(self.base_ccy, Decimal("0")))
        equity = pol.quantize_money(cash + position_value)

        return LedgerSnapshot(
            ts_utc_last=str(ts_utc_last),
            seq_last=int(seq_last),
            account=self._account,
            unrealized_pnl_by_ccy={self.base_ccy: pol.quantize_money(unreal)},
            equity_by_ccy={self.base_ccy: equity},
            hash_inputs=None,
        )

    # ---------------------------------------------------------------------
    # Internals
    # ---------------------------------------------------------------------

    def _check_ordering(self, ts_utc: str, seq: int) -> None:
        if not ts_utc.endswith("Z"):
            raise ValueError("ts_utc must be UTC ISO8601 with trailing 'Z'")
        key = (ts_utc, int(seq))
        if self._last_key is not None and key < self._last_key:
            raise ValueError(f"Non-monotonic event ordering: {key} < {self._last_key}")
        self._last_key = key

    def _get_pos(self, instrument: str) -> PositionState:
        if instrument not in self._account.positions:
            self._account.positions[instrument] = PositionState()
        return self._account.positions[instrument]

    def _apply_mark(self, ev: MarkEvent) -> List[LedgerEntry]:
        self._check_ordering(ev.ts_utc, ev.seq)
        pol = self.decimal_policy
        price_q = pol.quantize_price(ev.price)
        pos = self._get_pos(ev.instrument)
        pos.last_mark_price = price_q
        return [
            LedgerEntry(
                ts_utc=ev.ts_utc,
                seq=ev.seq,
                kind="MARK",
                instrument=ev.instrument,
                fields={"price": price_q},
            )
        ]

    def _apply_fill(self, ev: FillEvent) -> List[LedgerEntry]:
        self._check_ordering(ev.ts_utc, ev.seq)
        pol = self.decimal_policy

        side = str(ev.side).upper()
        if side not in {"BUY", "SELL"}:
            raise ValueError(f"Unsupported side: {ev.side!r}")

        qty = pol.quantize_qty(ev.qty)
        price = pol.quantize_price(ev.price)
        fee = pol.quantize_money(ev.fee)
        fee_ccy = str(ev.fee_ccy or self.base_ccy)

        if qty < 0:
            raise ValueError("qty must be >= 0")

        signed_qty = qty if side == "BUY" else -qty
        notional = pol.quantize_money(qty * price)

        # Cash movements (base_ccy for notional, fee_ccy for fees).
        cash_cur = self._account.cash_by_ccy.get(self.base_ccy, Decimal("0"))
        cash_delta = -notional if side == "BUY" else notional
        self._account.cash_by_ccy[self.base_ccy] = pol.quantize_money(cash_cur + cash_delta)

        fee_cash_cur = self._account.cash_by_ccy.get(fee_ccy, Decimal("0"))
        self._account.cash_by_ccy[fee_ccy] = pol.quantize_money(fee_cash_cur - fee)
        self._account.fees_by_ccy[fee_ccy] = pol.quantize_money(
            self._account.fees_by_ccy.get(fee_ccy, Decimal("0")) + fee
        )

        # FIFO matching against existing lots.
        pos = self._get_pos(ev.instrument)
        realized = Decimal("0")
        incoming = signed_qty

        # Ensure lots are in FIFO order by (ts_utc, seq) (stable).
        pos.lots.sort(key=lambda l: (l.ts_utc, l.seq))

        while incoming != 0 and pos.lots and _sign(incoming) != _sign(pos.lots[0].qty_signed):
            lot = pos.lots[0]
            lot_qty = pol.quantize_qty(lot.qty_signed)
            if lot_qty == 0:
                pos.lots.pop(0)
                continue

            match_abs = min(incoming.copy_abs(), lot_qty.copy_abs())
            match_abs = pol.quantize_qty(match_abs)
            if match_abs == 0:
                break

            if lot_qty > 0 and incoming < 0:
                # Closing long with SELL.
                realized += pol.quantize_money((price - lot.price) * match_abs)
            elif lot_qty < 0 and incoming > 0:
                # Closing short with BUY.
                realized += pol.quantize_money((lot.price - price) * match_abs)

            # Reduce lot and incoming.
            if lot_qty > 0:
                lot.qty_signed = pol.quantize_qty(lot_qty - match_abs)
                incoming = pol.quantize_qty(incoming + match_abs)  # incoming is negative here
            else:
                lot.qty_signed = pol.quantize_qty(lot_qty + match_abs)  # lot_qty negative
                incoming = pol.quantize_qty(incoming - match_abs)  # incoming positive here

            if lot.qty_signed == 0:
                pos.lots.pop(0)

        # If still remaining, open a new lot at fill price.
        if incoming != 0:
            pos.lots.append(
                PositionLot(qty_signed=pol.quantize_qty(incoming), price=price, ts_utc=ev.ts_utc, seq=ev.seq)
            )

        realized = pol.quantize_money(realized)
        self._account.realized_pnl_by_ccy[self.base_ccy] = pol.quantize_money(
            self._account.realized_pnl_by_ccy.get(self.base_ccy, Decimal("0")) + realized
        )

        # Stable ledger entries list.
        entries: List[LedgerEntry] = [
            LedgerEntry(
                ts_utc=ev.ts_utc,
                seq=ev.seq,
                kind="FILL",
                instrument=ev.instrument,
                fields={
                    "side": side,
                    "qty": qty,
                    "price": price,
                    "notional": notional,
                    "fee": fee,
                    "fee_ccy": fee_ccy,
                    "trade_id": ev.trade_id,
                    "cash_delta_base": cash_delta,
                    "realized_pnl_delta_base": realized,
                },
            )
        ]
        return entries
