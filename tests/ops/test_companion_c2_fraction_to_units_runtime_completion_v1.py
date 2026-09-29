"""Companion C2 runtime completion scaffold tests (no shadow/live binding)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.runtime_conversion_v1 import (
    COMPANION_RUNTIME_CONVERSION_ENABLED,
    CompanionRuntimeConversionError,
    convert_companion_fraction_to_quantity_units_v1,
    resolve_companion_position_size_for_signal_v1,
)
from tests.ops.test_companion_shadow_live_fraction_to_units_input_binding_v1 import (
    _equity_output,
    _instrument_output,
    _price_output,
)


def test_runtime_conversion_disabled_passthrough_fraction() -> None:
    assert COMPANION_RUNTIME_CONVERSION_ENABLED is False
    resolved = resolve_companion_position_size_for_signal_v1(
        position_fraction=Decimal("0.1"),
    )
    assert resolved.conversion_applied is False
    assert resolved.position_size == Decimal("0.1")
    assert resolved.input_unit == resolved.output_unit


def test_convert_with_governed_producers_matches_algebra() -> None:
    resolved = convert_companion_fraction_to_quantity_units_v1(
        position_fraction=Decimal("0.1"),
        equity_output=_equity_output(),
        reference_price_output=_price_output(),
        instrument_metadata_output=_instrument_output(),
    )
    assert resolved.conversion_applied is True
    assert resolved.position_size == Decimal("4.00")


def test_enabled_path_without_slice_authorization_fail_closed(monkeypatch) -> None:
    import src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.runtime_conversion_v1 as mod

    monkeypatch.setattr(mod, "COMPANION_RUNTIME_CONVERSION_ENABLED", True)
    with pytest.raises(CompanionRuntimeConversionError):
        resolve_companion_position_size_for_signal_v1(position_fraction=Decimal("0.1"))
