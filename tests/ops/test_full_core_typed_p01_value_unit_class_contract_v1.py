"""Typed P01 value unit class ratification. No formula. No producer."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    GOVERNED_PRODUCER_CREATED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    P01_APPLICABILITY_RESOLVED,
    P01_COMBINATION_PRECEDENCE_RESOLVED,
    P01_DIRECT_ADDITIVE_SUBTRACTION_COMPATIBLE,
    P01_EXACT_MEMBER_COUNT,
    P01_EXACT_MEMBER_IDENTITY_SET,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED,
    P01_PARENT_DIMENSION_COMPATIBILITY,
    P01_REQUIRES_DIMENSIONAL_TRANSFORMATION,
    P01_RUNTIME_INSTANCE_PRESENT,
    P01_SEMANTIC_DIMENSION,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_RESOLVED,
    P01_VALUE_UNIT_CLASS,
    P01_VALUE_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT,
    P01_VALUE_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_VALUE_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    P01_VALUE_UNIT_CLASS_SELECTED_OPTION,
    P01_ZERO_ABSENCE_NA_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SOURCE_SELECTED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_DECOMPOSED_CONTRACT_GAP,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_exact_member_identity_contract_v1 import (
    MEMBER_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_value_unit_class_contract_v1 import (
    PARENT_DIMENSION_COMPATIBILITY,
    RATIFICATION_SCOPE,
    REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS,
    SELECTED_OPTION,
    SEMANTIC_DIMENSION,
    VALUE_UNIT_CLASS,
    P01ValueUnitClassContractError,
    P01ValueUnitClassContractV1,
    build_p01_value_unit_class_contract_v1,
    reject_p01_inferred_value_unit_class_v1,
    reject_p01_unit_as_formula_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_P01_VALUE_UNIT_CLASS_CONTRACT_V1.md"
AK_HEADING = "11.2.1.AK FULL_CORE_TYPED_P01_EXACT_MEMBER_IDENTITY_CONTRACT"
AL_HEADING = "11.2.1.AL FULL_CORE_TYPED_P01_VALUE_UNIT_CLASS_CONTRACT"
AM_HEADING = "11.2.1.AM FULL_CORE_TYPED_P01_APPLICABILITY_CLASS_CONTRACT"


def _contract() -> P01ValueUnitClassContractV1:
    return build_p01_value_unit_class_contract_v1(
        p01_value_unit_class_contract_id="SYNTHETIC_P01_VALUE_UNIT_CLASS_CONTRACT_ID"
    )


def _al_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    al_start = runbook.index(AL_HEADING)
    return runbook[al_start : runbook.index(AM_HEADING, al_start)]


def test_p01_value_unit_class_contract_constructs() -> None:
    contract = _contract()
    assert isinstance(contract, P01ValueUnitClassContractV1)
    assert SCHEMA_CLASS == "P01_VALUE_UNIT_CLASS_CONTRACT_V1"
    assert contract.member_id == MEMBER_ID
    assert contract.p01_value_unit_class == VALUE_UNIT_CLASS
    assert contract.p01_value_unit_class == "ABSOLUTE_MONETARY_REDUCTION_AMOUNT"
    assert contract.p01_semantic_dimension == SEMANTIC_DIMENSION
    assert contract.p01_semantic_dimension == "PARENT_EQUITY_DIMENSION_REDUCTION_AMOUNT"
    assert contract.p01_parent_dimension_compatibility == PARENT_DIMENSION_COMPATIBILITY
    assert contract.ratification_scope == RATIFICATION_SCOPE
    assert contract.selected_option == SELECTED_OPTION
    assert contract.p01_term_set_resolved_status == "true"
    assert contract.p01_value_unit_class_resolved_status == "true"
    assert contract.p01_requires_dimensional_transformation == "false"
    assert contract.p01_direct_additive_subtraction_compatible == "true"
    assert contract.p01_runtime_instance_present == "false"
    assert contract.p01_authority_effect == "NONE"
    assert P01_TERM_SET_RESOLVED is True
    assert P01_VALUE_UNIT_CLASS_RESOLVED is True
    assert P01_VALUE_UNIT_CLASS == "ABSOLUTE_MONETARY_REDUCTION_AMOUNT"
    assert P01_SEMANTIC_DIMENSION == "PARENT_EQUITY_DIMENSION_REDUCTION_AMOUNT"
    assert P01_PARENT_DIMENSION_COMPATIBILITY == (
        "SAME_DIMENSION_CLASS_AS_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
    )
    assert P01_REQUIRES_DIMENSIONAL_TRANSFORMATION is False
    assert P01_DIRECT_ADDITIVE_SUBTRACTION_COMPATIBLE is True
    assert P01_VALUE_UNIT_CLASS_SELECTED_OPTION == "P01_OP_VU_ABSOLUTE_MONETARY_REDUCTION_V1"
    assert P01_EXACT_MEMBER_COUNT == 1
    assert P01_EXACT_MEMBER_IDENTITY_SET == MEMBER_ID
    assert P01_VALUE_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT is True
    assert P01_VALUE_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT is False
    assert P01_VALUE_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT == "NONE"
    assert P01_RUNTIME_INSTANCE_PRESENT is False


def test_object_is_immutable() -> None:
    contract = _contract()
    with pytest.raises(FrozenInstanceError):
        contract.p01_value_unit_class_resolved_status = "false"  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = _contract()
    second = _contract()
    assert first.provenance_digest == second.provenance_digest


def test_unit_class_does_not_ratify_formula_operator_or_sign() -> None:
    contract = _contract()
    assert contract.unit_does_not_ratify_formula == "true"
    assert contract.unit_does_not_ratify_operator == "true"
    assert contract.unit_does_not_ratify_sign == "true"
    assert contract.unit_does_not_ratify_applicability == "true"
    assert contract.unit_does_not_ratify_source_mapping == "true"
    assert contract.unit_does_not_close_p01_term_semantics == "true"
    assert contract.unit_does_not_close_haircut_reserve_depletion_unspecified == "true"
    assert P01_TERM_SEMANTICS_RESOLVED is False
    assert P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert P01_APPLICABILITY_RESOLVED is False
    assert P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED is False
    assert P01_ZERO_ABSENCE_NA_RESOLVED is False
    assert P01_COMBINATION_PRECEDENCE_RESOLVED is False
    assert "P01_VALUE_UNIT_CLASS_UNSPECIFIED" not in contract.remaining_unresolved_semantics
    assert "P01_APPLICABILITY_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert contract.remaining_unresolved_semantics == REMAINING_UNRESOLVED_SEMANTICS
    with pytest.raises(P01ValueUnitClassContractError) as formula:
        reject_p01_unit_as_formula_v1(formula="equity = equity - P01")
    assert "P01_UNIT_IS_NOT_FORMULA" in str(formula.value)


def test_distinctness_and_negative_unit_pins_remain() -> None:
    contract = _contract()
    assert contract.p01_unit_identity_is_distinct_from_authority_identity == "true"
    assert contract.p01_unit_identity_is_distinct_from_member_identity == "true"
    assert contract.p01_settlement_currency_is_not_unit_identity == "true"
    assert contract.p01_parent_dimension_is_not_authority_source == "true"
    assert contract.p01_value_unit_class_is_not_ratio == "true"
    assert contract.p01_value_unit_class_is_not_percentage == "true"
    assert contract.p01_value_unit_class_is_not_bps == "true"
    assert contract.p01_value_unit_class_is_not_contracts_qty == "true"
    assert contract.p01_value_unit_class_is_not_python_numeric_type == "true"
    assert (
        contract.p01m_governed_deployability_conservatism_reduction_is_not_haircut_alias == "true"
    )
    assert contract.p01m_governed_deployability_conservatism_reduction_is_not_u04 == "true"
    assert contract.p01m_governed_deployability_conservatism_reduction_is_not_availeq == "true"
    for inferred in ("USDC", "ratio", "percentage", "bps", "contracts qty", "float"):
        with pytest.raises(P01ValueUnitClassContractError) as raised:
            reject_p01_inferred_value_unit_class_v1(value_unit_class=inferred)
        assert "P01_VALUE_UNIT_CLASS_INFERRED_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01ValueUnitClassContractError) as extra:
        build_p01_value_unit_class_contract_v1(
            p01_value_unit_class_contract_id="SYNTHETIC_P01_VALUE_UNIT_CLASS_CONTRACT_ID",
            p01_value_unit_class="USDC",
        )
    assert "P01_VALUE_UNIT_CLASS_INFERRED_FORBIDDEN" in str(
        extra.value
    ) or "P01_VALUE_UNIT_CLASS_MISMATCH" in str(extra.value)


def test_missing_and_malformed_inputs_fail_closed() -> None:
    with pytest.raises(P01ValueUnitClassContractError) as missing:
        build_p01_value_unit_class_contract_v1(
            p01_value_unit_class_contract_id="SYNTHETIC_P01_VALUE_UNIT_CLASS_CONTRACT_ID",
            member_id=None,
        )
    assert "P01_FIELD_MISSING:member_id" in str(missing.value)
    with pytest.raises(P01ValueUnitClassContractError) as malformed:
        build_p01_value_unit_class_contract_v1(
            p01_value_unit_class_contract_id="SYNTHETIC_P01_VALUE_UNIT_CLASS_CONTRACT_ID",
            member_id=False,
        )
    assert "P01_FIELD_NOT_STRING:member_id" in str(malformed.value)


def test_gap_dag_and_live_pins_remain_fail_closed() -> None:
    dag = live_admission_gap_dag_v1()
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED"
    assert dag["P01_TERM_SET_RESOLVED"] is True
    assert dag["P01_VALUE_UNIT_CLASS_RESOLVED"] is True
    assert dag["P01_VALUE_UNIT_CLASS"] == "ABSOLUTE_MONETARY_REDUCTION_AMOUNT"
    assert dag["P01_SEMANTIC_DIMENSION"] == "PARENT_EQUITY_DIMENSION_REDUCTION_AMOUNT"
    assert dag["P01_REQUIRES_DIMENSIONAL_TRANSFORMATION"] is False
    assert dag["P01_DIRECT_ADDITIVE_SUBTRACTION_COMPATIBLE"] is True
    assert dag["P01_EXACT_MEMBER_COUNT"] == 1
    assert dag["P01_EXACT_MEMBER_IDENTITY_SET"] == MEMBER_ID
    assert dag["P01_VALUE_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["P01_VALUE_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT"] == "NONE"
    assert dag["P01_TERM_SEMANTICS_RESOLVED"] is False
    assert dag["P01_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["P01_APPLICABILITY_RESOLVED"] is False
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_runbook_al_consumes_go_without_rewriting_ak() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    al_section = _al_section()
    ak_start = runbook.index(AK_HEADING)
    ak_section = runbook[ak_start : runbook.index(AL_HEADING, ak_start)]
    assert "P01_EXACT_MEMBER_IDENTITY_CONTRACT_SCHEMA_PRESENT=true" in ak_section
    assert "THIS_SLICE=11.2.1.AL" not in ak_section
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=false" in ak_section
    assert "P01M_GOVERNED_DEPLOYABILITY_CONSERVATISM_REDUCTION" in ak_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_P01_VALUE_UNIT_CLASS_RATIFICATION_V1" in al_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in al_section
    assert "P01_VALUE_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT=true" in al_section
    assert "P01_TERM_SET_RESOLVED=true" in al_section
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=true" in al_section
    assert "P01_VALUE_UNIT_CLASS=ABSOLUTE_MONETARY_REDUCTION_AMOUNT" in al_section
    assert "P01_SEMANTIC_DIMENSION=PARENT_EQUITY_DIMENSION_REDUCTION_AMOUNT" in al_section
    assert "P01_REQUIRES_DIMENSIONAL_TRANSFORMATION=false" in al_section
    assert "P01_DIRECT_ADDITIVE_SUBTRACTION_COMPATIBLE=true" in al_section
    assert "P01_UNIT_IDENTITY_IS_DISTINCT_FROM_AUTHORITY_IDENTITY=true" in al_section
    assert "equity = equity - P01" in al_section
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in al_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED=false" in al_section
    assert "P01_RUNTIME_INSTANCE_PRESENT=false" in al_section
    assert "P01_AUTHORITY_EFFECT=NONE" in al_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in al_section
    assert "CANONICAL_FORMULA_PROVEN=false" in al_section
    assert "SOURCE_SELECTED=false" in al_section
    assert "MAPPING_PROVEN=false" in al_section
    assert "GOVERNED_PRODUCER_CREATED=false" in al_section
    assert "EXISTING_UNIVERSE_TOPOLOGY_PRESERVED=true" in al_section
    assert "EXISTING_AUTHORITY_GRAPH_PRESERVED=true" in al_section
    assert "NEW_UNIVERSE_CREATED=false" in al_section
    assert "NEW_AUTHORITY_OWNER_CREATED=false" in al_section
    assert "NEW_PARALLEL_PRODUCER_CREATED=false" in al_section
    assert (
        "EARLIEST_DECOMPOSED_CONTRACT_GAP=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in al_section
    )
    assert "EARLIEST_NARROW_P01_DEPENDENCY=P01_APPLICABILITY_UNSPECIFIED" in al_section
    assert "DOCS_TOKEN_FULL_CORE_TYPED_P01_VALUE_UNIT_CLASS_CONTRACT_V1" in spec
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=true" in spec
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in spec
    assert "CANONICAL_FORMULA_PROVEN=false" in spec
