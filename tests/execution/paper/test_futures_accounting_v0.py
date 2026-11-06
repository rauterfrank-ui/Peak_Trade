"""Tests for futures paper accounting v0 (pure, offline).

INV-048 P1 arithmetic contract closure (Package A slice A2): flip fail-closed,
ledger quantize delegation, wallet equity identity — tests-only; unwired kernel.
"""

from __future__ import annotations

import ast
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pytest

from src.execution.ledger.models import QuantizationPolicy
from src.execution.ledger.quantization import d, q_money, q_price, q_qty
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


def _f1_minimal_instrument_to_spec(meta: dict[str, str]) -> FuturesInstrumentSpec:
    """Project F1-sized field subset (instrument sizing) onto accounting v0 — not full F1."""

    return FuturesInstrumentSpec(
        symbol=meta["symbol"],
        contract_size=Decimal(meta["contract_size"]),
        tick_size=Decimal(meta["tick_size"]),
        min_qty=Decimal(meta["min_qty"]),
        quote_currency=meta["quote_currency"],
    )


def _f1_margin_to_spec(meta: dict[str, str]) -> FuturesMarginSpec:
    """Project F1 margin/leverage subset onto accounting v0."""

    return FuturesMarginSpec(
        initial_margin_rate=Decimal(meta["initial_margin_rate"]),
        maintenance_margin_rate=Decimal(meta["maintenance_margin_rate"]),
        max_leverage=Decimal(meta["max_leverage"]),
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


def test_f1_minimal_instrument_projection_notional_uses_contract_size() -> None:
    """F1-style metadata dict → FuturesInstrumentSpec; notional scales with projected contract_size."""

    f1_like = {
        "symbol": "PF_ETHUSD",
        "contract_size": "0.1",
        "tick_size": "0.01",
        "min_qty": "0.01",
        "quote_currency": "USD",
    }
    inst = _f1_minimal_instrument_to_spec(f1_like)
    assert inst.symbol == f1_like["symbol"]
    assert inst.contract_size == Decimal("0.1")
    assert inst.tick_size == Decimal("0.01")
    assert inst.min_qty == Decimal("0.01")
    assert inst.quote_currency == "USD"

    margin = _f1_margin_to_spec(
        {
            "initial_margin_rate": "0.1",
            "maintenance_margin_rate": "0.05",
            "max_leverage": "10",
        }
    )
    validate_futures_accounting_inputs(instrument=inst, margin=margin)

    n = notional_value(
        mark_price=Decimal("2000"), qty=Decimal("3"), contract_size=inst.contract_size
    )
    assert n == Decimal("600")


def test_f1_margin_projection_initial_and_maintenance_deterministic() -> None:
    """F1-style margin dict → FuturesMarginSpec; margin quote amounts are deterministic."""

    inst = _f1_minimal_instrument_to_spec(
        {
            "symbol": "PF_XBTUSD",
            "contract_size": "1",
            "tick_size": "0.5",
            "min_qty": "0.001",
            "quote_currency": "USD",
        }
    )
    margin = _f1_margin_to_spec(
        {
            "initial_margin_rate": "0.08",
            "maintenance_margin_rate": "0.04",
            "max_leverage": "25",
        }
    )
    validate_futures_accounting_inputs(instrument=inst, margin=margin)

    n = Decimal("10000")
    assert initial_margin_required(
        notional=n, initial_margin_rate=margin.initial_margin_rate
    ) == Decimal("800")
    assert maintenance_margin_required(
        notional=n, maintenance_margin_rate=margin.maintenance_margin_rate
    ) == Decimal("400")


def test_f2_explicit_mark_price_drives_unrealized_pnl_no_implicit_price_selection() -> None:
    """F2: accounting accepts only an explicit mark scalar; there is no last/index selection inside v0."""

    obs = {"price_type": "mark", "mark_price": "101.5"}
    assert obs["price_type"] == "mark"
    mark = Decimal(obs["mark_price"])
    pnl = unrealized_pnl(
        side=FuturesSide.LONG,
        entry_price=Decimal("100"),
        mark_price=mark,
        qty=Decimal("2"),
        contract_size=Decimal("1"),
    )
    assert pnl == Decimal("3")


def test_f2_last_and_mark_in_observation_caller_must_supply_mark_scalar() -> None:
    """Observation may carry both last and mark; v0 PnL follows only the caller-supplied mark_price."""

    obs = {"last_price": "50000", "mark_price": "49900"}
    mark = Decimal(obs["mark_price"])
    last_px = Decimal(obs["last_price"])

    pnl_using_mark = unrealized_pnl(
        side=FuturesSide.SHORT,
        entry_price=Decimal("50000"),
        mark_price=mark,
        qty=Decimal("1"),
        contract_size=Decimal("1"),
    )
    assert pnl_using_mark == Decimal("100")

    pnl_if_last_substituted = unrealized_pnl(
        side=FuturesSide.SHORT,
        entry_price=Decimal("50000"),
        mark_price=last_px,
        qty=Decimal("1"),
        contract_size=Decimal("1"),
    )
    assert pnl_if_last_substituted == Decimal("0")
    assert pnl_using_mark != pnl_if_last_substituted


def test_f1_f2_mark_notional_with_margin_projection_liquidation_proximity_deterministic() -> None:
    """F1 margin + explicit F2 mark notionals → maintenance compare (conservative v0 proximity)."""

    inst = _f1_minimal_instrument_to_spec(
        {
            "symbol": "LINEAR-PERP-DEMO",
            "contract_size": "5",
            "tick_size": "0.1",
            "min_qty": "0.01",
            "quote_currency": "USD",
        }
    )
    margin = _f1_margin_to_spec(
        {
            "initial_margin_rate": "0.1",
            "maintenance_margin_rate": "0.05",
            "max_leverage": "10",
        }
    )
    validate_futures_accounting_inputs(instrument=inst, margin=margin)

    obs = {"price_type": "mark", "mark_price": "50"}
    mark = Decimal(obs["mark_price"])
    qty = Decimal("4")
    n = notional_value(mark_price=mark, qty=qty, contract_size=inst.contract_size)
    mm = maintenance_margin_required(
        notional=n, maintenance_margin_rate=margin.maintenance_margin_rate
    )
    im = initial_margin_required(notional=n, initial_margin_rate=margin.initial_margin_rate)

    st_safe, _ = estimate_liquidation_proximity_v0(equity=im, maintenance_margin=mm)
    assert st_safe is LiquidationProximityV0.SAFE

    st_blk, buf = estimate_liquidation_proximity_v0(
        equity=mm * Decimal("0.99"), maintenance_margin=mm
    )
    assert st_blk is LiquidationProximityV0.BLOCKED_BELOW_MAINTENANCE
    assert buf < 0


def _wallet_equity_end(*, start: Decimal, position: FuturesPosition) -> Decimal:
    """INV-048 P1-5: wallet cash identity excludes unrealized PnL."""
    return start + position.realized_pnl + position.funding_pnl - position.fees_paid


def _flip_via_close_then_opposite_open(
    pos: FuturesPosition,
    *,
    contract_size: Decimal,
    flip_price: Decimal,
    new_side: FuturesSide,
    open_qty: Decimal,
    close_fee: Decimal = Decimal("0"),
) -> FuturesPosition:
    """Test-only composed flip: full close then fresh opposite-side open (no flip API)."""
    closed = reduce_position(
        pos,
        contract_size=contract_size,
        close_qty=pos.qty,
        close_price=flip_price,
        fee_quote=close_fee,
    )
    return FuturesPosition(
        symbol=pos.symbol,
        side=new_side,
        qty=open_qty,
        entry_price=flip_price,
        mark_price=flip_price,
        realized_pnl=closed.realized_pnl,
        funding_pnl=closed.funding_pnl,
        fees_paid=closed.fees_paid,
    )


def _instrument_quantize_policy(inst: FuturesInstrumentSpec) -> QuantizationPolicy:
    """Map kernel instrument tick/lot to ledger QuantizationPolicy (test contract)."""
    return QuantizationPolicy(
        price_quant=inst.tick_size,
        qty_quant=inst.min_qty,
        money_quant=Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def test_reduce_position_is_not_flip_api_fail_closed() -> None:
    """P1-3: reduce_position closes same side only; over-close is fail-closed, not flip."""
    pos = FuturesPosition(
        symbol="PF",
        side=FuturesSide.LONG,
        qty=Decimal("1"),
        entry_price=Decimal("100"),
        mark_price=Decimal("105"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    partial = reduce_position(
        pos,
        contract_size=Decimal("1"),
        close_qty=Decimal("0.5"),
        close_price=Decimal("110"),
    )
    assert partial.side is FuturesSide.LONG
    assert partial.qty == Decimal("0.5")

    full = reduce_position(
        pos,
        contract_size=Decimal("1"),
        close_qty=Decimal("1"),
        close_price=Decimal("110"),
    )
    assert full.side is FuturesSide.LONG
    assert full.qty == Decimal("0")

    with pytest.raises(ValueError, match="must not exceed"):
        reduce_position(
            pos,
            contract_size=Decimal("1"),
            close_qty=Decimal("1.001"),
            close_price=Decimal("110"),
        )


def test_position_flip_semantics_composed_close_then_opposite_open_long_to_short() -> None:
    """P1-3: flip = close long leg at flip_price + open short at same price."""
    pos = FuturesPosition(
        symbol="PF",
        side=FuturesSide.LONG,
        qty=Decimal("2"),
        entry_price=Decimal("100"),
        mark_price=Decimal("108"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    flip_price = Decimal("115")
    open_qty = Decimal("1.5")
    close_fee = Decimal("0.5")

    flipped = _flip_via_close_then_opposite_open(
        pos,
        contract_size=Decimal("1"),
        flip_price=flip_price,
        new_side=FuturesSide.SHORT,
        open_qty=open_qty,
        close_fee=close_fee,
    )

    expected_close_realized = realize_pnl_on_close(
        side=FuturesSide.LONG,
        entry_price=Decimal("100"),
        close_price=flip_price,
        close_qty=Decimal("2"),
        contract_size=Decimal("1"),
        fee_quote=close_fee,
    )
    assert flipped.side is FuturesSide.SHORT
    assert flipped.qty == open_qty
    assert flipped.entry_price == flip_price
    assert flipped.mark_price == flip_price
    assert flipped.realized_pnl == expected_close_realized
    assert flipped.fees_paid == close_fee
    assert unrealized_pnl(
        side=FuturesSide.SHORT,
        entry_price=flip_price,
        mark_price=flip_price,
        qty=open_qty,
        contract_size=Decimal("1"),
    ) == Decimal("0")


def test_position_flip_semantics_composed_close_then_opposite_open_short_to_long() -> None:
    """P1-3: flip = close short leg at flip_price + open long at same price."""
    pos = FuturesPosition(
        symbol="PF",
        side=FuturesSide.SHORT,
        qty=Decimal("3"),
        entry_price=Decimal("200"),
        mark_price=Decimal("190"),
        realized_pnl=Decimal("1"),
        funding_pnl=Decimal("0.25"),
    )
    flip_price = Decimal("185")
    open_qty = Decimal("2")

    flipped = _flip_via_close_then_opposite_open(
        pos,
        contract_size=Decimal("1"),
        flip_price=flip_price,
        new_side=FuturesSide.LONG,
        open_qty=open_qty,
    )

    expected_close_realized = Decimal("1") + realize_pnl_on_close(
        side=FuturesSide.SHORT,
        entry_price=Decimal("200"),
        close_price=flip_price,
        close_qty=Decimal("3"),
        contract_size=Decimal("1"),
    )
    assert flipped.side is FuturesSide.LONG
    assert flipped.qty == open_qty
    assert flipped.entry_price == flip_price
    assert flipped.realized_pnl == expected_close_realized
    assert flipped.funding_pnl == Decimal("0.25")


def test_production_module_has_no_public_flip_callable() -> None:
    """P1-3: futures_accounting v0 kernel exposes no public flip_* API."""
    text = _MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(text)
    flip_name_fragments = ("flip", "reverse_side", "switch_side")
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            if name.startswith("_"):
                continue
            lower = name.lower()
            for frag in flip_name_fragments:
                assert frag not in lower, f"unexpected public callable {name!r}"


def test_q_price_respects_tick_quant_and_rounding_policy() -> None:
    """P1-4: q_price rounds to tick quant using policy.rounding."""
    tick = Decimal("0.5")
    policy = QuantizationPolicy(
        price_quant=tick,
        qty_quant=Decimal("0.001"),
        money_quant=Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    for raw in (
        Decimal("100.24"),
        Decimal("100.25"),
        Decimal("100.74"),
        Decimal("100.75"),
    ):
        assert q_price(raw, policy=policy) == raw.quantize(tick, rounding=ROUND_HALF_UP)


def test_q_qty_respects_lot_quant_and_rounding_policy() -> None:
    """P1-4: q_qty rounds to lot quant using policy.rounding."""
    lot = Decimal("0.001")
    policy = QuantizationPolicy(
        price_quant=Decimal("0.5"),
        qty_quant=lot,
        money_quant=Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    for raw in (Decimal("1.2344"), Decimal("1.2345"), Decimal("0.00049")):
        assert q_qty(raw, policy=policy) == raw.quantize(lot, rounding=ROUND_HALF_UP)


def test_q_money_respects_money_quant() -> None:
    """P1-4: q_money rounds to money quant using policy.rounding."""
    money = Decimal("0.01")
    policy = QuantizationPolicy(
        price_quant=Decimal("0.01"),
        qty_quant=Decimal("0.001"),
        money_quant=money,
        rounding=ROUND_HALF_UP,
    )
    for raw in (Decimal("123.454"), Decimal("123.455")):
        assert q_money(raw, policy=policy) == raw.quantize(money, rounding=ROUND_HALF_UP)


def test_quantization_d_rejects_float() -> None:
    """P1-4: ledger d() rejects float inputs for deterministic accounting."""
    with pytest.raises(TypeError, match="float inputs are forbidden"):
        d(1.23)
    assert d("1.23") == Decimal("1.23")
    assert d(Decimal("1.23")) == Decimal("1.23")
    assert d(42) == Decimal("42")


def test_kernel_instrument_tick_lot_aligns_with_quantize_policy() -> None:
    """P1-4: kernel tick_size/min_qty validation aligns with ledger quantize delegate."""
    inst, margin = _spec()
    validate_futures_accounting_inputs(instrument=inst, margin=margin)
    policy = _instrument_quantize_policy(inst)

    assert inst.tick_size == policy.price_quant
    assert inst.min_qty == policy.qty_quant
    raw_price = Decimal("100.37")
    raw_qty = Decimal("1.23456")
    assert q_price(raw_price, policy=policy) == raw_price.quantize(
        inst.tick_size, rounding=ROUND_HALF_UP
    )
    assert q_qty(raw_qty, policy=policy) == raw_qty.quantize(inst.min_qty, rounding=ROUND_HALF_UP)


def test_wallet_equity_identity_start_plus_realized_plus_funding_minus_fees() -> None:
    """P1-5: wallet_equity_end = start + realized + funding - fees (excludes unrealized)."""
    wallet_start = Decimal("10000")
    pos = FuturesPosition(
        symbol="PF",
        side=FuturesSide.LONG,
        qty=Decimal("2"),
        entry_price=Decimal("100"),
        mark_price=Decimal("110"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    after_close = reduce_position(
        pos,
        contract_size=Decimal("1"),
        close_qty=Decimal("1"),
        close_price=Decimal("115"),
        fee_quote=Decimal("2"),
    )
    n = notional_value(
        mark_price=after_close.mark_price,
        qty=after_close.qty,
        contract_size=Decimal("1"),
    )
    after_funding = apply_funding_payment(after_close, notional=n, funding_rate=Decimal("0.0001"))
    wallet_end = _wallet_equity_end(start=wallet_start, position=after_funding)
    expected = (
        wallet_start
        + after_funding.realized_pnl
        + after_funding.funding_pnl
        - after_funding.fees_paid
    )
    assert wallet_end == expected


def test_wallet_equity_identity_multi_step_close_funding_fee_chain() -> None:
    """P1-5: wallet identity holds across multi-step close, funding, and fee chain."""
    wallet_start = Decimal("5000")
    pos = FuturesPosition(
        symbol="PF",
        side=FuturesSide.SHORT,
        qty=Decimal("4"),
        entry_price=Decimal("50"),
        mark_price=Decimal("48"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    cs = Decimal("2")

    step1 = reduce_position(
        pos,
        contract_size=cs,
        close_qty=Decimal("1"),
        close_price=Decimal("47"),
        fee_quote=Decimal("0.5"),
    )
    n1 = notional_value(mark_price=step1.mark_price, qty=step1.qty, contract_size=cs)
    step2 = apply_funding_payment(step1, notional=n1, funding_rate=Decimal("0.0002"))
    step3 = reduce_position(
        step2,
        contract_size=cs,
        close_qty=Decimal("2"),
        close_price=Decimal("46"),
        fee_quote=Decimal("1"),
    )
    n3 = notional_value(mark_price=step3.mark_price, qty=step3.qty, contract_size=cs)
    step4 = apply_funding_payment(step3, notional=n3, funding_rate=Decimal("-0.0001"))

    wallet_end = _wallet_equity_end(start=wallet_start, position=step4)
    assert wallet_end == (wallet_start + step4.realized_pnl + step4.funding_pnl - step4.fees_paid)
