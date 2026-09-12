"""Typed P01 haircut/reserve/depletion term contract. No productive reconstruction."""

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
    INCLUSION_PROVEN,
    INTERNAL_RECONSTRUCTION_PROVEN,
    INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT,
    INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT,
    LIVE_ACCOUNT_BOUND_JOIN_PRESENT,
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_RESTART_RECONSTRUCTED,
    MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING,
    MAPPING_PROVEN,
    NORMALIZATION_SCHEMA_PRESENT,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_TERM_CONTRACT_AUTHORITY_EFFECT,
    P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_CONTRACT_SCHEMA_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    RAW_TO_WITNESS_PROVEN,
    RECONCILIATION_CONTRACT_CREATED,
    RECONSTRUCTION_ALGEBRA_AUTHORITY_EFFECT,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT,
    RUNTIME_VALUE_BINDING_PRESENT,
    SEMANTIC_MAPPING_PROVEN,
    SOURCE_OBJECT_PRESENT,
    SOURCE_SELECTED,
    VENUE_WITNESS_SCHEMA_PRESENT,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    ALGEBRAIC_ROLE,
    APPLICABILITY_STATE,
    CURRENCY_VALUATION_DOMAIN,
    DOUBLE_COUNTING_GUARD,
    ECONOMIC_MEANING,
    EMBEDDED_STATE,
    EVIDENCE_CLASSIFICATION,
    INCLUSION_STATE,
    ORIGIN_CLASS,
    OVERLAP_STATE,
    POLICY_ID,
    REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS,
    SEMANTIC_CLASS,
    SIGN_CONSTRAINTS,
    TERM_ID,
    TERM_SEMANTICS_RESOLVED_STATUS,
    UNSPECIFIED_CLOSED_STATUS,
    VALUE_UNIT_CLASS,
    ZERO_VALIDITY_SEMANTICS,
    P01HaircutReserveDepletionTermContractError,
    P01HaircutReserveDepletionTermContractV1,
    build_p01_haircut_reserve_depletion_term_contract_v1,
    prove_p01_does_not_resolve_u04_u05_u06_v1,
    prove_p01_present_zero_distinct_from_missing_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    EMBEDDED_NO,
    EMBEDDED_NOT_APPLICABLE,
    INCLUSION_NOT_APPLICABLE,
    INCLUSION_NOT_IN_BASE,
    NUMERIC_MALFORMED,
    NUMERIC_MISSING,
    NUMERIC_PRESENT_ZERO,
    ROLE_REDUCTION_ONLY_UNSPECIFIED,
    ROLE_SUBTRACTIVE,
    SIGN_REDUCTION_ONLY,
    TERM_FEE,
    TERM_LIABILITY,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
    TERM_PENDING_ORDER_RESERVATION,
    UNRESOLVED_ALGEBRA_TERMS,
    ReconstructionAlgebraContractError,
    build_algebra_term_v1,
    build_reconstruction_algebra_contract_v1,
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
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_P01_HAIRCUT_RESERVE_DEPLETION_TERM_CONTRACT_V1.md"
)
SCHEMA_PATH = (
    REPO_ROOT
    / "src/ops/governed_productive_account_equity_authority_producer_v1"
    / "p01_haircut_reserve_depletion_term_contract_v1.py"
)
AA_HEADING = "11.2.1.AA FULL_CORE_TYPED_RECONSTRUCTION_ALGEBRA_CONTRACT"
AB_HEADING = "11.2.1.AB FULL_CORE_TYPED_P01_HAIRCUT_RESERVE_DEPLETION_TERM_CONTRACT"
AC_HEADING = "11.2.1.AC FULL_CORE_TYPED_P01_TERM_SET_AND_UNIT_CLASS_CONTRACT"


def _ab_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ab_start = runbook.index(AB_HEADING)
    return runbook[ab_start : runbook.index(AC_HEADING, ab_start)]


