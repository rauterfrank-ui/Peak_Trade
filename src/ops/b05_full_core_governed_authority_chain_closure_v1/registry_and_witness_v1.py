"""B05 Full-Core governed authority-chain registry and runtime witness v1.

Declares and witnesses producer→transformation→typed binding→authorized consumer
lineages for Account Equity, Reference Price, and Instrument Metadata on the
Full-Core enter-live-29p capital path only. Does not close Companion C2.
Does not activate observation/transport as authority. Does not POST.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping

from src.governance.capital_risk_sizing_v1 import InstrumentQuantityConstraintsV1
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    PRODUCER_IDENTITY as EQUITY_PRODUCER_IDENTITY,
    CurrentProductive29PRiskCapitalOutputV1,
)
from src.ops.governed_productive_instrument_metadata_authority_producer_v1.constants_v1 import (
    GOVERNED_PRODUCER_CREATED as INSTRUMENT_GOVERNED_PRODUCER_CREATED,
    INSTRUMENT_METADATA_AUTHORITY_OWNER,
    OWNER as INSTRUMENT_OWNER,
)
from src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1 import (
    CurrentProductiveInstrumentMetadataProducerOutputV1,
)
from src.ops.governed_productive_reference_price_authority_producer_v1.constants_v1 import (
    GOVERNED_PRODUCER_CREATED as REFERENCE_GOVERNED_PRODUCER_CREATED,
    REFERENCE_PRICE_AUTHORITY_OWNER,
)
from src.ops.governed_productive_reference_price_authority_producer_v1.current_productive_mv2_mark_reference_price_producer_v1 import (
    CurrentProductiveReferencePriceProducerOutputV1,
)
from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
    CanonicalCoreRuntimeCapitalContextV0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
)

OWNER_GO = "OWNER_GO_B05_FULL_CORE_GOVERNED_AUTHORITY_CHAIN_CLOSURE_V1"
B05_FULL_CORE_AUTHORITY_CHAIN_CLOSURE_CREATED = True
SCOPE_TRACK = "FULL_CORE"
COMPANION_C2_OUT_OF_SCOPE = True
OBSERVATION_IS_NOT_AUTHORITY = True

ACCOUNT_EQUITY_AUTHORITY_OWNER = "ops.governed_productive_account_equity_authority_producer_v1"
EQUITY_GOVERNED_PRODUCER_SYMBOL = (
    "src.ops.governed_productive_account_equity_authority_producer_v1."
    "current_productive_29p_risk_capital_model_v1.produce_current_productive_29p_risk_capital_v1"
)
EQUITY_TYPED_BINDING_SYMBOL = (
    "src.ops.governed_productive_account_equity_authority_producer_v1."
    "current_productive_29p_risk_capital_model_v1.bind_step_29p_typed_equity_from_risk_capital_v1"
)
EQUITY_TRANSFORM_ID = "DETAILS_USDC_AVAILEQ_MINUS_CONDITIONAL_P01_USDC_V1"
EQUITY_CONSUMER_SYMBOL = (
    "src.ops.full_core_live_path_composition_root_v1."
    "current_productive_mv2_capital_context_rebind_v1."
    "build_current_productive_live_account_capital_context_v1"
)

REFERENCE_PRODUCER_SYMBOL = (
    "src.ops.governed_productive_reference_price_authority_producer_v1."
    "current_productive_mv2_mark_reference_price_producer_v1."
    "produce_current_productive_reference_price_from_mv2_mark_v1"
)
REFERENCE_PRICE_SEMANTICS_CLASS = "mark_price"

INSTRUMENT_PRODUCER_SYMBOL = (
    "src.ops.governed_productive_instrument_metadata_authority_producer_v1."
    "current_productive_okx_instruments_row_producer_v1."
    "produce_current_productive_instrument_quantity_constraints_from_okx_row_v1"
)

JOIN_SEAM_SYMBOL = (
    "src.ops.full_core_live_path_composition_root_v1."
    "current_productive_enter_live_29p_join_v1."
    "join_current_productive_enter_live_29p_before_venue_plan_v1"
)
AUTHORITY_BINDING_SEAM_ID = "B05_FULL_CORE_ENTER_LIVE_29P_CAPITAL_AUTHORITY_BINDING_V1"


class B05FullCoreAuthorityChainClosureError(RuntimeError):
    """Fail-closed B05 Full-Core authority-chain witness violation."""


@dataclass(frozen=True)
class B05FullCoreDomainClosurePinsV1:
    domain_id: str
    canonical_owner: str
    governed_producer_created: bool
    authority_binding_implemented: bool
    authority_chain_closed: bool
    observation_is_not_authority: bool


@dataclass(frozen=True)
class B05FullCoreAuthorityBindingWitnessV1:
    owner_go: str
    scope_track: str
    authority_binding_seam_id: str
    account_equity: B05FullCoreDomainClosurePinsV1
    reference_price: B05FullCoreDomainClosurePinsV1
    instrument_metadata: B05FullCoreDomainClosurePinsV1
    companion_c2_touched: bool
    companion_fraction_handoff_touched: bool


def _resolve_symbol(module_path: str, attr: str) -> object:
    mod = importlib.import_module(module_path)
    return getattr(mod, attr)


def verify_b05_full_core_registry_symbols_importable_v1() -> None:
    """Static import proof for declared lineage symbols (no network)."""
    pairs = (
        (
            "src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1",
            "produce_current_productive_29p_risk_capital_v1",
        ),
        (
            "src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1",
            "bind_step_29p_typed_equity_from_risk_capital_v1",
        ),
        (
            "src.ops.governed_productive_reference_price_authority_producer_v1.current_productive_mv2_mark_reference_price_producer_v1",
            "produce_current_productive_reference_price_from_mv2_mark_v1",
        ),
        (
            "src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1",
            "produce_current_productive_instrument_quantity_constraints_from_okx_row_v1",
        ),
        (
            "src.ops.full_core_live_path_composition_root_v1.current_productive_mv2_capital_context_rebind_v1",
            "build_current_productive_live_account_capital_context_v1",
        ),
        (
            "src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1",
            "join_current_productive_enter_live_29p_before_venue_plan_v1",
        ),
    )
    for module_path, attr in pairs:
        obj = _resolve_symbol(module_path, attr)
        if not callable(obj):
            raise B05FullCoreAuthorityChainClosureError(
                f"REGISTRY_SYMBOL_NOT_CALLABLE:{module_path}.{attr}"
            )


def build_b05_full_core_domain_closure_pins_v1() -> tuple[
    B05FullCoreDomainClosurePinsV1,
    B05FullCoreDomainClosurePinsV1,
    B05FullCoreDomainClosurePinsV1,
]:
    """Machine-readable closure pins after registry verification."""
    verify_b05_full_core_registry_symbols_importable_v1()
    from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
        CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_CREATED,
    )

    equity_producer_created = CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_CREATED is True
    if not equity_producer_created:
        raise B05FullCoreAuthorityChainClosureError("EQUITY_GOVERNED_PRODUCER_NOT_CREATED")

    equity = B05FullCoreDomainClosurePinsV1(
        domain_id="ACCOUNT_EQUITY",
        canonical_owner=ACCOUNT_EQUITY_AUTHORITY_OWNER,
        governed_producer_created=True,
        authority_binding_implemented=True,
        authority_chain_closed=True,
        observation_is_not_authority=True,
    )
    if REFERENCE_GOVERNED_PRODUCER_CREATED is not True:
        raise B05FullCoreAuthorityChainClosureError("REFERENCE_GOVERNED_PRODUCER_NOT_CREATED")
    reference = B05FullCoreDomainClosurePinsV1(
        domain_id="REFERENCE_PRICE",
        canonical_owner=REFERENCE_PRICE_AUTHORITY_OWNER,
        governed_producer_created=True,
        authority_binding_implemented=True,
        authority_chain_closed=True,
        observation_is_not_authority=True,
    )
    if INSTRUMENT_GOVERNED_PRODUCER_CREATED is not True:
        raise B05FullCoreAuthorityChainClosureError("INSTRUMENT_GOVERNED_PRODUCER_NOT_CREATED")
    instrument = B05FullCoreDomainClosurePinsV1(
        domain_id="INSTRUMENT_METADATA",
        canonical_owner=INSTRUMENT_METADATA_AUTHORITY_OWNER,
        governed_producer_created=True,
        authority_binding_implemented=True,
        authority_chain_closed=True,
        observation_is_not_authority=True,
    )
    if INSTRUMENT_OWNER != INSTRUMENT_METADATA_AUTHORITY_OWNER:
        raise B05FullCoreAuthorityChainClosureError("INSTRUMENT_OWNER_DRIFT")
    return equity, reference, instrument


def witness_b05_full_core_capital_authority_bindings_v1(
    *,
    owner_go: str,
    equity_output: CurrentProductive29PRiskCapitalOutputV1,
    price_output: CurrentProductiveReferencePriceProducerOutputV1,
    metadata_output: CurrentProductiveInstrumentMetadataProducerOutputV1,
    live_ctx: CanonicalCoreRuntimeCapitalContextV0,
    typed_account_equity: Decimal,
    reference_price: Decimal,
) -> B05FullCoreAuthorityBindingWitnessV1:
    """Witness Full-Core capital authority bindings at enter-live-29p join (fail-closed)."""
    if owner_go != OWNER_GO:
        raise B05FullCoreAuthorityChainClosureError("OWNER_GO_MISMATCH")
    if str(equity_output.produced or "").lower() != "true":
        raise B05FullCoreAuthorityChainClosureError("EQUITY_PRODUCER_NOT_PRODUCED")
    if str(equity_output.producer_identity or "") != EQUITY_PRODUCER_IDENTITY:
        raise B05FullCoreAuthorityChainClosureError("EQUITY_PRODUCER_IDENTITY_MISMATCH")
    if price_output.produced is not True or price_output.reference_price is None:
        raise B05FullCoreAuthorityChainClosureError("REFERENCE_PRICE_NOT_PRODUCED")
    if price_output.producer_identity != REFERENCE_PRICE_AUTHORITY_OWNER:
        raise B05FullCoreAuthorityChainClosureError("REFERENCE_PRODUCER_IDENTITY_MISMATCH")
    if price_output.price_semantics_class != REFERENCE_PRICE_SEMANTICS_CLASS:
        raise B05FullCoreAuthorityChainClosureError("REFERENCE_PRICE_SEMANTICS_MISMATCH")
    if metadata_output.produced is not True or metadata_output.constraints is None:
        raise B05FullCoreAuthorityChainClosureError("INSTRUMENT_METADATA_NOT_PRODUCED")
    if metadata_output.producer_identity != INSTRUMENT_OWNER:
        raise B05FullCoreAuthorityChainClosureError("INSTRUMENT_PRODUCER_IDENTITY_MISMATCH")
    if live_ctx.capital_risk_mode != CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND:
        raise B05FullCoreAuthorityChainClosureError("CAPITAL_CONTEXT_NOT_LIVE_ACCOUNT_BOUND")
    if live_ctx.account_equity != typed_account_equity:
        raise B05FullCoreAuthorityChainClosureError("EQUITY_NOT_BOUND_IN_CAPITAL_CONTEXT")
    if live_ctx.reference_price != reference_price:
        raise B05FullCoreAuthorityChainClosureError("REFERENCE_PRICE_NOT_BOUND_IN_CAPITAL_CONTEXT")
    if not isinstance(metadata_output.constraints, InstrumentQuantityConstraintsV1):
        raise B05FullCoreAuthorityChainClosureError("INSTRUMENT_CONSTRAINTS_TYPE_DRIFT")

    equity_pins, ref_pins, inst_pins = build_b05_full_core_domain_closure_pins_v1()
    return B05FullCoreAuthorityBindingWitnessV1(
        owner_go=OWNER_GO,
        scope_track=SCOPE_TRACK,
        authority_binding_seam_id=AUTHORITY_BINDING_SEAM_ID,
        account_equity=equity_pins,
        reference_price=ref_pins,
        instrument_metadata=inst_pins,
        companion_c2_touched=False,
        companion_fraction_handoff_touched=False,
    )


def closure_pins_to_mapping_v1(
    witness: B05FullCoreAuthorityBindingWitnessV1,
) -> Mapping[str, Any]:
    """Serialize witness for evidence persistence."""

    def _domain(d: B05FullCoreDomainClosurePinsV1) -> dict[str, Any]:
        return {
            "domain_id": d.domain_id,
            "canonical_owner": d.canonical_owner,
            "GOVERNED_PRODUCER_CREATED": d.governed_producer_created,
            "AUTHORITY_BINDING_IMPLEMENTED": d.authority_binding_implemented,
            "AUTHORITY_CHAIN_CLOSED": d.authority_chain_closed,
            "OBSERVATION_IS_NOT_AUTHORITY": d.observation_is_not_authority,
        }

    return {
        "OWNER_GO": witness.owner_go,
        "SCOPE_TRACK": witness.scope_track,
        "AUTHORITY_BINDING_SEAM_ID": witness.authority_binding_seam_id,
        "ACCOUNT_EQUITY": _domain(witness.account_equity),
        "REFERENCE_PRICE": _domain(witness.reference_price),
        "INSTRUMENT_METADATA": _domain(witness.instrument_metadata),
        "COMPANION_C2_TOUCHED": witness.companion_c2_touched,
        "COMPANION_FRACTION_HANDOFF_TOUCHED": witness.companion_fraction_handoff_touched,
        "B05_FULL_CORE_AUTHORITY_CHAIN_VERDICT": "CLOSED",
    }
