"""Offline regression for pilot capital guard existing exposure parsing."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_pilot_capital_guard_post_bind_v1 import (
    PilotCapitalGuardPostBindError,
    _existing_exposure_notional_usdc_v1,
)
from tests.ops._pilot_guard_enter_post_test_helpers_v1 import PILOT_TEST_INST

INST = PILOT_TEST_INST


def _payload(rows: list[dict]) -> dict:
    return {"code": "0", "data": rows}


def test_empty_positions_list_returns_zero() -> None:
    assert (
        _existing_exposure_notional_usdc_v1(
            positions_payload=_payload([]),
            native_instrument_id=INST,
        )
        == "0"
    )


def test_valid_flat_position_returns_zero() -> None:
    assert (
        _existing_exposure_notional_usdc_v1(
            positions_payload=_payload([{"instId": INST, "pos": "0"}]),
            native_instrument_id=INST,
        )
        == "0"
    )


def test_valid_positive_position_sums_notional() -> None:
    out = _existing_exposure_notional_usdc_v1(
        positions_payload=_payload(
            [{"instId": INST, "pos": "2", "notionalUsd": "150.5"}],
        ),
        native_instrument_id=INST,
    )
    assert Decimal(out) == Decimal("150.5")


def test_missing_pos_fails_closed() -> None:
    with pytest.raises(PilotCapitalGuardPostBindError, match="EXISTING_EXPOSURE_UNKNOWN"):
        _existing_exposure_notional_usdc_v1(
            positions_payload=_payload([{"instId": INST, "notionalUsd": "10"}]),
            native_instrument_id=INST,
        )


def test_invalid_pos_fails_closed() -> None:
    with pytest.raises(PilotCapitalGuardPostBindError, match="EXISTING_EXPOSURE_UNKNOWN"):
        _existing_exposure_notional_usdc_v1(
            positions_payload=_payload([{"instId": INST, "pos": "not-a-number"}]),
            native_instrument_id=INST,
        )


def test_positive_notional_with_missing_pos_fails_closed() -> None:
    with pytest.raises(PilotCapitalGuardPostBindError, match="EXISTING_EXPOSURE_UNKNOWN"):
        _existing_exposure_notional_usdc_v1(
            positions_payload=_payload([{"instId": INST, "notionalUsd": "500"}]),
            native_instrument_id=INST,
        )


def test_contradictory_flat_pos_with_nonzero_notional_fails_closed() -> None:
    with pytest.raises(PilotCapitalGuardPostBindError, match="EXISTING_EXPOSURE_UNKNOWN"):
        _existing_exposure_notional_usdc_v1(
            positions_payload=_payload(
                [{"instId": INST, "pos": "0", "notionalUsd": "25"}],
            ),
            native_instrument_id=INST,
        )


def test_known_positive_plus_unknown_row_fails_closed() -> None:
    with pytest.raises(PilotCapitalGuardPostBindError, match="EXISTING_EXPOSURE_UNKNOWN"):
        _existing_exposure_notional_usdc_v1(
            positions_payload=_payload(
                [
                    {"instId": INST, "pos": "1", "notionalUsd": "100"},
                    {"instId": INST, "pos": "2"},
                ],
            ),
            native_instrument_id=INST,
        )


def test_irrelevant_instrument_ignored() -> None:
    assert (
        _existing_exposure_notional_usdc_v1(
            positions_payload=_payload(
                [
                    {"instId": "OTHER-USDT-SWAP", "pos": "99", "notionalUsd": "9999"},
                    {"instId": INST, "pos": "0"},
                ],
            ),
            native_instrument_id=INST,
        )
        == "0"
    )


def test_non_mapping_row_fails_closed() -> None:
    with pytest.raises(PilotCapitalGuardPostBindError, match="EXISTING_EXPOSURE_UNKNOWN"):
        _existing_exposure_notional_usdc_v1(
            positions_payload=_payload(["bad-row"]),  # type: ignore[list-item]
            native_instrument_id=INST,
        )
