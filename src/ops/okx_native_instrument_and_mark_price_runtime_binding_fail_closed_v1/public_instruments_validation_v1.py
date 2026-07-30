"""Validate resolved venue instrument IDs against public OKX instruments inventory."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.constants_v1 import (
    ACTIVE_INSTRUMENT_STATES,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.error_classes_v1 import (
    MarketDataBindingErrorV1,
)


def _rows_for_inst_id(
    instruments_inventory: Sequence[Mapping[str, Any]],
    *,
    venue_instrument_id: str,
) -> list[Mapping[str, Any]]:
    wanted = str(venue_instrument_id).strip()
    matches: list[Mapping[str, Any]] = []
    for row in instruments_inventory:
        if not isinstance(row, Mapping):
            continue
        inst = str(row.get("instId") or "").strip()
        if inst == wanted:
            matches.append(row)
    return matches


def validate_venue_instrument_in_public_inventory_v1(
    *,
    venue_instrument_id: str,
    instruments_inventory: Sequence[Mapping[str, Any]],
    expected_inst_type: str,
) -> Mapping[str, Any]:
    """Fail-closed inventory validation for a resolved native OKX instId."""
    if not venue_instrument_id or not str(venue_instrument_id).strip():
        raise MarketDataBindingErrorV1(
            "CANONICAL_INSTRUMENT_MAPPING_MISSING", "venue_instrument_id_empty"
        )
    matches = _rows_for_inst_id(instruments_inventory, venue_instrument_id=venue_instrument_id)
    if not matches:
        raise MarketDataBindingErrorV1(
            "CANONICAL_INSTRUMENT_MAPPING_MISSING",
            f"inventory_miss:{venue_instrument_id}",
        )
    if len(matches) > 1:
        raise MarketDataBindingErrorV1(
            "CANONICAL_INSTRUMENT_MAPPING_AMBIGUOUS",
            f"matches={len(matches)}",
        )
    row = matches[0]
    inst_type = str(row.get("instType") or "").strip()
    if expected_inst_type and inst_type and inst_type != expected_inst_type:
        raise MarketDataBindingErrorV1(
            "VENUE_INSTRUMENT_RESPONSE_MISMATCH",
            f"instType={inst_type}",
        )
    state = str(row.get("state") or "").strip().lower()
    if state and state not in ACTIVE_INSTRUMENT_STATES:
        raise MarketDataBindingErrorV1(
            "VENUE_INSTRUMENT_INACTIVE",
            f"state={state}",
        )
    if not state:
        # Inventory rows must declare state for productive acceptance.
        raise MarketDataBindingErrorV1(
            "VENUE_INSTRUMENT_INACTIVE",
            "state_missing",
        )
    return row


def extract_instruments_data_array_v1(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    if str(payload.get("code", "0")) not in {"0", ""}:
        raise MarketDataBindingErrorV1(
            "TRANSPORT_FAILURE",
            f"PROVIDER_CODE_{payload.get('code')}",
        )
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise MarketDataBindingErrorV1(
            "CANONICAL_INSTRUMENT_MAPPING_MISSING",
            "instruments_data_empty",
        )
    rows: list[Mapping[str, Any]] = []
    for item in data:
        if isinstance(item, Mapping):
            rows.append(item)
    if not rows:
        raise MarketDataBindingErrorV1(
            "CANONICAL_INSTRUMENT_MAPPING_MISSING",
            "instruments_rows_empty",
        )
    return rows
