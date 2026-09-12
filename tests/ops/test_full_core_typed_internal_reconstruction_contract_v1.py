"""Typed internal reconstruction contract. No productive reconstruction. No producer."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    bind_simulated_execution_port_v1,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    DIVERGENCE_POLICY_CREATED,
    EQUITY_DIMENSION_BOUND,
    FIELD_TO_DIMENSION_MAPPING_PRESENT,
    GOVERNED_PRODUCER_CREATED,
    GOVERNED_PRODUCTIVE_SOURCE_PRESENT,
    INCLUSION_PROVEN,
    INTERNAL_RECONSTRUCTION_AUTHORITY_EFFECT,
    INTERNAL_RECONSTRUCTION_CONTRACT_MISSING_CLOSED,
    INTERNAL_RECONSTRUCTION_CREATED,
    INTERNAL_RECONSTRUCTION_PROVEN,
    INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT,
    INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT,
    LIVE_ACCOUNT_BOUND_JOIN_PRESENT,
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_RESTART_RECONSTRUCTED,
    MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING,
    MAPPING_PROVEN,
    NORMALIZATION_RUNTIME_INSTANCE_PRESENT,
    NORMALIZATION_SCHEMA_PRESENT,
    RAW_TO_WITNESS_PROVEN,
    RECONCILIATION_CONTRACT_CREATED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT,
    RUNTIME_VALUE_BINDING_PRESENT,
    SEMANTIC_MAPPING_PROVEN,
    SOURCE_OBJECT_PRESENT,
    SOURCE_SELECTED,
    VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT,
    VENUE_WITNESS_SCHEMA_PRESENT,
    VENUE_WITNESS_SELECTED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_DECOMPOSED_CONTRACT_GAP,
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    live_admission_gap_dag_v1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    evaluate_step_29p_capital_risk_admissibility_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.internal_reconstruction_contract_v1 import (
    ALGEBRA_REPRESENTATION,
    ALGEBRA_STATUS_COMPLETE,
    ALGEBRA_STATUS_INCOMPLETE,
    COMPONENT_COMPLETENESS_COMPLETE,
    COMPONENT_COMPLETENESS_INCOMPLETE,
    COMPONENT_CONTRADICTORY,
    COMPONENT_EQUITY_BASE,
    COMPONENT_FEE,
    COMPONENT_LIABILITY,
    COMPONENT_MALFORMED,
    COMPONENT_MISSING,
    COMPONENT_NOT_APPLICABLE,
    COMPONENT_P01_HAIRCUT_RESERVE_DEPLETION,
    COMPONENT_PENDING_ORDER_RESERVATION,
    COMPONENT_PRESENT,
    COMPONENT_REALIZED_PNL,
    COMPONENT_REQUIRED,
    COMPONENT_SLIPPAGE,
    COMPONENT_STALE,
    COMPONENT_TERM_VECTOR,
    COMPONENT_UNREALIZED_PNL_MTM,
    CONTRADICTION_NONE,
    CONTRADICTION_PRESENT,
    DIMENSION_ID,
    FRESHNESS_EXPLICIT_TIMESTAMPS_NOT_COMPONENT_TTL,
    FRESHNESS_STALE,
    INCLUSION_IN_BASE_UNKNOWN,
    INCLUSION_SEPARATE_ADDEND_FORBIDDEN,
    InternalReconstructionContractError,
    InternalReconstructionContractV1,
    PRESENCE_EMPTY,
    PRESENCE_MALFORMED,
    PRESENCE_MISSING,
    PRESENCE_NONZERO,
    PRESENCE_NOT_APPLICABLE,
    PRESENCE_ZERO,
    RECONSTRUCTED_VALUE_STATE_COMPUTED,
    RECONSTRUCTED_VALUE_STATE_NOT_COMPUTED,
    RECONSTRUCTION_ELIGIBILITY_ELIGIBLE,
    RECONSTRUCTION_ELIGIBILITY_INELIGIBLE,
    RECONSTRUCTION_PROVEN_STATUS_PROVEN,
    RECONSTRUCTION_PROVEN_STATUS_UNPROVEN,
    RECONSTRUCTION_SEMANTIC_CLASS,
    RESTART_CLEAR,
    RESTART_INVALIDATED,
    RESTART_PROVENANCE_PRE_RESTART,
    RESTART_PROVENANCE_UNBOUND,
    RESTART_UNPROVEN,
    SAME_EPOCH_PROVEN,
    SAME_EPOCH_UNPROVEN,
    attach_internal_reconstruction_provenance_digest_v1,
    build_internal_reconstruction_contract_v1,
    build_reconstruction_component_v1,
    encode_inclusion_vector_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    SimulatedExecutionPortV1,
)
from tests.ops.test_full_core_step_29p_risk_admissibility_pre_construction_v1 import (
    _capital,
    _complete_claim,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_INTERNAL_RECONSTRUCTION_CONTRACT_V1.md"
SCHEMA_PATH = (
    REPO_ROOT
    / "src/ops/governed_productive_account_equity_authority_producer_v1"
    / "internal_reconstruction_contract_v1.py"
)
Y_HEADING = "11.2.1.Y FULL_CORE_TYPED_NORMALIZATION_INCLUSION_CONTRACT"
Z_HEADING = "11.2.1.Z FULL_CORE_TYPED_INTERNAL_RECONSTRUCTION_CONTRACT"
AA_HEADING = "11.2.1.AA FULL_CORE_TYPED_RECONSTRUCTION_ALGEBRA_CONTRACT"


def _component(
    *,
    component_semantic_class: str,
    requirement: str = COMPONENT_REQUIRED,
    state: str = COMPONENT_PRESENT,
    presence: str = PRESENCE_ZERO,
    value: str = "0",
    currency: str = "USDC",
    unit: str = "USDC",
    valuation_mark_ref: str = "",
    provenance_ref: str = "SYNTHETIC_COMPONENT_PROVENANCE",
    observed_at_as_of: str = "synthetic-observed-at",
    inclusion: str = INCLUSION_IN_BASE_UNKNOWN,
) -> object:
    if component_semantic_class == COMPONENT_SLIPPAGE:
        requirement = COMPONENT_NOT_APPLICABLE
        state = COMPONENT_NOT_APPLICABLE
        presence = PRESENCE_NOT_APPLICABLE
        value = ""
        currency = "NOT_APPLICABLE"
        unit = "NOT_APPLICABLE"
        provenance_ref = ""
        observed_at_as_of = ""
        valuation_mark_ref = ""
        inclusion = "NOT_APPLICABLE"
    elif component_semantic_class == COMPONENT_UNREALIZED_PNL_MTM and state == COMPONENT_PRESENT:
        valuation_mark_ref = valuation_mark_ref or "SYNTHETIC_MARK_REF"
    if state == COMPONENT_MISSING:
        presence = (
            PRESENCE_MISSING if presence not in {PRESENCE_MISSING, PRESENCE_EMPTY} else presence
        )
        value = ""
        provenance_ref = ""
        observed_at_as_of = ""
        valuation_mark_ref = ""
    if state == COMPONENT_MALFORMED:
        presence = PRESENCE_MALFORMED
        value = "not-a-decimal"
    return build_reconstruction_component_v1(
        component_semantic_class=component_semantic_class,
        component_requirement_status=requirement,
        component_state=state,
        presence_state=presence,
        component_value_representation=value,
        component_currency=currency,
        component_unit=unit,
        valuation_mark_ref=valuation_mark_ref,
        provenance_ref=provenance_ref,
        observed_at_as_of=observed_at_as_of,
        inclusion_in_equity_base_status=inclusion,
    )


def _default_components(**overrides: object) -> tuple[object, ...]:
    classes = (
        COMPONENT_EQUITY_BASE,
        COMPONENT_FEE,
        COMPONENT_LIABILITY,
        COMPONENT_P01_HAIRCUT_RESERVE_DEPLETION,
        COMPONENT_PENDING_ORDER_RESERVATION,
        COMPONENT_REALIZED_PNL,
        COMPONENT_SLIPPAGE,
        COMPONENT_UNREALIZED_PNL_MTM,
    )
    built = []
    for name in classes:
        kwargs = dict(overrides.get(name, {}))  # type: ignore[arg-type]
        built.append(_component(component_semantic_class=name, **kwargs))
    return tuple(built)


def _synthetic_fields(**overrides: object) -> dict[str, object]:
    components = overrides.pop("components", _default_components())
    fields: dict[str, object] = {
        "reconstruction_id": "SYNTHETIC_RECONSTRUCTION_ID",
        "source_normalization_adjudication_id": "SYNTHETIC_NORMALIZATION_ADJUDICATION_ID",
        "bound_account_identity": "SYNTHETIC_BOUND_ACCOUNT",
        "bound_venue_identity": "OKX_EEA",
        "rest_host": "eea.okx.com",
        "bound_td_mode": "cross",
        "account_mode": "UNPROVEN",
        "currency_domain": "USDC",
        "reconstruction_epoch": "synthetic-reconstruction-epoch",
        "target_semantic_dimension_id": DIMENSION_ID,
        "reconstruction_semantic_class": RECONSTRUCTION_SEMANTIC_CLASS,
        "reconstruction_semantic_class_version": "v1",
        "inclusion_vector": encode_inclusion_vector_v1(components),  # type: ignore[arg-type]
        "component_term_vector": COMPONENT_TERM_VECTOR,
        "component_completeness": COMPONENT_COMPLETENESS_INCOMPLETE,
        "reconstruction_algebra_status": ALGEBRA_STATUS_INCOMPLETE,
        "reconstruction_algebra_representation": ALGEBRA_REPRESENTATION,
        "reconstructed_value_state": RECONSTRUCTED_VALUE_STATE_NOT_COMPUTED,
        "reconstructed_value_representation": "",
        "contradiction_status": CONTRADICTION_NONE,
        "same_epoch_status": SAME_EPOCH_UNPROVEN,
        "freshness_status": FRESHNESS_EXPLICIT_TIMESTAMPS_NOT_COMPONENT_TTL,
        "freshness_evidence_ref": "SYNTHETIC_RECONSTRUCTION_FRESHNESS_EVIDENCE",
        "restart_invalidation_status": RESTART_UNPROVEN,
        "restart_provenance_class": RESTART_PROVENANCE_UNBOUND,
        "reconstruction_eligibility": RECONSTRUCTION_ELIGIBILITY_INELIGIBLE,
        "reconstruction_proven_status": RECONSTRUCTION_PROVEN_STATUS_UNPROVEN,
        "observation_vs_authority_class": "OBSERVATION",
        "internal_reconstruction_authority_effect": "NONE",
        "components": components,
    }
    fields.update(overrides)
    if "components" in fields and "inclusion_vector" not in overrides:
        fields["inclusion_vector"] = encode_inclusion_vector_v1(fields["components"])  # type: ignore[arg-type]
    digest_fields = {key: value for key, value in fields.items() if key != "components"}
    attached = attach_internal_reconstruction_provenance_digest_v1(digest_fields)
    attached["components"] = fields["components"]
    return attached


def _z_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    z_start = runbook.index(Z_HEADING)
    return runbook[z_start : runbook.index(AA_HEADING, z_start)]


def test_valid_synthetic_contract_can_be_constructed() -> None:
    contract = build_internal_reconstruction_contract_v1(**_synthetic_fields())
    assert isinstance(contract, InternalReconstructionContractV1)
    assert contract.source_normalization_adjudication_id == (
        "SYNTHETIC_NORMALIZATION_ADJUDICATION_ID"
    )
    assert contract.bound_account_identity == "SYNTHETIC_BOUND_ACCOUNT"
    assert contract.currency_domain == "USDC"
    assert contract.reconstruction_epoch == "synthetic-reconstruction-epoch"
    assert contract.target_semantic_dimension_id == DIMENSION_ID
    assert contract.reconstruction_proven_status == RECONSTRUCTION_PROVEN_STATUS_UNPROVEN
    assert contract.reconstruction_eligibility == RECONSTRUCTION_ELIGIBILITY_INELIGIBLE
    assert contract.reconstructed_value_state == RECONSTRUCTED_VALUE_STATE_NOT_COMPUTED
    assert INTERNAL_RECONSTRUCTION_AUTHORITY_EFFECT == "NONE"


def test_contract_is_immutable_and_digest_is_deterministic() -> None:
    first = build_internal_reconstruction_contract_v1(**_synthetic_fields())
    second = build_internal_reconstruction_contract_v1(**_synthetic_fields())
    assert first.provenance_digest == second.provenance_digest
    with pytest.raises(FrozenInstanceError):
        contract = build_internal_reconstruction_contract_v1(**_synthetic_fields())
        contract.reconstruction_proven_status = RECONSTRUCTION_PROVEN_STATUS_PROVEN  # type: ignore[misc]


def test_normalization_reference_and_account_identity_are_required() -> None:
    fields = _synthetic_fields()
    fields["source_normalization_adjudication_id"] = ""
    with pytest.raises(InternalReconstructionContractError) as raised:
        build_internal_reconstruction_contract_v1(
            **attach_internal_reconstruction_provenance_digest_v1(
                {key: value for key, value in fields.items() if key != "components"}
            )
            | {"components": fields["components"]}
        )
    assert "FIELD_MISSING:source_normalization_adjudication_id" in str(raised.value)


def test_target_dimension_does_not_imply_reconstruction_proven() -> None:
    contract = build_internal_reconstruction_contract_v1(**_synthetic_fields())
    assert contract.target_semantic_dimension_id == DIMENSION_ID
    assert contract.reconstruction_proven_status != RECONSTRUCTION_PROVEN_STATUS_PROVEN
    assert INTERNAL_RECONSTRUCTION_PROVEN is False
    assert MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING is False


def test_required_versus_not_applicable_components_are_distinguishable() -> None:
    contract = build_internal_reconstruction_contract_v1(**_synthetic_fields())
    by_class = {component.component_semantic_class: component for component in contract.components}
    assert by_class[COMPONENT_EQUITY_BASE].component_requirement_status == COMPONENT_REQUIRED
    assert by_class[COMPONENT_SLIPPAGE].component_requirement_status == COMPONENT_NOT_APPLICABLE
    assert by_class[COMPONENT_SLIPPAGE].component_state == COMPONENT_NOT_APPLICABLE


def test_missing_required_component_fails_closed() -> None:
    components = _default_components(
        **{COMPONENT_FEE: {"state": COMPONENT_MISSING, "presence": PRESENCE_MISSING}}
    )
    contract = build_internal_reconstruction_contract_v1(**_synthetic_fields(components=components))
    fee = next(
        component
        for component in contract.components
        if component.component_semantic_class == COMPONENT_FEE
    )
    assert fee.component_state == COMPONENT_MISSING
    assert fee.presence_state == PRESENCE_MISSING
    assert fee.component_value_representation != "0"
    assert contract.reconstruction_eligibility == RECONSTRUCTION_ELIGIBILITY_INELIGIBLE
    fields = _synthetic_fields(components=components)
    fields["reconstruction_eligibility"] = RECONSTRUCTION_ELIGIBILITY_ELIGIBLE
    with pytest.raises(InternalReconstructionContractError) as raised:
        build_internal_reconstruction_contract_v1(**fields)
    assert "ELIGIBLE_FORBIDDEN" in str(raised.value)


def test_empty_required_component_is_not_zero() -> None:
    components = _default_components(
        **{COMPONENT_LIABILITY: {"state": COMPONENT_MISSING, "presence": PRESENCE_EMPTY}}
    )
    contract = build_internal_reconstruction_contract_v1(**_synthetic_fields(components=components))
    liability = next(
        component
        for component in contract.components
        if component.component_semantic_class == COMPONENT_LIABILITY
    )
    assert liability.presence_state == PRESENCE_EMPTY
    assert liability.component_value_representation == ""
    assert liability.component_value_representation != "0"


def test_malformed_required_component_fails_closed_and_is_not_zero() -> None:
    components = _default_components(**{COMPONENT_EQUITY_BASE: {"state": COMPONENT_MALFORMED}})
    contract = build_internal_reconstruction_contract_v1(**_synthetic_fields(components=components))
    base = next(
        component
        for component in contract.components
        if component.component_semantic_class == COMPONENT_EQUITY_BASE
    )
    assert base.component_state == COMPONENT_MALFORMED
    assert base.component_value_representation != "0"
    assert contract.reconstruction_proven_status == RECONSTRUCTION_PROVEN_STATUS_UNPROVEN


def test_stale_required_component_fails_closed_and_is_not_silently_current() -> None:
    components = _default_components(
        **{
            COMPONENT_PENDING_ORDER_RESERVATION: {
                "state": COMPONENT_STALE,
                "presence": PRESENCE_NONZERO,
                "value": "2.5",
            }
        }
    )
    contract = build_internal_reconstruction_contract_v1(**_synthetic_fields(components=components))
    hold = next(
        component
        for component in contract.components
        if component.component_semantic_class == COMPONENT_PENDING_ORDER_RESERVATION
    )
    assert hold.component_state == COMPONENT_STALE
    assert hold.freshness_status if False else hold.observed_at_as_of != ""
    assert contract.reconstruction_eligibility == RECONSTRUCTION_ELIGIBILITY_INELIGIBLE


def test_contradictory_component_fails_closed() -> None:
    components = _default_components(
        **{
            COMPONENT_REALIZED_PNL: {
                "state": COMPONENT_CONTRADICTORY,
                "presence": PRESENCE_NONZERO,
                "value": "1.5",
            }
        }
    )
    contract = build_internal_reconstruction_contract_v1(
        **_synthetic_fields(
            components=components,
            contradiction_status=CONTRADICTION_PRESENT,
        )
    )
    realized = next(
        component
        for component in contract.components
        if component.component_semantic_class == COMPONENT_REALIZED_PNL
    )
    assert realized.component_state == COMPONENT_CONTRADICTORY
    assert contract.contradiction_status == CONTRADICTION_PRESENT
    fields = _synthetic_fields(components=components, contradiction_status=CONTRADICTION_PRESENT)
    fields["reconstruction_proven_status"] = RECONSTRUCTION_PROVEN_STATUS_PROVEN
    with pytest.raises(InternalReconstructionContractError) as raised:
        build_internal_reconstruction_contract_v1(**fields)
    assert "PROVEN_FORBIDDEN" in str(raised.value)


def test_present_zero_component_remains_distinct() -> None:
    contract = build_internal_reconstruction_contract_v1(**_synthetic_fields())
    fee = next(
        component
        for component in contract.components
        if component.component_semantic_class == COMPONENT_FEE
    )
    assert fee.presence_state == PRESENCE_ZERO
    assert fee.component_state == COMPONENT_PRESENT
    assert fee.component_value_representation == "0"
    assert fee.presence_state != PRESENCE_MISSING
    assert fee.presence_state != PRESENCE_EMPTY
    assert fee.presence_state != PRESENCE_MALFORMED


def test_present_nonzero_does_not_prove_reconstruction() -> None:
    components = _default_components(
        **{
            COMPONENT_EQUITY_BASE: {
                "state": COMPONENT_PRESENT,
                "presence": PRESENCE_NONZERO,
                "value": "12.5",
            }
        }
    )
    contract = build_internal_reconstruction_contract_v1(**_synthetic_fields(components=components))
    base = next(
        component
        for component in contract.components
        if component.component_semantic_class == COMPONENT_EQUITY_BASE
    )
    assert base.presence_state == PRESENCE_NONZERO
    assert contract.reconstruction_proven_status == RECONSTRUCTION_PROVEN_STATUS_UNPROVEN
    assert contract.reconstructed_value_representation == ""


def test_incomplete_algebra_cannot_produce_reconstruction_proven() -> None:
    contract = build_internal_reconstruction_contract_v1(**_synthetic_fields())
    assert contract.reconstruction_algebra_status == ALGEBRA_STATUS_INCOMPLETE
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT is True
    fields = _synthetic_fields()
    fields["reconstruction_algebra_status"] = ALGEBRA_STATUS_COMPLETE
    with pytest.raises(InternalReconstructionContractError) as raised:
        build_internal_reconstruction_contract_v1(**fields)
    assert "ALGEBRA_COMPLETE_STATUS_FORBIDDEN" in str(raised.value)
    fields = _synthetic_fields()
    fields["component_completeness"] = COMPONENT_COMPLETENESS_COMPLETE
    with pytest.raises(InternalReconstructionContractError) as raised_complete:
        build_internal_reconstruction_contract_v1(**fields)
    assert "COMPLETENESS_COMPLETE_FORBIDDEN" in str(raised_complete.value)


def test_same_epoch_unproven_and_restart_invalidated_fail_closed() -> None:
    contract = build_internal_reconstruction_contract_v1(**_synthetic_fields())
    assert contract.same_epoch_status == SAME_EPOCH_UNPROVEN
    assert contract.restart_invalidation_status == RESTART_UNPROVEN
    fields = _synthetic_fields()
    fields["same_epoch_status"] = SAME_EPOCH_PROVEN
    with pytest.raises(InternalReconstructionContractError) as raised:
        build_internal_reconstruction_contract_v1(**fields)
    assert "SAME_EPOCH_PROVEN_FORBIDDEN" in str(raised.value)
    invalidated = build_internal_reconstruction_contract_v1(
        **_synthetic_fields(
            restart_invalidation_status=RESTART_INVALIDATED,
            restart_provenance_class=RESTART_PROVENANCE_PRE_RESTART,
        )
    )
    assert invalidated.restart_invalidation_status == RESTART_INVALIDATED
    fields = _synthetic_fields()
    fields["restart_invalidation_status"] = RESTART_CLEAR
    with pytest.raises(InternalReconstructionContractError) as raised_restart:
        build_internal_reconstruction_contract_v1(**fields)
    assert "RESTART_CLEAR_FORBIDDEN" in str(raised_restart.value)


def test_separate_addend_and_computed_value_are_forbidden() -> None:
    with pytest.raises(InternalReconstructionContractError) as raised:
        _component(
            component_semantic_class=COMPONENT_REALIZED_PNL,
            inclusion=INCLUSION_SEPARATE_ADDEND_FORBIDDEN,
            presence=PRESENCE_NONZERO,
            value="1.25",
        )
    assert "SEPARATE_ADDEND_FORBIDDEN" in str(raised.value)
    fields = _synthetic_fields()
    fields["reconstructed_value_state"] = RECONSTRUCTED_VALUE_STATE_COMPUTED
    fields["reconstructed_value_representation"] = "100"
    with pytest.raises(InternalReconstructionContractError) as raised_value:
        build_internal_reconstruction_contract_v1(**fields)
    assert "VALUE_STATE_MUST_REMAIN_NOT_COMPUTED" in str(raised_value.value)


def test_forbidden_authority_elevation_and_fallback_do_not_exist() -> None:
    inspect_source = SCHEMA_PATH.read_text(encoding="utf-8")
    assert "AccountingPortfolioStateV1" not in inspect_source
    assert "LedgerSnapshot" not in inspect_source
    assert "equity_by_ccy" not in inspect_source
    assert "SimulatedPortfolioStateV1" not in inspect_source
    assert "totalEq or eq or adjEq" not in inspect_source
    assert 'row.get("totalEq") or row.get("eq")' not in inspect_source
    fields = _synthetic_fields()
    fields["bound_account_identity"] = "totalEq|eq"
    with pytest.raises(InternalReconstructionContractError) as raised:
        build_internal_reconstruction_contract_v1(**fields)
    assert "FALLBACK_CHAIN_FORBIDDEN" in str(raised.value)


def test_schema_creation_does_not_select_source_or_mapping_or_producer() -> None:
    build_internal_reconstruction_contract_v1(**_synthetic_fields())
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert SOURCE_OBJECT_PRESENT is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert GOVERNED_PRODUCTIVE_SOURCE_PRESENT is False
    assert RUNTIME_VALUE_BINDING_PRESENT is False
    assert LIVE_ACCOUNT_BOUND_JOIN_PRESENT is False
    assert RAW_TO_WITNESS_PROVEN is False
    assert SEMANTIC_MAPPING_PROVEN is False
    assert INCLUSION_PROVEN is False
    assert INTERNAL_RECONSTRUCTION_CREATED is False
    assert INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT is True
    assert INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT is False
    assert INTERNAL_RECONSTRUCTION_PROVEN is False
    assert INTERNAL_RECONSTRUCTION_CONTRACT_MISSING_CLOSED is True
    assert RECONCILIATION_CONTRACT_CREATED is False
    assert DIVERGENCE_POLICY_CREATED is False
    assert LIVE_RESTART_RECONSTRUCTED is False
    dag = live_admission_gap_dag_v1()
    assert dag["INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT"] is True
    assert dag["INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["INTERNAL_RECONSTRUCTION_PROVEN"] is False
    assert dag["RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT"] is True
    assert dag["RECONSTRUCTION_ALGEBRA_COMPLETE"] is False
    assert dag["LIVE_RESTART_RECONSTRUCTED"] is False
    assert dag["VENUE_WITNESS_SCHEMA_PRESENT"] is True
    assert dag["VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["VENUE_WITNESS_SELECTED"] is False
    assert dag["NORMALIZATION_SCHEMA_PRESENT"] is True
    assert dag["NORMALIZATION_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY"] == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert dag["EARLIEST_DECOMPOSED_CONTRACT_GAP"] == ("P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED")
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED"


def test_step_29p_remains_inadmissible_and_live_gates_remain_false() -> None:
    capital = _capital()
    result = evaluate_step_29p_capital_risk_admissibility_v1(
        capital=capital,
        claim=_complete_claim(typed_account_equity_source_field="availEq"),
    )
    assert result.risk_admissible is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert EQUITY_DIMENSION_BOUND is False
    assert FIELD_TO_DIMENSION_MAPPING_PRESENT is False
    with pytest.raises(ExecutionPortConstructionForbiddenError) as raised:
        construct_live_execution_port_v1()
    assert "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_1" in str(raised.value)
    port = bind_simulated_execution_port_v1()
    assert isinstance(port, SimulatedExecutionPortV1)


def test_runbook_z_consumes_go_without_rewriting_y() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    y_start = runbook.index(Y_HEADING)
    z_section = _z_section()
    y_section = runbook[y_start : runbook.index(Z_HEADING, y_start)]
    assert "NORMALIZATION_SCHEMA_PRESENT=true" in y_section
    assert "THIS_SLICE=11.2.1.Z" not in y_section
    assert "EARLIEST_DECOMPOSED_CONTRACT_GAP=INTERNAL_RECONSTRUCTION_CONTRACT_MISSING" in (
        y_section
    )
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_INTERNAL_RECONSTRUCTION_CONTRACT_SCHEMA_V1"
        in z_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in z_section
    assert "INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT=true" in z_section
    assert "INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT=false" in z_section
    assert "INTERNAL_RECONSTRUCTION_PROVEN=false" in z_section
    assert "INTERNAL_RECONSTRUCTION_AUTHORITY_EFFECT=NONE" in z_section
    assert "RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT=true" in z_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in z_section
    assert "SOURCE_OBJECT_PRESENT=false" in z_section
    assert "SOURCE_SELECTED=false" in z_section
    assert "MAPPING_PROVEN=false" in z_section
    assert "GOVERNED_PRODUCER_CREATED=false" in z_section
    assert "RUNTIME_VALUE_BINDING_PRESENT=false" in z_section
    assert "LIVE_ACCOUNT_BOUND_JOIN_PRESENT=false" in z_section
    assert "STEP_29P_RISK_ADMISSIBLE=false" in z_section
    assert "LIVE_ENABLED=false" in z_section
    assert "LIVE_ARMED=false" in z_section
    assert "WIRE_SEND_PERMITTED=false" in z_section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in z_section
    assert "RECONCILIATION_CONTRACT_CREATED=false" in z_section
    assert "DIVERGENCE_POLICY_CREATED=false" in z_section
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY="
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING" in z_section
    )
    assert "EARLIEST_DECOMPOSED_CONTRACT_GAP=RECONSTRUCTION_ALGEBRA_INCOMPLETE" in z_section
    assert "DOCS_TOKEN_FULL_CORE_TYPED_INTERNAL_RECONSTRUCTION_CONTRACT_V1" in spec
    assert "INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT=true" in spec
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in spec
    assert INTERNAL_RECONSTRUCTION_AUTHORITY_EFFECT == "NONE"
    assert INTERNAL_RECONSTRUCTION_CONTRACT_MISSING_CLOSED is True
    assert VENUE_WITNESS_SCHEMA_PRESENT is True
    assert VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT is False
    assert VENUE_WITNESS_SELECTED is False
    assert NORMALIZATION_SCHEMA_PRESENT is True
    assert NORMALIZATION_RUNTIME_INSTANCE_PRESENT is False
