"""Registry and witness for Companion C2 conversion dependency closure v1."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping

from src.governance.capital_risk_sizing_v1 import InstrumentQuantityConstraintsV1
from src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.constants_v1 import (
    BINDING_ID,
    CONTRACT_ID,
    C2_AUTHORITY_ADDED,
    OWNER_GO,
    RUNTIME_CONVERSION_IMPLEMENTED,
)
from src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.conversion_algebra_v1 import (
    dimensional_proof_summary_v1,
)
from src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.read_binding_v1 import (
    CompanionC2ConversionInputBundleV1,
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


class CompanionC2DependencyClosureError(RuntimeError):
    """Fail-closed companion dependency-closure witness violation."""


@dataclass(frozen=True)
class CompanionC2DependencyClosureWitnessV1:
    owner_go: str
    binding_id: str
    contract_id: str
    input_bundle: CompanionC2ConversionInputBundleV1
    conversion_algebra_proven: bool
    unit_dimension_proven: bool
    c2_authority_added: bool
    runtime_conversion_implemented: bool


READ_BINDING_SYMBOL = (
    "src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.read_binding_v1."
    "bind_companion_c2_conversion_inputs_read_only_v1"
)
ALGEBRA_SYMBOL = (
    "src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.conversion_algebra_v1."
    "derive_pre_normalization_quantity_base_units_v1"
)


def verify_companion_c2_registry_symbols_importable_v1() -> None:
    for module_path, attr in (
        (
            "src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.read_binding_v1",
            "bind_companion_c2_conversion_inputs_read_only_v1",
        ),
        (
            "src.ops.companion_shadow_live_fraction_to_units_input_binding_v1.conversion_algebra_v1",
            "derive_pre_normalization_quantity_base_units_v1",
        ),
        (
            "src.ops.governed_productive_account_equity_authority_producer_v1."
            "current_productive_available_for_sizing_producer_v1",
            "CurrentProductiveAvailableForSizingProducerOutputV1",
        ),
        (
            "src.ops.governed_productive_reference_price_authority_producer_v1."
            "current_productive_mv2_mark_reference_price_producer_v1",
            "produce_current_productive_reference_price_from_mv2_mark_v1",
        ),
        (
            "src.ops.governed_productive_instrument_metadata_authority_producer_v1."
            "current_productive_okx_instruments_row_producer_v1",
            "produce_current_productive_instrument_quantity_constraints_from_okx_row_v1",
        ),
    ):
        mod = importlib.import_module(module_path)
        obj = getattr(mod, attr)
        if module_path.endswith("read_binding_v1") or module_path.endswith("conversion_algebra_v1"):
            if not callable(obj):
                raise CompanionC2DependencyClosureError(
                    f"REGISTRY_SYMBOL_NOT_CALLABLE:{module_path}.{attr}"
                )


def witness_companion_c2_conversion_dependency_closure_v1(
    *,
    owner_go: str,
    equity_output: CurrentProductiveAvailableForSizingProducerOutputV1,
    reference_price_output: CurrentProductiveReferencePriceProducerOutputV1,
    instrument_metadata_output: CurrentProductiveInstrumentMetadataProducerOutputV1,
    sample_position_fraction: Decimal,
) -> CompanionC2DependencyClosureWitnessV1:
    if owner_go != OWNER_GO:
        raise CompanionC2DependencyClosureError("OWNER_GO_MISMATCH")
    verify_companion_c2_registry_symbols_importable_v1()
    bundle = bind_companion_c2_conversion_inputs_read_only_v1(
        equity_output=equity_output,
        reference_price_output=reference_price_output,
        instrument_metadata_output=instrument_metadata_output,
    )
    constraints = instrument_metadata_output.constraints
    if not isinstance(constraints, InstrumentQuantityConstraintsV1):
        raise CompanionC2DependencyClosureError("INSTRUMENT_CONSTRAINTS_MISSING")
    prove_algebra_with_instrument_v1(
        input_bundle=bundle,
        instrument_constraints=constraints,
        position_fraction=sample_position_fraction,
    )
    if not dimensional_proof_summary_v1().get("algebra_id"):
        raise CompanionC2DependencyClosureError("DIMENSIONAL_PROOF_MISSING")
    if C2_AUTHORITY_ADDED is not False:
        raise CompanionC2DependencyClosureError("C2_AUTHORITY_ADDED_DRIFT")
    if RUNTIME_CONVERSION_IMPLEMENTED is not False:
        raise CompanionC2DependencyClosureError("RUNTIME_CONVERSION_IMPLEMENTED_DRIFT")
    return CompanionC2DependencyClosureWitnessV1(
        owner_go=OWNER_GO,
        binding_id=BINDING_ID,
        contract_id=CONTRACT_ID,
        input_bundle=bundle,
        conversion_algebra_proven=True,
        unit_dimension_proven=True,
        c2_authority_added=False,
        runtime_conversion_implemented=False,
    )


def witness_to_mapping_v1(witness: CompanionC2DependencyClosureWitnessV1) -> Mapping[str, Any]:
    return {
        "OWNER_GO": witness.owner_go,
        "BINDING_ID": witness.binding_id,
        "CONTRACT_ID": witness.contract_id,
        "CONVERSION_ALGEBRA_PROVEN": witness.conversion_algebra_proven,
        "UNIT_DIMENSION_PROVEN": witness.unit_dimension_proven,
        "C2_AUTHORITY_ADDED": witness.c2_authority_added,
        "RUNTIME_CONVERSION_IMPLEMENTED": witness.runtime_conversion_implemented,
        "CONVERSION_READY": True,
        "C2_STATUS": "CONVERSION_DEPENDENCIES_CLOSED_PROVEN",
    }