def test_p01_contract_constructs() -> None:
    contract = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID"
    )
    assert isinstance(contract, P01HaircutReserveDepletionTermContractV1)
    assert SCHEMA_CLASS == "P01_HAIRCUT_RESERVE_DEPLETION_TERM_CONTRACT_V1"
    assert contract.policy_id == POLICY_ID
    assert contract.term_id == TERM_ID
    assert contract.semantic_class == SEMANTIC_CLASS
    assert contract.algebraic_role == ALGEBRAIC_ROLE
    assert contract.algebraic_role == ROLE_REDUCTION_ONLY_UNSPECIFIED


def test_object_is_immutable() -> None:
    contract = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID"
    )
    with pytest.raises(FrozenInstanceError):
        contract.term_semantics_resolved_status = "true"  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID"
    )
    second = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID"
    )
    assert first.provenance_digest == second.provenance_digest
    assert first.provenance_digest == first.to_canonical_dict()["provenance_digest"]


def test_p01_identity_semantic_class_and_algebraic_role_are_explicit() -> None:
    contract = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID"
    )
    assert contract.term_id == TERM_P01_HAIRCUT_RESERVE_DEPLETION
    assert contract.semantic_class == "HAIRCUT_RESERVE_DEPLETION_FAMILY"
    assert contract.algebraic_role == "REDUCTION_ONLY_UNSPECIFIED"
    assert contract.economic_meaning == ECONOMIC_MEANING
    assert "MUST_NOT_INCREASE_EQUITY" in contract.economic_meaning
    with pytest.raises(P01HaircutReserveDepletionTermContractError) as raised:
        build_p01_haircut_reserve_depletion_term_contract_v1(
            p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID",
            algebraic_role=ROLE_SUBTRACTIVE,
        )
    assert "P01_INDEPENDENT_SUBTRACTIVE_UNPROVEN" in str(raised.value)


def test_provenance_applicability_unit_and_sign_are_represented() -> None:
    contract = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID"
    )
    assert contract.provenance_requirements.startswith("NO_VENUE_RAW_HAIRCUTS")
    assert contract.applicability_state == APPLICABILITY_STATE
    assert contract.value_unit_class == VALUE_UNIT_CLASS
    assert contract.currency_valuation_domain == CURRENCY_VALUATION_DOMAIN
    assert contract.sign_constraints == SIGN_CONSTRAINTS
    assert contract.negative_allowed == "false"
    assert contract.origin_class == ORIGIN_CLASS
    assert "UNSPECIFIED" in contract.value_unit_class
    with pytest.raises(P01HaircutReserveDepletionTermContractError) as inferred:
        build_p01_haircut_reserve_depletion_term_contract_v1(
            p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID",
            value_unit_class="USDC",
        )
    assert "P01_UNIT_INFERRED_CURRENCY_FORBIDDEN" in str(inferred.value)


def test_present_zero_is_distinct_from_missing_and_is_not_canonical_zero() -> None:
    present_zero, missing = prove_p01_present_zero_distinct_from_missing_v1()
    assert present_zero == NUMERIC_PRESENT_ZERO
    assert missing == NUMERIC_MISSING
    assert present_zero != missing
    contract = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID"
    )
    assert contract.numeric_state != NUMERIC_PRESENT_ZERO
    assert contract.numeric_state != NUMERIC_MISSING
    assert contract.zero_validity_semantics == ZERO_VALIDITY_SEMANTICS
    with pytest.raises(P01HaircutReserveDepletionTermContractError) as raised:
        build_p01_haircut_reserve_depletion_term_contract_v1(
            p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID",
            numeric_state=NUMERIC_PRESENT_ZERO,
        )
    assert "P01_ZERO_WITHOUT_EXPLICIT_POLICY_FORBIDDEN" in str(raised.value)


