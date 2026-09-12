"""Typed P01 member freshness inheritance adjudication. No productive reconstruction."""

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
    P01_EMBEDDED_STATE_RESOLVED,
    P01_EQUITY_BASE_INCLUSION_RESOLVED,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_AUTHORITY_EFFECT,
    P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_SCHEMA_PRESENT,
    P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED,
    P01_NUMERIC_VALUE_PROVENANCE_RESOLVED,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_member_freshness_inheritance_contract_v1 import (
    CANDIDATE_FRESHNESS_RULES_CLASSIFICATION,
    EVIDENCE_CLASSIFICATION,
    P01_MEMBER_FRESHNESS_RULE,
    P01_MEMBER_FRESHNESS_STATUS,
    P01_U09_FRESHNESS_RELATION,
    REJECTED_FRESHNESS_INFERENCES,
    REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS,
    P01MemberFreshnessInheritanceContractError,
    P01MemberFreshnessInheritanceContractV1,
    build_p01_member_freshness_inheritance_contract_v1,
    reject_p01_current_time_as_freshness_v1,
    reject_p01_member_aggregation_rule_v1,
    reject_p01_missing_freshness_as_fresh_v1,
    reject_p01_stale_as_admissible_v1,
    reject_p01_u09_freshness_as_p01_authority_v1,
    reject_p01_unproven_freshness_as_authority_v1,
    reject_p01_unproven_freshness_as_ignore_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_V1.md"
)
AH_HEADING = "11.2.1.AH FULL_CORE_TYPED_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT"
AI_HEADING = "11.2.1.AI FULL_CORE_TYPED_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT"
AJ_HEADING = "11.2.1.AJ FULL_CORE_TYPED_P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT"


def _ai_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ai_start = runbook.index(AI_HEADING)
    return runbook[ai_start : runbook.index(AJ_HEADING, ai_start)]


def test_p01_member_freshness_contract_constructs() -> None:
    contract = build_p01_member_freshness_inheritance_contract_v1(
        p01_member_freshness_inheritance_contract_id=(
            "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
        )
    )
    assert isinstance(contract, P01MemberFreshnessInheritanceContractV1)
    assert SCHEMA_CLASS == "P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_V1"
    assert contract.p01_member_freshness_status == P01_MEMBER_FRESHNESS_STATUS
    assert contract.p01_member_freshness_status == "UNPROVEN"
    assert contract.p01_member_freshness_rule == P01_MEMBER_FRESHNESS_RULE
    assert contract.p01_member_freshness_rule == "UNSPECIFIED"
    assert contract.p01_u09_freshness_relation == P01_U09_FRESHNESS_RELATION
    assert contract.p01_u09_freshness_relation == "UNSPECIFIED"
    assert contract.p01_member_freshness_inheritance_resolved_status == "false"
    assert P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED is False
    assert P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_SCHEMA_PRESENT is True
    assert P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT is False
    assert P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_AUTHORITY_EFFECT == "NONE"


def test_object_is_immutable() -> None:
    contract = build_p01_member_freshness_inheritance_contract_v1(
        p01_member_freshness_inheritance_contract_id=(
            "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
        )
    )
    with pytest.raises(FrozenInstanceError):
        contract.p01_member_freshness_inheritance_resolved_status = "true"  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = build_p01_member_freshness_inheritance_contract_v1(
        p01_member_freshness_inheritance_contract_id=(
            "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
        )
    )
    second = build_p01_member_freshness_inheritance_contract_v1(
        p01_member_freshness_inheritance_contract_id=(
            "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
        )
    )
    assert first.provenance_digest == second.provenance_digest


def test_unproven_freshness_is_not_authority() -> None:
    contract = build_p01_member_freshness_inheritance_contract_v1(
        p01_member_freshness_inheritance_contract_id=(
            "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
        )
    )
    assert contract.unknown_is_not_freshness_authority == "true"
    assert contract.unproven_is_not_freshness_authority == "true"
    assert contract.unspecified_is_not_freshness_authority == "true"
    with pytest.raises(P01MemberFreshnessInheritanceContractError) as raised:
        build_p01_member_freshness_inheritance_contract_v1(
            p01_member_freshness_inheritance_contract_id=(
                "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
            ),
            p01_member_freshness_inheritance_resolved_status="true",
        )
    assert "P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01MemberFreshnessInheritanceContractError) as helper:
        reject_p01_unproven_freshness_as_authority_v1(freshness_status="UNPROVEN")
    assert "P01_UNPROVEN_FRESHNESS_AUTHORITY_FORBIDDEN" in str(helper.value)


