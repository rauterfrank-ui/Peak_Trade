from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

from src.execution.determinism import stable_id

from .models import JournalEntry, Posting, Position, QuantizationPolicy, ValuationSnapshot
from .pnl import total_unrealized_pnl
from .quantization import (
    canonical_json,
    d,
    parse_symbol,
    q_money,
    q_price,
    q_qty,
)


def _acct_cash(quote: str) -> str:
    return f"CASH:{quote}"


def _acct_inventory(symbol: str, quote: str) -> str:
    # Inventory cost is kept in quote currency; symbol scopes the sub-ledger.
    return f"INVENTORY_COST:{symbol}:{quote}"


def _acct_fees(quote: str) -> str:
    return f"FEES_EXPENSE:{quote}"


def _acct_realized_pnl(quote: str) -> str:
    return f"REALIZED_PNL:{quote}"


def _acct_opening_equity(quote: str) -> str:
    return f"EQUITY_OPENING:{quote}"


@dataclass
class LedgerState:
    quote_currency: str
    policy: QuantizationPolicy = field(default_factory=QuantizationPolicy)

    accounts: Dict[str, Decimal] = field(default_factory=dict)
    positions: Dict[str, Position] = field(default_factory=dict)
    journal: List[JournalEntry] = field(default_factory=list)

    # Determinism / idempotency
    seen_event_ids: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_ts_sim: int = -1

    def get_account(self, account: str) -> Decimal:
        return self.accounts.get(account, Decimal("0"))

    def set_account(self, account: str, value: Decimal) -> None:
        self.accounts[account] = value

    def cash(self) -> Decimal:
        return self.get_account(_acct_cash(self.quote_currency))