def test_missing_and_malformed_p01_are_not_zero() -> None:
    with pytest.raises(P01HaircutReserveDepletionTermContractError) as missing:
        build_p01_haircut_reserve_depletion_term_contract_v1(
            p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID",
            numeric_state=NUMERIC_MISSING,
        )
    assert "P01_MISSING_VALUE_ZERO_COERCION_FORBIDDEN" in str(missing.value)
    with pytest.raises(P01HaircutReserveDepletionTermContractError) as malformed:
        build_p01_haircut_reserve_depletion_term_contract_v1(
            p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID",
            numeric_state=NUMERIC_MALFORMED,
        )
    assert "P01_MALFORMED_VALUE_ZERO_COERCION_FORBIDDEN" in str(malformed.value)
    algebra = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    p01 = next(term for term in algebra.terms if term.term_id == TERM_P01_HAIRCUT_RESERVE_DEPLETION)
    assert p01.sign_semantics == SIGN_REDUCTION_ONLY
    with pytest.raises(ReconstructionAlgebraContractError) as algebra_missing:
        build_algebra_term_v1(
            **{**p01.to_canonical_dict(), "numeric_participation_state": NUMERIC_MISSING}
        )
    assert "MISSING_TERM_ZERO_COERCION_FORBIDDEN" in str(algebra_missing.value)


def test_unresolved_applicability_does_not_become_not_applicable() -> None:
    contract = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID"
    )
    assert contract.applicability_state != "NOT_APPLICABLE"
    with pytest.raises(P01HaircutReserveDepletionTermContractError) as raised:
        build_p01_haircut_reserve_depletion_term_contract_v1(
            p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID",
            applicability_state="NOT_APPLICABLE",
        )
    assert "P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN" in str(raised.value)
    algebra = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    p01 = next(term for term in algebra.terms if term.term_id == TERM_P01_HAIRCUT_RESERVE_DEPLETION)
    with pytest.raises(ReconstructionAlgebraContractError) as inclusion:
        build_algebra_term_v1(
            **{**p01.to_canonical_dict(), "inclusion_state": INCLUSION_NOT_APPLICABLE}
        )
    assert "P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN" in str(inclusion.value)
    with pytest.raises(ReconstructionAlgebraContractError) as embedded:
        build_algebra_term_v1(
            **{**p01.to_canonical_dict(), "embedded_term_state": EMBEDDED_NOT_APPLICABLE}
        )
    assert "P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN" in str(embedded.value)


def test_unresolved_overlap_does_not_become_safe_and_cannot_double_count() -> None:
    contract = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID"
    )
    assert contract.overlap_state == OVERLAP_STATE
    assert "UNKNOWN_OVERLAP_FAIL_CLOSED" in contract.overlap_state
    assert contract.double_counting_guard == DOUBLE_COUNTING_GUARD
    assert "SAFE" not in contract.overlap_state
    with pytest.raises(P01HaircutReserveDepletionTermContractError) as raised:
        build_p01_haircut_reserve_depletion_term_contract_v1(
            p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID",
            overlap_state="SAFE",
        )
    assert "P01_UNKNOWN_OVERLAP_AUTO_SAFE_FORBIDDEN" in str(raised.value)
    algebra = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    p01 = next(term for term in algebra.terms if term.term_id == TERM_P01_HAIRCUT_RESERVE_DEPLETION)
    with pytest.raises(ReconstructionAlgebraContractError) as guard:
        build_algebra_term_v1(
            **{**p01.to_canonical_dict(), "double_count_guard_id": "P01_OVERLAP_SAFE"}
        )
    assert "P01_UNKNOWN_OVERLAP_AUTO_SAFE_FORBIDDEN" in str(guard.value)
    with pytest.raises(ReconstructionAlgebraContractError) as embedded:
        build_algebra_term_v1(**{**p01.to_canonical_dict(), "embedded_term_state": EMBEDDED_NO})
    assert "P01_NON_EMBEDDING_UNPROVEN" in str(embedded.value)
    with pytest.raises(ReconstructionAlgebraContractError) as inclusion:
        build_algebra_term_v1(
            **{**p01.to_canonical_dict(), "inclusion_state": INCLUSION_NOT_IN_BASE}
        )
    assert "P01_BASE_EXCLUSION_UNPROVEN" in str(inclusion.value)


