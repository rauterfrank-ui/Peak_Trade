"""Companion C2 Fraction→Units runtime conversion v1 (scaffold; fail-closed).

Provides optional conversion from governed producer outputs to lot-floored quantity
base units. Default pin keeps shadow/live pass-through semantics unchanged.

Does not import or mutate shadow_session, live_session, or signal_to_orders.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.constants_v1 import (
    INPUT_UNIT,
    OUTPUT_UNIT,
    RUNTIME_CONVERSION_IMPLEMENTED,
)
from src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.conversion_algebra_v1 import (
    apply_lot_floor_policy_v1,
    validate_position_fraction_v1,
)
from src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.read_binding_v1 import (
    CompanionC2ReadBindingError,
    bind_companion_c2_conversion_inputs_read_only_v1,
    prove_algebra_with_instrument_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    CurrentProductiveAvailableForSizingProducerOutputV1,
)
from src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1 import (
    CurrentProductiveInstrumentMetadataProducerOutputV1,
)
from src.ops.governed_productive_reference_price_authority_producer_v1.current_productive_mv2_mark_reference_price_producer_v1 import (
    CurrentProductiveReferencePriceProducerOutputV1,
)

REASON_RUNTIME_CONVERSION_DISABLED = "COMPANION_RUNTIME_CONVERSION_DISABLED"
REASON_RUNTIME_CONVERSION_SLICE_UNAUTHORIZED = "COMPANION_RUNTIME_CONVERSION_SLICE_UNAUTHORIZED"
REASON_PRODUCER_BUNDLE_REQUIRED = "COMPANION_RUNTIME_CONVERSION_PRODUCER_BUNDLE_REQUIRED"

# Fail-closed pin: shadow/live binding requires separate scoped Owner-GO.
COMPANION_RUNTIME_CONVERSION_ENABLED = False
NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED = False


class CompanionRuntimeConversionError(RuntimeError):
    """Fail-closed companion runtime conversion violation."""


@dataclass(frozen=True)
class CompanionRuntimePositionSizeResolutionV1:
    position_size: Decimal
    input_unit: str
    output_unit: str
    conversion_applied: bool


def convert_companion_fraction_to_quantity_units_v1(
    *,
    position_fraction: Decimal,
    equity_output: CurrentProductiveAvailableForSizingProducerOutputV1,
    reference_price_output: CurrentProductiveReferencePriceProducerOutputV1,
    instrument_metadata_output: CurrentProductiveInstrumentMetadataProducerOutputV1,
    apply_lot_floor: bool = True,
) -> CompanionRuntimePositionSizeResolutionV1:
    """Convert fraction to quantity using governed producers (read-only binding)."""
    validate_position_fraction_v1(position_fraction)
    bundle = bind_companion_c2_conversion_inputs_read_only_v1(
        equity_output=equity_output,
        reference_price_output=reference_price_output,
        instrument_metadata_output=instrument_metadata_output,
    )
    constraints = instrument_metadata_output.constraints
    if constraints is None:
        raise CompanionRuntimeConversionError(REASON_PRODUCER_BUNDLE_REQUIRED)
    qty_pre, _alloc = prove_algebra_with_instrument_v1(
        input_bundle=bundle,
        instrument_constraints=constraints,
        position_fraction=position_fraction,
    )
    qty = (
        apply_lot_floor_policy_v1(pre_normalization_quantity=qty_pre, instrument=constraints)
        if apply_lot_floor
        else qty_pre
    )
    return CompanionRuntimePositionSizeResolutionV1(
        position_size=qty,
        input_unit=INPUT_UNIT,
        output_unit=OUTPUT_UNIT,
        conversion_applied=True,
    )


def resolve_companion_position_size_for_signal_v1(
    *,
    position_fraction: Decimal,
    equity_output: Optional[CurrentProductiveAvailableForSizingProducerOutputV1] = None,
    reference_price_output: Optional[CurrentProductiveReferencePriceProducerOutputV1] = None,
    instrument_metadata_output: Optional[
        CurrentProductiveInstrumentMetadataProducerOutputV1
    ] = None,
) -> CompanionRuntimePositionSizeResolutionV1:
    """Resolve position_size for companion signal_to_orders handoff (default passthrough)."""
    if RUNTIME_CONVERSION_IMPLEMENTED is not False:
        raise CompanionRuntimeConversionError("RUNTIME_CONVERSION_IMPLEMENTED_DRIFT")
    if not COMPANION_RUNTIME_CONVERSION_ENABLED:
        validate_position_fraction_v1(position_fraction)
        return CompanionRuntimePositionSizeResolutionV1(
            position_size=position_fraction,
            input_unit=INPUT_UNIT,
            output_unit=INPUT_UNIT,
            conversion_applied=False,
        )
    if not NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED:
        raise CompanionRuntimeConversionError(REASON_RUNTIME_CONVERSION_SLICE_UNAUTHORIZED)
    if (
        equity_output is None
        or reference_price_output is None
        or instrument_metadata_output is None
    ):
        raise CompanionRuntimeConversionError(REASON_PRODUCER_BUNDLE_REQUIRED)
    try:
        return convert_companion_fraction_to_quantity_units_v1(
            position_fraction=position_fraction,
            equity_output=equity_output,
            reference_price_output=reference_price_output,
            instrument_metadata_output=instrument_metadata_output,
        )
    except CompanionC2ReadBindingError as exc:
        raise CompanionRuntimeConversionError(str(exc)) from exc
