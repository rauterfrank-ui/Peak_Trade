"""Typed reconstruction algebra contract. No productive reconstruction."""

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
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    ALGEBRA_AUTHORITY_EFFECT_NONE,
    ALGEBRA_REPRESENTATION,
    ALGEBRA_STATUS_COMPLETE,
    ALGEBRA_STATUS_INCOMPLETE,
    CANONICAL_FORMULA_REPRESENTATION,
    CANONICAL_FORMULA_STATUS_PROVEN,
    CANONICAL_FORMULA_STATUS_UNPROVEN,
    CONTRADICTION_PRESENT,
    DIMENSION_ID,
    EARLIEST_UNRESOLVED_ALGEBRA_TERM,
    EMBEDDED_YES,
    INCLUSION_UNRESOLVED,
    NUMERIC_MALFORMED,
    NUMERIC_MISSING,
    NUMERIC_NOT_COMPUTED,
    NUMERIC_PRESENT_ZERO,
    RECONSTRUCTION_CONTRACT_SCHEMA_CLASS,
    REJECTED_NAIVE_FORMULA,
    ROLE_ADDITIVE,
    ROLE_EMBEDDED_NOT_SEPARATE,
    ROLE_PROHIBITED,
    ROLE_SUBTRACTIVE,
    ROLE_VALUATION_INPUT_ONLY,
    SCHEMA_CLASS,
    SIGN_ADD,
    TERM_EQUITY_BASE,
    TERM_P01_HAIRCUT_RESERVE_DEPLETION,
    TERM_REALIZED_PNL,
    TERM_SLIPPAGE,
    TERM_UNREALIZED_PNL_MTM,
    UNRESOLVED_ALGEBRA_TERMS,
    AlgebraTermV1,
    ReconstructionAlgebraContractError,
    ReconstructionAlgebraContractV1,
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
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_RECONSTRUCTION_ALGEBRA_CONTRACT_V1.md"
SCHEMA_PATH = (
    REPO_ROOT
    / "src/ops/governed_productive_account_equity_authority_producer_v1"
    / "reconstruction_algebra_contract_v1.py"
)
Z_HEADING = "11.2.1.Z FULL_CORE_TYPED_INTERNAL_RECONSTRUCTION_CONTRACT"
AA_HEADING = "11.2.1.AA FULL_CORE_TYPED_RECONSTRUCTION_ALGEBRA_CONTRACT"
AB_HEADING = "11.2.1.AB FULL_CORE_TYPED_P01_HAIRCUT_RESERVE_DEPLETION_TERM_CONTRACT"


def _aa_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    aa_start = runbook.index(AA_HEADING)
    return runbook[aa_start : runbook.index(AB_HEADING, aa_start)]


def test_algebra_contract_constructs() -> None:
    contract = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    assert isinstance(contract, ReconstructionAlgebraContractV1)
    assert all(isinstance(term, AlgebraTermV1) for term in contract.terms)
    assert contract.algebra_completeness_status == ALGEBRA_STATUS_INCOMPLETE
    assert contract.target_semantic_dimension_id == DIMENSION_ID
    assert contract.reconstruction_contract_schema_class == (RECONSTRUCTION_CONTRACT_SCHEMA_CLASS)
    assert SCHEMA_CLASS == "RECONSTRUCTION_ALGEBRA_CONTRACT_V1"


def test_object_is_immutable() -> None:
    contract = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    with pytest.raises(FrozenInstanceError):
        contract.algebra_completeness_status = ALGEBRA_STATUS_COMPLETE  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    second = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    assert first.provenance_digest == second.provenance_digest
    assert first.provenance_digest == first.to_canonical_dict()["provenance_digest"]


def test_target_dimension_and_reconstruction_reference_are_typed() -> None:
    contract = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    assert contract.target_semantic_dimension_id == ("RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING")
    assert contract.reconstruction_contract_schema_class == ("INTERNAL_RECONSTRUCTION_CONTRACT_V1")
    with pytest.raises(ReconstructionAlgebraContractError) as raised:
        build_reconstruction_algebra_contract_v1(
            algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID",
            target_semantic_dimension_id="SOME_OTHER_DIMENSION",
        )
    assert "TARGET_DIMENSION_MISMATCH" in str(raised.value)


def test_schema_presence_is_not_algebra_completeness() -> None:
    contract = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    assert RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT is True
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert contract.algebra_completeness_status == ALGEBRA_STATUS_INCOMPLETE
    with pytest.raises(ReconstructionAlgebraContractError) as raised:
        build_reconstruction_algebra_contract_v1(
            algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID",
            algebra_completeness_status=ALGEBRA_STATUS_COMPLETE,
        )
    assert "COMPLETE_STATUS_FORBIDDEN" in str(raised.value)


