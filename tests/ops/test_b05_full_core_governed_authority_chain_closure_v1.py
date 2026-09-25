"""Runtime witness tests for B05 Full-Core authority-chain closure."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.governance.capital_risk_sizing_v1 import InstrumentQuantityConstraintsV1
from src.ops.b05_full_core_governed_authority_chain_closure_v1.registry_and_witness_v1 import (
    B05FullCoreAuthorityChainClosureError,
    OWNER_GO,
    build_b05_full_core_domain_closure_pins_v1,
    verify_b05_full_core_registry_symbols_importable_v1,
    witness_b05_full_core_capital_authority_bindings_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    PRODUCER_IDENTITY,
    CurrentProductive29PRiskCapitalOutputV1,
)
from src.ops.governed_productive_instrument_metadata_authority_producer_v1.constants_v1 import (
    OWNER as INSTRUMENT_OWNER,
)
from src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1 import (
    CurrentProductiveInstrumentMetadataProducerOutputV1,
)
from src.ops.governed_productive_reference_price_authority_producer_v1.constants_v1 import (
    REFERENCE_PRICE_AUTHORITY_OWNER,
)
from src.ops.governed_productive_reference_price_authority_producer_v1.current_productive_mv2_mark_reference_price_producer_v1 import (
    CurrentProductiveReferencePriceProducerOutputV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_mv2_capital_context_rebind_v1 import (
    build_current_productive_live_account_capital_context_v1,
)


def test_registry_imports_and_closure_pins() -> None:
    verify_b05_full_core_registry_symbols_importable_v1()
    equity, reference, instrument = build_b05_full_core_domain_closure_pins_v1()
    assert equity.authority_chain_closed is True
    assert reference.governed_producer_created is True
    assert instrument.authority_binding_implemented is True


def _equity_output() -> CurrentProductive29PRiskCapitalOutputV1:
    return CurrentProductive29PRiskCapitalOutputV1(
        produced="true",
        value="1000",
        settlement_currency="USDC",
        dimension_id="RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING",
        producer_identity=PRODUCER_IDENTITY,
        algebra_id="test",
        output_unit="USDC",
        output_class="CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING",
        bound_account_identity="uid",
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch="epoch-1",
        observed_at_as_of="2026-09-25T00:00:00Z",
        input_set_digest="d",
        observation_surface="test",
        u04_applied="false",
        p01_applied="false",
        double_counting_guard="true",
        reconciliation_status="N/A",
        restart_reconstruction_status="N/A",
        reason_codes=(),
    )


def _price_output() -> CurrentProductiveReferencePriceProducerOutputV1:
    return CurrentProductiveReferencePriceProducerOutputV1(
        produced=True,
        reference_price=Decimal("100"),
        reason_codes=(),
        producer_identity=REFERENCE_PRICE_AUTHORITY_OWNER,
        reference_price_version="v1",
        price_semantics_class="mark_price",
        instrument_id="ADA-USDT-SWAP",
        observed_at_as_of="2026-09-25T00:00:00Z",
    )


def _metadata_output() -> CurrentProductiveInstrumentMetadataProducerOutputV1:
    return CurrentProductiveInstrumentMetadataProducerOutputV1(
        produced=True,
        constraints=InstrumentQuantityConstraintsV1(
            instrument_id="ADA-USDT-SWAP",
            market_type="SWAP",
            contract_kind="linear",
            contract_multiplier=Decimal("1"),
            lot_size=Decimal("1"),
            minimum_quantity=Decimal("1"),
            maximum_quantity=None,
            minimum_notional=Decimal("0"),
            tick_size=Decimal("0.001"),
            instrument_metadata_version="v1",
        ),
        reason_codes=(),
        producer_identity=INSTRUMENT_OWNER,
        instrument_metadata_version="v1",
        observed_at_as_of="2026-09-25T00:00:00Z",
    )


def test_witness_passes_on_coherent_bindings() -> None:
    eq = Decimal("1000")
    ref = Decimal("100")
    meta = _metadata_output()
    assert meta.constraints is not None
    live_ctx = build_current_productive_live_account_capital_context_v1(
        instrument_id="ADA-USDT-SWAP",
        typed_account_equity=eq,
        reference_price=ref,
        protective_stop_price=Decimal("90"),
        instrument_constraints=meta.constraints,
    )
    witness = witness_b05_full_core_capital_authority_bindings_v1(
        owner_go=OWNER_GO,
        equity_output=_equity_output(),
        price_output=_price_output(),
        metadata_output=_metadata_output(),
        live_ctx=live_ctx,
        typed_account_equity=eq,
        reference_price=ref,
    )
    assert witness.companion_c2_touched is False
    assert witness.account_equity.authority_chain_closed is True


def test_witness_fail_closed_on_producer_identity_mismatch() -> None:
    bad = _equity_output()
    bad = CurrentProductive29PRiskCapitalOutputV1(**{**bad.__dict__, "producer_identity": "wrong"})
    with pytest.raises(B05FullCoreAuthorityChainClosureError):
        witness_b05_full_core_capital_authority_bindings_v1(
            owner_go=OWNER_GO,
            equity_output=bad,
            price_output=_price_output(),
            metadata_output=_metadata_output(),
            live_ctx=build_current_productive_live_account_capital_context_v1(
                instrument_id="ADA-USDT-SWAP",
                typed_account_equity=Decimal("1000"),
                reference_price=Decimal("100"),
                protective_stop_price=Decimal("90"),
                instrument_constraints=_metadata_output().constraints,
            ),
            typed_account_equity=Decimal("1000"),
            reference_price=Decimal("100"),
        )
