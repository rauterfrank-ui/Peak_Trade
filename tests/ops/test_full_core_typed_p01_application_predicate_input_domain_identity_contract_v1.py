"""Typed P01 application-predicate input-domain identity. No concrete members."""

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
    P01_APPLICATION_PREDICATE,
    P01_APPLICATION_PREDICATE_RESOLVED,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_RESOLVED,
    P01_VALUE_UNIT_CLASS,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SOURCE_SELECTED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_DECOMPOSED_CONTRACT_GAP,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    P01_APPLICATION_FALSE_RULE_RESOLVED,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_AUTHORITY_EFFECT,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_SCHEMA_PRESENT,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_SELECTED_OPTION,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED,
    P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED,
    P01_APPLICATION_PREDICATE_MODEL,
    P01_APPLICATION_TRUE_RULE_RESOLVED,
    P01_INPUT_FRESHNESS_RULE_RESOLVED,
    P01_INPUT_NORMALIZATION_RULE_RESOLVED,
    P01_INPUT_READINESS_RULE_RESOLVED,
    P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED,
    P01_PREDICATE_INPUT_DOMAIN_ALLOWED_INPUT_CLASS,
    P01_PREDICATE_INPUT_DOMAIN_BOUNDARY_RESOLVED,
    P01_PREDICATE_INPUT_DOMAIN_CLASS,
    P01_PREDICATE_INPUT_DOMAIN_DEFAULT,
    P01_PREDICATE_INPUT_DOMAIN_GOVERNED,
    P01_PREDICATE_INPUT_DOMAIN_IDENTITY_RESOLVED,
    P01_PREDICATE_INPUT_DOMAIN_IS_CLOSED_WORLD,
    P01_PREDICATE_INPUT_DOMAIN_TYPED,
    P01_PREDICATE_OPTIONAL_FIELDS_RESOLVED,
    P01_PREDICATE_REQUIRED_FIELDS_RESOLVED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_application_predicate_input_domain_identity_contract_v1 import (
    ALLOWED_INPUT_CLASS,
    INPUT_DOMAIN_CLASS,
    RATIFICATION_SCOPE,
    REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS,
    SELECTED_OPTION,
    P01ApplicationPredicateInputDomainIdentityContractError,
    P01ApplicationPredicateInputDomainIdentityContractV1,
    build_p01_application_predicate_input_domain_identity_contract_v1,
    reject_p01_concrete_input_member_inference_v1,
    reject_p01_foreign_system_state_promotion_v1,
    reject_p01_implicit_input_promotion_v1,
    reject_p01_missing_required_input_as_does_not_apply_v1,
    reject_p01_unratified_fact_admission_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_exact_member_identity_contract_v1 import (
    MEMBER_ID,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_TYPED_P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_V1.md"
)
AN_HEADING = "11.2.1.AN FULL_CORE_TYPED_P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT"
AO_HEADING = "11.2.1.AO FULL_CORE_TYPED_P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT"


def _contract() -> P01ApplicationPredicateInputDomainIdentityContractV1:
    return build_p01_application_predicate_input_domain_identity_contract_v1(
        p01_application_predicate_input_domain_identity_contract_id=(
            "SYNTHETIC_P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_ID"
        )
    )


def _ao_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ao_start = runbook.index(AO_HEADING)
    return runbook[ao_start : runbook.index("## 11.3 Autonomy state model", ao_start)]


def test_p01_application_predicate_input_domain_identity_contract_constructs() -> None:
    contract = _contract()
    assert isinstance(contract, P01ApplicationPredicateInputDomainIdentityContractV1)
    assert SCHEMA_CLASS == "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_V1"
    assert contract.member_id == MEMBER_ID
    assert contract.p01_predicate_input_domain_class == INPUT_DOMAIN_CLASS
    assert contract.p01_predicate_input_domain_class == (
        "TYPED_GOVERNED_P01_RECONSTRUCTION_CONTEXT_V1"
    )
    assert contract.allowed_input_class == ALLOWED_INPUT_CLASS
    assert contract.input_domain_default == "NO_IMPLICIT_MEMBERS"
    assert contract.ratification_scope == RATIFICATION_SCOPE
    assert contract.selected_option == SELECTED_OPTION
    assert contract.p01_predicate_input_domain_identity_resolved_status == "true"
    assert contract.p01_predicate_input_domain_boundary_resolved_status == "true"
    assert contract.p01_application_predicate_input_domain_resolved_status == "false"
    assert contract.p01_predicate_concrete_input_members_resolved_status == "false"
    assert contract.p01_runtime_instance_present == "false"
    assert contract.p01_authority_effect == "NONE"
    assert P01_TERM_SET_RESOLVED is True
    assert P01_VALUE_UNIT_CLASS_RESOLVED is True
    assert P01_VALUE_UNIT_CLASS == "ABSOLUTE_MONETARY_REDUCTION_AMOUNT"
    assert P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED is True
    assert P01_APPLICATION_PREDICATE_MODEL == "TYPED_GOVERNED_APPLICABILITY_DECISION_V1"
    assert P01_PREDICATE_INPUT_DOMAIN_IDENTITY_RESOLVED is True
    assert P01_PREDICATE_INPUT_DOMAIN_BOUNDARY_RESOLVED is True
    assert P01_PREDICATE_INPUT_DOMAIN_CLASS == "TYPED_GOVERNED_P01_RECONSTRUCTION_CONTEXT_V1"
    assert P01_PREDICATE_INPUT_DOMAIN_TYPED is True
    assert P01_PREDICATE_INPUT_DOMAIN_GOVERNED is True
    assert P01_PREDICATE_INPUT_DOMAIN_IS_CLOSED_WORLD is True
    assert P01_PREDICATE_INPUT_DOMAIN_ALLOWED_INPUT_CLASS == (
        "TYPED_GOVERNED_P01_RECONSTRUCTION_FACTS_ONLY"
    )
    assert P01_PREDICATE_INPUT_DOMAIN_DEFAULT == "NO_IMPLICIT_MEMBERS"
    assert P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_SELECTED_OPTION == (
        "P01_OP_APPLICATION_PREDICATE_INPUT_DOMAIN_TYPED_RECONSTRUCTION_CONTEXT_V1"
    )
    assert P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED is False
    assert P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED is False
    assert P01_PREDICATE_REQUIRED_FIELDS_RESOLVED is False
    assert P01_PREDICATE_OPTIONAL_FIELDS_RESOLVED is False
    assert P01_APPLICATION_TRUE_RULE_RESOLVED is False
    assert P01_APPLICATION_FALSE_RULE_RESOLVED is False
    assert P01_APPLICATION_PREDICATE_RESOLVED is False
    assert P01_APPLICATION_PREDICATE == "UNSPECIFIED_FAIL_CLOSED"
    assert P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_SCHEMA_PRESENT is True
    assert P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT is (
        False
    )
    assert P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_AUTHORITY_EFFECT == "NONE"
    assert P01_RUNTIME_INSTANCE_PRESENT is False


def test_object_is_immutable() -> None:
    contract = _contract()
    with pytest.raises(FrozenInstanceError):
        contract.p01_predicate_input_domain_identity_resolved_status = "false"  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = _contract()
    second = _contract()
    assert first.provenance_digest == second.provenance_digest


def test_identity_does_not_ratify_concrete_members_or_true_false_formula() -> None:
    contract = _contract()
    assert contract.identity_does_not_ratify_concrete_members == "true"
    assert contract.identity_does_not_ratify_required_fields == "true"
    assert contract.identity_does_not_ratify_optional_fields == "true"
    assert contract.identity_does_not_ratify_true_rule == "true"
    assert contract.identity_does_not_ratify_false_rule == "true"
    assert contract.identity_does_not_ratify_formula == "true"
    assert P01_TERM_SEMANTICS_RESOLVED is False
    assert P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert P01_INPUT_READINESS_RULE_RESOLVED is False
    assert P01_INPUT_FRESHNESS_RULE_RESOLVED is False
    assert P01_INPUT_NORMALIZATION_RULE_RESOLVED is False
    assert "P01_PREDICATE_CONCRETE_INPUT_MEMBERS_UNSPECIFIED" in (
        contract.remaining_unresolved_semantics
    )
    assert contract.remaining_unresolved_semantics == REMAINING_UNRESOLVED_SEMANTICS
    with pytest.raises(P01ApplicationPredicateInputDomainIdentityContractError) as members:
        reject_p01_concrete_input_member_inference_v1(member="P01_TERM_PRESENCE")
    assert "P01_IDENTITY_IS_NOT_CONCRETE_MEMBERS" in str(members.value)


def test_fail_closed_domain_boundary_semantics_are_exact() -> None:
    contract = _contract()
    assert contract.missing_required_input_result == "UNKNOWN_FAIL_CLOSED"
    assert contract.malformed_input_result == "UNKNOWN_FAIL_CLOSED"
    assert contract.contradictory_input_result == "UNKNOWN_FAIL_CLOSED"
    assert contract.unsupported_input_result == "UNKNOWN_FAIL_CLOSED"
    assert contract.unratified_input_result == "UNKNOWN_FAIL_CLOSED"
    assert contract.unratified_fact_admission == "FORBIDDEN"
    assert contract.implicit_input_promotion == "FORBIDDEN"
    assert contract.foreign_system_state_promotion == "FORBIDDEN"
    assert contract.does_not_apply_requires_explicit_false_rule == "true"
    assert contract.missing_does_not_mean_does_not_apply == "true"
    assert contract.zero_does_not_mean_does_not_apply == "true"
    assert contract.absence_does_not_mean_does_not_apply == "true"
    assert contract.reconstruction_incomplete_does_not_mean_does_not_apply == "true"
    with pytest.raises(P01ApplicationPredicateInputDomainIdentityContractError) as unratified:
        reject_p01_unratified_fact_admission_v1(fact="CONFIG_FLAG")
    assert "P01_UNRATIFIED_FACT_ADMISSION_FORBIDDEN" in str(unratified.value)
    with pytest.raises(P01ApplicationPredicateInputDomainIdentityContractError) as implicit:
        reject_p01_implicit_input_promotion_v1(source="P01_TERM_PRESENCE")
    assert "P01_IMPLICIT_INPUT_PROMOTION_FORBIDDEN" in str(implicit.value)
    with pytest.raises(P01ApplicationPredicateInputDomainIdentityContractError) as foreign:
        reject_p01_foreign_system_state_promotion_v1(source="RISK_SIZING_INPUT_DOMAIN")
    assert "P01_FOREIGN_SYSTEM_STATE_PROMOTION_FORBIDDEN" in str(foreign.value)
    with pytest.raises(P01ApplicationPredicateInputDomainIdentityContractError) as missing:
        reject_p01_missing_required_input_as_does_not_apply_v1(input_name="UNSPECIFIED")
    assert "P01_MISSING_IS_NOT_DOES_NOT_APPLY" in str(missing.value)


def test_authority_and_reconstruction_boundary_are_preserved() -> None:
    contract = _contract()
    assert (
        contract.p01_predicate_input_domain_must_remain_inside_existing_reconstruction_boundary
        == "true"
    )
    assert contract.p01_predicate_input_domain_is_not_account_equity_authority == "true"
    assert contract.p01_predicate_input_domain_is_not_parallel_producer == "true"
    assert contract.p01_predicate_input_domain_is_not_trading_logic_authority == "true"
    assert contract.new_authority_owner == "false"
    assert contract.new_parallel_producer == "false"
    assert contract.new_universe == "false"
    assert contract.master_v2_is_not_p01_predicate_input_authority == "true"
    assert contract.u04_u05_u06_input_inheritance_forbidden == "true"
    assert contract.risk_sizing_input_domains_are_not_p01_predicate_input == "true"
    for inferred in ("ALWAYS_APPLIES", "LIVE_ENABLED", "U04", "availEq"):
        with pytest.raises(P01ApplicationPredicateInputDomainIdentityContractError) as raised:
            build_p01_application_predicate_input_domain_identity_contract_v1(
                p01_application_predicate_input_domain_identity_contract_id=(
                    "SYNTHETIC_P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_ID"
                ),
                p01_predicate_input_domain_class=inferred,
            )
        assert "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_INFERRED_FORBIDDEN" in str(
            raised.value
        ) or "P01_PREDICATE_INPUT_DOMAIN_CLASS_MISMATCH" in str(raised.value)


def test_missing_and_malformed_inputs_fail_closed() -> None:
    with pytest.raises(P01ApplicationPredicateInputDomainIdentityContractError) as missing:
        build_p01_application_predicate_input_domain_identity_contract_v1(
            p01_application_predicate_input_domain_identity_contract_id=(
                "SYNTHETIC_P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_ID"
            ),
            member_id=None,
        )
    assert "P01_FIELD_MISSING:member_id" in str(missing.value)
    with pytest.raises(P01ApplicationPredicateInputDomainIdentityContractError) as malformed:
        build_p01_application_predicate_input_domain_identity_contract_v1(
            p01_application_predicate_input_domain_identity_contract_id=(
                "SYNTHETIC_P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_ID"
            ),
            member_id=False,
        )
    assert "P01_FIELD_NOT_STRING:member_id" in str(malformed.value)


def test_gap_dag_and_live_pins_remain_fail_closed() -> None:
    dag = live_admission_gap_dag_v1()
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED"
    assert dag["P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED"] is True
    assert dag["P01_PREDICATE_INPUT_DOMAIN_IDENTITY_RESOLVED"] is True
    assert dag["P01_PREDICATE_INPUT_DOMAIN_BOUNDARY_RESOLVED"] is True
    assert dag["P01_PREDICATE_INPUT_DOMAIN_CLASS"] == (
        "TYPED_GOVERNED_P01_RECONSTRUCTION_CONTEXT_V1"
    )
    assert dag["P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED"] is False
    assert dag["P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED"] is False
    assert dag["P01_APPLICATION_TRUE_RULE_RESOLVED"] is False
    assert dag["P01_APPLICATION_FALSE_RULE_RESOLVED"] is False
    assert dag[
        "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT"
    ] is (False)
    assert dag["P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_AUTHORITY_EFFECT"] == (
        "NONE"
    )
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_runbook_ao_consumes_go_without_rewriting_an() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    ao_section = _ao_section()
    an_start = runbook.index(AN_HEADING)
    an_section = runbook[an_start : runbook.index(AO_HEADING, an_start)]
    assert "P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_SCHEMA_PRESENT=true" in an_section
    assert "THIS_SLICE=11.2.1.AO" not in an_section
    assert "P01_PREDICATE_INPUT_DOMAIN_IDENTITY_RESOLVED=true" not in an_section
    assert (
        "EARLIEST_NARROW_P01_DEPENDENCY=P01_APPLICATION_PREDICATE_INPUT_DOMAIN_UNSPECIFIED"
        in an_section
    )
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_BOUNDARY_RATIFICATION_V1"
        in ao_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in ao_section
    assert "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_SCHEMA_PRESENT=true" in (
        ao_section
    )
    assert "P01_PREDICATE_INPUT_DOMAIN_IDENTITY_RESOLVED=true" in ao_section
    assert "P01_PREDICATE_INPUT_DOMAIN_BOUNDARY_RESOLVED=true" in ao_section
    assert "P01_PREDICATE_INPUT_DOMAIN_CLASS=TYPED_GOVERNED_P01_RECONSTRUCTION_CONTEXT_V1" in (
        ao_section
    )
    assert "ALLOWED_INPUT_CLASS=TYPED_GOVERNED_P01_RECONSTRUCTION_FACTS_ONLY" in ao_section
    assert "INPUT_DOMAIN_IS_CLOSED_WORLD=true" in ao_section
    assert "INPUT_DOMAIN_DEFAULT=NO_IMPLICIT_MEMBERS" in ao_section
    assert "INPUT_DOMAIN_AUTHORITY_EFFECT=NONE" in ao_section
    assert "UNRATIFIED_FACT_ADMISSION=FORBIDDEN" in ao_section
    assert "MISSING_REQUIRED_INPUT_RESULT=UNKNOWN_FAIL_CLOSED" in ao_section
    assert "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED=false" in ao_section
    assert "P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED=false" in ao_section
    assert "P01_APPLICATION_TRUE_RULE_RESOLVED=false" in ao_section
    assert "P01_APPLICATION_FALSE_RULE_RESOLVED=false" in ao_section
    assert "THIS_SLICE=11.2.1.AO" in ao_section
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in ao_section
    assert "P01_RUNTIME_INSTANCE_PRESENT=false" in ao_section
    assert "P01_AUTHORITY_EFFECT=NONE" in ao_section
    assert "FORMULA_RATIFIED=false" in ao_section
    assert "SOURCE_MAPPING_RATIFIED=false" in ao_section
    assert "PRODUCER_IMPLEMENTED=false" in ao_section
    assert "LIVE_EFFECT_ADDED=false" in ao_section
    assert "NEW_UNIVERSE_ALLOWED=false" in ao_section
    assert "NEW_AUTHORITY_OWNER_ALLOWED=false" in ao_section
    assert "NEW_PARALLEL_PRODUCER_ALLOWED=false" in ao_section
    assert "P01_MUST_REMAIN_INSIDE_EXISTING_RECONSTRUCTION_BOUNDARY=true" in ao_section
    assert (
        "EARLIEST_NARROW_P01_DEPENDENCY=P01_PREDICATE_CONCRETE_INPUT_MEMBERS_UNSPECIFIED"
        in ao_section
    )
    assert (
        "DOCS_TOKEN_FULL_CORE_TYPED_P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_V1"
        in (spec)
    )
    assert "P01_PREDICATE_INPUT_DOMAIN_IDENTITY_RESOLVED=true" in spec
    assert "P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED=false" in spec
    assert P01_APPLICABILITY_CLASS == "GOVERNED_CONDITIONAL"