def test_u09_is_not_p01_freshness_authority() -> None:
    contract = build_p01_member_freshness_inheritance_contract_v1(
        p01_member_freshness_inheritance_contract_id=(
            "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
        )
    )
    assert contract.u09_is_not_p01_freshness_authority == "true"
    assert contract.p01_freshness_does_not_inherit_u09 == "true"
    assert contract.p01_freshness_not_equivalent_to_u09 == "true"
    assert contract.u09_comparison_evidence_only == "true"
    for inferred in ("U09", "INHERITS_U09", "EQUIVALENT_TO_U09", "COPY_U09"):
        with pytest.raises(P01MemberFreshnessInheritanceContractError) as raised:
            build_p01_member_freshness_inheritance_contract_v1(
                p01_member_freshness_inheritance_contract_id=(
                    "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
                ),
                p01_member_freshness_rule=inferred,
            )
        message = str(raised.value)
        assert (
            "P01_FRESHNESS_RULE_INFERRED_FORBIDDEN" in message
            or "P01_MEMBER_FRESHNESS_RULE_MISMATCH" in message
        )
    with pytest.raises(P01MemberFreshnessInheritanceContractError) as helper:
        reject_p01_u09_freshness_as_p01_authority_v1(freshness_rule="U09")
    assert "P01_FRESHNESS_RULE_INFERRED_FORBIDDEN" in str(
        helper.value
    ) or "P01_U09_FRESHNESS_AUTHORITY_FORBIDDEN" in str(helper.value)


def test_member_aggregation_rules_remain_unproven() -> None:
    contract = build_p01_member_freshness_inheritance_contract_v1(
        p01_member_freshness_inheritance_contract_id=(
            "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
        )
    )
    assert contract.oldest_member_wins_unproven == "true"
    assert contract.newest_member_wins_unproven == "true"
    assert contract.min_freshness_unproven == "true"
    assert contract.max_freshness_unproven == "true"
    for inferred in ("OLDEST_MEMBER", "NEWEST_MEMBER", "MIN_FRESHNESS", "MAX_FRESHNESS"):
        with pytest.raises(P01MemberFreshnessInheritanceContractError) as raised:
            build_p01_member_freshness_inheritance_contract_v1(
                p01_member_freshness_inheritance_contract_id=(
                    "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
                ),
                p01_member_freshness_rule=inferred,
            )
        assert "P01_FRESHNESS_RULE_INFERRED_FORBIDDEN" in str(
            raised.value
        ) or "P01_MEMBER_FRESHNESS_RULE_MISMATCH" in str(raised.value)
    with pytest.raises(P01MemberFreshnessInheritanceContractError) as helper:
        reject_p01_member_aggregation_rule_v1(freshness_rule="NEWEST_MEMBER")
    assert "P01_FRESHNESS_RULE_INFERRED_FORBIDDEN" in str(helper.value)


def test_current_time_is_not_p01_freshness() -> None:
    contract = build_p01_member_freshness_inheritance_contract_v1(
        p01_member_freshness_inheritance_contract_id=(
            "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
        )
    )
    assert contract.current_time_is_not_p01_freshness == "true"
    with pytest.raises(P01MemberFreshnessInheritanceContractError) as raised:
        build_p01_member_freshness_inheritance_contract_v1(
            p01_member_freshness_inheritance_contract_id=(
                "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
            ),
            p01_member_freshness_rule="CURRENT_TIME",
        )
    assert "P01_FRESHNESS_RULE_INFERRED_FORBIDDEN" in str(
        raised.value
    ) or "P01_MEMBER_FRESHNESS_RULE_MISMATCH" in str(raised.value)
    with pytest.raises(P01MemberFreshnessInheritanceContractError) as helper:
        reject_p01_current_time_as_freshness_v1(freshness_rule="CURRENT_TIME")
    assert "P01_FRESHNESS_RULE_INFERRED_FORBIDDEN" in str(
        helper.value
    ) or "P01_CURRENT_TIME_FRESHNESS_FORBIDDEN" in str(helper.value)


def test_missing_is_not_fresh_and_stale_is_not_admissible() -> None:
    contract = build_p01_member_freshness_inheritance_contract_v1(
        p01_member_freshness_inheritance_contract_id=(
            "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
        )
    )
    assert contract.missing_freshness_is_not_fresh == "true"
    assert contract.stale_p01_is_not_admissible == "true"
    with pytest.raises(P01MemberFreshnessInheritanceContractError) as missing:
        reject_p01_missing_freshness_as_fresh_v1(freshness_state="MISSING_IS_FRESH")
    assert "P01_MISSING_FRESHNESS_IS_NOT_FRESH" in str(
        missing.value
    ) or "P01_FRESHNESS_RULE_INFERRED_FORBIDDEN" in str(missing.value)
    with pytest.raises(P01MemberFreshnessInheritanceContractError) as stale:
        reject_p01_stale_as_admissible_v1(freshness_state="STALE_ADMISSIBLE")
    assert "P01_STALE_FRESHNESS_ADMISSION_FORBIDDEN" in str(
        stale.value
    ) or "P01_FRESHNESS_RULE_INFERRED_FORBIDDEN" in str(stale.value)


