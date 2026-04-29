"""Table-driven invariant tests for futures paper accounting v0 (pure kernel).

Algebraic/accounting properties only — no runtime wiring, no engine integration.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.execution.paper.futures_accounting import (
    FuturesPosition,
    FuturesSide,
    LiquidationProximityV0,
    apply_fee_on_notional,
    apply_funding_payment,
    estimate_liquidation_proximity_v0,
    funding_payment_quote,
    initial_margin_required,
    maintenance_margin_required,
    notional_value,
    reduce_position,
    unrealized_pnl,
)

_PROXIMITY_RANK = {
    LiquidationProximityV0.BLOCKED_BELOW_MAINTENANCE: 0,
    LiquidationProximityV0.WARNING_INSUFFICIENT_BUFFER: 1,
    LiquidationProximityV0.SAFE: 2,
}


def _rank_proximity(st: LiquidationProximityV0) -> int:
    return _PROXIMITY_RANK[st]


@pytest.mark.parametrize(
    "mark_lo,mark_hi,qty,cs",
    [
        (Decimal("100"), Decimal("101"), Decimal("2"), Decimal("0.5")),
        (Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4")),
        (Decimal("0.01"), Decimal("0.02"), Decimal("100"), Decimal("1")),
    ],
)
def test_notional_monotonic_in_mark_price(
    mark_lo: Decimal, mark_hi: Decimal, qty: Decimal, cs: Decimal
) -> None:
    n_lo = notional_value(mark_price=mark_lo, qty=qty, contract_size=cs)
    n_hi = notional_value(mark_price=mark_hi, qty=qty, contract_size=cs)
    assert n_lo < n_hi
    assert n_hi - n_lo == qty * cs * (mark_hi - mark_lo)


@pytest.mark.parametrize(
    "mark,qty,cs",
    [
        (Decimal("50"), Decimal("1"), Decimal("10")),
        (Decimal("200"), Decimal("0.25"), Decimal("4")),
    ],
)
def test_notional_linear_in_qty(mark: Decimal, qty: Decimal, cs: Decimal) -> None:
    base = notional_value(mark_price=mark, qty=qty, contract_size=cs)
    doubled = notional_value(mark_price=mark, qty=qty * 2, contract_size=cs)
    assert doubled == base * 2


@pytest.mark.parametrize(
    "entry,mark,qty,cs",
    [
        (Decimal("100"), Decimal("105"), Decimal("2"), Decimal("1")),
        (Decimal("50"), Decimal("40"), Decimal("1"), Decimal("2")),
    ],
)
def test_unrealized_long_short_antisymmetry(
    entry: Decimal, mark: Decimal, qty: Decimal, cs: Decimal
) -> None:
    long_p = unrealized_pnl(
        side=FuturesSide.LONG,
        entry_price=entry,
        mark_price=mark,
        qty=qty,
        contract_size=cs,
    )
    short_p = unrealized_pnl(
        side=FuturesSide.SHORT,
        entry_price=entry,
        mark_price=mark,
        qty=qty,
        contract_size=cs,
    )
    assert long_p == -short_p


@pytest.mark.parametrize(
    "mark_lo,mark_hi",
    [(Decimal("90"), Decimal("110")), (Decimal("10"), Decimal("10.001"))],
)
def test_long_unrealized_increases_with_mark(mark_lo: Decimal, mark_hi: Decimal) -> None:
    entry = Decimal("100")
    qty = Decimal("3")
    cs = Decimal("1")
    p_lo = unrealized_pnl(
        side=FuturesSide.LONG,
        entry_price=entry,
        mark_price=mark_lo,
        qty=qty,
        contract_size=cs,
    )
    p_hi = unrealized_pnl(
        side=FuturesSide.LONG,
        entry_price=entry,
        mark_price=mark_hi,
        qty=qty,
        contract_size=cs,
    )
    assert p_lo < p_hi


@pytest.mark.parametrize(
    "mark_lo,mark_hi",
    [(Decimal("90"), Decimal("110")), (Decimal("10"), Decimal("10.001"))],
)
def test_short_unrealized_decreases_with_mark(mark_lo: Decimal, mark_hi: Decimal) -> None:
    entry = Decimal("100")
    qty = Decimal("3")
    cs = Decimal("1")
    p_lo = unrealized_pnl(
        side=FuturesSide.SHORT,
        entry_price=entry,
        mark_price=mark_lo,
        qty=qty,
        contract_size=cs,
    )
    p_hi = unrealized_pnl(
        side=FuturesSide.SHORT,
        entry_price=entry,
        mark_price=mark_hi,
        qty=qty,
        contract_size=cs,
    )
    assert p_hi < p_lo


@pytest.mark.parametrize(
    "n_lo,n_hi,imr,mmr",
    [
        (Decimal("1000"), Decimal("5000"), Decimal("0.1"), Decimal("0.05")),
        (Decimal("1"), Decimal("100"), Decimal("0.2"), Decimal("0.1")),
    ],
)
def test_margin_increases_with_notional_maintenance_le_initial(
    n_lo: Decimal, n_hi: Decimal, imr: Decimal, mmr: Decimal
) -> None:
    im_lo = initial_margin_required(notional=n_lo, initial_margin_rate=imr)
    im_hi = initial_margin_required(notional=n_hi, initial_margin_rate=imr)
    mm_lo = maintenance_margin_required(notional=n_lo, maintenance_margin_rate=mmr)
    mm_hi = maintenance_margin_required(notional=n_hi, maintenance_margin_rate=mmr)
    assert im_lo < im_hi
    assert mm_lo < mm_hi
    assert mm_lo <= im_lo
    assert mm_hi <= im_hi


@pytest.mark.parametrize(
    "notional,bps_a,bps_b",
    [
        (Decimal("10000"), Decimal("1"), Decimal("5")),
        (Decimal("250"), Decimal("0"), Decimal("10")),
    ],
)
def test_fee_monotonic_in_bps_zero_returns_zero(
    notional: Decimal, bps_a: Decimal, bps_b: Decimal
) -> None:
    assert apply_fee_on_notional(notional=notional, fee_bps=Decimal("0")) == Decimal("0")
    f_a = apply_fee_on_notional(notional=notional, fee_bps=bps_a)
    f_b = apply_fee_on_notional(notional=notional, fee_bps=bps_b)
    if bps_a < bps_b:
        assert f_a < f_b
    elif bps_a == bps_b:
        assert f_a == f_b


@pytest.mark.parametrize("notional", [Decimal("1000"), Decimal("3.5")])
@pytest.mark.parametrize("rate_pos", [Decimal("0.0001"), Decimal("0.02")])
def test_funding_sign_opposes_rate_sign_for_long(notional: Decimal, rate_pos: Decimal) -> None:
    pay_pos = funding_payment_quote(side=FuturesSide.LONG, notional=notional, funding_rate=rate_pos)
    pay_neg = funding_payment_quote(
        side=FuturesSide.LONG, notional=notional, funding_rate=-rate_pos
    )
    assert pay_neg == -pay_pos
    assert pay_pos == -rate_pos * notional


@pytest.mark.parametrize("notional", [Decimal("8000"), Decimal("12")])
@pytest.mark.parametrize("rate", [Decimal("0.0003"), Decimal("-0.01")])
def test_funding_long_short_opposite_sign(notional: Decimal, rate: Decimal) -> None:
    long_pay = funding_payment_quote(side=FuturesSide.LONG, notional=notional, funding_rate=rate)
    short_pay = funding_payment_quote(side=FuturesSide.SHORT, notional=notional, funding_rate=rate)
    assert long_pay == -short_pay


@pytest.mark.parametrize("rate", [Decimal("0.0002"), Decimal("-0.0005")])
def test_apply_funding_payment_accumulates_linearly(rate: Decimal) -> None:
    pos = FuturesPosition(
        symbol="X",
        side=FuturesSide.LONG,
        qty=Decimal("1"),
        entry_price=Decimal("1"),
        mark_price=Decimal("1"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    n = Decimal("5000")
    once = apply_funding_payment(pos, notional=n, funding_rate=rate)
    twice = apply_funding_payment(once, notional=n, funding_rate=rate)
    d = funding_payment_quote(side=FuturesSide.LONG, notional=n, funding_rate=rate)
    assert once.funding_pnl == d
    assert twice.funding_pnl == d * 2


def test_liquidation_proximity_non_decreasing_in_equity() -> None:
    mm = Decimal("100")
    wf = Decimal("0.05")
    equities = [
        Decimal("90"),
        Decimal("99.99"),
        Decimal("100"),
        Decimal("104.99"),
        Decimal("105"),
        Decimal("500"),
    ]
    ranks = []
    for eq in equities:
        st, _ = estimate_liquidation_proximity_v0(
            equity=eq, maintenance_margin=mm, warning_buffer_fraction=wf
        )
        ranks.append(_rank_proximity(st))
    assert ranks == sorted(ranks)


def test_reduce_position_split_closes_match_single_close_total_realized() -> None:
    close_price = Decimal("118")
    fee_each = Decimal("0.5")
    fee_total = Decimal("1")
    pos = FuturesPosition(
        symbol="P",
        side=FuturesSide.LONG,
        qty=Decimal("2"),
        entry_price=Decimal("100"),
        mark_price=Decimal("110"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    via_split = reduce_position(
        reduce_position(
            pos,
            contract_size=Decimal("1"),
            close_qty=Decimal("1"),
            close_price=close_price,
            fee_quote=fee_each,
        ),
        contract_size=Decimal("1"),
        close_qty=Decimal("1"),
        close_price=close_price,
        fee_quote=fee_each,
    )
    via_full = reduce_position(
        pos,
        contract_size=Decimal("1"),
        close_qty=Decimal("2"),
        close_price=close_price,
        fee_quote=fee_total,
    )
    assert via_split.realized_pnl == via_full.realized_pnl
    assert via_split.fees_paid == via_full.fees_paid
    assert via_split.qty == via_full.qty == Decimal("0")
