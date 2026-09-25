"""Read-only Companion C2 conversion input binding v1.

Validates governed producer outputs (Q0 equity, mark reference price,
instrument metadata) with shared instrument/account context. Fail-closed.
Does not fetch network data or mint authority.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Tuple

from src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    EQUITY_DIMENSION_ID,
    INSTRUMENT_METADATA_AUTHORITY_OWNER,
    REFERENCE_PRICE_AUTHORITY_OWNER,
    REFERENCE_PRICE_SEMANTICS_CLASS,
)
from src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.conversion_algebra_v1 import (
    CompanionFractionToUnitsAlgebraError,
    derive_pre_normalization_quantity_base_units_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    CurrentProductiveAvailableForSizingProducerOutputV1,
)
from src.governance.capital_risk_sizing_v1 import InstrumentQuantityConstraintsV1
from src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1 import (
    CurrentProductiveInstrumentMetadataProducerOutputV1,
)
from src.ops.governed_productive_reference_price_authority_producer_v1.current_productive_mv2_mark_reference_price_producer_v1 import (
    CurrentProductiveReferencePriceProducerOutputV1,
)

REASON_EQUITY_NOT_PRODUCED = "COMPANION_EQUITY_PRODUCER_NOT_PRODUCED"
REASON_EQUITY_IDENTITY = "COMPANION_EQUITY_PRODUCER_IDENTITY_MISMATCH"
REASON_EQUITY_DIMENSION = "COMPANION_EQUITY_DIMENSION_MISMATCH"
REASON_PRICE_NOT_PRODUCED = "COMPANION_REFERENCE_PRICE_NOT_PRODUCED"
REASON_PRICE_IDENTITY = "COMPANION_REFERENCE_PRICE_PRODUCER_IDENTITY_MISMATCH"
REASON_PRICE_SEMANTICS = "COMPANION_REFERENCE_PRICE_SEMANTICS_MISMATCH"
REASON_INSTRUMENT_NOT_PRODUCED = "COMPANION_INSTRUMENT_METADATA_NOT_PRODUCED"
REASON_INSTRUMENT_IDENTITY = "COMPANION_INSTRUMENT_METADATA_PRODUCER_IDENTITY_MISMATCH"
REASON_INSTRUMENT_MISMATCH = "COMPANION_INSTRUMENT_ID_CONTEXT_MISMATCH"
REASON_ACCOUNT_VENUE_MISMATCH = "COMPANION_ACCOUNT_VENUE_CONTEXT_MISMATCH"


class CompanionC2ReadBindingError(RuntimeError):
    """Fail-closed companion conversion input read-binding violation."""


@dataclass(frozen=True)
class CompanionC2ConversionInputBundleV1:
    account_equity_available_for_sizing: Decimal
    reference_price: Decimal
    instrument_id: str
    bound_account_identity: str
    bound_venue_identity: str
    price_observed_at_as_of: str
    instrument_metadata_version: str
    equity_producer_identity: str
    reference_price_producer_identity: str
    instrument_metadata_producer_identity: str


def _parse_equity_value(output: CurrentProductiveAvailableForSizingProducerOutputV1) -> Decimal:
    try:
        value = Decimal(str(output.value or "").strip())
    except (InvalidOperation, ValueError) as exc:
        raise CompanionC2ReadBindingError(REASON_EQUITY_NOT_PRODUCED) from exc
    if not value.is_finite() or value <= 0:
        raise CompanionC2ReadBindingError(REASON_EQUITY_NOT_PRODUCED)
    return value


def bind_companion_c2_conversion_inputs_read_only_v1(
    *,
    equity_output: CurrentProductiveAvailableForSizingProducerOutputV1,
    reference_price_output: CurrentProductiveReferencePriceProducerOutputV1,
    instrument_metadata_output: CurrentProductiveInstrumentMetadataProducerOutputV1,
) -> CompanionC2ConversionInputBundleV1:
    """Authority-preserving read binding; observation alone is insufficient."""
    if str(equity_output.produced or "").lower() != "true":
        raise CompanionC2ReadBindingError(REASON_EQUITY_NOT_PRODUCED)
    if equity_output.producer_identity != CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY:
        raise CompanionC2ReadBindingError(REASON_EQUITY_IDENTITY)
    dim = equity_output.dimension_id or EQUITY_DIMENSION_ID
    if dim != CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION:
        raise CompanionC2ReadBindingError(REASON_EQUITY_DIMENSION)

    if (
        reference_price_output.produced is not True
        or reference_price_output.reference_price is None
    ):
        raise CompanionC2ReadBindingError(REASON_PRICE_NOT_PRODUCED)
    if reference_price_output.producer_identity != REFERENCE_PRICE_AUTHORITY_OWNER:
        raise CompanionC2ReadBindingError(REASON_PRICE_IDENTITY)
    if reference_price_output.price_semantics_class != REFERENCE_PRICE_SEMANTICS_CLASS:
        raise CompanionC2ReadBindingError(REASON_PRICE_SEMANTICS)

    if (
        instrument_metadata_output.produced is not True
        or instrument_metadata_output.constraints is None
    ):
        raise CompanionC2ReadBindingError(REASON_INSTRUMENT_NOT_PRODUCED)
    if instrument_metadata_output.producer_identity != INSTRUMENT_METADATA_AUTHORITY_OWNER:
        raise CompanionC2ReadBindingError(REASON_INSTRUMENT_IDENTITY)

    inst_id = str(instrument_metadata_output.constraints.instrument_id or "").strip()
    ref_inst = str(reference_price_output.instrument_id or "").strip()
    if not inst_id or not ref_inst or inst_id != ref_inst:
        raise CompanionC2ReadBindingError(REASON_INSTRUMENT_MISMATCH)

    account = str(equity_output.bound_account_identity or "").strip()
    venue = str(equity_output.bound_venue_identity or "").strip()
    if not account or not venue:
        raise CompanionC2ReadBindingError(REASON_ACCOUNT_VENUE_MISMATCH)

    equity_value = _parse_equity_value(equity_output)
    return CompanionC2ConversionInputBundleV1(
        account_equity_available_for_sizing=equity_value,
        reference_price=reference_price_output.reference_price,
        instrument_id=inst_id,
        bound_account_identity=account,
        bound_venue_identity=venue,
        price_observed_at_as_of=str(reference_price_output.observed_at_as_of or ""),
        instrument_metadata_version=str(
            instrument_metadata_output.instrument_metadata_version or ""
        ),
        equity_producer_identity=ACCOUNT_EQUITY_AUTHORITY_OWNER,
        reference_price_producer_identity=REFERENCE_PRICE_AUTHORITY_OWNER,
        instrument_metadata_producer_identity=INSTRUMENT_METADATA_AUTHORITY_OWNER,
    )


def prove_algebra_with_instrument_v1(
    *,
    input_bundle: CompanionC2ConversionInputBundleV1,
    instrument_constraints: InstrumentQuantityConstraintsV1,
    position_fraction: Decimal,
) -> Tuple[Decimal, Decimal]:
    if instrument_constraints.instrument_id != input_bundle.instrument_id:
        raise CompanionC2ReadBindingError(REASON_INSTRUMENT_MISMATCH)
    try:
        return derive_pre_normalization_quantity_base_units_v1(
            account_equity_available_for_sizing=input_bundle.account_equity_available_for_sizing,
            position_fraction=position_fraction,
            reference_price=input_bundle.reference_price,
            instrument=instrument_constraints,
        )
    except CompanionFractionToUnitsAlgebraError as exc:
        raise CompanionC2ReadBindingError(str(exc)) from exc