def test_term_identity_and_additive_subtractive_distinction() -> None:
    contract = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    by_id = {term.term_id: term for term in contract.terms}
    assert by_id[TERM_EQUITY_BASE].algebraic_role == ROLE_ADDITIVE
    assert by_id[TERM_EQUITY_BASE].sign_semantics == SIGN_ADD
    assert by_id[TERM_P01_HAIRCUT_RESERVE_DEPLETION].algebraic_role == ROLE_SUBTRACTIVE
    assert by_id[TERM_REALIZED_PNL].algebraic_role == ROLE_EMBEDDED_NOT_SEPARATE
    assert by_id[TERM_UNREALIZED_PNL_MTM].algebraic_role == ROLE_EMBEDDED_NOT_SEPARATE
    assert by_id[TERM_SLIPPAGE].algebraic_role == ROLE_PROHIBITED
    assert by_id[TERM_P01_HAIRCUT_RESERVE_DEPLETION].term_set_status == "SPECIFIED"


def test_embedded_term_cannot_be_independently_counted() -> None:
    contract = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    realized = next(term for term in contract.terms if term.term_id == TERM_REALIZED_PNL)
    assert realized.embedded_term_state == EMBEDDED_YES
    with pytest.raises(ReconstructionAlgebraContractError) as raised:
        build_algebra_term_v1(**{**realized.to_canonical_dict(), "sign_semantics": SIGN_ADD})
    assert "EMBEDDED_TERM_CANNOT_BE_INDEPENDENTLY_COUNTED" in str(raised.value)


def test_valuation_only_input_cannot_become_additive() -> None:
    contract = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    mtm = next(term for term in contract.terms if term.term_id == TERM_UNREALIZED_PNL_MTM)
    with pytest.raises(ReconstructionAlgebraContractError) as raised:
        build_algebra_term_v1(
            **{
                **mtm.to_canonical_dict(),
                "algebraic_role": ROLE_VALUATION_INPUT_ONLY,
                "sign_semantics": SIGN_ADD,
            }
        )
    assert "VALUATION_INPUT_CANNOT_BECOME_ADDITIVE" in str(raised.value)


def test_prohibited_term_cannot_participate() -> None:
    contract = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    slippage = next(term for term in contract.terms if term.term_id == TERM_SLIPPAGE)
    with pytest.raises(ReconstructionAlgebraContractError) as raised:
        build_algebra_term_v1(
            **{
                **slippage.to_canonical_dict(),
                "numeric_participation_state": NUMERIC_PRESENT_ZERO,
            }
        )
    assert "PROHIBITED_TERM_CANNOT_PARTICIPATE" in str(raised.value)


def test_unresolved_required_term_blocks_completeness() -> None:
    contract = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    assert EARLIEST_UNRESOLVED_ALGEBRA_TERM in contract.unresolved_required_terms
    for name in UNRESOLVED_ALGEBRA_TERMS:
        assert name in contract.unresolved_required_terms
    u04 = next(term for term in contract.terms if term.term_id == "PENDING_ORDER_RESERVATION")
    assert u04.inclusion_state == INCLUSION_UNRESOLVED
    assert contract.algebra_completeness_status != ALGEBRA_STATUS_COMPLETE


def test_contradictory_term_blocks_completeness() -> None:
    contract = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    terms = tuple(
        build_algebra_term_v1(
            **{
                **term.to_canonical_dict(),
                "contradiction_state": CONTRADICTION_PRESENT
                if term.term_id == TERM_EQUITY_BASE
                else term.contradiction_state,
            }
        )
        for term in contract.terms
    )
    contradicted = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID",
        terms=terms,
        contradiction_status=CONTRADICTION_PRESENT,
    )
    assert contradicted.contradiction_status == CONTRADICTION_PRESENT
    assert contradicted.algebra_completeness_status == ALGEBRA_STATUS_INCOMPLETE
    with pytest.raises(ReconstructionAlgebraContractError) as raised:
        build_reconstruction_algebra_contract_v1(
            algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID",
            terms=terms,
            contradiction_status=CONTRADICTION_PRESENT,
            algebra_completeness_status=ALGEBRA_STATUS_COMPLETE,
        )
    assert "COMPLETE_STATUS_FORBIDDEN" in str(raised.value)