class LedgerEngine:
    """
    Deterministic ledger engine that consumes execution events and produces:
    - Double-entry journal entries (quote currency)
    - Account balances
    - Position state (WAC)
    - Deterministic snapshots (valuation)
    """

    def __init__(self, *, quote_currency: str, policy: Optional[QuantizationPolicy] = None):
        self.state = LedgerState(
            quote_currency=quote_currency, policy=policy or QuantizationPolicy()
        )

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def apply(self, event: Union[Mapping[str, Any], "FillLike"]) -> LedgerState:
        """
        Apply an event and mutate internal state deterministically.

        Supported inputs:
        - BETA_EXEC_V1 dict events emitted by ExecutionOrchestrator (Slice 1)
        - Fill-like objects (duck-typed) with .symbol/.side/.quantity/.price/.fee/.fee_currency
        """
        if isinstance(event, Mapping):
            self._apply_beta_event(event)
            return self.state

        # Duck-typed fill
        self._apply_fill_like(event)
        return self.state

    def open_cash(self, *, amount: Decimal, entry_id: str = "opening_cash") -> LedgerState:
        """
        Book an opening cash balance via a balanced journal entry.
        """
        amt = q_money(d(amount), policy=self.state.policy)
        je = JournalEntry(
            entry_id=entry_id,
            ts_sim=0,
            event_id=stable_id(
                kind="ledger_opening", fields={"entry_id": entry_id, "amount": str(amt)}
            ),
            symbol="",
            kind="OPENING",
            postings=[
                Posting(account=_acct_cash(self.state.quote_currency), amount=amt),
                Posting(account=_acct_opening_equity(self.state.quote_currency), amount=-amt),
            ],
            meta={"quote_currency": self.state.quote_currency},
        )
        self._commit_journal_entry(je)
        return self.state

    def snapshot(
        self,
        *,
        ts_sim: int,
        mark_prices: Optional[Dict[str, Decimal]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> ValuationSnapshot:
        mark_prices = mark_prices or {}
        policy = self.state.policy

        # Positions list must be stable (sorted by symbol)
        pos_list = [self.state.positions[s].to_dict() for s in sorted(self.state.positions.keys())]

        realized = q_money(
            sum((p.realized_pnl for p in self.state.positions.values()), Decimal("0")),
            policy=policy,
        )
        unrealized = total_unrealized_pnl(
            self.state.positions, mark_prices=mark_prices, policy=policy
        )

        # Equity: cash + sum(qty * mark)
        position_value = Decimal("0")
        for sym, pos in self.state.positions.items():
            if sym not in mark_prices:
                continue
            position_value += q_money(mark_prices[sym] * pos.quantity, policy=policy)
        position_value = q_money(position_value, policy=policy)

        equity = q_money(self.state.cash() + position_value, policy=policy)

        return ValuationSnapshot(
            ts_sim=ts_sim,
            quote_currency=self.state.quote_currency,
            cash=self.state.cash(),
            positions=pos_list,
            realized_pnl=realized,
            unrealized_pnl=unrealized,
            equity=equity,
            meta=meta or {},
        )

    def export_snapshot_json(
        self,
        *,
        ts_sim: int,
        mark_prices: Optional[Dict[str, Decimal]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        snap = self.snapshot(ts_sim=ts_sim, mark_prices=mark_prices, meta=meta)
        return json.dumps(snap.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    # -------------------------------------------------------------------------
    # Beta event ingestion (Slice 1 logs)
    # -------------------------------------------------------------------------

    def _apply_beta_event(self, event: Mapping[str, Any]) -> None:
        schema = event.get("schema_version")
        if schema != "BETA_EXEC_V1":
            raise ValueError(f"Unsupported event schema_version: {schema!r}")

        event_id = str(event.get("event_id") or "")
        if not event_id:
            raise ValueError("Missing event_id")

        # Idempotent replay: exact duplicate is a no-op; mismatch is an error.
        if event_id in self.state.seen_event_ids:
            prior = self.state.seen_event_ids[event_id]
            if dict(prior) == dict(event):
                return
            raise ValueError(f"Conflicting duplicate event_id detected: {event_id}")

        ts_sim = int(event.get("ts_sim", -1))
        if ts_sim < 0:
            raise ValueError("Missing/invalid ts_sim")
        if ts_sim < self.state.last_ts_sim:
            # Enforce deterministic monotonicity; caller should sort upstream.
            raise ValueError(f"Non-monotonic ts_sim: {ts_sim} < {self.state.last_ts_sim}")

        self.state.last_ts_sim = ts_sim
        self.state.seen_event_ids[event_id] = dict(event)

        event_type = str(event.get("event_type") or "")
        if event_type != "FILL":
            return  # Slice 2 consumes economic events only

        symbol = str(event.get("symbol") or "")
        if not symbol:
            raise ValueError("FILL missing symbol")

        payload = event.get("payload") or {}
        if not isinstance(payload, Mapping):
            raise ValueError("payload must be a mapping")

        side = payload.get("side")
        if side is None:
            # Safety: without side, accounting cannot be correct.
            raise ValueError(
                "BETA_EXEC_V1 FILL payload missing 'side'. "
                "Update Slice-1 emitter to include side for deterministic accounting."
            )

        qty = q_qty(d(payload.get("quantity")), policy=self.state.policy)
        price = q_price(d(payload.get("price")), policy=self.state.policy)
        fee = q_money(d(payload.get("fee", "0")), policy=self.state.policy)
        fee_ccy = str(payload.get("fee_currency") or self.state.quote_currency)

        base, quote = parse_symbol(symbol)
        if quote != self.state.quote_currency:
            raise ValueError(
                f"Quote currency mismatch: engine={self.state.quote_currency}, event={quote}"
            )
        if fee_ccy != self.state.quote_currency:
            raise ValueError(
                f"Fee currency mismatch (Slice 2 single-ccy): fee_currency={fee_ccy}, quote={quote}"
            )

        client_order_id = str(event.get("client_order_id") or "")

        self._apply_fill(
            symbol=symbol,
            side=str(side),
            qty=qty,
            price=price,
            fee=fee,
            ts_sim=ts_sim,
            event_id=event_id,
            meta={
                "client_order_id": client_order_id,
                "fill_id": payload.get("fill_id"),
            },
        )

    # -------------------------------------------------------------------------
    # Fill application (core accounting)
    # -------------------------------------------------------------------------

    def _apply_fill_like(self, fill: Any) -> None:
        # Minimal duck typing; this path is mainly for unit tests / adapters.
        symbol = str(getattr(fill, "symbol"))
        side = getattr(fill, "side")
        side_s = side.value if hasattr(side, "value") else str(side)
        qty = q_qty(d(getattr(fill, "quantity")), policy=self.state.policy)
        price = q_price(d(getattr(fill, "price")), policy=self.state.policy)
        fee = q_money(d(getattr(fill, "fee", "0")), policy=self.state.policy)
        fee_ccy = str(getattr(fill, "fee_currency", self.state.quote_currency))
        _, quote = parse_symbol(symbol)
        if quote != self.state.quote_currency or fee_ccy != self.state.quote_currency:
            raise ValueError("Slice 2 LedgerEngine supports a single quote currency only")

        # Use stable_id to deterministically derive event_id for fill-like objects.
        event_id = stable_id(
            kind="fill_like",
            fields={
                "symbol": symbol,
                "side": side_s,
                "quantity": str(qty),
                "price": str(price),
                "fee": str(fee),
            },
        )
        self._apply_fill(
            symbol=symbol,
            side=side_s,
            qty=qty,
            price=price,
            fee=fee,
            ts_sim=max(self.state.last_ts_sim, 0) + 1,
            event_id=event_id,
            meta={"source": "fill_like"},
        )

    def _get_position(self, symbol: str) -> Position:
        if symbol not in self.state.positions:
            self.state.positions[symbol] = Position(symbol=symbol)
        return self.state.positions[symbol]

    def _apply_fill(
        self,
        *,
        symbol: str,
        side: str,
        qty: Decimal,
        price: Decimal,
        fee: Decimal,
        ts_sim: int,
        event_id: str,
        meta: Dict[str, Any],
    ) -> None:
        policy = self.state.policy
        side_u = side.upper()
        if side_u not in {"BUY", "SELL"}:
            raise ValueError(f"Unsupported side: {side!r}")

        notional = q_money(qty * price, policy=policy)

        pos = self._get_position(symbol)
        pre_qty = pos.quantity
        pre_avg = pos.avg_cost
        pre_inv = q_money(pos.inventory_cost_balance(), policy=policy)

        realized = Decimal("0")

        if side_u == "BUY":
            # BUY increases qty; may cover short first.
            if pre_qty < 0:
                cover_qty = min(qty, abs(pre_qty))
                realized = q_money((pre_avg - price) * cover_qty, policy=policy)
            self._update_position_wac(symbol=symbol, side=side_u, qty=qty, price=price, fee=fee)
        else:
            # SELL decreases qty; may close long first.
            if pre_qty > 0:
                close_qty = min(qty, pre_qty)
                realized = q_money((price - pre_avg) * close_qty, policy=policy)
            self._update_position_wac(symbol=symbol, side=side_u, qty=qty, price=price, fee=fee)

        post_inv = q_money(self.state.positions[symbol].inventory_cost_balance(), policy=policy)
        inv_delta = q_money(post_inv - pre_inv, policy=policy)

        # Account postings (quote currency)
        cash_delta = (
            q_money(notional - fee, policy=policy)
            if side_u == "SELL"
            else q_money(-(notional + fee), policy=policy)
        )
        fees_delta = q_money(fee, policy=policy)
        realized_posting = q_money(-realized, policy=policy) if realized != 0 else Decimal("0")

        postings: List[Posting] = [
            Posting(account=_acct_cash(self.state.quote_currency), amount=cash_delta),
            Posting(account=_acct_fees(self.state.quote_currency), amount=fees_delta),
            Posting(account=_acct_inventory(symbol, self.state.quote_currency), amount=inv_delta),
        ]
        if realized_posting != 0:
            postings.append(
                Posting(
                    account=_acct_realized_pnl(self.state.quote_currency), amount=realized_posting
                )
            )

        # Stable ordering of postings for deterministic exports
        postings = sorted(postings, key=lambda p: (p.account, str(p.amount)))

        entry_id = stable_id(
            kind="journal_entry",
            fields={
                "event_id": event_id,
                "ts_sim": ts_sim,
                "symbol": symbol,
                "side": side_u,
                "qty": str(qty),
                "price": str(price),
                "fee": str(fee),
            },
        )[:32]

        je = JournalEntry(
            entry_id=f"je_{entry_id}",
            ts_sim=ts_sim,
            event_id=event_id,
            symbol=symbol,
            kind="FILL",
            postings=postings,
            meta={
                **meta,
                "side": side_u,
                "quantity": str(qty),
                "price": str(price),
                "notional": str(notional),
                "fee": str(fee),
                "realized_pnl": str(realized),
            },
        )
        self._commit_journal_entry(je)

    def _update_position_wac(
        self, *, symbol: str, side: str, qty: Decimal, price: Decimal, fee: Decimal
    ) -> None:
        """
        Update Position using weighted-average-cost (WAC), deterministic and short-aware.
        Fees do not affect avg_cost; they are tracked separately (fees expense).
        """
        policy = self.state.policy
        pos = self._get_position(symbol)

        qty = q_qty(qty, policy=policy)
        price = q_price(price, policy=policy)

        pre_qty = pos.quantity
        pre_avg = pos.avg_cost

        def _abs(x: Decimal) -> Decimal:
            return x.copy_abs()

        if side == "BUY":
            if pre_qty >= 0:
                # Increase long / open new long
                new_qty = q_qty(pre_qty + qty, policy=policy)
                if new_qty == 0:
                    pos.quantity = Decimal("0")
                    pos.avg_cost = Decimal("0")
                else:
                    pre_cost = q_money(pre_avg * pre_qty, policy=policy)
                    add_cost = q_money(price * qty, policy=policy)
                    new_cost = q_money(pre_cost + add_cost, policy=policy)
                    pos.quantity = new_qty
                    pos.avg_cost = q_price(new_cost / new_qty, policy=policy)
            else:
                # Cover short, possibly flip to long
                cover_qty = min(qty, _abs(pre_qty))
                remaining = q_qty(qty - cover_qty, policy=policy)

                # If fully covered: pre_qty + cover_qty == 0
                post_qty_after_cover = q_qty(pre_qty + cover_qty, policy=policy)

                if post_qty_after_cover == 0 and remaining == 0:
                    pos.quantity = Decimal("0")
                    pos.avg_cost = Decimal("0")
                elif post_qty_after_cover == 0 and remaining > 0:
                    # Flip to long with remaining at new price
                    pos.quantity = remaining
                    pos.avg_cost = price
                else:
                    # Still short after partial cover: avg_cost unchanged
                    pos.quantity = post_qty_after_cover
                    pos.avg_cost = pre_avg

        else:  # SELL
            if pre_qty <= 0:
                # Increase short / open new short
                new_qty = q_qty(pre_qty - qty, policy=policy)  # more negative
                if new_qty == 0:
                    pos.quantity = Decimal("0")
                    pos.avg_cost = Decimal("0")
                else:
                    pre_cost_abs = q_money(pre_avg * _abs(pre_qty), policy=policy)
                    add_cost_abs = q_money(price * qty, policy=policy)
                    new_cost_abs = q_money(pre_cost_abs + add_cost_abs, policy=policy)
                    pos.quantity = new_qty
                    pos.avg_cost = q_price(new_cost_abs / _abs(new_qty), policy=policy)
            else:
                # Close long, possibly flip to short
                close_qty = min(qty, pre_qty)
                remaining = q_qty(qty - close_qty, policy=policy)
                post_qty_after_close = q_qty(pre_qty - close_qty, policy=policy)

                if post_qty_after_close == 0 and remaining == 0:
                    pos.quantity = Decimal("0")
                    pos.avg_cost = Decimal("0")
                elif post_qty_after_close == 0 and remaining > 0:
                    # Flip to short with remaining at new price
                    pos.quantity = q_qty(-remaining, policy=policy)
                    pos.avg_cost = price
                else:
                    # Still long after partial close: avg_cost unchanged
                    pos.quantity = post_qty_after_close
                    pos.avg_cost = pre_avg

        # Fees always accumulate; realized PnL is booked separately in journal, but tracked on position too.
        pos.fees = q_money(pos.fees + fee, policy=policy)

        # NOTE: pos.realized_pnl is updated by _apply_fill via realized calc; keep deterministic.
        # This method only updates qty/avg_cost/fees.

    # -------------------------------------------------------------------------
    # Journal commit (invariants + balances)
    # -------------------------------------------------------------------------

    def _commit_journal_entry(self, je: JournalEntry) -> None:
        policy = self.state.policy

        # Invariant: double-entry in quote currency.
        s = q_money(je.postings_sum(), policy=policy)
        if s != 0:
            raise AssertionError(
                f"Double-entry invariant violated: postings_sum={s} for {je.entry_id}"
            )

        # Apply postings to balances
        for p in je.postings:
            cur = self.state.get_account(p.account)
            self.state.set_account(p.account, q_money(cur + p.amount, policy=policy))

        # Update realized pnl accumulator on positions if present
        if je.kind == "FILL":
            sym = je.symbol
            realized_str = je.meta.get("realized_pnl")
            if sym and realized_str is not None:
                realized = q_money(d(realized_str), policy=policy)
                self._get_position(sym).realized_pnl = q_money(
                    self._get_position(sym).realized_pnl + realized, policy=policy
                )

        self.state.journal.append(je)


# Type alias for duck-typed fill objects.
class FillLike:
    symbol: str
    side: Any
    quantity: Any
    price: Any
    fee: Any
    fee_currency: str
