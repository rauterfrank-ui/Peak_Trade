"""Typed P01 haircut/reserve/depletion semantics. No productive reconstruction."""

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
    P01_DEPLETION_SEMANTICS_RESOLVED,
    P01_EMBEDDED_STATE_RESOLVED,
    P01_EQUITY_BASE_INCLUSION_RESOLVED,
    P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_AUTHORITY_EFFECT,
    P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_SCHEMA_PRESENT,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_HAIRCUT_SEMANTICS_RESOLVED,
    P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED,
    P01_NUMERIC_VALUE_PROVENANCE_RESOLVED,
    P01_RESERVE_SEMANTICS_RESOLVED,
    P01_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_RESOLVED,
    P01_U04_OVERLAP_RESOLVED,
    P01_U05_OVERLAP_RESOLVED,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SOURCE_SELECTED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_DECOMPOSED_CONTRACT_GAP,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_semantics_contract_v1 import (
    APPLICABILITY_UNSPECIFIED,
    CANDIDATE_ROLES_CLASSIFICATION,
    COMBINATION_RULE,
    EVIDENCE_CLASSIFICATION,
    IDENTITY_CLASS,
    REJECTED_COMBINATION_INFERENCES,
    REJECTED_FORMULA_INFERENCES,
    REJECTED_ROLE_INFERENCES,
    REMAINING_UNRESOLVED_SEMANTICS,
    ROLE_UNSPECIFIED,
    SCHEMA_CLASS,
    SIGN_UNSPECIFIED,
    UNIT_UNSPECIFIED,
    ZERO_ABSENCE_NA_RULE,
    P01HaircutReserveDepletionSemanticsContractError,
    P01HaircutReserveDepletionSemanticsContractV1,
    build_p01_haircut_reserve_depletion_semantics_contract_v1,
    reject_p01_combination_rule_v1,
    reject_p01_inferred_formula_v1,
    reject_p01_inferred_role_v1,
    reject_p01_missing_as_zero_v1,
    reject_p01_unspecified_semantics_as_arithmetic_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_TYPED_P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_V1.md"
)
AI_HEADING = "11.2.1.AI FULL_CORE_TYPED_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT"
AJ_HEADING = "11.2.1.AJ FULL_CORE_TYPED_P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT"


def _contract() -> P01HaircutReserveDepletionSemanticsContractV1:
    return build_p01_haircut_reserve_depletion_semantics_contract_v1(
        p01_haircut_reserve_depletion_semantics_contract_id=(
            "SYNTHETIC_P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_ID"
        )
    )


def _aj_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    aj_start = runbook.index(AJ_HEADING)
    return runbook[aj_start : runbook.index("## 11.3 Autonomy state model", aj_start)]


def test_p01_semantics_contract_constructs() -> None:
    contract = _contract()
    assert isinstance(contract, P01HaircutReserveDepletionSemanticsContractV1)
    assert SCHEMA_CLASS == "P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_V1"
    assert contract.p01_haircut_role == ROLE_UNSPECIFIED
    assert contract.p01_reserve_role == ROLE_UNSPECIFIED
    assert contract.p01_depletion_role == ROLE_UNSPECIFIED
    assert contract.p01_haircut_sign_semantics == SIGN_UNSPECIFIED
    assert contract.p01_reserve_sign_semantics == SIGN_UNSPECIFIED
    assert contract.p01_depletion_sign_semantics == SIGN_UNSPECIFIED
    assert contract.p01_haircut_unit_class == UNIT_UNSPECIFIED
    assert contract.p01_reserve_unit_class == UNIT_UNSPECIFIED
    assert contract.p01_depletion_unit_class == UNIT_UNSPECIFIED
    assert contract.p01_haircut_applicability == APPLICABILITY_UNSPECIFIED
    assert contract.p01_reserve_applicability == APPLICABILITY_UNSPECIFIED
    assert contract.p01_depletion_applicability == APPLICABILITY_UNSPECIFIED
    assert contract.p01_haircut_identity_class == IDENTITY_CLASS
    assert contract.p01_zero_absence_na_rule == ZERO_ABSENCE_NA_RULE
    assert contract.p01_haircut_reserve_depletion_combination_rule == COMBINATION_RULE
    assert contract.p01_haircut_semantics_resolved_status == "false"
    assert contract.p01_runtime_instance_present == "false"
    assert contract.p01_authority_effect == "NONE"
    assert P01_HAIRCUT_SEMANTICS_RESOLVED is False
    assert P01_RESERVE_SEMANTICS_RESOLVED is False
    assert P01_DEPLETION_SEMANTICS_RESOLVED is False
    assert P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_SCHEMA_PRESENT is True
    assert P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_RUNTIME_INSTANCE_PRESENT is False
    assert P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_AUTHORITY_EFFECT == "NONE"
    assert P01_RUNTIME_INSTANCE_PRESENT is False


def test_object_is_immutable() -> None:
    contract = _contract()
    with pytest.raises(FrozenInstanceError):
        contract.p01_haircut_semantics_resolved_status = "true"  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = _contract()
    second = _contract()
    assert first.provenance_digest == second.provenance_digest


