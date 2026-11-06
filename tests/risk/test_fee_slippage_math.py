"""Deterministic fee and slippage math tests (Phase B)."""

from __future__ import annotations

from decimal import Decimal

import pytest


def fee_maker_bps(notional: Decimal, maker_bps: int) -> Decimal:
    """Deterministic maker fee: notional * maker_bps / 10000."""
    return notional * Decimal(maker_bps) / Decimal(10000)


def fee_taker_bps(notional: Decimal, taker_bps: int) -> Decimal:
    """Deterministic taker fee: notional * taker_bps / 10000."""
    return notional * Decimal(taker_bps) / Decimal(10000)


def slippage_adjustment(price: Decimal, bps: int, side: str) -> Decimal:
    """BUY: price * (1 + bps/10000), SELL: price * (1 - bps/10000)."""
    factor = Decimal(bps) / Decimal(10000)
    if side.upper() == "BUY":
        return price * (Decimal(1) + factor)
    return price * (Decimal(1) - factor)


def test_fee_maker_exact() -> None:
    """Maker fee at 10 bps on 10000 notional = 10."""
    assert fee_maker_bps(Decimal("10000"), 10) == Decimal("10")


def test_fee_taker_exact() -> None:
    """Taker fee at 15 bps on 10000 notional = 15."""
    assert fee_taker_bps(Decimal("10000"), 15) == Decimal("15")


def test_fee_deterministic() -> None:
    """Same inputs -> same output."""
    n = Decimal("12345.67")
    bps = 12
    r1 = fee_maker_bps(n, bps)
    r2 = fee_maker_bps(n, bps)
    assert r1 == r2


def test_slippage_buy_increases_price() -> None:
    """BUY with 5 bps slippage: pay more."""
    price = Decimal("50000")
    filled = slippage_adjustment(price, 5, "BUY")
    assert filled > price
    assert filled == price * Decimal("1.0005")


def test_slippage_sell_decreases_price() -> None:
    """SELL with 5 bps slippage: receive less."""
    price = Decimal("50000")
    filled = slippage_adjustment(price, 5, "SELL")
    assert filled < price
    assert filled == price * Decimal("0.9995")


def test_slippage_deterministic() -> None:
    """Same inputs -> same output."""
    p = Decimal("50000")
    bps = 5
    r1 = slippage_adjustment(p, bps, "BUY")
    r2 = slippage_adjustment(p, bps, "BUY")
    assert r1 == r2
