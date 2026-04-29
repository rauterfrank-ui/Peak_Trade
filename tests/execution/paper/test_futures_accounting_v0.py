"""Tests for futures paper accounting v0 (pure, offline)."""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest

from src.execution.paper.futures_accounting import (
    FuturesInstrumentSpec,
    FuturesMarginSpec,
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
    validate_futures_accounting_inputs,
)

_MODULE_PATH = (
    Path(__file__).resolve().parents[3] / "src" / "execution" / "paper" / "futures_accounting.py"
)


def _spec() -> tuple[FuturesInstrumentSpec, FuturesMarginSpec]:
    inst = FuturesInstrumentSpec(
        symbol="PF_XBTUSD",
        contract_size=Decimal("1"),
        tick_size=Decimal("0.5"),
        min_qty=Decimal("0.001"),
        quote_currency="USD",
    )
    margin = FuturesMarginSpec(
        initial_margin_rate=Decimal("0.1"),
        maintenance_margin_rate=Decimal("0.05"),
        max_leverage=Decimal("10"),
    )
    return inst, margin


def test_unrealized_long_positive_when_mark_above_entry() -> None:
    pnl = unrealized_pnl(
        side=FuturesSide.LONG,
        entry_price=Decimal("100"),
        mark_price=Decimal("110"),
        qty=Decimal("2"),
        contract_size=Decimal("1"),
    )
    assert pnl == Decimal("20")


def test_unrealized_long_negative_when_mark_below_entry() -> None:
    pnl = unrealized_pnl(
        side=FuturesSide.LONG,
        entry_price=Decimal("100"),
        mark_price=Decimal("90"),
        qty=Decimal("1"),
        contract_size=Decimal("1"),
    )
    assert pnl == Decimal("-10")


def test_unrealized_short_positive_when_mark_below_entry() -> None:
    pnl = unrealized_pnl(
        side=FuturesSide.SHORT,
        entry_price=Decimal("100"),
        mark_price=Decimal("90"),
        qty=Decimal("2"),
        contract_size=Decimal("1"),
    )
    assert pnl == Decimal("20")


def test_unrealized_short_negative_when_mark_above_entry() -> None:
    pnl = unrealized_pnl(
        side=FuturesSide.SHORT,
        entry_price=Decimal("100"),
        mark_price=Decimal("110"),
        qty=Decimal("1"),
        contract_size=Decimal("1"),
    )
    assert pnl == Decimal("-10")


def test_notional_scales_with_contract_size() -> None:
    n = notional_value(mark_price=Decimal("50"), qty=Decimal("4"), contract_size=Decimal("10"))
    assert n == Decimal("2000")


def test_initial_margin_deterministic() -> None:
    im = initial_margin_required(notional=Decimal("1000"), initial_margin_rate=Decimal("0.1"))
    assert im == Decimal("100")


def test_maintenance_margin_deterministic() -> None:
    mm = maintenance_margin_required(
        notional=Decimal("800"), maintenance_margin_rate=Decimal("0.05")
    )
    assert mm == Decimal("40")


def test_funding_side_aware() -> None:
    n = Decimal("10000")
    rate = Decimal("0.0001")
    long_pay = funding_payment_quote(side=FuturesSide.LONG, notional=n, funding_rate=rate)
    short_pay = funding_payment_quote(side=FuturesSide.SHORT, notional=n, funding_rate=rate)
    assert long_pay == -rate * n
    assert short_pay == rate * n
    pos = FuturesPosition(
        symbol="PF",
        side=FuturesSide.LONG,
        qty=Decimal("1"),
        entry_price=Decimal("100"),
        mark_price=Decimal("100"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    after = apply_funding_payment(pos, notional=n, funding_rate=rate)
    assert after.funding_pnl == long_pay


def test_liquidation_proximity_placeholder() -> None:
    st, buf = estimate_liquidation_proximity_v0(
        equity=Decimal("100"),
        maintenance_margin=Decimal("100"),
        warning_buffer_fraction=Decimal("0.05"),
    )
    assert st == LiquidationProximityV0.WARNING_INSUFFICIENT_BUFFER
    assert buf == Decimal("0")

    st2, _ = estimate_liquidation_proximity_v0(
        equity=Decimal("50"),
        maintenance_margin=Decimal("100"),
    )
    assert st2 == LiquidationProximityV0.BLOCKED_BELOW_MAINTENANCE

    st3, _ = estimate_liquidation_proximity_v0(
        equity=Decimal("200"),
        maintenance_margin=Decimal("100"),
    )
    assert st3 == LiquidationProximityV0.SAFE


def test_invalid_inputs_fail_closed() -> None:
    with pytest.raises(ValueError):
        notional_value(mark_price=Decimal("-1"), qty=Decimal("1"), contract_size=Decimal("1"))
    with pytest.raises(ValueError):
        unrealized_pnl(
            side=FuturesSide.LONG,
            entry_price=Decimal("0"),
            mark_price=Decimal("10"),
            qty=Decimal("1"),
            contract_size=Decimal("1"),
        )
    inst, margin = _spec()
    bad_margin = FuturesMarginSpec(
        initial_margin_rate=Decimal("0.05"),
        maintenance_margin_rate=Decimal("0.04"),
        max_leverage=Decimal("10"),
    )
    with pytest.raises(ValueError):
        validate_futures_accounting_inputs(instrument=inst, margin=bad_margin)
    bad_inst = FuturesInstrumentSpec(
        symbol="",
        contract_size=Decimal("1"),
        tick_size=Decimal("1"),
        min_qty=Decimal("1"),
        quote_currency="USD",
    )
    with pytest.raises(ValueError):
        validate_futures_accounting_inputs(instrument=bad_inst, margin=margin)


def test_reduce_position_realizes_pnl() -> None:
    pos = FuturesPosition(
        symbol="PF",
        side=FuturesSide.LONG,
        qty=Decimal("2"),
        entry_price=Decimal("100"),
        mark_price=Decimal("110"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    new_p = reduce_position(
        pos,
        contract_size=Decimal("1"),
        close_qty=Decimal("1"),
        close_price=Decimal("120"),
        fee_quote=Decimal("1"),
    )
    assert new_p.qty == Decimal("1")
    assert new_p.realized_pnl == Decimal("19")
    assert new_p.fees_paid == Decimal("1")


def test_no_forbidden_imports_in_module() -> None:
    text = _MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(text)
    banned = ("master_v2", "live", "ccxt", "requests")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base = (alias.name or "").split(".")[0]
                assert base not in banned, alias.name
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None
            mod = node.module
            for b in banned:
                assert b not in mod, mod


def test_apply_fee_on_notional_matches_bps_idiom() -> None:
    fee = apply_fee_on_notional(notional=Decimal("10000"), fee_bps=Decimal("10"))
    assert fee == Decimal("10")
