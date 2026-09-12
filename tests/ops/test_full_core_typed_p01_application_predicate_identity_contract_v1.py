"""Typed P01 application-predicate identity. No input domain. No producer."""

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
    P01_APPLICABILITY_CLASS_RESOLVED,
    P01_APPLICABILITY_RESOLVED,
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
    P01_APPLICATION_FALSE_RULE_RESOLVED,
    P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_AUTHORITY_EFFECT,
    P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_SCHEMA_PRESENT,
    P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED,
    P01_APPLICATION_PREDICATE_IDENTITY_SELECTED_OPTION,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED,
    P01_APPLICATION_PREDICATE_MODEL,
    P01_APPLICATION_TRUE_RULE_RESOLVED,
    P01_APPLICABILITY_DECISION_STATE_MODEL,
    P01_INPUT_PRECONDITIONS_RESOLVED,
    P01_OPTIONALITY_RESOLVED,
    P01_RECONSTRUCTION_STATE_PRECONDITIONS_RESOLVED,
    P01_REQUIREDNESS_RESOLVED,
    P01_ZERO_SEMANTICS_RESOLVED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_application_predicate_identity_contract_v1 import (
    DECISION_STATE_MODEL,
    PREDICATE_MODEL,
    RATIFICATION_SCOPE,
    REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS,
    SELECTED_OPTION,
    STATE_APPLIES,
    STATE_DOES_NOT_APPLY,
    STATE_UNKNOWN_FAIL_CLOSED,
    P01ApplicationPredicateIdentityContractError,
    P01ApplicationPredicateIdentityContractV1,
    build_p01_application_predicate_identity_contract_v1,
    reject_p01_application_predicate_authority_from_forbidden_surface_v1,
    reject_p01_application_predicate_identity_as_account_equity_authority_v1,
    reject_p01_application_predicate_identity_as_false_rule_v1,
    reject_p01_application_predicate_identity_as_formula_v1,
    reject_p01_application_predicate_identity_as_true_rule_v1,
    reject_p01_application_predicate_inherited_from_u04_u05_u06_v1,
    reject_p01_contradictory_decision_v1,
    reject_p01_malformed_decision_v1,
    reject_p01_unknown_or_missing_decision_v1,
    reject_p01_unsupported_decision_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_exact_member_identity_contract_v1 import (
    MEMBER_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_value_unit_class_contract_v1 import (
    VALUE_UNIT_CLASS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_V1.md"
)
AM_HEADING = "11.2.1.AM FULL_CORE_TYPED_P01_APPLICABILITY_CLASS_CONTRACT"
AN_HEADING = "11.2.1.AN FULL_CORE_TYPED_P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT"
AO_HEADING = "11.2.1.AO FULL_CORE_TYPED_P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT"


def _contract() -> P01ApplicationPredicateIdentityContractV1:
    return build_p01_application_predicate_identity_contract_v1(
        p01_application_predicate_identity_contract_id=(
            "SYNTHETIC_P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_ID"
        )
    )


def _an_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    an_start = runbook.index(AN_HEADING)
    return runbook[an_start : runbook.index(AO_HEADING, an_start)]


def test_p01_application_predicate_identity_contract_constructs() -> None:
    contract = _contract()
    assert isinstance(contract, P01ApplicationPredicateIdentityContractV1)
    assert SCHEMA_CLASS == "P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_V1"
    assert contract.member_id == MEMBER_ID
    assert contract.member_id == "P01M_GOVERNED_DEPLOYABILITY_CONSERVATISM_REDUCTION"
    assert contract.p01_value_unit_class == VALUE_UNIT_CLASS
    assert contract.p01_applicability_class == P01_APPLICABILITY_CLASS
    assert contract.p01_application_predicate_model == PREDICATE_MODEL
    assert contract.p01_application_predicate_model == "TYPED_GOVERNED_APPLICABILITY_DECISION_V1"
    assert contract.p01_applicability_decision_state_model == DECISION_STATE_MODEL
    assert contract.p01_applicability_decision_state_model == (
        "APPLIES_DOES_NOT_APPLY_UNKNOWN_FAIL_CLOSED"
    )
    assert contract.p01_applicability_decision_state_applies == STATE_APPLIES
    assert contract.p01_applicability_decision_state_does_not_apply == STATE_DOES_NOT_APPLY
    assert contract.p01_applicability_decision_state_unknown_fail_closed == (
        STATE_UNKNOWN_FAIL_CLOSED
    )
    assert contract.ratification_scope == RATIFICATION_SCOPE
    assert contract.selected_option == SELECTED_OPTION
    assert contract.p01_application_predicate_identity_resolved_status == "true"
    assert contract.p01_application_predicate_resolved_status == "false"
    assert contract.p01_application_predicate == P01_APPLICATION_PREDICATE
    assert contract.p01_application_predicate == "UNSPECIFIED_FAIL_CLOSED"
    assert contract.p01_runtime_instance_present == "false"
    assert contract.p01_authority_effect == "NONE"
    assert P01_TERM_SET_RESOLVED is True
    assert P01_VALUE_UNIT_CLASS_RESOLVED is True
    assert P01_VALUE_UNIT_CLASS == "ABSOLUTE_MONETARY_REDUCTION_AMOUNT"
    assert P01_APPLICABILITY_CLASS_RESOLVED is True
    assert P01_APPLICABILITY_CLASS == "GOVERNED_CONDITIONAL"
    assert P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED is True
    assert P01_APPLICATION_PREDICATE_MODEL == "TYPED_GOVERNED_APPLICABILITY_DECISION_V1"
    assert P01_APPLICABILITY_DECISION_STATE_MODEL == ("APPLIES_DOES_NOT_APPLY_UNKNOWN_FAIL_CLOSED")
    assert P01_APPLICATION_PREDICATE_IDENTITY_SELECTED_OPTION == (
        "P01_OP_APPLICATION_PREDICATE_TYPED_GOVERNED_APPLICABILITY_DECISION_V1"
    )
    assert P01_APPLICATION_PREDICATE_RESOLVED is False
    assert P01_APPLICATION_PREDICATE == "UNSPECIFIED_FAIL_CLOSED"
    assert P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED is False
    assert P01_APPLICATION_TRUE_RULE_RESOLVED is False
    assert P01_APPLICATION_FALSE_RULE_RESOLVED is False
    assert P01_EXACT_MEMBER_COUNT == 1
    assert P01_EXACT_MEMBER_IDENTITY_SET == MEMBER_ID
    assert P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_SCHEMA_PRESENT is True
    assert P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT is False
    assert P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_AUTHORITY_EFFECT == "NONE"
    assert P01_RUNTIME_INSTANCE_PRESENT is False


def test_object_is_immutable() -> None:
    contract = _contract()
    with pytest.raises(FrozenInstanceError):
        contract.p01_application_predicate_identity_resolved_status = "false"  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = _contract()
    second = _contract()
    assert first.provenance_digest == second.provenance_digest


def test_identity_does_not_ratify_input_true_false_formula_or_sign() -> None:
    contract = _contract()
    assert contract.identity_does_not_ratify_input_domain == "true"
    assert contract.identity_does_not_ratify_true_rule == "true"
    assert contract.identity_does_not_ratify_false_rule == "true"
    assert contract.identity_does_not_ratify_formula == "true"
    assert contract.identity_does_not_ratify_operator == "true"
    assert contract.identity_does_not_ratify_sign == "true"
    assert contract.identity_does_not_ratify_source_mapping == "true"
    assert contract.identity_does_not_close_p01_term_semantics == "true"
    assert P01_TERM_SEMANTICS_RESOLVED is False
    assert P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert P01_APPLICABILITY_RESOLVED is False
    assert P01_APPLICATION_PREDICATE_RESOLVED is False
    assert P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED is False
    assert P01_ZERO_ABSENCE_NA_RESOLVED is False
    assert P01_REQUIREDNESS_RESOLVED is False
    assert P01_OPTIONALITY_RESOLVED is False
    assert P01_ZERO_SEMANTICS_RESOLVED is False
    assert P01_ABSENCE_SEMANTICS_RESOLVED is False
    assert P01_COMBINATION_PRECEDENCE_RESOLVED is False
    assert "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_UNSPECIFIED" in (
        contract.remaining_unresolved_semantics
    )
    assert "P01_APPLICATION_TRUE_RULE_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert "P01_APPLICATION_FALSE_RULE_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert contract.remaining_unresolved_semantics == REMAINING_UNRESOLVED_SEMANTICS
    with pytest.raises(P01ApplicationPredicateIdentityContractError) as formula:
        reject_p01_application_predicate_identity_as_formula_v1(formula="equity = equity - P01")
    assert "P01_IDENTITY_IS_NOT_FORMULA" in str(formula.value)
    with pytest.raises(P01ApplicationPredicateIdentityContractError) as true_rule:
        reject_p01_application_predicate_identity_as_true_rule_v1(rule="ALWAYS_APPLIES")
    assert "P01_IDENTITY_IS_NOT_TRUE_RULE" in str(true_rule.value)
    with pytest.raises(P01ApplicationPredicateIdentityContractError) as false_rule:
        reject_p01_application_predicate_identity_as_false_rule_v1(rule="NEVER_APPLIES")
    assert "P01_IDENTITY_IS_NOT_FALSE_RULE" in str(false_rule.value)


def test_fail_closed_decision_semantics_are_exact() -> None:
    contract = _contract()
    assert contract.p01_applicability_decision_is_typed == "true"
    assert contract.p01_applicability_decision_is_governed == "true"
    assert contract.unknown_or_missing_decision_must_fail_closed == "true"
    assert contract.malformed_decision_must_fail_closed == "true"
    assert contract.contradictory_decision_must_fail_closed == "true"
    assert contract.unsupported_decision_must_fail_closed == "true"
    assert contract.unknown_cannot_become_false == "true"
    assert contract.unknown_cannot_become_does_not_apply == "true"
    assert contract.unknown_cannot_become_not_applicable == "true"
    assert contract.unknown_cannot_become_zero == "true"
    assert contract.missing_cannot_become_zero == "true"
    assert contract.missing_cannot_auto_become_does_not_apply == "true"
    with pytest.raises(P01ApplicationPredicateIdentityContractError) as unknown:
        reject_p01_unknown_or_missing_decision_v1(decision_state="DOES_NOT_APPLY")
    assert "P01_UNKNOWN_CANNOT_BECOME_DOES_NOT_APPLY" in str(unknown.value)
    with pytest.raises(P01ApplicationPredicateIdentityContractError) as malformed:
        reject_p01_malformed_decision_v1(decision_state="not-a-state")
    assert "P01_MALFORMED_DECISION_MUST_FAIL_CLOSED" in str(malformed.value)
    with pytest.raises(P01ApplicationPredicateIdentityContractError) as contradictory:
        reject_p01_contradictory_decision_v1(decision_state="APPLIES_AND_DOES_NOT_APPLY")
    assert "P01_CONTRADICTORY_DECISION_MUST_FAIL_CLOSED" in str(contradictory.value)
    with pytest.raises(P01ApplicationPredicateIdentityContractError) as unsupported:
        reject_p01_unsupported_decision_v1(decision_state="OPTIONAL")
    assert "P01_UNSUPPORTED_DECISION_MUST_FAIL_CLOSED" in str(unsupported.value)


def test_authority_and_reconstruction_boundary_are_preserved() -> None:
    contract = _contract()
    assert (
        contract.p01_applicability_decision_must_remain_inside_existing_reconstruction_boundary
        == "true"
    )
    assert contract.p01_applicability_decision_is_not_account_equity_authority == "true"
    assert contract.p01_applicability_decision_is_not_parallel_producer == "true"
    assert contract.p01_applicability_decision_is_not_trading_logic_authority == "true"
    assert contract.p01_applicability_decision_is_distinct_from_p01_value == "true"
    assert contract.p01_applicability_decision_is_distinct_from_p01_zero == "true"
    assert contract.p01_applicability_decision_is_distinct_from_p01_absence == "true"
    assert contract.p01_applicability_decision_is_distinct_from_p01_requiredness == "true"
    assert contract.p01_applicability_decision_is_distinct_from_p01_completeness == "true"
    assert contract.u04_u05_u06_predicate_inheritance_forbidden == "true"
    assert contract.venue_raw_is_not_p01_predicate_authority == "true"
    assert contract.step_29p_is_not_p01_predicate_authority == "true"
    assert contract.live_account_bound_is_not_p01_predicate_authority == "true"
    assert contract.master_v2_is_not_p01_predicate_authority == "true"
    assert contract.double_play_is_not_p01_predicate_authority == "true"
    assert contract.top20_is_not_p01_predicate_authority == "true"
    assert contract.learning_is_not_p01_predicate_authority == "true"
    assert contract.full_core_autonomy_is_not_p01_predicate_authority == "true"
    assert P01_INPUT_PRECONDITIONS_RESOLVED is False
    assert P01_RECONSTRUCTION_STATE_PRECONDITIONS_RESOLVED is False
    for inferred in ("ALWAYS_APPLIES", "LIVE_ENABLED", "U04", "availEq"):
        with pytest.raises(P01ApplicationPredicateIdentityContractError) as raised:
            build_p01_application_predicate_identity_contract_v1(
                p01_application_predicate_identity_contract_id=(
                    "SYNTHETIC_P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_ID"
                ),
                p01_application_predicate_model=inferred,
            )
        assert "P01_APPLICATION_PREDICATE_IDENTITY_INFERRED_FORBIDDEN" in str(
            raised.value
        ) or "P01_APPLICATION_PREDICATE_MODEL_MISMATCH" in str(raised.value)
    with pytest.raises(P01ApplicationPredicateIdentityContractError) as equity:
        reject_p01_application_predicate_identity_as_account_equity_authority_v1(
            source="ACCOUNT_EQUITY_AUTHORITY_OWNER"
        )
    assert "P01_IDENTITY_IS_NOT_ACCOUNT_EQUITY_AUTHORITY" in str(equity.value)
    with pytest.raises(P01ApplicationPredicateIdentityContractError) as u04:
        reject_p01_application_predicate_inherited_from_u04_u05_u06_v1(source="U04")
    assert "P01_U04_U05_U06_PREDICATE_INHERITANCE_FORBIDDEN" in str(u04.value)
    with pytest.raises(P01ApplicationPredicateIdentityContractError) as venue:
        reject_p01_application_predicate_authority_from_forbidden_surface_v1(source="availEq")
    assert "P01_FORBIDDEN_PREDICATE_AUTHORITY" in str(venue.value)


def test_missing_and_malformed_inputs_fail_closed() -> None:
    with pytest.raises(P01ApplicationPredicateIdentityContractError) as missing:
        build_p01_application_predicate_identity_contract_v1(
            p01_application_predicate_identity_contract_id=(
                "SYNTHETIC_P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_ID"
            ),
            member_id=None,
        )
    assert "P01_FIELD_MISSING:member_id" in str(missing.value)
    with pytest.raises(P01ApplicationPredicateIdentityContractError) as malformed:
        build_p01_application_predicate_identity_contract_v1(
            p01_application_predicate_identity_contract_id=(
                "SYNTHETIC_P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_ID"
            ),
            member_id=False,
        )
    assert "P01_FIELD_NOT_STRING:member_id" in str(malformed.value)


def test_gap_dag_and_live_pins_remain_fail_closed() -> None:
    dag = live_admission_gap_dag_v1()
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED"
    assert dag["P01_TERM_SET_RESOLVED"] is True
    assert dag["P01_VALUE_UNIT_CLASS_RESOLVED"] is True
    assert dag["P01_APPLICABILITY_CLASS_RESOLVED"] is True
    assert dag["P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED"] is True
    assert dag["P01_APPLICATION_PREDICATE_MODEL"] == "TYPED_GOVERNED_APPLICABILITY_DECISION_V1"
    assert dag["P01_APPLICATION_PREDICATE_RESOLVED"] is False
    assert dag["P01_APPLICATION_PREDICATE"] == "UNSPECIFIED_FAIL_CLOSED"
    assert dag["P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED"] is False
    assert dag["P01_APPLICATION_TRUE_RULE_RESOLVED"] is False
    assert dag["P01_APPLICATION_FALSE_RULE_RESOLVED"] is False
    assert dag["P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_AUTHORITY_EFFECT"] == "NONE"
    assert dag["P01_TERM_SEMANTICS_RESOLVED"] is False
    assert dag["P01_RUNTIME_INSTANCE_PRESENT"] is False
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_runbook_an_consumes_go_without_rewriting_am() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    an_section = _an_section()
    am_start = runbook.index(AM_HEADING)
    am_section = runbook[am_start : runbook.index(AN_HEADING, am_start)]
    assert "P01_APPLICABILITY_CLASS_CONTRACT_SCHEMA_PRESENT=true" in am_section
    assert "THIS_SLICE=11.2.1.AN" not in am_section
    assert "P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED=true" not in am_section
    assert "EARLIEST_NARROW_P01_DEPENDENCY=P01_APPLICATION_PREDICATE_UNSPECIFIED" in am_section
    assert "P01M_GOVERNED_DEPLOYABILITY_CONSERVATISM_REDUCTION" in am_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_P01_APPLICATION_PREDICATE_IDENTITY_BOUNDARY_RATIFICATION_V1"
        in an_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in an_section
    assert "P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_SCHEMA_PRESENT=true" in an_section
    assert "P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED=true" in an_section
    assert "P01_APPLICATION_PREDICATE_MODEL=TYPED_GOVERNED_APPLICABILITY_DECISION_V1" in (
        an_section
    )
    assert "P01_APPLICABILITY_DECISION_STATE_MODEL=APPLIES_DOES_NOT_APPLY_UNKNOWN_FAIL_CLOSED" in (
        an_section
    )
    assert "P01_APPLICABILITY_DECISION_IS_TYPED=true" in an_section
    assert "P01_APPLICABILITY_DECISION_IS_GOVERNED=true" in an_section
    assert "P01_APPLICATION_PREDICATE_RESOLVED=false" in an_section
    assert "P01_APPLICATION_PREDICATE=UNSPECIFIED_FAIL_CLOSED" in an_section
    assert "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED=false" in an_section
    assert "P01_APPLICATION_TRUE_RULE_RESOLVED=false" in an_section
    assert "P01_APPLICATION_FALSE_RULE_RESOLVED=false" in an_section
    assert "P01_REQUIREDNESS_RESOLVED=false" in an_section
    assert "P01_OPTIONALITY_RESOLVED=false" in an_section
    assert "P01_ZERO_SEMANTICS_RESOLVED=false" in an_section
    assert "P01_ABSENCE_SEMANTICS_RESOLVED=false" in an_section
    assert "MASTER_V2_IS_NOT_P01_PREDICATE_AUTHORITY=true" in an_section
    assert "DOUBLE_PLAY_IS_NOT_P01_PREDICATE_AUTHORITY=true" in an_section
    assert "TOP20_IS_NOT_P01_PREDICATE_AUTHORITY=true" in an_section
    assert "LEARNING_IS_NOT_P01_PREDICATE_AUTHORITY=true" in an_section
    assert "FULL_CORE_AUTONOMY_IS_NOT_P01_PREDICATE_AUTHORITY=true" in an_section
    assert "VENUE_RAW_IS_NOT_P01_PREDICATE_AUTHORITY=true" in an_section
    assert "STEP_29P_IS_NOT_P01_PREDICATE_AUTHORITY=true" in an_section
    assert "LIVE_ACCOUNT_BOUND_IS_NOT_P01_PREDICATE_AUTHORITY=true" in an_section
    assert "THIS_SLICE=11.2.1.AN" in an_section
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in an_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED=false" in an_section
    assert "P01_RUNTIME_INSTANCE_PRESENT=false" in an_section
    assert "P01_AUTHORITY_EFFECT=NONE" in an_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in an_section
    assert "CANONICAL_FORMULA_PROVEN=false" in an_section
    assert "FORMULA_RATIFIED=false" in an_section
    assert "OPERATOR_RATIFIED=false" in an_section
    assert "SIGN_RATIFIED=false" in an_section
    assert "SOURCE_MAPPING_RATIFIED=false" in an_section
    assert "PRODUCER_IMPLEMENTED=false" in an_section
    assert "RUNTIME_BINDING_ADDED=false" in an_section
    assert "LIVE_EFFECT_ADDED=false" in an_section
    assert "SOURCE_SELECTED=false" in an_section
    assert "MAPPING_PROVEN=false" in an_section
    assert "GOVERNED_PRODUCER_CREATED=false" in an_section
    assert "EXISTING_UNIVERSE_TOPOLOGY_PRESERVED=true" in an_section
    assert "EXISTING_AUTHORITY_GRAPH_PRESERVED=true" in an_section
    assert "EXISTING_UNIVERSE_TOPOLOGY_MUST_REMAIN_UNCHANGED=true" in an_section
    assert "EXISTING_AUTHORITY_GRAPH_MUST_REMAIN_UNCHANGED=true" in an_section
    assert "NEW_UNIVERSE_ALLOWED=false" in an_section
    assert "NEW_AUTHORITY_OWNER_ALLOWED=false" in an_section
    assert "NEW_PARALLEL_PRODUCER_ALLOWED=false" in an_section
    assert "PARALLEL_EQUITY_AUTHORITY_FORBIDDEN=true" in an_section
    assert "PARALLEL_ACCOUNTING_AUTHORITY_FORBIDDEN=true" in an_section
    assert "VENUE_DIRECT_P01_AUTHORITY_FORBIDDEN=true" in an_section
    assert "STEP_29P_AS_P01_AUTHORITY_FORBIDDEN=true" in an_section
    assert "LIVE_ACCOUNT_BOUND_AS_P01_AUTHORITY_FORBIDDEN=true" in an_section
    assert "P01_MUST_REMAIN_INSIDE_EXISTING_RECONSTRUCTION_BOUNDARY=true" in an_section
    assert "P01_CROSS_SYSTEM_SIDE_EFFECT_ALLOWED=false" in an_section
    assert "NEW_UNIVERSE_CREATED=false" in an_section
    assert "NEW_AUTHORITY_OWNER_CREATED=false" in an_section
    assert "NEW_PARALLEL_PRODUCER_CREATED=false" in an_section
    assert (
        "EARLIEST_DECOMPOSED_CONTRACT_GAP=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in an_section
    )
    assert (
        "EARLIEST_NARROW_P01_DEPENDENCY=P01_APPLICATION_PREDICATE_INPUT_DOMAIN_UNSPECIFIED"
        in an_section
    )
    assert "DOCS_TOKEN_FULL_CORE_TYPED_P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_V1" in spec
    assert "P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED=true" in spec
    assert "P01_APPLICATION_PREDICATE_RESOLVED=false" in spec
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in spec
    assert "CANONICAL_FORMULA_PROVEN=false" in spec
    assert "FORMULA_RATIFIED=false" in spec
    assert "OPERATOR_RATIFIED=false" in spec
    assert "SIGN_RATIFIED=false" in spec
    assert "SOURCE_MAPPING_RATIFIED=false" in spec
    assert "PRODUCER_IMPLEMENTED=false" in spec
    assert "RUNTIME_BINDING_ADDED=false" in spec
    assert "LIVE_EFFECT_ADDED=false" in spec
