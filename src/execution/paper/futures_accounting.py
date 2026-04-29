"""
Futures paper accounting v0 — pure, offline, side-effect free.

Deterministic primitives for notional, margin estimates, PnL, funding placeholder,
and conservative liquidation proximity. Not exchange-accurate; not wired to runners.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional, Tuple, Union


class FuturesSide(str, Enum):
    LONG = "long"
    SHORT = "short"


class LiquidationProximityV0(str, Enum):
    """Conservative v0 proximity vs maintenance margin — not venue liquidation."""

    SAFE = "safe"
    WARNING_INSUFFICIENT_BUFFER = "warning_insufficient_buffer"
    BLOCKED_BELOW_MAINTENANCE = "blocked_below_maintenance"


@dataclass(frozen=True)
class FuturesInstrumentSpec:
    symbol: str
    contract_size: Decimal
    tick_size: Decimal
    min_qty: Decimal
    quote_currency: str


@dataclass(frozen=True)
class FuturesMarginSpec:
    initial_margin_rate: Decimal
    maintenance_margin_rate: Decimal
    max_leverage: Decimal


@dataclass(frozen=True)
class FuturesPosition:
    symbol: str
    side: FuturesSide
    qty: Decimal
    entry_price: Decimal
    mark_price: Decimal
    realized_pnl: Decimal
    funding_pnl: Decimal
    fees_paid: Decimal = Decimal("0")


def _to_decimal(name: str, value: Union[Decimal, float, int, str]) -> Decimal:
    if isinstance(value, Decimal):
        d = value
    else:
        d = Decimal(str(value))
    if not d.is_finite():
        raise ValueError(f"{name} must be finite")
    return d


def validate_futures_accounting_inputs(
    *,
    instrument: FuturesInstrumentSpec,
    margin: FuturesMarginSpec,
    wallet_equity: Optional[Decimal] = None,
    position: Optional[FuturesPosition] = None,
) -> None:
    """Fail-closed validation for v0 accounting inputs."""
    if not instrument.symbol.strip():
        raise ValueError("instrument.symbol must be non-empty")
    if not instrument.quote_currency.strip():
        raise ValueError("instrument.quote_currency must be non-empty")

    for label, field in (
        ("contract_size", instrument.contract_size),
        ("tick_size", instrument.tick_size),
        ("min_qty", instrument.min_qty),
    ):
        d = _to_decimal(label, field)
        if d <= 0:
            raise ValueError(f"instrument.{label} must be > 0")

    imr = _to_decimal("initial_margin_rate", margin.initial_margin_rate)
    mmr = _to_decimal("maintenance_margin_rate", margin.maintenance_margin_rate)
    ml = _to_decimal("max_leverage", margin.max_leverage)
    if imr <= 0 or imr >= 1:
        raise ValueError("margin.initial_margin_rate must be in (0, 1)")
    if mmr <= 0 or mmr >= 1:
        raise ValueError("margin.maintenance_margin_rate must be in (0, 1)")
    if mmr > imr:
        raise ValueError("maintenance_margin_rate must not exceed initial_margin_rate")
    if ml < 1:
        raise ValueError("margin.max_leverage must be >= 1")
    # Consistency: margin fractions must support at most max_leverage notional per unit margin.
    if ml * imr < Decimal("1"):
        raise ValueError(
            "inconsistent margin: max_leverage * initial_margin_rate must be >= 1 "
            "(e.g. 10x leverage needs at least 10% initial margin rate)"
        )

    if wallet_equity is not None:
        we = _to_decimal("wallet_equity", wallet_equity)
        if we < 0:
            raise ValueError("wallet_equity must be >= 0")

    if position is not None:
        _validate_position_primitives(
            qty=position.qty,
            entry_price=position.entry_price,
            mark_price=position.mark_price,
        )


def _validate_position_primitives(
    *,
    qty: Decimal,
    entry_price: Decimal,
    mark_price: Decimal,
) -> None:
    q = _to_decimal("qty", qty)
    ep = _to_decimal("entry_price", entry_price)
    mp = _to_decimal("mark_price", mark_price)
    if q <= 0:
        raise ValueError("qty must be > 0")
    if ep <= 0 or mp <= 0:
        raise ValueError("entry_price and mark_price must be > 0")


def notional_value(*, mark_price: Decimal, qty: Decimal, contract_size: Decimal) -> Decimal:
    """Notional in quote currency: |qty| * mark * contract_size (qty magnitude convention: positive)."""
    mp = _to_decimal("mark_price", mark_price)
    q = _to_decimal("qty", qty)
    cs = _to_decimal("contract_size", contract_size)
    if q <= 0 or mp <= 0 or cs <= 0:
        raise ValueError("mark_price, qty, contract_size must be > 0")
    return q * mp * cs


def unrealized_pnl(
    *,
    side: FuturesSide,
    entry_price: Decimal,
    mark_price: Decimal,
    qty: Decimal,
    contract_size: Decimal,
) -> Decimal:
    """Linear v0: long (mark-entry)*q*cs; short (entry-mark)*q*cs."""
    _validate_position_primitives(qty=qty, entry_price=entry_price, mark_price=mark_price)
    cs = _to_decimal("contract_size", contract_size)
    if cs <= 0:
        raise ValueError("contract_size must be > 0")
    q = _to_decimal("qty", qty)
    ep = _to_decimal("entry_price", entry_price)
    mp = _to_decimal("mark_price", mark_price)
    unit = q * cs
    if side == FuturesSide.LONG:
        return (mp - ep) * unit
    return (ep - mp) * unit


def initial_margin_required(*, notional: Decimal, initial_margin_rate: Decimal) -> Decimal:
    n = _to_decimal("notional", notional)
    r = _to_decimal("initial_margin_rate", initial_margin_rate)
    if n < 0:
        raise ValueError("notional must be >= 0")
    if r <= 0 or r >= 1:
        raise ValueError("initial_margin_rate must be in (0, 1)")
    return n * r


def maintenance_margin_required(
    *,
    notional: Decimal,
    maintenance_margin_rate: Decimal,
) -> Decimal:
    n = _to_decimal("notional", notional)
    r = _to_decimal("maintenance_margin_rate", maintenance_margin_rate)
    if n < 0:
        raise ValueError("notional must be >= 0")
    if r <= 0 or r >= 1:
        raise ValueError("maintenance_margin_rate must be in (0, 1)")
    return n * r


def funding_payment_quote(
    *,
    side: FuturesSide,
    notional: Decimal,
    funding_rate: Decimal,
) -> Decimal:
    """
    Signed quote-currency funding payment for one accrual step.

    funding_rate > 0 means long pays short (long debited, short credited).
    """
    n = _to_decimal("notional", notional)
    fr = _to_decimal("funding_rate", funding_rate)
    if n < 0:
        raise ValueError("notional must be >= 0")
    if side == FuturesSide.LONG:
        return -fr * n
    return fr * n


def apply_funding_payment(
    position: FuturesPosition,
    *,
    notional: Decimal,
    funding_rate: Decimal,
) -> FuturesPosition:
    """Return a copy with funding_pnl adjusted by funding_payment_quote."""
    delta = funding_payment_quote(side=position.side, notional=notional, funding_rate=funding_rate)
    return FuturesPosition(
        symbol=position.symbol,
        side=position.side,
        qty=position.qty,
        entry_price=position.entry_price,
        mark_price=position.mark_price,
        realized_pnl=position.realized_pnl,
        funding_pnl=position.funding_pnl + delta,
        fees_paid=position.fees_paid,
    )


def estimate_liquidation_proximity_v0(
    *,
    equity: Decimal,
    maintenance_margin: Decimal,
    warning_buffer_fraction: Decimal = Decimal("0.05"),
) -> Tuple[LiquidationProximityV0, Optional[Decimal]]:
    """
    Conservative placeholder: compares equity to maintenance margin only.

    Returns (status, buffer_quote) where buffer = equity - maintenance_margin.
    """
    eq = _to_decimal("equity", equity)
    mm = _to_decimal("maintenance_margin", maintenance_margin)
    wf = _to_decimal("warning_buffer_fraction", warning_buffer_fraction)
    if mm <= 0:
        raise ValueError("maintenance_margin must be > 0")
    if wf < 0 or wf >= 1:
        raise ValueError("warning_buffer_fraction must be in [0, 1)")

    buffer_ = eq - mm
    if buffer_ < 0:
        return LiquidationProximityV0.BLOCKED_BELOW_MAINTENANCE, buffer_
    if buffer_ < mm * wf:
        return LiquidationProximityV0.WARNING_INSUFFICIENT_BUFFER, buffer_
    return LiquidationProximityV0.SAFE, buffer_


def realize_pnl_on_close(
    *,
    side: FuturesSide,
    entry_price: Decimal,
    close_price: Decimal,
    close_qty: Decimal,
    contract_size: Decimal,
    fee_quote: Decimal = Decimal("0"),
) -> Decimal:
    """Realized quote PnL for closing `close_qty` at `close_price`, minus fee_quote."""
    cq = _to_decimal("close_qty", close_qty)
    if cq <= 0:
        raise ValueError("close_qty must be > 0")
    gross = unrealized_pnl(
        side=side,
        entry_price=entry_price,
        mark_price=close_price,
        qty=cq,
        contract_size=contract_size,
    )
    fee = _to_decimal("fee_quote", fee_quote)
    if fee < 0:
        raise ValueError("fee_quote must be >= 0")
    return gross - fee


def reduce_position(
    position: FuturesPosition,
    *,
    contract_size: Decimal,
    close_qty: Decimal,
    close_price: Decimal,
    fee_quote: Decimal = Decimal("0"),
) -> FuturesPosition:
    """Partial or full close at close_price; updates qty and realized_pnl."""
    cq = _to_decimal("close_qty", close_qty)
    if cq <= 0:
        raise ValueError("close_qty must be > 0")
    if cq > position.qty:
        raise ValueError("close_qty must not exceed open qty")
    realized_delta = realize_pnl_on_close(
        side=position.side,
        entry_price=position.entry_price,
        close_price=close_price,
        close_qty=cq,
        contract_size=contract_size,
        fee_quote=fee_quote,
    )
    new_qty = position.qty - cq
    return FuturesPosition(
        symbol=position.symbol,
        side=position.side,
        qty=new_qty,
        entry_price=position.entry_price,
        mark_price=position.mark_price,
        realized_pnl=position.realized_pnl + realized_delta,
        funding_pnl=position.funding_pnl,
        fees_paid=position.fees_paid + _to_decimal("fee_quote", fee_quote),
    )


def apply_fee_on_notional(
    *,
    notional: Decimal,
    fee_bps: Decimal,
) -> Decimal:
    """Optional helper: fee = notional * fee_bps / 10000 (same idiom as PaperBroker)."""
    n = _to_decimal("notional", notional)
    bps = _to_decimal("fee_bps", fee_bps)
    if n < 0:
        raise ValueError("notional must be >= 0")
    if bps < 0:
        raise ValueError("fee_bps must be >= 0")
    return n * bps / Decimal("10000")
