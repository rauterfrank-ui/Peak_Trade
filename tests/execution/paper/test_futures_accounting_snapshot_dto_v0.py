"""Tests for FuturesPaperAccountingSnapshotV0 and pure builder (offline kernel only)."""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest

from src.execution.paper.futures_accounting import (
    FUTURES_PAPER_ACCOUNTING_SNAPSHOT_SCHEMA_V0,
    FuturesInstrumentSpec,
    FuturesMarginSpec,
    FuturesPosition,
    FuturesSide,
    LiquidationProximityV0,
    build_futures_paper_accounting_snapshot_v0,
)

_MODULE_PATH = (
    Path(__file__).resolve().parents[3] / "src" / "execution" / "paper" / "futures_accounting.py"
)


def _inst_margin() -> tuple[FuturesInstrumentSpec, FuturesMarginSpec]:
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


def test_snapshot_long_deterministic_gold() -> None:
    inst, margin = _inst_margin()
    pos = FuturesPosition(
        symbol="PF_XBTUSD",
        side=FuturesSide.LONG,
        qty=Decimal("2"),
        entry_price=Decimal("100"),
        mark_price=Decimal("100"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
        fees_paid=Decimal("0"),
    )
    snap = build_futures_paper_accounting_snapshot_v0(
        instrument=inst,
        margin=margin,
        position=pos,
        mark_price=Decimal("110"),
        equity=None,
    )
    assert snap.schema_version == FUTURES_PAPER_ACCOUNTING_SNAPSHOT_SCHEMA_V0
    assert snap.symbol == "PF_XBTUSD"
    assert snap.side == FuturesSide.LONG
    assert snap.quantity == Decimal("2")
    assert snap.entry_price == Decimal("100")
    assert snap.mark_price == Decimal("110")
    assert snap.notional == Decimal("220")
    assert snap.initial_margin_required == Decimal("22")
    assert snap.maintenance_margin_required == Decimal("11")
    assert snap.unrealized_pnl == Decimal("20")
    assert snap.realized_pnl == Decimal("0")
    assert snap.fees_paid == Decimal("0")
    assert snap.funding_paid == Decimal("0")
    assert snap.liquidation_proximity is None


def test_snapshot_short_deterministic_gold() -> None:
    inst, margin = _inst_margin()
    pos = FuturesPosition(
        symbol="PF_XBTUSD",
        side=FuturesSide.SHORT,
        qty=Decimal("1"),
        entry_price=Decimal("100"),
        mark_price=Decimal("100"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
        fees_paid=Decimal("0"),
    )
    snap = build_futures_paper_accounting_snapshot_v0(
        instrument=inst,
        margin=margin,
        position=pos,
        mark_price=Decimal("90"),
        equity=None,
    )
    assert snap.notional == Decimal("90")
    assert snap.initial_margin_required == Decimal("9")
    assert snap.maintenance_margin_required == Decimal("4.5")
    assert snap.unrealized_pnl == Decimal("10")


def test_equity_none_leaves_liquidation_proximity_none() -> None:
    inst, margin = _inst_margin()
    pos = FuturesPosition(
        symbol="PF_XBTUSD",
        side=FuturesSide.LONG,
        qty=Decimal("1"),
        entry_price=Decimal("1"),
        mark_price=Decimal("1"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    snap = build_futures_paper_accounting_snapshot_v0(
        instrument=inst,
        margin=margin,
        position=pos,
        mark_price=Decimal("1"),
        equity=None,
    )
    assert snap.liquidation_proximity is None


def test_equity_populates_liquidation_proximity() -> None:
    inst, margin = _inst_margin()
    pos = FuturesPosition(
        symbol="PF_XBTUSD",
        side=FuturesSide.LONG,
        qty=Decimal("2"),
        entry_price=Decimal("100"),
        mark_price=Decimal("100"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    snap = build_futures_paper_accounting_snapshot_v0(
        instrument=inst,
        margin=margin,
        position=pos,
        mark_price=Decimal("110"),
        equity=Decimal("200"),
    )
    assert snap.liquidation_proximity == LiquidationProximityV0.SAFE

    snap_warn = build_futures_paper_accounting_snapshot_v0(
        instrument=inst,
        margin=margin,
        position=pos,
        mark_price=Decimal("110"),
        equity=Decimal("11"),
    )
    assert snap_warn.liquidation_proximity == LiquidationProximityV0.WARNING_INSUFFICIENT_BUFFER


def test_validation_failures_propagate() -> None:
    inst, margin = _inst_margin()
    bad_inst = FuturesInstrumentSpec(
        symbol="",
        contract_size=Decimal("1"),
        tick_size=Decimal("1"),
        min_qty=Decimal("1"),
        quote_currency="USD",
    )
    pos = FuturesPosition(
        symbol="",
        side=FuturesSide.LONG,
        qty=Decimal("1"),
        entry_price=Decimal("1"),
        mark_price=Decimal("1"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    with pytest.raises(ValueError, match="instrument.symbol"):
        build_futures_paper_accounting_snapshot_v0(
            instrument=bad_inst,
            margin=margin,
            position=pos,
            mark_price=Decimal("1"),
        )

    bad_margin = FuturesMarginSpec(
        initial_margin_rate=Decimal("0.1"),
        maintenance_margin_rate=Decimal("0.11"),
        max_leverage=Decimal("10"),
    )
    pos_ok = FuturesPosition(
        symbol="PF_XBTUSD",
        side=FuturesSide.LONG,
        qty=Decimal("1"),
        entry_price=Decimal("100"),
        mark_price=Decimal("100"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    with pytest.raises(ValueError, match="maintenance_margin_rate must not exceed"):
        build_futures_paper_accounting_snapshot_v0(
            instrument=inst,
            margin=bad_margin,
            position=pos_ok,
            mark_price=Decimal("100"),
        )


def test_symbol_mismatch_raises() -> None:
    inst, margin = _inst_margin()
    pos = FuturesPosition(
        symbol="OTHER",
        side=FuturesSide.LONG,
        qty=Decimal("1"),
        entry_price=Decimal("100"),
        mark_price=Decimal("100"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("0"),
    )
    with pytest.raises(ValueError, match="position.symbol must match"):
        build_futures_paper_accounting_snapshot_v0(
            instrument=inst,
            margin=margin,
            position=pos,
            mark_price=Decimal("100"),
        )


def test_snapshot_does_not_mutate_position() -> None:
    inst, margin = _inst_margin()
    pos = FuturesPosition(
        symbol="PF_XBTUSD",
        side=FuturesSide.LONG,
        qty=Decimal("2"),
        entry_price=Decimal("100"),
        mark_price=Decimal("100"),
        realized_pnl=Decimal("3"),
        funding_pnl=Decimal("-1"),
        fees_paid=Decimal("2"),
    )
    before = (
        pos.symbol,
        pos.side,
        pos.qty,
        pos.entry_price,
        pos.mark_price,
        pos.realized_pnl,
        pos.funding_pnl,
        pos.fees_paid,
    )
    build_futures_paper_accounting_snapshot_v0(
        instrument=inst,
        margin=margin,
        position=pos,
        mark_price=Decimal("150"),
        equity=None,
    )
    after = (
        pos.symbol,
        pos.side,
        pos.qty,
        pos.entry_price,
        pos.mark_price,
        pos.realized_pnl,
        pos.funding_pnl,
        pos.fees_paid,
    )
    assert before == after


def test_futures_accounting_module_imports_remain_stdlib_only() -> None:
    allowed_roots = frozenset({"__future__", "dataclasses", "decimal", "enum", "typing"})
    text = _MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(text)
    banned_substrings = (
        "master_v2",
        "ccxt",
        "requests",
        "urllib",
        "socket",
        "paper.engine",
        "paper.broker",
        "paper.journal",
        "PaperExecutionEngine",
        "PaperBroker",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name or ""
                assert mod.split(".")[0] not in ("src", "execution"), mod
                for b in banned_substrings:
                    assert b not in mod, mod
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None
            mod = node.module
            root = mod.split(".")[0]
            assert root in allowed_roots, f"unexpected import {mod!r}"
            for b in banned_substrings:
                assert b not in mod, mod


def test_funding_paid_reflects_position_funding_pnl() -> None:
    inst, margin = _inst_margin()
    pos = FuturesPosition(
        symbol="PF_XBTUSD",
        side=FuturesSide.LONG,
        qty=Decimal("1"),
        entry_price=Decimal("50"),
        mark_price=Decimal("50"),
        realized_pnl=Decimal("0"),
        funding_pnl=Decimal("-12.5"),
        fees_paid=Decimal("0"),
    )
    snap = build_futures_paper_accounting_snapshot_v0(
        instrument=inst,
        margin=margin,
        position=pos,
        mark_price=Decimal("50"),
        equity=None,
    )
    assert snap.funding_paid == Decimal("-12.5")