def test_unproven_freshness_cannot_authorize_ignore_or_fallback() -> None:
    contract = build_p01_member_freshness_inheritance_contract_v1(
        p01_member_freshness_inheritance_contract_id=(
            "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
        )
    )
    assert contract.unproven_cannot_authorize_ignore == "true"
    assert contract.unproven_cannot_authorize_fallback == "true"
    assert contract.fallback_freshness_state == "FORBIDDEN"
    for action in ("IGNORE", "FALLBACK", "STALE_FILTER"):
        with pytest.raises(P01MemberFreshnessInheritanceContractError) as raised:
            reject_p01_unproven_freshness_as_ignore_v1(requested_action=action)
        assert "P01_UNPROVEN_FRESHNESS_IGNORE_FORBIDDEN" in str(
            raised.value
        ) or "P01_FRESHNESS_RULE_INFERRED_FORBIDDEN" in str(raised.value)


def test_missing_and_malformed_inputs_fail_closed() -> None:
    with pytest.raises(P01MemberFreshnessInheritanceContractError) as missing:
        build_p01_member_freshness_inheritance_contract_v1(
            p01_member_freshness_inheritance_contract_id=(
                "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
            ),
            p01_member_freshness_rule=None,
        )
    assert "P01_FIELD_MISSING:p01_member_freshness_rule" in str(missing.value)
    with pytest.raises(P01MemberFreshnessInheritanceContractError) as malformed:
        build_p01_member_freshness_inheritance_contract_v1(
            p01_member_freshness_inheritance_contract_id=(
                "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
            ),
            p01_member_freshness_rule=False,
        )
    assert "P01_FIELD_NOT_STRING:p01_member_freshness_rule" in str(malformed.value)


def test_p01_global_semantics_and_algebra_remain_unresolved() -> None:
    contract = build_p01_member_freshness_inheritance_contract_v1(
        p01_member_freshness_inheritance_contract_id=(
            "SYNTHETIC_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_ID"
        )
    )
    assert contract.remaining_unresolved_semantics == REMAINING_UNRESOLVED_SEMANTICS
    assert "P01_NUMERIC_VALUE_PROVENANCE_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert P01_NUMERIC_VALUE_PROVENANCE_RESOLVED is False
    assert P01_TERM_SEMANTICS_RESOLVED is False
    assert P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert contract.rejected_freshness_inferences == REJECTED_FRESHNESS_INFERENCES
    assert "CANONICAL_AUTHORITY" in EVIDENCE_CLASSIFICATION
    assert "NO_WINNER_RATIFIED=true" in CANDIDATE_FRESHNESS_RULES_CLASSIFICATION
    dag = live_admission_gap_dag_v1()
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED"
    assert dag["P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED"] is False
    assert dag["P01_NUMERIC_VALUE_PROVENANCE_RESOLVED"] is False
    assert dag["P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_AUTHORITY_EFFECT"] == "NONE"
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_runbook_ai_consumes_go_without_rewriting_ah() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    ai_section = _ai_section()
    ah_start = runbook.index(AH_HEADING)
    ah_section = runbook[ah_start : runbook.index(AI_HEADING, ah_start)]
    assert "P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_SCHEMA_PRESENT=true" in ah_section
    assert "THIS_SLICE=11.2.1.AI" not in ah_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_V1"
        in ai_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in ai_section
    assert "P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_SCHEMA_PRESENT=true" in ai_section
    assert "P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED=false" in ai_section
    assert "P01_MEMBER_FRESHNESS_STATUS=UNPROVEN" in ai_section
    assert "P01_MEMBER_FRESHNESS_RULE=UNSPECIFIED" in ai_section
    assert "P01_U09_FRESHNESS_RELATION=UNSPECIFIED" in ai_section
    assert "P01_NUMERIC_VALUE_PROVENANCE_RESOLVED=false" in ai_section
    assert "P01_U04_OVERLAP_RESOLVED=false" in ai_section
    assert "P01_U05_OVERLAP_RESOLVED=false" in ai_section
    assert "P01_EMBEDDED_STATE_RESOLVED=false" in ai_section
    assert "P01_EQUITY_BASE_INCLUSION_RESOLVED=false" in ai_section
    assert "P01_APPLICABILITY_RESOLVED=false" in ai_section
    assert "P01_TERM_SET_RESOLVED=false" in ai_section
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=false" in ai_section
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in ai_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED=false" in ai_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in ai_section
    assert "CANONICAL_FORMULA_PROVEN=false" in ai_section
    assert "SOURCE_SELECTED=false" in ai_section
    assert "MAPPING_PROVEN=false" in ai_section
    assert (
        "EARLIEST_DECOMPOSED_CONTRACT_GAP=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in ai_section
    )
    assert "DOCS_TOKEN_FULL_CORE_TYPED_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_V1" in spec
    assert "P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED=false" in spec
    assert "P01_MEMBER_FRESHNESS_STATUS=UNPROVEN" in spec
    assert P01_TERM_SET_RESOLVED is True
    assert P01_VALUE_UNIT_CLASS_RESOLVED is False
    assert P01_APPLICABILITY_RESOLVED is False
    assert P01_EQUITY_BASE_INCLUSION_RESOLVED is False
    assert P01_EMBEDDED_STATE_RESOLVED is False
    assert P01_U04_OVERLAP_RESOLVED is False
    assert P01_U05_OVERLAP_RESOLVED is False
