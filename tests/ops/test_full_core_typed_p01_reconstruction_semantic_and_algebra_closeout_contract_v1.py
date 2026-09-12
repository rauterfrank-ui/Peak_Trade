"""P01 reconstruction semantic and algebra closeout. No productive source."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal
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
    P01_APPLICATION_PREDICATE,
    P01_CLOSEOUT_MODEL,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_OPERATOR,
    P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED,
    P01_PREDICATE_INPUT_MEMBER,
    P01_PRODUCT_SEMANTICS_COMPLETE,
    P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_RESOLVED,
    P01_RECONSTRUCTION_ALGEBRA_CONTRACT_COMPLETE,
    P01_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SOURCE_SELECTED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_DECOMPOSED_CONTRACT_GAP,
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    P01_APPLICATION_FALSE_RULE_RESOLVED,
    P01_APPLICATION_TRUE_RULE_RESOLVED,
    P01_INPUT_FRESHNESS_RULE_RESOLVED,
    P01_PRODUCTIVE_DIRECTIVE_PRODUCER_IMPLEMENTED,
    P01_PRODUCTIVE_RUNTIME_BINDING_ADDED,
    P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_BLOCKER,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.governed_p01_reduction_directive_v1 import (
    STATE_APPLIES,
    STATE_DOES_NOT_APPLY,
    STATE_UNKNOWN_FAIL_CLOSED,
    GovernedP01ReductionDirectiveError,
    build_governed_p01_reduction_directive_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_exact_member_identity_contract_v1 import (
    MEMBER_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_governed_reduction_directive_evaluator_v1 import (
    ALGEBRA_UNRESOLVED,
    REJECTED_AUTOMATIC_P01_PREDICATE_CANDIDATES,
    evaluate_p01_application_predicate_from_payloads_v1,
    evaluate_p01_application_predicate_v1,
    evaluate_p01_reconstruction_term_v1,
    reject_p01_implicit_candidate_promotion_v1,
    reject_u04_u05_u06_p01_inheritance_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_reconstruction_semantic_and_algebra_closeout_contract_v1 import (
    SCHEMA_CLASS,
    P01ReconstructionSemanticAndAlgebraCloseoutContractError,
    P01ReconstructionSemanticAndAlgebraCloseoutContractV1,
    build_p01_reconstruction_semantic_and_algebra_closeout_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    EMBEDDED_NO,
    INCLUSION_NOT_IN_BASE,
    ROLE_SUBTRACTIVE,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
    build_reconstruction_algebra_contract_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_TYPED_P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_V1.md"
)
AO_HEADING = "11.2.1.AO FULL_CORE_TYPED_P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT"
AP_HEADING = "11.2.1.AP FULL_CORE_TYPED_P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT"
PROTECTED_SURFACES = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "governed_p01_reduction_directive_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "p01_governed_reduction_directive_evaluator_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "p01_reconstruction_semantic_and_algebra_closeout_contract_v1.py",
)


def _contract() -> P01ReconstructionSemanticAndAlgebraCloseoutContractV1:
    return build_p01_reconstruction_semantic_and_algebra_closeout_contract_v1(
        p01_reconstruction_semantic_and_algebra_closeout_contract_id=(
            "SYNTHETIC_P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_ID"
        )
    )


def _ap_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ap_start = runbook.index(AP_HEADING)
    return runbook[
        ap_start : runbook.index(
            "11.2.1.AQ FULL_CORE_EQUITY_RECOVERY_PR1_GOVERNANCE_REOPEN_AND_CANDIDATE_CENSUS",
            ap_start,
        )
    ]


def test_closeout_contract_constructs() -> None:
    contract = _contract()
    assert isinstance(contract, P01ReconstructionSemanticAndAlgebraCloseoutContractV1)
    assert SCHEMA_CLASS == "P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_V1"
    assert contract.member_id == MEMBER_ID
    assert contract.p01_predicate_input_member == "GOVERNED_P01_REDUCTION_DIRECTIVE_V1"
    assert contract.p01_predicate_concrete_input_member_count == "1"
    assert contract.p01_application_true_rule_resolved_status == "true"
    assert contract.p01_application_false_rule_resolved_status == "true"
    assert contract.p01_operator == "SUBTRACTION"
    assert contract.p01_runtime_instance_present == "false"
    assert contract.p01_authority_effect == "NONE"
    assert P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED is True
    assert P01_APPLICATION_TRUE_RULE_RESOLVED is True
    assert P01_APPLICATION_FALSE_RULE_RESOLVED is True
    assert P01_TERM_SEMANTICS_RESOLVED is True
    assert P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is True
    assert P01_PRODUCT_SEMANTICS_COMPLETE is True
    assert P01_RECONSTRUCTION_ALGEBRA_CONTRACT_COMPLETE is True
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_RESOLVED is False
    assert P01_PRODUCTIVE_DIRECTIVE_PRODUCER_IMPLEMENTED is False
    assert P01_PRODUCTIVE_RUNTIME_BINDING_ADDED is False
    assert P01_INPUT_FRESHNESS_RULE_RESOLVED is False
    assert P01_APPLICATION_PREDICATE == "GOVERNED_P01_REDUCTION_DIRECTIVE_PREDICATE_V1"
    assert P01_PREDICATE_INPUT_MEMBER == "GOVERNED_P01_REDUCTION_DIRECTIVE_V1"
    assert P01_CLOSEOUT_MODEL == "GOVERNED_REDUCTION_DIRECTIVE_SINGLE_PR_CLOSEOUT_V1"
    assert P01_OPERATOR == "SUBTRACTION"
    assert P01_RUNTIME_INSTANCE_PRESENT is False


def test_object_is_immutable() -> None:
    contract = _contract()
    with pytest.raises(FrozenInstanceError):
        contract.p01_product_semantics_complete_status = "false"  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = _contract()
    second = _contract()
    assert first.provenance_digest == second.provenance_digest
    directive_a = build_governed_p01_reduction_directive_v1(
        directive_id="P01_DIR_A",
        applicability_state=STATE_APPLIES,
        evidence_ref="P01_EVIDENCE_A",
        authorized_reduction_amount="12.50",
    )
    directive_b = build_governed_p01_reduction_directive_v1(
        directive_id="P01_DIR_A",
        applicability_state=STATE_APPLIES,
        evidence_ref="P01_EVIDENCE_A",
        authorized_reduction_amount="12.50",
    )
    assert directive_a.semantic_digest == directive_b.semantic_digest
    assert directive_a.provenance_digest == directive_a.semantic_digest


def test_applies_positive_reduction_subtracts() -> None:
    directive = build_governed_p01_reduction_directive_v1(
        directive_id="P01_DIR_POS",
        applicability_state=STATE_APPLIES,
        evidence_ref="P01_EVIDENCE_POS",
        authorized_reduction_amount="25",
    )
    result = evaluate_p01_reconstruction_term_v1(
        pre_p01_equity=Decimal("100"),
        directives=(directive,),
    )
    assert result.decision.decision_state == STATE_APPLIES
    assert result.subtracted_amount == "25"
    assert result.post_p01_equity == "75"


def test_applies_explicit_zero_remains_applies() -> None:
    directive = build_governed_p01_reduction_directive_v1(
        directive_id="P01_DIR_ZERO",
        applicability_state=STATE_APPLIES,
        evidence_ref="P01_EVIDENCE_ZERO",
        authorized_reduction_amount="0",
    )
    result = evaluate_p01_reconstruction_term_v1(
        pre_p01_equity=Decimal("100"),
        directives=(directive,),
    )
    assert result.decision.decision_state == STATE_APPLIES
    assert result.subtracted_amount == "0"
    assert result.post_p01_equity == "100"


def test_explicit_does_not_apply_is_zero_by_predicate() -> None:
    directive = build_governed_p01_reduction_directive_v1(
        directive_id="P01_DIR_DNA",
        applicability_state=STATE_DOES_NOT_APPLY,
        evidence_ref="P01_EVIDENCE_DNA",
    )
    result = evaluate_p01_reconstruction_term_v1(
        pre_p01_equity=Decimal("100"),
        directives=(directive,),
    )
    assert result.decision.decision_state == STATE_DOES_NOT_APPLY
    assert result.subtracted_amount == "0"
    assert result.post_p01_equity == "100"


def test_missing_directive_is_unknown_not_does_not_apply_or_zero() -> None:
    decision = evaluate_p01_application_predicate_v1(())
    assert decision.decision_state == STATE_UNKNOWN_FAIL_CLOSED
    assert decision.decision_state != STATE_DOES_NOT_APPLY
    assert decision.algebra_contribution_state == ALGEBRA_UNRESOLVED
    result = evaluate_p01_reconstruction_term_v1(pre_p01_equity=Decimal("100"), directives=())
    assert result.post_p01_equity == ""
    assert result.subtracted_amount == ""


def test_malformed_wrong_member_and_invalid_provenance_are_unknown() -> None:
    malformed = evaluate_p01_application_predicate_from_payloads_v1(
        (
            {
                "directive_id": "",
                "applicability_state": STATE_APPLIES,
                "evidence_ref": "P01_EVIDENCE_MALFORMED",
                "authorized_reduction_amount": "1",
            },
        )
    )
    assert malformed.decision_state == STATE_UNKNOWN_FAIL_CLOSED
    wrong = evaluate_p01_application_predicate_from_payloads_v1(
        (
            {
                "directive_id": "P01_DIR_WRONG",
                "applicability_state": STATE_APPLIES,
                "evidence_ref": "P01_EVIDENCE_WRONG",
                "authorized_reduction_amount": "1",
                "member_id": "U04_PENDING_ORDER_RESERVATION",
            },
        )
    )
    assert wrong.decision_state == STATE_UNKNOWN_FAIL_CLOSED
    assert "UNRATIFIED" in wrong.reason_code or "MALFORMED" in wrong.reason_code
    valid = build_governed_p01_reduction_directive_v1(
        directive_id="P01_DIR_PROV",
        applicability_state=STATE_APPLIES,
        evidence_ref="P01_EVIDENCE_PROV",
        authorized_reduction_amount="1",
    )
    provenance = evaluate_p01_application_predicate_from_payloads_v1(
        (
            {
                "directive_id": "P01_DIR_PROV",
                "applicability_state": STATE_APPLIES,
                "evidence_ref": "P01_EVIDENCE_PROV",
                "authorized_reduction_amount": "1",
                "provenance_digest": "0" * 64,
                "semantic_digest": valid.semantic_digest,
            },
        )
    )
    assert provenance.decision_state == STATE_UNKNOWN_FAIL_CLOSED
    assert provenance.reason_code == "P01_INVALID_PROVENANCE"


def test_negative_non_finite_and_applies_without_amount_are_rejected() -> None:
    with pytest.raises(GovernedP01ReductionDirectiveError) as negative:
        build_governed_p01_reduction_directive_v1(
            directive_id="P01_DIR_NEG",
            applicability_state=STATE_APPLIES,
            evidence_ref="P01_EVIDENCE_NEG",
            authorized_reduction_amount="-1",
        )
    assert "P01_NEGATIVE_AMOUNT_FORBIDDEN" in str(negative.value)
    with pytest.raises(GovernedP01ReductionDirectiveError) as non_finite:
        build_governed_p01_reduction_directive_v1(
            directive_id="P01_DIR_INF",
            applicability_state=STATE_APPLIES,
            evidence_ref="P01_EVIDENCE_INF",
            authorized_reduction_amount="NaN",
        )
    assert "P01_AMOUNT_NON_FINITE" in str(non_finite.value)
    with pytest.raises(GovernedP01ReductionDirectiveError) as missing_amount:
        build_governed_p01_reduction_directive_v1(
            directive_id="P01_DIR_NO_AMT",
            applicability_state=STATE_APPLIES,
            evidence_ref="P01_EVIDENCE_NO_AMT",
            authorized_reduction_amount="",
            amount_present="false",
        )
    assert "P01_APPLIES_AMOUNT_REQUIRED" in str(missing_amount.value)


def test_contradictory_does_not_apply_payload_is_rejected() -> None:
    with pytest.raises(GovernedP01ReductionDirectiveError) as raised:
        build_governed_p01_reduction_directive_v1(
            directive_id="P01_DIR_DNA_NZ",
            applicability_state=STATE_DOES_NOT_APPLY,
            evidence_ref="P01_EVIDENCE_DNA_NZ",
            authorized_reduction_amount="8",
            amount_present="true",
        )
    assert "P01_DOES_NOT_APPLY_NONZERO_FORBIDDEN" in str(raised.value)
    rejected = evaluate_p01_application_predicate_from_payloads_v1(
        (
            {
                "directive_id": "P01_DIR_DNA_NZ",
                "applicability_state": STATE_DOES_NOT_APPLY,
                "evidence_ref": "P01_EVIDENCE_DNA_NZ",
                "authorized_reduction_amount": "8",
                "amount_present": "true",
            },
        )
    )
    assert rejected.decision_state == STATE_UNKNOWN_FAIL_CLOSED


def test_dimensional_compatibility_and_no_implicit_promotion() -> None:
    with pytest.raises(GovernedP01ReductionDirectiveError) as dimension:
        build_governed_p01_reduction_directive_v1(
            directive_id="P01_DIR_DIM",
            applicability_state=STATE_APPLIES,
            evidence_ref="P01_EVIDENCE_DIM",
            authorized_reduction_amount="1",
            semantic_dimension="USDC",
        )
    assert "P01_SEMANTIC_DIMENSION_MISMATCH" in str(dimension.value)
    assert len(REJECTED_AUTOMATIC_P01_PREDICATE_CANDIDATES) == 12
    for candidate_id in REJECTED_AUTOMATIC_P01_PREDICATE_CANDIDATES:
        with pytest.raises(GovernedP01ReductionDirectiveError) as raised:
            reject_p01_implicit_candidate_promotion_v1(candidate_id=candidate_id)
        assert "P01_IMPLICIT_CANDIDATE_PROMOTION_FORBIDDEN" in str(raised.value)
    with pytest.raises(GovernedP01ReductionDirectiveError) as inherited:
        reject_u04_u05_u06_p01_inheritance_v1()
    assert "U04_U05_U06_INPUT_INHERITANCE_FORBIDDEN" in str(inherited.value)


def test_double_counting_and_algebra_integration() -> None:
    directive = build_governed_p01_reduction_directive_v1(
        directive_id="P01_DIR_DC",
        applicability_state=STATE_APPLIES,
        evidence_ref="P01_EVIDENCE_DC",
        authorized_reduction_amount="10",
    )
    blocked = evaluate_p01_reconstruction_term_v1(
        pre_p01_equity=Decimal("100"),
        directives=(directive,),
        pre_p01_base_already_includes_p01_reduction=True,
    )
    assert blocked.decision.decision_state == STATE_UNKNOWN_FAIL_CLOSED
    assert blocked.decision.reason_code == "P01_DOUBLE_COUNTING_FORBIDDEN"
    assert blocked.post_p01_equity == ""
    algebra = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    p01 = next(term for term in algebra.terms if term.term_id == TERM_P01_HAIRCUT_RESERVE_DEPLETION)
    assert p01.algebraic_role == ROLE_SUBTRACTIVE
    assert p01.inclusion_state == INCLUSION_NOT_IN_BASE
    assert p01.embedded_term_state == EMBEDDED_NO
    assert p01.term_set_status == "SPECIFIED"
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" not in algebra.unresolved_required_terms
    assert "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED" in algebra.unresolved_required_terms
    assert algebra.algebra_completeness_status == "INCOMPLETE"


def test_protected_surfaces_and_live_pins_remain_fail_closed() -> None:
    forbidden_imports = (
        "src.trading",
        "src.strategy",
        "src.learning",
        "src.ranking",
        "LiveExecutionPort",
        "construct_live_execution_port_v1",
    )
    for rel in PROTECTED_SURFACES:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for token in forbidden_imports:
            assert token not in text
    contract = _contract()
    assert contract.master_v2_is_not_p01_authority == "true"
    assert contract.double_play_is_not_p01_authority == "true"
    assert contract.live_execution_is_not_p01_authority == "true"
    dag = live_admission_gap_dag_v1()
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == (
        "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED"
    )
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert dag["P01_PRODUCT_SEMANTICS_COMPLETE"] is True
    assert dag["P01_RECONSTRUCTION_ALGEBRA_CONTRACT_COMPLETE"] is True
    assert dag["P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_RESOLVED"] is False
    assert dag["P01_INPUT_FRESHNESS_RULE_RESOLVED"] is False
    assert dag["P01_PREDICATE_INPUT_MEMBER"] == "GOVERNED_P01_REDUCTION_DIRECTIVE_V1"
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_runbook_ap_consumes_owner_selection_without_rewriting_ao() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    ap_section = _ap_section()
    ao_start = runbook.index(AO_HEADING)
    ao_section = runbook[ao_start : runbook.index(AP_HEADING, ao_start)]
    assert "THIS_SLICE=11.2.1.AO" in ao_section
    assert "THIS_SLICE=11.2.1.AP" not in ao_section
    assert "P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED=false" in ao_section
    assert (
        "OWNER_SELECTION=OWNER_SELECT_P01_OP_GOVERNED_REDUCTION_DIRECTIVE_SINGLE_PR_CLOSEOUT_V1"
        in ap_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in ap_section
    assert "P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_SCHEMA_PRESENT=true" in (
        ap_section
    )
    assert "P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED=true" in ap_section
    assert "P01_APPLICATION_TRUE_RULE_RESOLVED=true" in ap_section
    assert "P01_APPLICATION_FALSE_RULE_RESOLVED=true" in ap_section
    assert "P01_PRODUCT_SEMANTICS_COMPLETE=true" in ap_section
    assert "P01_RECONSTRUCTION_ALGEBRA_CONTRACT_COMPLETE=true" in ap_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED=false" in ap_section or (
        "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED=true" in ap_section
    )
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in ap_section
    assert "P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_RESOLVED=false" in ap_section
    assert "P01_INPUT_FRESHNESS_RULE_RESOLVED=false" in ap_section
    assert P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_BLOCKER in ap_section
    assert (
        "EARLIEST_DECOMPOSED_CONTRACT_GAP=U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED"
        in (ap_section)
    )
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
        in ap_section
    )
    assert "P01_CLOSEOUT_DOES_NOT_RESOLVE_ACCOUNT_EQUITY_SOURCE_MAPPING=true" in ap_section
    assert "LIVE_ENABLED=false" in ap_section
    assert "LIVE_ARMED=false" in ap_section
    assert "WIRE_SEND_PERMITTED=false" in ap_section
    assert (
        "DOCS_TOKEN_FULL_CORE_TYPED_P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_V1"
        in (spec)
    )
    with pytest.raises(P01ReconstructionSemanticAndAlgebraCloseoutContractError) as runtime:
        build_p01_reconstruction_semantic_and_algebra_closeout_contract_v1(
            p01_reconstruction_semantic_and_algebra_closeout_contract_id=(
                "SYNTHETIC_P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_ID"
            ),
            p01_runtime_instance_present="true",
        )
    assert "P01_P01_RUNTIME_INSTANCE_PRESENT_FORBIDDEN" in str(runtime.value) or (
        "FORBIDDEN" in str(runtime.value)
    )
