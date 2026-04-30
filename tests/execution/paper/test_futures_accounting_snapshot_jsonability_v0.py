"""
Test-local JSON interoperability for FuturesPaperAccountingSnapshotV0.

No production serialization API — conversion rules live only here.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Mapping

from src.execution.paper.futures_accounting import (
    FuturesInstrumentSpec,
    FuturesMarginSpec,
    FuturesPaperAccountingSnapshotV0,
    FuturesPosition,
    FuturesSide,
    LiquidationProximityV0,
    build_futures_paper_accounting_snapshot_v0,
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


def _decimal_to_json_str(d: Decimal) -> str:
    """Plain-decimal string without exponent; strip redundant fractional zeros."""
    s = format(d, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s if s else "0"


def _liquidation_proximity_to_jsonable(
    liq: LiquidationProximityV0 | None,
) -> dict[str, str] | None:
    if liq is None:
        return None
    return {"status": liq.value}


def _futures_snapshot_v0_to_jsonable(
    snap: FuturesPaperAccountingSnapshotV0,
) -> dict[str, Any]:
    """Test-local mapping: JSON-serializable primitives only."""
    return {
        "schema_version": snap.schema_version,
        "symbol": snap.symbol,
        "side": snap.side.value,
        "quantity": _decimal_to_json_str(snap.quantity),
        "entry_price": _decimal_to_json_str(snap.entry_price),
        "mark_price": _decimal_to_json_str(snap.mark_price),
        "notional": _decimal_to_json_str(snap.notional),
        "initial_margin_required": _decimal_to_json_str(snap.initial_margin_required),
        "maintenance_margin_required": _decimal_to_json_str(snap.maintenance_margin_required),
        "unrealized_pnl": _decimal_to_json_str(snap.unrealized_pnl),
        "realized_pnl": _decimal_to_json_str(snap.realized_pnl),
        "fees_paid": _decimal_to_json_str(snap.fees_paid),
        "funding_paid": _decimal_to_json_str(snap.funding_paid),
        "liquidation_proximity": _liquidation_proximity_to_jsonable(snap.liquidation_proximity),
    }


def test_long_snapshot_jsonable_gold_equity_none() -> None:
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
    payload = _futures_snapshot_v0_to_jsonable(snap)
    expected: Mapping[str, Any] = {
        "schema_version": "futures_paper_accounting/snapshot/v0",
        "symbol": "PF_XBTUSD",
        "side": "long",
        "quantity": "2",
        "entry_price": "100",
        "mark_price": "110",
        "notional": "220",
        "initial_margin_required": "22",
        "maintenance_margin_required": "11",
        "unrealized_pnl": "20",
        "realized_pnl": "0",
        "fees_paid": "0",
        "funding_paid": "0",
        "liquidation_proximity": None,
    }
    assert payload == dict(expected)
    dumped = json.dumps(payload, sort_keys=True)
    assert dumped
    assert json.loads(dumped) == payload


def test_equity_none_serializes_liquidation_proximity_null() -> None:
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
    payload = _futures_snapshot_v0_to_jsonable(snap)
    assert payload["liquidation_proximity"] is None
    assert "null" in json.dumps(payload)


def test_json_dumps_with_liquidation_proximity_nested_dict() -> None:
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
    payload = _futures_snapshot_v0_to_jsonable(snap)
    assert payload["liquidation_proximity"] == {"status": "safe"}
    dumped = json.dumps(payload, sort_keys=True)
    assert json.loads(dumped)["liquidation_proximity"] == {"status": "safe"}
