"""Companion C2 Fraction→Units input read-binding and algebra tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.governance.capital_risk_sizing_v1 import InstrumentQuantityConstraintsV1
from src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.conversion_algebra_v1 import (
    CompanionFractionToUnitsAlgebraError,
    apply_lot_floor_policy_v1,
    derive_pre_normalization_quantity_base_units_v1,
    validate_position_fraction_v1,
)
from src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.read_binding_v1 import (
    CompanionC2ReadBindingError,
    bind_companion_c2_conversion_inputs_read_only_v1,
    prove_algebra_with_instrument_v1,
)
from src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.registry_and_witness_v1 import (
    witness_companion_c2_conversion_dependency_closure_v1,
)
from src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.constants_v1 import (
    OWNER_GO,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    CurrentProductiveAvailableForSizingProducerOutputV1,
)
from src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1 import (
    produce_current_productive_instrument_quantity_constraints_from_okx_row_v1,
)
from src.ops.governed_productive_reference_price_authority_producer_v1.current_productive_mv2_mark_reference_price_producer_v1 import (
    produce_current_productive_reference_price_from_mv2_mark_v1,
)


def _equity_output(*, value: str = "10000") -> CurrentProductiveAvailableForSizingProducerOutputV1:
    return CurrentProductiveAvailableForSizingProducerOutputV1(
        produced="true",
        value=value,
        settlement_currency="USDC",
        dimension_id=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION,
        producer_identity=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY,
        algebra_id="BASE_MINUS_U04_MINUS_CONDITIONAL_P01_USDC_V1",
        output_unit="USDC",
        output_class="AVAILABLE_FOR_SIZING",
        bound_account_identity="acct-bound",
        bound_venue_identity="OKX_EEA",
        bound_td_mode="cross",
        decision_epoch="1",
        observed_at_as_of="2026-09-25T00:00:00Z",
        input_set_digest="d",
        u04_applied="false",
        p01_applied="false",
        double_counting_guard="true",
        reconciliation_status="RECONCILED",
        restart_reconstruction_status="OK",
        reason_codes=(),
        step_29p_risk_admissible="true",
    )


def _instrument_output():
    row = {
        "data": [
            {
                "instId": "ETH-USDT-SWAP",
                "instType": "SWAP",
                "ctType": "linear",
                "state": "live",
                "ctVal": "0.1",
                "lotSz": "0.01",
                "minSz": "0.01",
                "tickSz": "0.01",
            }
        ]
    }
    return produce_current_productive_instrument_quantity_constraints_from_okx_row_v1(
        venue_native_id="ETH-USDT-SWAP",
        instruments_payload=row,
        observed_at_as_of="2026-09-25T00:00:00Z",
        bound_instrument_id="ETH-USDT-SWAP",
    )


def _price_output():
    return produce_current_productive_reference_price_from_mv2_mark_v1(
        mark_price="2500",
        instrument_id="ETH-USDT-SWAP",
        observed_at_as_of="2026-09-25T00:00:00Z",
    )


def test_read_binding_accepts_governed_producer_outputs() -> None:
    bundle = bind_companion_c2_conversion_inputs_read_only_v1(
        equity_output=_equity_output(),
        reference_price_output=_price_output(),
        instrument_metadata_output=_instrument_output(),
    )
    assert bundle.account_equity_available_for_sizing == Decimal("10000")
    assert bundle.reference_price == Decimal("2500")
    assert bundle.instrument_id == "ETH-USDT-SWAP"


def test_read_binding_rejects_candle_close_only_path() -> None:
    bad_price = produce_current_productive_reference_price_from_mv2_mark_v1(
        mark_price="",
        instrument_id="ETH-USDT-SWAP",
        observed_at_as_of="2026-09-25T00:00:00Z",
    )
    with pytest.raises(CompanionC2ReadBindingError):
        bind_companion_c2_conversion_inputs_read_only_v1(
            equity_output=_equity_output(),
            reference_price_output=bad_price,
            instrument_metadata_output=_instrument_output(),
        )


def test_algebra_linear_fraction_to_quantity() -> None:
    inst = _instrument_output().constraints
    assert isinstance(inst, InstrumentQuantityConstraintsV1)
    qty, alloc = derive_pre_normalization_quantity_base_units_v1(
        account_equity_available_for_sizing=Decimal("10000"),
        position_fraction=Decimal("0.1"),
        reference_price=Decimal("2500"),
        instrument=inst,
    )
    assert alloc == Decimal("1000")
    assert qty == Decimal("4")


def test_algebra_fail_closed_fraction_and_inverse() -> None:
    inst = _instrument_output().constraints
    assert isinstance(inst, InstrumentQuantityConstraintsV1)
    with pytest.raises(CompanionFractionToUnitsAlgebraError):
        validate_position_fraction_v1(Decimal("1.5"))
    inverse = InstrumentQuantityConstraintsV1(
        instrument_id=inst.instrument_id,
        market_type=inst.market_type,
        contract_kind="INVERSE",
        contract_multiplier=inst.contract_multiplier,
        lot_size=inst.lot_size,
        minimum_quantity=inst.minimum_quantity,
        maximum_quantity=None,
        minimum_notional=None,
        tick_size=inst.tick_size,
        instrument_metadata_version=inst.instrument_metadata_version,
    )
    with pytest.raises(CompanionFractionToUnitsAlgebraError):
        derive_pre_normalization_quantity_base_units_v1(
            account_equity_available_for_sizing=Decimal("1000"),
            position_fraction=Decimal("0.1"),
            reference_price=Decimal("2500"),
            instrument=inverse,
        )


def test_witness_dependency_closure() -> None:
    witness = witness_companion_c2_conversion_dependency_closure_v1(
        owner_go=OWNER_GO,
        equity_output=_equity_output(),
        reference_price_output=_price_output(),
        instrument_metadata_output=_instrument_output(),
        sample_position_fraction=Decimal("0.1"),
    )
    assert witness.conversion_algebra_proven is True
    assert witness.runtime_conversion_implemented is False
    assert witness.c2_authority_added is False


def test_lot_floor_reuses_crs_primitive() -> None:
    inst = _instrument_output().constraints
    assert isinstance(inst, InstrumentQuantityConstraintsV1)
    raw = Decimal("4.009")
    floored = apply_lot_floor_policy_v1(pre_normalization_quantity=raw, instrument=inst)
    assert floored == Decimal("4.00")


def test_prove_algebra_with_bound_bundle() -> None:
    bundle = bind_companion_c2_conversion_inputs_read_only_v1(
        equity_output=_equity_output(),
        reference_price_output=_price_output(),
        instrument_metadata_output=_instrument_output(),
    )
    inst = _instrument_output().constraints
    assert isinstance(inst, InstrumentQuantityConstraintsV1)
    qty, _ = prove_algebra_with_instrument_v1(
        input_bundle=bundle,
        instrument_constraints=inst,
        position_fraction=Decimal("0.1"),
    )
    assert qty == Decimal("4")
