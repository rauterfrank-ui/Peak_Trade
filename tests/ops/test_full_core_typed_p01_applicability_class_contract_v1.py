"""Typed P01 applicability class ratification. No predicate. No producer."""

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
    P01_APPLICABILITY_CLASS,
    P01_APPLICABILITY_CLASS_CONTRACT_AUTHORITY_EFFECT,
    P01_APPLICABILITY_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_APPLICABILITY_CLASS_CONTRACT_SCHEMA_PRESENT,
    P01_APPLICABILITY_CLASS_RESOLVED,
    P01_APPLICABILITY_CLASS_SELECTED_OPTION,
    P01_APPLICABILITY_RESOLVED,
    P01_APPLICABILITY_STATE_MODEL,
    P01_APPLICATION_PREDICATE,
    P01_APPLICATION_PREDICATE_RESOLVED,
    P01_COMBINATION_PRECEDENCE_RESOLVED,
    P01_EXACT_MEMBER_COUNT,
    P01_EXACT_MEMBER_IDENTITY_SET,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED,
    P01_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_RESOLVED,
    P01_VALUE_UNIT_CLASS,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    P01_ZERO_ABSENCE_NA_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SOURCE_SELECTED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_DECOMPOSED_CONTRACT_GAP,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    P01_ABSENCE_SEMANTICS_RESOLVED,
    P01_APPLICABILITY_IS_DISTINCT_FROM_ABSENCE,
    P01_APPLICABILITY_IS_DISTINCT_FROM_NOT_APPLICABLE_VALUE_ENCODING,
    P01_APPLICABILITY_IS_DISTINCT_FROM_VALUE,
    P01_APPLICABILITY_IS_DISTINCT_FROM_ZERO,
    P01_INPUT_PRECONDITIONS_RESOLVED,
    P01_OPTIONALITY_RESOLVED,
    P01_RECONSTRUCTION_STATE_PRECONDITIONS_RESOLVED,
    P01_REQUIREDNESS_RESOLVED,
    P01_ZERO_SEMANTICS_RESOLVED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_exact_member_identity_contract_v1 import (
    MEMBER_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_applicability_class_contract_v1 import (
    APPLICABILITY_CLASS,
    APPLICABILITY_STATE_MODEL,
    APPLICATION_PREDICATE,
    RATIFICATION_SCOPE,
    REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS,
    SELECTED_OPTION,
    STATE_APPLIES,
    STATE_DOES_NOT_APPLY,
    STATE_UNKNOWN_FAIL_CLOSED,
    P01ApplicabilityClassContractError,
    P01ApplicabilityClassContractV1,
    build_p01_applicability_class_contract_v1,
    reject_p01_applies_as_valid_numeric_value_v1,
    reject_p01_applicability_authority_from_forbidden_surface_v1,
    reject_p01_applicability_class_as_formula_v1,
    reject_p01_applicability_inherited_from_u04_u05_u06_v1,
    reject_p01_does_not_apply_as_numeric_zero_v1,
    reject_p01_missing_as_does_not_apply_v1,
    reject_p01_missing_as_zero_v1,
    reject_p01_unknown_as_does_not_apply_v1,
    reject_p01_unknown_as_zero_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_value_unit_class_contract_v1 import (
    VALUE_UNIT_CLASS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_P01_APPLICABILITY_CLASS_CONTRACT_V1.md"
AL_HEADING = "11.2.1.AL FULL_CORE_TYPED_P01_VALUE_UNIT_CLASS_CONTRACT"
AM_HEADING = "11.2.1.AM FULL_CORE_TYPED_P01_APPLICABILITY_CLASS_CONTRACT"
AN_HEADING = "11.2.1.AN FULL_CORE_TYPED_P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT"


def _contract() -> P01ApplicabilityClassContractV1:
    return build_p01_applicability_class_contract_v1(
        p01_applicability_class_contract_id="SYNTHETIC_P01_APPLICABILITY_CLASS_CONTRACT_ID"
    )


def _am_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    am_start = runbook.index(AM_HEADING)
    return runbook[am_start : runbook.index(AN_HEADING, am_start)]


def test_p01_applicability_class_contract_constructs() -> None:
    contract = _contract()
    assert isinstance(contract, P01ApplicabilityClassContractV1)
    assert SCHEMA_CLASS == "P01_APPLICABILITY_CLASS_CONTRACT_V1"
    assert contract.member_id == MEMBER_ID
    assert contract.member_id == "P01M_GOVERNED_DEPLOYABILITY_CONSERVATISM_REDUCTION"
    assert contract.p01_value_unit_class == VALUE_UNIT_CLASS
    assert contract.p01_value_unit_class == "ABSOLUTE_MONETARY_REDUCTION_AMOUNT"
    assert contract.p01_applicability_class == APPLICABILITY_CLASS
    assert contract.p01_applicability_class == "GOVERNED_CONDITIONAL"
    assert contract.p01_applicability_state_model == APPLICABILITY_STATE_MODEL
    assert contract.p01_applicability_state_model == "APPLIES_DOES_NOT_APPLY_UNKNOWN_FAIL_CLOSED"
    assert contract.p01_applicability_state_applies == STATE_APPLIES
    assert contract.p01_applicability_state_does_not_apply == STATE_DOES_NOT_APPLY
    assert contract.p01_applicability_state_unknown_fail_closed == STATE_UNKNOWN_FAIL_CLOSED
    assert contract.ratification_scope == RATIFICATION_SCOPE
    assert contract.selected_option == SELECTED_OPTION
    assert contract.p01_term_set_resolved_status == "true"
    assert contract.p01_value_unit_class_resolved_status == "true"
    assert contract.p01_applicability_class_resolved_status == "true"
    assert contract.p01_application_predicate_resolved_status == "false"
    assert contract.p01_application_predicate == APPLICATION_PREDICATE
    assert contract.p01_application_predicate == "UNSPECIFIED_FAIL_CLOSED"
    assert contract.p01_runtime_instance_present == "false"
    assert contract.p01_authority_effect == "NONE"
    assert P01_TERM_SET_RESOLVED is True
    assert P01_VALUE_UNIT_CLASS_RESOLVED is True
    assert P01_VALUE_UNIT_CLASS == "ABSOLUTE_MONETARY_REDUCTION_AMOUNT"
    assert P01_APPLICABILITY_CLASS_RESOLVED is True
    assert P01_APPLICABILITY_CLASS == "GOVERNED_CONDITIONAL"
    assert P01_APPLICABILITY_STATE_MODEL == "APPLIES_DOES_NOT_APPLY_UNKNOWN_FAIL_CLOSED"
    assert P01_APPLICABILITY_CLASS_SELECTED_OPTION == "P01_OP_APPLICABILITY_GOVERNED_CONDITIONAL_V1"
    assert P01_APPLICATION_PREDICATE_RESOLVED is True
    assert P01_APPLICATION_PREDICATE == "GOVERNED_P01_REDUCTION_DIRECTIVE_PREDICATE_V1"
    assert P01_EXACT_MEMBER_COUNT == 1
    assert P01_EXACT_MEMBER_IDENTITY_SET == MEMBER_ID
    assert P01_APPLICABILITY_CLASS_CONTRACT_SCHEMA_PRESENT is True
    assert P01_APPLICABILITY_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT is False
    assert P01_APPLICABILITY_CLASS_CONTRACT_AUTHORITY_EFFECT == "NONE"
    assert P01_RUNTIME_INSTANCE_PRESENT is False


def test_object_is_immutable() -> None:
    contract = _contract()
    with pytest.raises(FrozenInstanceError):
        contract.p01_applicability_class_resolved_status = "false"  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = _contract()
    second = _contract()
    assert first.provenance_digest == second.provenance_digest


def test_class_does_not_ratify_predicate_formula_operator_or_sign() -> None:
    contract = _contract()
    assert contract.class_does_not_ratify_predicate == "true"
    assert contract.class_does_not_ratify_formula == "true"
    assert contract.class_does_not_ratify_operator == "true"
    assert contract.class_does_not_ratify_sign == "true"
    assert contract.class_does_not_ratify_source_mapping == "true"
    assert contract.class_does_not_close_p01_term_semantics == "true"
    assert contract.class_does_not_close_haircut_reserve_depletion_unspecified == "true"
    assert P01_TERM_SEMANTICS_RESOLVED is True
    assert P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is True
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert P01_APPLICABILITY_RESOLVED is True
    assert P01_APPLICATION_PREDICATE_RESOLVED is True
    assert P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED is True
    assert P01_ZERO_ABSENCE_NA_RESOLVED is True
    assert P01_REQUIREDNESS_RESOLVED is True
    assert P01_OPTIONALITY_RESOLVED is True
    assert P01_ZERO_SEMANTICS_RESOLVED is True
    assert P01_ABSENCE_SEMANTICS_RESOLVED is True
    assert P01_COMBINATION_PRECEDENCE_RESOLVED is True
    assert "P01_APPLICATION_PREDICATE_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert contract.remaining_unresolved_semantics == REMAINING_UNRESOLVED_SEMANTICS
    with pytest.raises(P01ApplicabilityClassContractError) as formula:
        reject_p01_applicability_class_as_formula_v1(formula="equity = equity - P01")
    assert "P01_CLASS_IS_NOT_FORMULA" in str(formula.value)


def test_unknown_and_missing_cannot_coerce() -> None:
    contract = _contract()
    assert contract.unknown_cannot_become_false == "true"
    assert contract.unknown_cannot_become_does_not_apply == "true"
    assert contract.unknown_cannot_become_not_applicable == "true"
    assert contract.unknown_cannot_become_zero == "true"
    assert contract.missing_cannot_become_zero == "true"
    assert contract.missing_cannot_auto_become_does_not_apply == "true"
    assert contract.does_not_apply_is_not_numeric_zero == "true"
    assert contract.applies_does_not_imply_valid_numeric_value == "true"
    with pytest.raises(P01ApplicabilityClassContractError) as unknown_na:
        reject_p01_unknown_as_does_not_apply_v1(applicability_state="DOES_NOT_APPLY")
    assert "P01_UNKNOWN_CANNOT_BECOME_DOES_NOT_APPLY" in str(unknown_na.value)
    with pytest.raises(P01ApplicabilityClassContractError) as unknown_zero:
        reject_p01_unknown_as_zero_v1(applicability_state="0")
    assert "P01_UNKNOWN_CANNOT_BECOME_ZERO" in str(unknown_zero.value)
    with pytest.raises(P01ApplicabilityClassContractError) as missing_zero:
        reject_p01_missing_as_zero_v1(numeric_state="MISSING")
    assert "P01_MISSING_CANNOT_BECOME_ZERO" in str(missing_zero.value)
    with pytest.raises(P01ApplicabilityClassContractError) as missing_dna:
        reject_p01_missing_as_does_not_apply_v1(applicability_state="missing")
    assert "P01_MISSING_CANNOT_AUTO_BECOME_DOES_NOT_APPLY" in str(missing_dna.value)
    with pytest.raises(P01ApplicabilityClassContractError) as dna_zero:
        reject_p01_does_not_apply_as_numeric_zero_v1(numeric_state="0")
    assert "P01_DOES_NOT_APPLY_IS_NOT_NUMERIC_ZERO" in str(dna_zero.value)
    with pytest.raises(P01ApplicabilityClassContractError) as applies_value:
        reject_p01_applies_as_valid_numeric_value_v1(numeric_state="PRESENT_NONZERO")
    assert "P01_APPLIES_DOES_NOT_IMPLY_VALID_NUMERIC_VALUE" in str(applies_value.value)


def test_applicability_is_distinct_from_value_zero_and_absence() -> None:
    contract = _contract()
    assert contract.p01_applicability_is_distinct_from_value == "true"
    assert contract.p01_applicability_is_distinct_from_zero == "true"
    assert contract.p01_applicability_is_distinct_from_absence == "true"
    assert contract.p01_applicability_is_distinct_from_not_applicable_value_encoding == "true"
    assert P01_APPLICABILITY_IS_DISTINCT_FROM_VALUE is True
    assert P01_APPLICABILITY_IS_DISTINCT_FROM_ZERO is True
    assert P01_APPLICABILITY_IS_DISTINCT_FROM_ABSENCE is True
    assert P01_APPLICABILITY_IS_DISTINCT_FROM_NOT_APPLICABLE_VALUE_ENCODING is True
    assert P01_INPUT_PRECONDITIONS_RESOLVED is True
    assert P01_RECONSTRUCTION_STATE_PRECONDITIONS_RESOLVED is True


def test_forbidden_surfaces_are_not_applicability_authority() -> None:
    contract = _contract()
    assert contract.u04_u05_u06_applicability_inheritance_forbidden == "true"
    assert contract.venue_raw_is_not_p01_applicability_authority == "true"
    assert contract.step_29p_is_not_p01_applicability_authority == "true"
    assert contract.live_account_bound_is_not_p01_applicability_authority == "true"
    assert contract.master_v2_is_not_p01_applicability_authority == "true"
    assert contract.double_play_is_not_p01_applicability_authority == "true"
    assert contract.top20_is_not_p01_applicability_authority == "true"
    assert contract.learning_is_not_p01_applicability_authority == "true"
    assert contract.full_core_autonomy_is_not_p01_applicability_authority == "true"
    assert contract.class_is_not_unconditional_always_on == "true"
    assert contract.class_is_not_unconditional_never_on == "true"
    for inferred in ("ALWAYS_APPLIES", "NEVER_APPLIES", "OPTIONAL", "U04", "availEq"):
        with pytest.raises(P01ApplicabilityClassContractError) as raised:
            build_p01_applicability_class_contract_v1(
                p01_applicability_class_contract_id="SYNTHETIC_P01_APPLICABILITY_CLASS_CONTRACT_ID",
                p01_applicability_class=inferred,
            )
        assert "P01_APPLICABILITY_CLASS_INFERRED_FORBIDDEN" in str(
            raised.value
        ) or "P01_APPLICABILITY_CLASS_MISMATCH" in str(raised.value)
    with pytest.raises(P01ApplicabilityClassContractError) as u04:
        reject_p01_applicability_inherited_from_u04_u05_u06_v1(source="U04")
    assert "P01_U04_U05_U06_APPLICABILITY_INHERITANCE_FORBIDDEN" in str(u04.value)
    with pytest.raises(P01ApplicabilityClassContractError) as venue:
        reject_p01_applicability_authority_from_forbidden_surface_v1(source="availEq")
    assert "P01_FORBIDDEN_APPLICABILITY_AUTHORITY" in str(
        venue.value
    ) or "P01_APPLICABILITY_CLASS_INFERRED_FORBIDDEN" in str(venue.value)


def test_missing_and_malformed_inputs_fail_closed() -> None:
    with pytest.raises(P01ApplicabilityClassContractError) as missing:
        build_p01_applicability_class_contract_v1(
            p01_applicability_class_contract_id="SYNTHETIC_P01_APPLICABILITY_CLASS_CONTRACT_ID",
            member_id=None,
        )
    assert "P01_FIELD_MISSING:member_id" in str(missing.value)
    with pytest.raises(P01ApplicabilityClassContractError) as malformed:
        build_p01_applicability_class_contract_v1(
            p01_applicability_class_contract_id="SYNTHETIC_P01_APPLICABILITY_CLASS_CONTRACT_ID",
            member_id=False,
        )
    assert "P01_FIELD_NOT_STRING:member_id" in str(malformed.value)


def test_gap_dag_and_live_pins_remain_fail_closed() -> None:
    dag = live_admission_gap_dag_v1()
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED"
    assert dag["P01_TERM_SET_RESOLVED"] is True
    assert dag["P01_VALUE_UNIT_CLASS_RESOLVED"] is True
    assert dag["P01_VALUE_UNIT_CLASS"] == "ABSOLUTE_MONETARY_REDUCTION_AMOUNT"
    assert dag["P01_APPLICABILITY_CLASS_RESOLVED"] is True
    assert dag["P01_APPLICABILITY_CLASS"] == "GOVERNED_CONDITIONAL"
    assert dag["P01_APPLICABILITY_STATE_MODEL"] == "APPLIES_DOES_NOT_APPLY_UNKNOWN_FAIL_CLOSED"
    assert dag["P01_APPLICATION_PREDICATE_RESOLVED"] is True
    assert dag["P01_APPLICATION_PREDICATE"] == "GOVERNED_P01_REDUCTION_DIRECTIVE_PREDICATE_V1"
    assert dag["P01_EXACT_MEMBER_COUNT"] == 1
    assert dag["P01_EXACT_MEMBER_IDENTITY_SET"] == MEMBER_ID
    assert dag["P01_APPLICABILITY_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["P01_APPLICABILITY_CLASS_CONTRACT_AUTHORITY_EFFECT"] == "NONE"
    assert dag["P01_TERM_SEMANTICS_RESOLVED"] is True
    assert dag["P01_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["P01_APPLICABILITY_RESOLVED"] is True
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_runbook_am_consumes_go_without_rewriting_al() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    am_section = _am_section()
    al_start = runbook.index(AL_HEADING)
    al_section = runbook[al_start : runbook.index(AM_HEADING, al_start)]
    assert "P01_VALUE_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT=true" in al_section
    assert "THIS_SLICE=11.2.1.AM" not in al_section
    assert "P01_APPLICABILITY_CLASS_RESOLVED=true" not in al_section
    assert "EARLIEST_NARROW_P01_DEPENDENCY=P01_APPLICABILITY_UNSPECIFIED" in al_section
    assert "P01M_GOVERNED_DEPLOYABILITY_CONSERVATISM_REDUCTION" in al_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_P01_APPLICABILITY_CLASS_RATIFICATION_V1"
        in am_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in am_section
    assert "P01_APPLICABILITY_CLASS_CONTRACT_SCHEMA_PRESENT=true" in am_section
    assert "P01_TERM_SET_RESOLVED=true" in am_section
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=true" in am_section
    assert "P01_APPLICABILITY_CLASS_RESOLVED=true" in am_section
    assert "P01_APPLICABILITY_CLASS=GOVERNED_CONDITIONAL" in am_section
    assert "P01_APPLICABILITY_STATE_MODEL=APPLIES_DOES_NOT_APPLY_UNKNOWN_FAIL_CLOSED" in am_section
    assert "P01_APPLICATION_PREDICATE_RESOLVED=false" in am_section
    assert "P01_APPLICATION_PREDICATE=UNSPECIFIED_FAIL_CLOSED" in am_section
    assert "P01_APPLICABILITY_RESOLVED=false" in am_section
    assert "P01_APPLICABILITY_IS_DISTINCT_FROM_VALUE=true" in am_section
    assert "P01_APPLICABILITY_IS_DISTINCT_FROM_ZERO=true" in am_section
    assert "P01_APPLICABILITY_IS_DISTINCT_FROM_ABSENCE=true" in am_section
    assert "P01_REQUIREDNESS_RESOLVED=false" in am_section
    assert "P01_OPTIONALITY_RESOLVED=false" in am_section
    assert "P01_ZERO_SEMANTICS_RESOLVED=false" in am_section
    assert "P01_ABSENCE_SEMANTICS_RESOLVED=false" in am_section
    assert "P01_ZERO_ABSENCE_NA_RESOLVED=false" in am_section
    assert "MASTER_V2_IS_NOT_P01_APPLICABILITY_AUTHORITY=true" in am_section
    assert "DOUBLE_PLAY_IS_NOT_P01_APPLICABILITY_AUTHORITY=true" in am_section
    assert "TOP20_IS_NOT_P01_APPLICABILITY_AUTHORITY=true" in am_section
    assert "LEARNING_IS_NOT_P01_APPLICABILITY_AUTHORITY=true" in am_section
    assert "FULL_CORE_AUTONOMY_IS_NOT_P01_APPLICABILITY_AUTHORITY=true" in am_section
    assert "VENUE_RAW_IS_NOT_P01_APPLICABILITY_AUTHORITY=true" in am_section
    assert "STEP_29P_IS_NOT_P01_APPLICABILITY_AUTHORITY=true" in am_section
    assert "LIVE_ACCOUNT_BOUND_IS_NOT_P01_APPLICABILITY_AUTHORITY=true" in am_section
    assert "U04_U05_U06_APPLICABILITY_INHERITANCE_FORBIDDEN=true" in am_section
    assert "THIS_SLICE=11.2.1.AM" in am_section
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in am_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED=false" in am_section
    assert "P01_RUNTIME_INSTANCE_PRESENT=false" in am_section
    assert "P01_AUTHORITY_EFFECT=NONE" in am_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in am_section
    assert "CANONICAL_FORMULA_PROVEN=false" in am_section
    assert "SOURCE_SELECTED=false" in am_section
    assert "MAPPING_PROVEN=false" in am_section
    assert "GOVERNED_PRODUCER_CREATED=false" in am_section
    assert "EXISTING_UNIVERSE_TOPOLOGY_PRESERVED=true" in am_section
    assert "EXISTING_AUTHORITY_GRAPH_PRESERVED=true" in am_section
    assert "NEW_UNIVERSE_CREATED=false" in am_section
    assert "NEW_AUTHORITY_OWNER_CREATED=false" in am_section
    assert "NEW_PARALLEL_PRODUCER_CREATED=false" in am_section
    assert (
        "EARLIEST_DECOMPOSED_CONTRACT_GAP=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in am_section
    )
    assert "EARLIEST_NARROW_P01_DEPENDENCY=P01_APPLICATION_PREDICATE_UNSPECIFIED" in am_section
    assert "DOCS_TOKEN_FULL_CORE_TYPED_P01_APPLICABILITY_CLASS_CONTRACT_V1" in spec
    assert "P01_APPLICABILITY_CLASS_RESOLVED=true" in spec
    assert "P01_APPLICATION_PREDICATE_RESOLVED=false" in spec
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in spec
    assert "CANONICAL_FORMULA_PROVEN=false" in spec