def test_unknown_provenance_blocks_inclusion_and_p01_remains_unresolved() -> None:
    contract = build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID"
    )
    assert contract.inclusion_state == INCLUSION_STATE
    assert contract.embedded_state == EMBEDDED_STATE
    assert contract.term_semantics_resolved_status == TERM_SEMANTICS_RESOLVED_STATUS
    assert contract.unspecified_closed_status == UNSPECIFIED_CLOSED_STATUS
    assert P01_TERM_SEMANTICS_RESOLVED is False
    assert P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is False
    assert "P01_NUMERIC_VALUE_PROVENANCE_UNSPECIFIED" in contract.provenance_requirements
    assert contract.remaining_unresolved_semantics == REMAINING_UNRESOLVED_SEMANTICS
    with pytest.raises(P01HaircutReserveDepletionTermContractError) as raised:
        build_p01_haircut_reserve_depletion_term_contract_v1(
            p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID",
            term_semantics_resolved_status="true",
        )
    assert "P01_TERM_SEMANTICS_RESOLVED_FORBIDDEN" in str(raised.value)


def test_unresolved_p01_cannot_produce_algebra_completeness() -> None:
    algebra = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert algebra.algebra_completeness_status == "INCOMPLETE"
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in algebra.unresolved_required_terms
    p01 = next(term for term in algebra.terms if term.term_id == TERM_P01_HAIRCUT_RESERVE_DEPLETION)
    assert p01.completeness_participation == "BLOCKING"
    build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID"
    )
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False


def test_resolved_p01_schema_still_does_not_resolve_u04_u05_u06() -> None:
    u04, u05, u06 = prove_p01_does_not_resolve_u04_u05_u06_v1()
    assert u04 in UNRESOLVED_ALGEBRA_TERMS
    assert u05 in UNRESOLVED_ALGEBRA_TERMS
    assert u06 in UNRESOLVED_ALGEBRA_TERMS
    algebra = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    by_id = {term.term_id: term for term in algebra.terms}
    assert by_id[TERM_PENDING_ORDER_RESERVATION].inclusion_state == "UNRESOLVED"
    assert by_id[TERM_LIABILITY].inclusion_state == "UNRESOLVED"
    assert by_id[TERM_FEE].inclusion_state == "UNRESOLVED"


def test_p01_does_not_create_runtime_reconstruction_mapping_or_producer() -> None:
    build_p01_haircut_reserve_depletion_term_contract_v1(
        p01_term_contract_id="SYNTHETIC_P01_TERM_CONTRACT_ID"
    )
    assert P01_TERM_CONTRACT_SCHEMA_PRESENT is True
    assert P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT is False
    assert P01_TERM_CONTRACT_AUTHORITY_EFFECT == "NONE"
    assert INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT is True
    assert INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT is False
    assert INTERNAL_RECONSTRUCTION_PROVEN is False
    assert RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT is True
    assert RECONSTRUCTION_ALGEBRA_AUTHORITY_EFFECT == "NONE"
    assert SOURCE_SELECTED is False
    assert SOURCE_OBJECT_PRESENT is False
    assert MAPPING_PROVEN is False
    assert RAW_TO_WITNESS_PROVEN is False
    assert FIELD_TO_DIMENSION_MAPPING_PRESENT is False
    assert SEMANTIC_MAPPING_PROVEN is False
    assert INCLUSION_PROVEN is False
    assert EQUITY_DIMENSION_BOUND is False
    assert MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert RUNTIME_VALUE_BINDING_PRESENT is False
    assert RECONCILIATION_CONTRACT_CREATED is False
    assert DIVERGENCE_POLICY_CREATED is False
    assert LIVE_ACCOUNT_BOUND_JOIN_PRESENT is False
    assert LIVE_RESTART_RECONSTRUCTED is False
    inspect_source = SCHEMA_PATH.read_text(encoding="utf-8")
    assert "AccountingPortfolioStateV1" not in inspect_source
    assert "LedgerSnapshot" not in inspect_source
    assert "equity_by_ccy" not in inspect_source
    assert "SimulatedPortfolioStateV1" not in inspect_source
    assert "FundingAccountBalanceObservationV1" not in inspect_source
    assert "FreshAvailableMarginObservationV1" not in inspect_source
    assert "def reconstruct" not in inspect_source
    with pytest.raises(P01HaircutReserveDepletionTermContractError) as raised:
        build_p01_haircut_reserve_depletion_term_contract_v1(p01_term_contract_id="totalEq|eq")
    assert "FALLBACK_CHAIN_FORBIDDEN" in str(raised.value)


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
    assert VENUE_WITNESS_SCHEMA_PRESENT is True
    assert NORMALIZATION_SCHEMA_PRESENT is True
    with pytest.raises(ExecutionPortConstructionForbiddenError) as raised:
        construct_live_execution_port_v1()
    assert "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_1" in str(raised.value)
    port = bind_simulated_execution_port_v1()
    assert isinstance(port, SimulatedExecutionPortV1)


