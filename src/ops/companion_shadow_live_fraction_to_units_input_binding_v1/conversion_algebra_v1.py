"""Dimensional Fraction→Units algebra for Companion C2 (LINEAR futures only).

Derived from capital_risk_sizing_v1 linear notional per unit:
  notional_per_unit = reference_price * contract_multiplier
  capital_allocation = account_equity_available_for_sizing * position_fraction
  quantity_base_units = capital_allocation / notional_per_unit

No leverage multiplication. Inverse contracts fail-closed. Does not POST.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Tuple

from src.governance.capital_risk_sizing_v1 import InstrumentQuantityConstraintsV1, _floor_to_lot

REASON_FRACTION_INVALID = "COMPANION_FRACTION_INVALID"
REASON_EQUITY_INVALID = "COMPANION_EQUITY_INVALID"
REASON_PRICE_INVALID = "COMPANION_REFERENCE_PRICE_INVALID"
REASON_INSTRUMENT_UNSUPPORTED = "COMPANION_INSTRUMENT_CONTRACT_KIND_UNSUPPORTED"
REASON_NON_POSITIVE_QUANTITY = "COMPANION_DERIVED_QUANTITY_NON_POSITIVE"
REASON_BELOW_MIN_QUANTITY = "COMPANION_DERIVED_QUANTITY_BELOW_MINIMUM"


class CompanionFractionToUnitsAlgebraError(RuntimeError):
    """Fail-closed companion conversion algebra violation."""


def validate_position_fraction_v1(fraction: Decimal) -> None:
    if not fraction.is_finite():
        raise CompanionFractionToUnitsAlgebraError(REASON_FRACTION_INVALID)
    if fraction < 0 or fraction > 1:
        raise CompanionFractionToUnitsAlgebraError(REASON_FRACTION_INVALID)


def linear_notional_per_base_unit_v1(
    *,
    reference_price: Decimal,
    contract_multiplier: Decimal,
) -> Decimal:
    """Match capital_risk_sizing_v1._linear_notional_per_unit semantics."""
    if not reference_price.is_finite() or reference_price <= 0:
        raise CompanionFractionToUnitsAlgebraError(REASON_PRICE_INVALID)
    if not contract_multiplier.is_finite() or contract_multiplier <= 0:
        raise CompanionFractionToUnitsAlgebraError(REASON_PRICE_INVALID)
    return reference_price * contract_multiplier


def derive_pre_normalization_quantity_base_units_v1(
    *,
    account_equity_available_for_sizing: Decimal,
    position_fraction: Decimal,
    reference_price: Decimal,
    instrument: InstrumentQuantityConstraintsV1,
) -> Tuple[Decimal, Decimal]:
    """Return (pre_lot_floor_quantity, capital_allocation) for dimensional proof."""
    validate_position_fraction_v1(position_fraction)
    if (
        not account_equity_available_for_sizing.is_finite()
        or account_equity_available_for_sizing <= 0
    ):
        raise CompanionFractionToUnitsAlgebraError(REASON_EQUITY_INVALID)

    kind = str(instrument.contract_kind or "").upper()
    if kind != "LINEAR":
        raise CompanionFractionToUnitsAlgebraError(REASON_INSTRUMENT_UNSUPPORTED)

    notional_per_unit = linear_notional_per_base_unit_v1(
        reference_price=reference_price,
        contract_multiplier=instrument.contract_multiplier,
    )
    capital_allocation = account_equity_available_for_sizing * position_fraction
    try:
        raw_quantity = capital_allocation / notional_per_unit
    except (InvalidOperation, ZeroDivisionError) as exc:
        raise CompanionFractionToUnitsAlgebraError(REASON_NON_POSITIVE_QUANTITY) from exc
    if not raw_quantity.is_finite() or raw_quantity <= 0:
        raise CompanionFractionToUnitsAlgebraError(REASON_NON_POSITIVE_QUANTITY)
    return raw_quantity, capital_allocation


def apply_lot_floor_policy_v1(
    *,
    pre_normalization_quantity: Decimal,
    instrument: InstrumentQuantityConstraintsV1,
) -> Decimal:
    """Reuse CRS lot floor primitive; venue_translation_v1 does not own quantity."""
    floored = _floor_to_lot(pre_normalization_quantity, instrument.lot_size)
    if floored < instrument.minimum_quantity:
        raise CompanionFractionToUnitsAlgebraError(REASON_BELOW_MIN_QUANTITY)
    return floored


def dimensional_proof_summary_v1() -> dict[str, str]:
    return {
        "position_fraction_unit": "FRACTION_DECIMAL_0_1",
        "capital_base_unit": "USDC_SETTLEMENT_SCALAR",
        "capital_allocation_unit": "USDC_NOTIONAL",
        "reference_price_unit": "QUOTE_PER_BASE",
        "contract_multiplier_unit": "CONTRACT_VALUE_IN_QUOTE_PER_BASE",
        "notional_per_unit": "QUOTE_NOTIONAL_PER_BASE_UNIT",
        "output_unit": "QUANTITY_BASE_UNITS",
        "leverage_role": "NONE",
        "algebra_id": "LINEAR_FUTURES_CAPITAL_FRACTION_OVER_NOTIONAL_PER_UNIT_V1",
    }