def test_per_term_semantics_remain_unspecified() -> None:
    contract = _contract()
    assert contract.p01_haircut_positive_definition_state == "ABSENT"
    assert contract.p01_reserve_positive_definition_state == "ABSENT"
    assert contract.p01_depletion_positive_definition_state == "ABSENT"
    assert contract.terms_insufficiently_defined_for_algebraic_role == "true"
    assert contract.family_reduction_only_is_not_per_term_role == "true"
    with pytest.raises(P01HaircutReserveDepletionSemanticsContractError) as raised:
        build_p01_haircut_reserve_depletion_semantics_contract_v1(
            p01_haircut_reserve_depletion_semantics_contract_id=(
                "SYNTHETIC_P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_ID"
            ),
            p01_haircut_semantics_resolved_status="true",
        )
    assert "P01_HAIRCUT_SEMANTICS_RESOLVED_FORBIDDEN" in str(raised.value)


def test_inferred_roles_are_rejected() -> None:
    for inferred in (
        "MULTIPLICATIVE_HAIRCUT",
        "SUBTRACTIVE_ADJUSTMENT",
        "ADDITIVE_NEGATIVE_COMPONENT",
        "RESERVE_LOCK",
        "DEPLETION_STATE",
    ):
        with pytest.raises(P01HaircutReserveDepletionSemanticsContractError) as raised:
            build_p01_haircut_reserve_depletion_semantics_contract_v1(
                p01_haircut_reserve_depletion_semantics_contract_id=(
                    "SYNTHETIC_P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_ID"
                ),
                p01_haircut_role=inferred,
            )
        message = str(raised.value)
        assert (
            "P01_TERM_SEMANTICS_INFERRED_FORBIDDEN" in message
            or "P01_HAIRCUT_ROLE_UNSPECIFIED_REQUIRED" in message
        )
    with pytest.raises(P01HaircutReserveDepletionSemanticsContractError) as helper:
        reject_p01_inferred_role_v1(role="MULTIPLICATIVE_HAIRCUT")
    assert "P01_TERM_SEMANTICS_INFERRED_FORBIDDEN" in str(
        helper.value
    ) or "P01_TERM_ROLE_INFERRED_FORBIDDEN" in str(helper.value)


def test_inferred_formulas_are_rejected() -> None:
    contract = _contract()
    assert "P01_IS_NOT_EQUITY_BASE_MINUS_RESERVE" in contract.rejected_formula_inferences
    assert "P01_IS_NOT_EQUITY_BASE_TIMES_ONE_MINUS_HAIRCUT" in contract.rejected_formula_inferences
    assert "P01_IS_NOT_EQUITY_BASE_MINUS_DEPLETION" in contract.rejected_formula_inferences
    for formula in (
        "EQUITY_BASE_MINUS_RESERVE",
        "ONE_MINUS_HAIRCUT",
        "EQUITY_BASE_MINUS_DEPLETION",
    ):
        with pytest.raises(P01HaircutReserveDepletionSemanticsContractError) as raised:
            reject_p01_inferred_formula_v1(formula=formula)
        assert "P01_TERM_SEMANTICS_INFERRED_FORBIDDEN" in str(
            raised.value
        ) or "P01_INFERRED_FORMULA_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01HaircutReserveDepletionSemanticsContractError) as arithmetic:
        reject_p01_unspecified_semantics_as_arithmetic_v1(requested_op="SUBTRACTION")
    assert "P01_UNSPECIFIED_SEMANTICS_ARITHMETIC_FORBIDDEN" in str(
        arithmetic.value
    ) or "P01_TERM_SEMANTICS_INFERRED_FORBIDDEN" in str(arithmetic.value)


def test_missing_unknown_na_are_not_zero() -> None:
    contract = _contract()
    assert contract.missing_is_not_zero == "true"
    assert contract.unknown_is_not_zero == "true"
    assert contract.not_applicable_is_not_zero == "true"
    assert contract.absent_is_not_zero == "true"
    assert contract.unavailable_is_not_zero == "true"
    assert contract.embedded_is_not_omit == "true"
    assert contract.overlap_is_not_deduplicate == "true"
    for treatment in ("MISSING_IS_ZERO", "NA_IS_ZERO", "RESERVE_0", "HAIRCUT_0"):
        with pytest.raises(P01HaircutReserveDepletionSemanticsContractError) as raised:
            reject_p01_missing_as_zero_v1(treatment=treatment)
        assert "P01_MISSING_IS_NOT_ZERO" in str(
            raised.value
        ) or "P01_TERM_SEMANTICS_INFERRED_FORBIDDEN" in str(raised.value)


def test_combination_and_precedence_remain_unspecified() -> None:
    contract = _contract()
    assert contract.p01_precedence_rule == "UNSPECIFIED"
    assert contract.p01_haircut_reserve_depletion_combination_rule == "UNSPECIFIED"
    for rule in ("RESERVE_BEFORE_HAIRCUT", "HAIRCUT_BEFORE_RESERVE", "CUMULATIVE"):
        with pytest.raises(P01HaircutReserveDepletionSemanticsContractError) as raised:
            reject_p01_combination_rule_v1(combination_rule=rule)
        assert "P01_COMBINATION_RULE_INFERRED_FORBIDDEN" in str(
            raised.value
        ) or "P01_TERM_SEMANTICS_INFERRED_FORBIDDEN" in str(raised.value)


