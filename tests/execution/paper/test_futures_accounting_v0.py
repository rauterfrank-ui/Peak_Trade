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
    realize_pnl_on_close,
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


def test_reduce_position_full_close_zero_qty() -> None:
    pos = FuturesPosition(
        symbol="PF",
        side=FuturesSide.LONG,
        qty=Decimal("2"),
        entry_price=Decimal("100"),
        mark_price=Decimal("110"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    closed = reduce_position(
        pos,
        contract_size=Decimal("1"),
        close_qty=Decimal("2"),
        close_price=Decimal("120"),
        fee_quote=Decimal("2"),
    )
    assert closed.qty == Decimal("0")
    assert closed.realized_pnl == Decimal("38")
    assert closed.fees_paid == Decimal("2")
    expected_realized = realize_pnl_on_close(
        side=FuturesSide.LONG,
        entry_price=Decimal("100"),
        close_price=Decimal("120"),
        close_qty=Decimal("2"),
        contract_size=Decimal("1"),
        fee_quote=Decimal("2"),
    )
    assert closed.realized_pnl == expected_realized


def test_reduce_position_rejects_over_reduction() -> None:
    pos = FuturesPosition(
        symbol="PF",
        side=FuturesSide.LONG,
        qty=Decimal("1"),
        entry_price=Decimal("100"),
        mark_price=Decimal("100"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    with pytest.raises(ValueError, match="must not exceed"):
        reduce_position(
            pos,
            contract_size=Decimal("1"),
            close_qty=Decimal("1.1"),
            close_price=Decimal("100"),
        )


def test_reduce_position_rejects_non_positive_close_qty() -> None:
    pos = FuturesPosition(
        symbol="PF",
        side=FuturesSide.SHORT,
        qty=Decimal("1"),
        entry_price=Decimal("100"),
        mark_price=Decimal("100"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    with pytest.raises(ValueError, match="close_qty must be > 0"):
        reduce_position(
            pos,
            contract_size=Decimal("1"),
            close_qty=Decimal("0"),
            close_price=Decimal("100"),
        )
    with pytest.raises(ValueError, match="close_qty must be > 0"):
        reduce_position(
            pos,
            contract_size=Decimal("1"),
            close_qty=Decimal("-1"),
            close_price=Decimal("100"),
        )


def test_partial_reduce_preserves_identity_fields() -> None:
    pos = FuturesPosition(
        symbol="SYM",
        side=FuturesSide.SHORT,
        qty=Decimal("3"),
        entry_price=Decimal("50"),
        mark_price=Decimal("48"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    new_p = reduce_position(
        pos,
        contract_size=Decimal("2"),
        close_qty=Decimal("1"),
        close_price=Decimal("49"),
        fee_quote=Decimal("0"),
    )
    assert new_p.symbol == "SYM"
    assert new_p.side is FuturesSide.SHORT
    assert new_p.entry_price == Decimal("50")
    assert new_p.mark_price == Decimal("48")
    assert new_p.qty == Decimal("2")
    assert new_p.realized_pnl == Decimal("2")
    assert new_p.funding_pnl == Decimal("0")


def test_apply_funding_payment_short_opposite_sign_from_long() -> None:
    n = Decimal("5000")
    rate = Decimal("0.0002")
    long_delta = funding_payment_quote(side=FuturesSide.LONG, notional=n, funding_rate=rate)
    short_delta = funding_payment_quote(side=FuturesSide.SHORT, notional=n, funding_rate=rate)
    assert long_delta == -short_delta
    assert long_delta < Decimal("0")
    assert short_delta > Decimal("0")
    pos_s = FuturesPosition(
        symbol="PF",
        side=FuturesSide.SHORT,
        qty=Decimal("1"),
        entry_price=Decimal("100"),
        mark_price=Decimal("100"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    after = apply_funding_payment(pos_s, notional=n, funding_rate=rate)
    assert after.funding_pnl == short_delta


def test_liquidation_proximity_boundary_exact_safe_threshold() -> None:
    mm = Decimal("100")
    wf = Decimal("0.05")
    st, buf = estimate_liquidation_proximity_v0(
        equity=Decimal("105"), maintenance_margin=mm, warning_buffer_fraction=wf
    )
    assert st is LiquidationProximityV0.SAFE
    assert buf == Decimal("5")

    st_warn, buf_warn = estimate_liquidation_proximity_v0(
        equity=Decimal("104.99"), maintenance_margin=mm, warning_buffer_fraction=wf
    )
    assert st_warn is LiquidationProximityV0.WARNING_INSUFFICIENT_BUFFER
    assert buf_warn == Decimal("4.99")


def test_liquidation_proximity_blocked_strictly_below_maintenance() -> None:
    st, buf = estimate_liquidation_proximity_v0(
        equity=Decimal("99.99"),
        maintenance_margin=Decimal("100"),
    )
    assert st is LiquidationProximityV0.BLOCKED_BELOW_MAINTENANCE
    assert buf == Decimal("-0.01")


def test_liquidation_proximity_rejects_invalid_warning_fraction() -> None:
    with pytest.raises(ValueError, match="warning_buffer_fraction"):
        estimate_liquidation_proximity_v0(
            equity=Decimal("100"),
            maintenance_margin=Decimal("50"),
            warning_buffer_fraction=Decimal("1"),
        )


def test_validate_rejects_invalid_instrument_fields() -> None:
    inst, margin = _spec()
    for bad in (
        FuturesInstrumentSpec("X", Decimal("0"), Decimal("1"), Decimal("1"), "USD"),
        FuturesInstrumentSpec("X", Decimal("-1"), Decimal("1"), Decimal("1"), "USD"),
        FuturesInstrumentSpec("X", Decimal("1"), Decimal("0"), Decimal("1"), "USD"),
        FuturesInstrumentSpec("X", Decimal("1"), Decimal("1"), Decimal("0"), "USD"),
    ):
        with pytest.raises(ValueError):
            validate_futures_accounting_inputs(instrument=bad, margin=margin)


def test_validate_rejects_invalid_margin_fields() -> None:
    inst, good = _spec()
    with pytest.raises(ValueError):
        validate_futures_accounting_inputs(
            instrument=inst,
            margin=FuturesMarginSpec(
                initial_margin_rate=Decimal("0"),
                maintenance_margin_rate=Decimal("0.05"),
                max_leverage=Decimal("10"),
            ),
        )
    with pytest.raises(ValueError):
        validate_futures_accounting_inputs(
            instrument=inst,
            margin=FuturesMarginSpec(
                initial_margin_rate=Decimal("1"),
                maintenance_margin_rate=Decimal("0.05"),
                max_leverage=Decimal("10"),
            ),
        )
    with pytest.raises(ValueError):
        validate_futures_accounting_inputs(
            instrument=inst,
            margin=FuturesMarginSpec(
                initial_margin_rate=Decimal("0.1"),
                maintenance_margin_rate=Decimal("0"),
                max_leverage=Decimal("10"),
            ),
        )
    with pytest.raises(ValueError):
        validate_futures_accounting_inputs(
            instrument=inst,
            margin=FuturesMarginSpec(
                initial_margin_rate=Decimal("0.1"),
                maintenance_margin_rate=Decimal("1"),
                max_leverage=Decimal("10"),
            ),
        )
    with pytest.raises(ValueError, match="must not exceed"):
        validate_futures_accounting_inputs(
            instrument=inst,
            margin=FuturesMarginSpec(
                initial_margin_rate=Decimal("0.1"),
                maintenance_margin_rate=Decimal("0.15"),
                max_leverage=Decimal("10"),
            ),
        )
    with pytest.raises(ValueError, match="max_leverage must be"):
        validate_futures_accounting_inputs(
            instrument=inst,
            margin=FuturesMarginSpec(
                initial_margin_rate=Decimal("0.1"),
                maintenance_margin_rate=Decimal("0.05"),
                max_leverage=Decimal("0.5"),
            ),
        )
    with pytest.raises(ValueError, match="inconsistent margin"):
        validate_futures_accounting_inputs(
            instrument=inst,
            margin=FuturesMarginSpec(
                initial_margin_rate=Decimal("0.05"),
                maintenance_margin_rate=Decimal("0.04"),
                max_leverage=Decimal("10"),
            ),
        )


def test_validate_allows_maintenance_equal_initial() -> None:
    inst, _ = _spec()
    validate_futures_accounting_inputs(
        instrument=inst,
        margin=FuturesMarginSpec(
            initial_margin_rate=Decimal("0.1"),
            maintenance_margin_rate=Decimal("0.1"),
            max_leverage=Decimal("10"),
        ),
    )


def test_validate_rejects_negative_wallet_equity() -> None:
    inst, margin = _spec()
    with pytest.raises(ValueError, match="wallet_equity"):
        validate_futures_accounting_inputs(
            instrument=inst, margin=margin, wallet_equity=Decimal("-0.01")
        )


def test_apply_fee_on_notional_zero_and_positive_bps() -> None:
    assert apply_fee_on_notional(notional=Decimal("1000"), fee_bps=Decimal("0")) == Decimal("0")
    assert apply_fee_on_notional(notional=Decimal("10000"), fee_bps=Decimal("7")) == Decimal("7")


def test_apply_fee_on_notional_rejects_negative_bps() -> None:
    with pytest.raises(ValueError, match="fee_bps"):
        apply_fee_on_notional(notional=Decimal("100"), fee_bps=Decimal("-1"))


def test_realize_pnl_on_close_decimal_exactness_no_floats() -> None:
    out = realize_pnl_on_close(
        side=FuturesSide.LONG,
        entry_price=Decimal("0.1"),
        close_price=Decimal("0.3"),
        close_qty=Decimal("3"),
        contract_size=Decimal("0.25"),
        fee_quote=Decimal("0.01"),
    )
    assert out == Decimal("0.14")


def test_reduce_position_accumulates_fees_across_partial_closes() -> None:
    pos = FuturesPosition(
        symbol="PF",
        side=FuturesSide.LONG,
        qty=Decimal("2"),
        entry_price=Decimal("10"),
        mark_price=Decimal("10"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    step1 = reduce_position(
        pos,
        contract_size=Decimal("1"),
        close_qty=Decimal("1"),
        close_price=Decimal("12"),
        fee_quote=Decimal("0.5"),
    )
    step2 = reduce_position(
        step1,
        contract_size=Decimal("1"),
        close_qty=Decimal("1"),
        close_price=Decimal("11"),
        fee_quote=Decimal("0.25"),
    )
    assert step2.qty == Decimal("0")
    assert step2.fees_paid == Decimal("0.75")
    assert step2.realized_pnl == Decimal("2.25")