def test_duplicate_economic_effect_is_rejected() -> None:
    contract = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    base = next(term for term in contract.terms if term.term_id == TERM_EQUITY_BASE)
    p01 = next(
        term for term in contract.terms if term.term_id == TERM_P01_HAIRCUT_RESERVE_DEPLETION
    )
    duplicate = build_algebra_term_v1(
        **{**p01.to_canonical_dict(), "economic_effect_id": base.economic_effect_id}
    )
    terms = tuple(
        duplicate if term.term_id == TERM_P01_HAIRCUT_RESERVE_DEPLETION else term
        for term in contract.terms
    )
    with pytest.raises(ReconstructionAlgebraContractError) as raised:
        build_reconstruction_algebra_contract_v1(
            algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID",
            terms=terms,
        )
    assert "DUPLICATE_ECONOMIC_EFFECT" in str(raised.value)


def test_missing_and_malformed_terms_do_not_become_zero() -> None:
    contract = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    p01 = next(
        term for term in contract.terms if term.term_id == TERM_P01_HAIRCUT_RESERVE_DEPLETION
    )
    with pytest.raises(ReconstructionAlgebraContractError) as missing:
        build_algebra_term_v1(
            **{
                **p01.to_canonical_dict(),
                "numeric_participation_state": NUMERIC_MISSING,
            }
        )
    assert "MISSING_TERM_ZERO_COERCION_FORBIDDEN" in str(missing.value)
    with pytest.raises(ReconstructionAlgebraContractError) as malformed:
        build_algebra_term_v1(
            **{
                **p01.to_canonical_dict(),
                "numeric_participation_state": NUMERIC_MALFORMED,
            }
        )
    assert "MALFORMED_TERM_ZERO_COERCION_FORBIDDEN" in str(malformed.value)


def test_present_zero_remains_distinct_from_missing() -> None:
    contract = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    base = next(term for term in contract.terms if term.term_id == TERM_EQUITY_BASE)
    present_zero = build_algebra_term_v1(
        **{**base.to_canonical_dict(), "numeric_participation_state": NUMERIC_PRESENT_ZERO}
    )
    assert present_zero.numeric_participation_state == NUMERIC_PRESENT_ZERO
    assert present_zero.numeric_participation_state != NUMERIC_MISSING
    assert present_zero.numeric_participation_state != NUMERIC_NOT_COMPUTED
    terms = tuple(
        present_zero if term.term_id == TERM_EQUITY_BASE else term for term in contract.terms
    )
    rebuilt = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID",
        terms=terms,
    )
    rebuilt_base = next(term for term in rebuilt.terms if term.term_id == TERM_EQUITY_BASE)
    assert rebuilt_base.numeric_participation_state == NUMERIC_PRESENT_ZERO
    assert rebuilt.algebra_completeness_status == ALGEBRA_STATUS_INCOMPLETE
    assert rebuilt.canonical_formula_representation == CANONICAL_FORMULA_REPRESENTATION


def test_currency_and_valuation_dependencies_are_typed_and_block_false_completeness() -> None:
    contract = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    assert "USDC_NATIVE_OR_OWNER_RATIFIED_CONTRACT_ELSE_FAIL_CLOSED" in (
        contract.currency_unit_compatibility_status
    )
    assert contract.valuation_dependency_status == ("U03_MTM_IN_EQUITY_BASE_NOTIONAL_NOT_ADDITIVE")
    mtm = next(term for term in contract.terms if term.term_id == TERM_UNREALIZED_PNL_MTM)
    assert mtm.valuation_dependency == "NOTIONAL_PROHIBITED_AS_ADDEND"
    with pytest.raises(ReconstructionAlgebraContractError) as raised:
        build_reconstruction_algebra_contract_v1(
            algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID",
            currency_unit_compatibility_status="USD_EQUALS_USDC",
        )
    assert "CURRENCY_COMPATIBILITY_MISMATCH" in str(raised.value)
    with pytest.raises(ReconstructionAlgebraContractError) as valuation:
        build_reconstruction_algebra_contract_v1(
            algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID",
            valuation_dependency_status="UNRESOLVED_MARK_AUTO_ACCEPT",
        )
    assert "VALUATION_DEPENDENCY_MISMATCH" in str(valuation.value)


