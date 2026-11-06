"""Governed reference price producer — fail-closed MV2 mark binding."""

from __future__ import annotations

from decimal import Decimal

from src.ops.governed_productive_reference_price_authority_producer_v1.current_productive_mv2_mark_reference_price_producer_v1 import (
    REASON_MARK_INVALID,
    REASON_MARK_MISSING,
    produce_current_productive_reference_price_from_mv2_mark_v1,
)


def test_produce_success() -> None:
    out = produce_current_productive_reference_price_from_mv2_mark_v1(
        mark_price="3500.5",
        instrument_id="inst-eth-usdt-perp",
        observed_at_as_of="2026-09-25T00:00:00Z",
    )
    assert out.produced is True
    assert out.reference_price == Decimal("3500.5")
    assert out.price_semantics_class == "mark_price"
    assert out.reference_price_version


def test_missing_mark_fail_closed() -> None:
    out = produce_current_productive_reference_price_from_mv2_mark_v1(
        mark_price="",
        instrument_id="inst-eth-usdt-perp",
        observed_at_as_of="2026-09-25T00:00:00Z",
    )
    assert out.produced is False
    assert REASON_MARK_MISSING in out.reason_codes


def test_non_positive_mark_fail_closed() -> None:
    out = produce_current_productive_reference_price_from_mv2_mark_v1(
        mark_price="0",
        instrument_id="inst-eth-usdt-perp",
        observed_at_as_of="2026-09-25T00:00:00Z",
    )
    assert out.produced is False
    assert REASON_MARK_INVALID in out.reason_codes


def test_observed_at_required() -> None:
    out = produce_current_productive_reference_price_from_mv2_mark_v1(
        mark_price="100",
        instrument_id="inst-eth-usdt-perp",
        observed_at_as_of="",
    )
    assert out.produced is False