def test_dag_keeps_p01_gap_without_selecting_source() -> None:
    dag = live_admission_gap_dag_v1()
    assert dag["P01_TERM_CONTRACT_SCHEMA_PRESENT"] is True
    assert dag["P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["P01_TERM_CONTRACT_AUTHORITY_EFFECT"] == "NONE"
    assert dag["P01_TERM_SEMANTICS_RESOLVED"] is False
    assert dag["P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED"] is False
    assert dag["RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT"] is True
    assert dag["RECONSTRUCTION_ALGEBRA_COMPLETE"] is False
    assert dag["EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY"] == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert dag["EARLIEST_DECOMPOSED_CONTRACT_GAP"] == ("P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED")
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED"


def test_runbook_ab_consumes_go_without_rewriting_aa() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    aa_start = runbook.index(AA_HEADING)
    ab_section = _ab_section()
    aa_section = runbook[aa_start : runbook.index(AB_HEADING, aa_start)]
    assert "RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT=true" in aa_section
    assert "THIS_SLICE=11.2.1.AB" not in aa_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_P01_HAIRCUT_RESERVE_DEPLETION_TERM_CONTRACT_V1"
        in ab_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in ab_section
    assert "P01_TERM_CONTRACT_SCHEMA_PRESENT=true" in ab_section
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in ab_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED=false" in ab_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in ab_section
    assert "U04_STATUS=DECIDED" in ab_section
    assert "U05_STATUS=DECIDED" in ab_section
    assert "U06_STATUS=DECIDED" in ab_section
    assert "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED" in ab_section
    assert "SOURCE_SELECTED=false" in ab_section
    assert "MAPPING_PROVEN=false" in ab_section
    assert "GOVERNED_PRODUCER_CREATED=false" in ab_section
    assert "RUNTIME_VALUE_BINDING_PRESENT=false" in ab_section
    assert "LIVE_ACCOUNT_BOUND_JOIN_PRESENT=false" in ab_section
    assert "STEP_29P_RISK_ADMISSIBLE=false" in ab_section
    assert "LIVE_ENABLED=false" in ab_section
    assert "LIVE_ARMED=false" in ab_section
    assert "WIRE_SEND_PERMITTED=false" in ab_section
    assert "CANONICAL_FORMULA_PROVEN=false" in ab_section
    assert (
        "EARLIEST_DECOMPOSED_CONTRACT_GAP=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in ab_section
    )
    assert "DOCS_TOKEN_FULL_CORE_TYPED_P01_HAIRCUT_RESERVE_DEPLETION_TERM_CONTRACT_V1" in spec
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in spec
    assert contract_mentions_evidence_class()
    assert "CANONICAL_AUTHORITY" in EVIDENCE_CLASSIFICATION


def contract_mentions_evidence_class() -> bool:
    return "UNRESOLVED=" in EVIDENCE_CLASSIFICATION