def test_naive_closed_form_and_canonical_formula_remain_unproven() -> None:
    contract = build_reconstruction_algebra_contract_v1(
        algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID"
    )
    assert contract.canonical_formula_status == CANONICAL_FORMULA_STATUS_UNPROVEN
    assert contract.canonical_formula_representation == ""
    assert REJECTED_NAIVE_FORMULA not in contract.algebra_representation
    assert "ALGEBRA_COMPLETE=false" in ALGEBRA_REPRESENTATION
    with pytest.raises(ReconstructionAlgebraContractError) as raised:
        build_reconstruction_algebra_contract_v1(
            algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID",
            canonical_formula_status=CANONICAL_FORMULA_STATUS_PROVEN,
            canonical_formula_representation=REJECTED_NAIVE_FORMULA,
        )
    assert "CANONICAL_FORMULA_PROVEN_FORBIDDEN" in str(raised.value)


def test_complete_algebra_does_not_create_runtime_reconstruction_or_mapping() -> None:
    build_reconstruction_algebra_contract_v1(algebra_contract_id="SYNTHETIC_ALGEBRA_CONTRACT_ID")
    assert INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT is True
    assert INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT is False
    assert INTERNAL_RECONSTRUCTION_PROVEN is False
    assert INTERNAL_RECONSTRUCTION_AUTHORITY_EFFECT == "NONE"
    assert RECONSTRUCTION_ALGEBRA_AUTHORITY_EFFECT == ALGEBRA_AUTHORITY_EFFECT_NONE
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
    assert GOVERNED_PRODUCTIVE_SOURCE_PRESENT is False
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
    assert "totalEq or eq or adjEq" not in inspect_source
    assert "def reconstruct" not in inspect_source
    with pytest.raises(ReconstructionAlgebraContractError) as raised:
        build_reconstruction_algebra_contract_v1(algebra_contract_id="totalEq|eq")
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


def test_dag_moves_gap_without_selecting_source() -> None:
    dag = live_admission_gap_dag_v1()
    assert dag["RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT"] is True
    assert dag["RECONSTRUCTION_ALGEBRA_COMPLETE"] is False
    assert dag["RECONSTRUCTION_ALGEBRA_AUTHORITY_EFFECT"] == "NONE"
    assert dag["INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT"] is True
    assert dag["INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["INTERNAL_RECONSTRUCTION_PROVEN"] is False
    assert dag["EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY"] == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert dag["EARLIEST_DECOMPOSED_CONTRACT_GAP"] == (
        "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED"
    )
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED"


def test_runbook_aa_consumes_go_without_rewriting_z() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    z_start = runbook.index(Z_HEADING)
    aa_section = _aa_section()
    z_section = runbook[z_start : runbook.index(AA_HEADING, z_start)]
    assert "INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT=true" in z_section
    assert "THIS_SLICE=11.2.1.AA" not in z_section
    assert "EARLIEST_DECOMPOSED_CONTRACT_GAP=RECONSTRUCTION_ALGEBRA_INCOMPLETE" in (z_section)
    assert "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_RECONSTRUCTION_ALGEBRA_CONTRACT_V1" in aa_section
    assert "OWNER_GO_STATUS=CONSUMED" in aa_section
    assert "RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT=true" in aa_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in aa_section
    assert "RECONSTRUCTION_ALGEBRA_AUTHORITY_EFFECT=NONE" in aa_section
    assert "INTERNAL_RECONSTRUCTION_PROVEN=false" in aa_section
    assert "INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT=false" in aa_section
    assert "SOURCE_OBJECT_PRESENT=false" in aa_section
    assert "SOURCE_SELECTED=false" in aa_section
    assert "MAPPING_PROVEN=false" in aa_section
    assert "GOVERNED_PRODUCER_CREATED=false" in aa_section
    assert "RUNTIME_VALUE_BINDING_PRESENT=false" in aa_section
    assert "LIVE_ACCOUNT_BOUND_JOIN_PRESENT=false" in aa_section
    assert "STEP_29P_RISK_ADMISSIBLE=false" in aa_section
    assert "LIVE_ENABLED=false" in aa_section
    assert "LIVE_ARMED=false" in aa_section
    assert "WIRE_SEND_PERMITTED=false" in aa_section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in aa_section
    assert "RECONCILIATION_CONTRACT_CREATED=false" in aa_section
    assert "CANONICAL_FORMULA_PROVEN=false" in aa_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in aa_section
    assert (
        "EARLIEST_DECOMPOSED_CONTRACT_GAP=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in aa_section
    )
    assert "DOCS_TOKEN_FULL_CORE_TYPED_RECONSTRUCTION_ALGEBRA_CONTRACT_V1" in spec
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in spec
