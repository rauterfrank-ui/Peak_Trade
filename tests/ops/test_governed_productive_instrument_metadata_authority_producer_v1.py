"""Governed instrument metadata producer — fail-closed OKX row binding."""

from __future__ import annotations

from decimal import Decimal

from src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1 import (
    REASON_FIELD_MISSING,
    REASON_INST_ID_MISMATCH,
    produce_current_productive_instrument_quantity_constraints_from_okx_row_v1,
)

INST = "inst-eth-usdt-perp"


def _row(**overrides: str) -> dict[str, object]:
    base = {
        "instId": INST,
        "instType": "SWAP",
        "state": "live",
        "ctVal": "0.01",
        "ctValCcy": "ETH",
        "lotSz": "1",
        "minSz": "1",
        "tickSz": "0.01",
    }
    base.update(overrides)
    return {"code": "0", "data": [base]}


def test_produce_success() -> None:
    out = produce_current_productive_instrument_quantity_constraints_from_okx_row_v1(
        venue_native_id=INST,
        instruments_payload=_row(),
        observed_at_as_of="2026-09-25T00:00:00Z",
        bound_instrument_id=INST,
    )
    assert out.produced is True
    assert out.constraints is not None
    assert out.constraints.contract_multiplier == Decimal("0.01")
    assert out.constraints.lot_size == Decimal("1")
    assert out.constraints.instrument_metadata_version


def test_inst_id_mismatch_fail_closed() -> None:
    out = produce_current_productive_instrument_quantity_constraints_from_okx_row_v1(
        venue_native_id="other-id",
        instruments_payload=_row(),
        observed_at_as_of="2026-09-25T00:00:00Z",
    )
    assert out.produced is False
    assert REASON_INST_ID_MISMATCH in out.reason_codes


def test_missing_ctval_fail_closed() -> None:
    out = produce_current_productive_instrument_quantity_constraints_from_okx_row_v1(
        venue_native_id=INST,
        instruments_payload=_row(ctVal=""),
        observed_at_as_of="2026-09-25T00:00:00Z",
    )
    assert out.produced is False
    assert any(REASON_FIELD_MISSING in code for code in out.reason_codes)


def test_observed_at_required() -> None:
    out = produce_current_productive_instrument_quantity_constraints_from_okx_row_v1(
        venue_native_id=INST,
        instruments_payload=_row(),
        observed_at_as_of="",
    )
    assert out.produced is False


def test_no_silent_defaults_on_empty_payload() -> None:
    out = produce_current_productive_instrument_quantity_constraints_from_okx_row_v1(
        venue_native_id=INST,
        instruments_payload={"code": "0", "data": []},
        observed_at_as_of="2026-09-25T00:00:00Z",
    )
    assert out.produced is False