def test_missing_and_malformed_inputs_fail_closed() -> None:
    with pytest.raises(P01HaircutReserveDepletionSemanticsContractError) as missing:
        build_p01_haircut_reserve_depletion_semantics_contract_v1(
            p01_haircut_reserve_depletion_semantics_contract_id=(
                "SYNTHETIC_P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_ID"
            ),
            p01_haircut_role=None,
        )
    assert "P01_FIELD_MISSING:p01_haircut_role" in str(missing.value)
    with pytest.raises(P01HaircutReserveDepletionSemanticsContractError) as malformed:
        build_p01_haircut_reserve_depletion_semantics_contract_v1(
            p01_haircut_reserve_depletion_semantics_contract_id=(
                "SYNTHETIC_P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_ID"
            ),
            p01_haircut_role=False,
        )
    assert "P01_FIELD_NOT_STRING:p01_haircut_role" in str(malformed.value)


def test_p01_global_semantics_and_algebra_remain_unresolved() -> None:
    contract = _contract()
    assert contract.remaining_unresolved_semantics == REMAINING_UNRESOLVED_SEMANTICS
    assert P01_TERM_SEMANTICS_RESOLVED is False
    assert P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert contract.rejected_role_inferences == REJECTED_ROLE_INFERENCES
    assert contract.rejected_formula_inferences == REJECTED_FORMULA_INFERENCES
    assert contract.rejected_combination_inferences == REJECTED_COMBINATION_INFERENCES
    assert "CANONICAL_AUTHORITY" in EVIDENCE_CLASSIFICATION
    assert "NO_WINNER_RATIFIED=true" in CANDIDATE_ROLES_CLASSIFICATION
    dag = live_admission_gap_dag_v1()
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED"
    assert dag["P01_HAIRCUT_SEMANTICS_RESOLVED"] is False
    assert dag["P01_RESERVE_SEMANTICS_RESOLVED"] is False
    assert dag["P01_DEPLETION_SEMANTICS_RESOLVED"] is False
    assert dag["P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_AUTHORITY_EFFECT"] == "NONE"
    assert dag["P01_RUNTIME_INSTANCE_PRESENT"] is False
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_runbook_aj_consumes_go_without_rewriting_ai() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    aj_section = _aj_section()
    ai_start = runbook.index(AI_HEADING)
    ai_section = runbook[ai_start : runbook.index(AJ_HEADING, ai_start)]
    assert "P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_SCHEMA_PRESENT=true" in ai_section
    assert "THIS_SLICE=11.2.1.AJ" not in ai_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_P01_HAIRCUT_RESERVE_DEPLETION_CONTRACT_V1"
        in aj_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in aj_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_SCHEMA_PRESENT=true" in aj_section
    assert "P01_HAIRCUT_SEMANTICS_RESOLVED=false" in aj_section
    assert "P01_HAIRCUT_ROLE=UNSPECIFIED" in aj_section
    assert "P01_RESERVE_SEMANTICS_RESOLVED=false" in aj_section
    assert "P01_RESERVE_ROLE=UNSPECIFIED" in aj_section
    assert "P01_DEPLETION_SEMANTICS_RESOLVED=false" in aj_section
    assert "P01_DEPLETION_ROLE=UNSPECIFIED" in aj_section
    assert "P01_ZERO_ABSENCE_NA_RULE=UNSPECIFIED" in aj_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_COMBINATION_RULE=UNSPECIFIED" in aj_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED=false" in aj_section
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in aj_section
    assert "P01_RUNTIME_INSTANCE_PRESENT=false" in aj_section
    assert "P01_AUTHORITY_EFFECT=NONE" in aj_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in aj_section
    assert "CANONICAL_FORMULA_PROVEN=false" in aj_section
    assert "P01_NUMERIC_VALUE_PROVENANCE_RESOLVED=false" in aj_section
    assert "P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED=false" in aj_section
    assert (
        "EARLIEST_DECOMPOSED_CONTRACT_GAP=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in aj_section
    )
    assert "DOCS_TOKEN_FULL_CORE_TYPED_P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_V1" in spec
    assert "P01_HAIRCUT_SEMANTICS_RESOLVED=false" in spec
    assert P01_TERM_SET_RESOLVED is False
    assert P01_VALUE_UNIT_CLASS_RESOLVED is False
    assert P01_APPLICABILITY_RESOLVED is False
    assert P01_EQUITY_BASE_INCLUSION_RESOLVED is False
    assert P01_EMBEDDED_STATE_RESOLVED is False
    assert P01_U04_OVERLAP_RESOLVED is False
    assert P01_U05_OVERLAP_RESOLVED is False
    assert P01_NUMERIC_VALUE_PROVENANCE_RESOLVED is False
    assert P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED is False
