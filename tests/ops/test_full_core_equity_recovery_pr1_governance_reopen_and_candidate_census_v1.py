"""Equity recovery PR1: C17+ reopen mechanism and read-only census."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    C01_C16_REJECTION_STILL_BINDING,
    C01_C16_REVIVAL_ALLOWED,
    C17_CREATED,
    CANDIDATE_CENSUS_COMPLETE,
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    GOVERNED_PRODUCER_CREATED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_BOUNDARY_CURRENTLY_OPEN,
    MAPPING_PROVEN,
    MAPPING_REOPEN_MECHANISM_EXISTS,
    NEW_CANDIDATE_NAMESPACE_START,
    NEW_SOURCE_GENERATION_MECHANISM_RATIFIED,
    NEXT_EVIDENCE_GENERATION_BLOCKER,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SOURCE_ACCEPTANCE_CONJUNCTION_RATIFIED,
    SOURCE_PROMOTION_STATE_MACHINE_RATIFIED,
    SOURCE_SELECTED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.mapping_boundary_reopen_contract_v1 import (
    MappingBoundaryReopenContractError,
    evaluate_mapping_boundary_reopen_v1,
    future_reopen_predicate_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.source_acceptance_conjunction_v1 import (
    evaluate_source_acceptance_conjunction_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.source_candidate_census_v1 import (
    C01_C16_FINGERPRINTS,
    build_source_candidate_census_report_v1,
    materialize_c17_plus_candidates_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.source_candidate_v1 import (
    C01_C16_IDS,
    GovernedAccountEquitySourceCandidateError,
    build_governed_account_equity_source_candidate_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.source_promotion_state_machine_v1 import (
    STATE_ACCEPTABLE_FOR_OWNER_RATIFICATION,
    STATE_EVIDENCE_COMPLETE,
    STATE_GENERATED,
    STATE_MAPPING_PROVEN,
    STATE_OWNER_RATIFIED,
    STATE_PRODUCER_AUTHORIZED,
    STATE_RUNTIME_BINDING_AUTHORIZED,
    SourcePromotionStateMachineError,
    assert_legal_promotion_transition_v1,
    assert_owner_ratification_gate_v1,
    assert_pr1_candidate_status_allowed_v1,
    candidate_cannot_self_authorize_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_EQUITY_RECOVERY_PR1_GOVERNANCE_REOPEN_AND_CANDIDATE_CENSUS_V1.md"
)
AP_HEADING = "11.2.1.AP FULL_CORE_TYPED_P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT"
AQ_HEADING = "11.2.1.AQ FULL_CORE_EQUITY_RECOVERY_PR1_GOVERNANCE_REOPEN_AND_CANDIDATE_CENSUS"
_DIGEST = hashlib.sha256(b"equity-recovery-pr1-synthetic").hexdigest()
_COMPLETE_CHECKS = {
    "provenance_complete": "true",
    "account_venue_scope_bound": "true",
    "freshness_same_epoch_age": "true",
    "reconciliation_present": "true",
    "deterministic_digest": "true",
    "restart_reconstructability": "true",
    "step_29p_compatibility": "true",
    "unknown_inclusion_not_optimistic": "true",
    "durable_evidence_refs_present": "true",
}


def _aq_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    aq_start = runbook.index(AQ_HEADING)
    return runbook[aq_start : runbook.index("## 11.3 Autonomy state model", aq_start)]


def _synthetic_candidate_kwargs() -> dict[str, str]:
    return {
        "candidate_id": "C17_SYNTHETIC_TEST_ONLY",
        "generation_class": "NEW_SOURCE_GENERATION",
        "source_object_class": "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_V1",
        "producer_identity_claim": "ops.governed_productive_account_equity_authority_producer_v1",
        "account_scope": "bound_account_test",
        "venue_scope": "okx",
        "currency": "USDC",
        "unit_class": "ACCOUNT_EQUITY_SETTLEMENT_UNITS",
        "observation_authority_class": "NON_AUTHORITATIVE_CANDIDATE",
        "authority_contract_ref": "MASTER_RUNBOOK_11_2_1_AQ",
        "source_revision_or_digest": _DIGEST,
        "input_set_digest": _DIGEST,
        "freshness_contract_ref": "U09_FRESH_GET_PER_PRETRADE_DECISION",
        "reconciliation_contract_ref": "STEP_29P_EQUITY_RECONCILIATION_UNBOUND",
        "restart_reconstructability_class": "UNPROVEN",
        "step_29p_compatibility_class": "UNPROVEN",
        "evidence_refs": "tests/ops/test_full_core_equity_recovery_pr1_governance_reopen_and_candidate_census_v1.py",
        "candidate_status": "EVIDENCE_INCOMPLETE",
        "reason_codes": "SYNTHETIC_TEST_ONLY",
    }


def test_c01_c16_remain_fenced_and_namespace_starts_at_c17() -> None:
    assert C01_C16_REJECTION_STILL_BINDING is True
    assert C01_C16_REVIVAL_ALLOWED is False
    assert NEW_CANDIDATE_NAMESPACE_START == "C17"
    assert len(C01_C16_IDS) == 16
    assert len(C01_C16_FINGERPRINTS) == 16
    for candidate_id in C01_C16_IDS:
        with pytest.raises(GovernedAccountEquitySourceCandidateError) as err:
            build_governed_account_equity_source_candidate_v1(
                **{**_synthetic_candidate_kwargs(), "candidate_id": candidate_id}
            )
        assert "C01_C16_REVIVAL_FORBIDDEN" in str(err.value)


def test_candidate_cannot_self_authorize_or_skip_states() -> None:
    candidate_cannot_self_authorize_v1(claimed_status="EVIDENCE_COMPLETE")
    with pytest.raises(SourcePromotionStateMachineError):
        candidate_cannot_self_authorize_v1(claimed_status=STATE_OWNER_RATIFIED)
    with pytest.raises(SourcePromotionStateMachineError):
        assert_pr1_candidate_status_allowed_v1(STATE_MAPPING_PROVEN)
    with pytest.raises(SourcePromotionStateMachineError):
        assert_legal_promotion_transition_v1(current=STATE_GENERATED, nxt=STATE_OWNER_RATIFIED)
    with pytest.raises(SourcePromotionStateMachineError):
        assert_legal_promotion_transition_v1(
            current=STATE_ACCEPTABLE_FOR_OWNER_RATIFICATION,
            nxt=STATE_MAPPING_PROVEN,
        )
    assert_legal_promotion_transition_v1(current=STATE_GENERATED, nxt=STATE_EVIDENCE_COMPLETE)


def test_missing_malformed_wrong_currency_and_contradiction_fail_closed() -> None:
    missing = evaluate_source_acceptance_conjunction_v1(
        candidate_id="C17_SYNTHETIC_TEST_ONLY",
        checks={},
        observation_vs_authority_class="NON_AUTHORITATIVE_CANDIDATE",
        currency="USDC",
        unit_class="ACCOUNT_EQUITY_SETTLEMENT_UNITS",
        source_object_class="GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_V1",
        producer_identity_claim="ops.governed_productive_account_equity_authority_producer_v1",
        revival_equivalent=False,
        new_generation_identity=True,
        contradiction=False,
    )
    assert missing.acceptance_status == "EVIDENCE_INCOMPLETE"
    wrong_ccy = evaluate_source_acceptance_conjunction_v1(
        candidate_id="C17_SYNTHETIC_TEST_ONLY",
        checks=_COMPLETE_CHECKS,
        observation_vs_authority_class="NON_AUTHORITATIVE_CANDIDATE",
        currency="USD",
        unit_class="ACCOUNT_EQUITY_SETTLEMENT_UNITS",
        source_object_class="GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_V1",
        producer_identity_claim="ops.governed_productive_account_equity_authority_producer_v1",
        revival_equivalent=False,
        new_generation_identity=True,
        contradiction=False,
    )
    assert wrong_ccy.acceptance_status == "ACCEPTANCE_FAILED"
    assert "USD_IS_NOT_USDC" in wrong_ccy.reason_codes
    contradictory = evaluate_source_acceptance_conjunction_v1(
        candidate_id="C17_SYNTHETIC_TEST_ONLY",
        checks=_COMPLETE_CHECKS,
        observation_vs_authority_class="NON_AUTHORITATIVE_CANDIDATE",
        currency="USDC",
        unit_class="ACCOUNT_EQUITY_SETTLEMENT_UNITS",
        source_object_class="GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_V1",
        producer_identity_claim="ops.governed_productive_account_equity_authority_producer_v1",
        revival_equivalent=False,
        new_generation_identity=True,
        contradiction=True,
    )
    assert contradictory.acceptance_status == "ACCEPTANCE_FAILED"
    with pytest.raises(GovernedAccountEquitySourceCandidateError):
        build_governed_account_equity_source_candidate_v1(
            **{**_synthetic_candidate_kwargs(), "candidate_id": ""}
        )
    with pytest.raises(GovernedAccountEquitySourceCandidateError):
        build_governed_account_equity_source_candidate_v1(
            **{
                **_synthetic_candidate_kwargs(),
                "source_revision_or_digest": "not-a-digest",
            }
        )


def test_observation_cannot_mint_authority() -> None:
    minted = evaluate_source_acceptance_conjunction_v1(
        candidate_id="C17_SYNTHETIC_TEST_ONLY",
        checks=_COMPLETE_CHECKS,
        observation_vs_authority_class="AUTHORITY",
        currency="USDC",
        unit_class="ACCOUNT_EQUITY_SETTLEMENT_UNITS",
        source_object_class="GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_V1",
        producer_identity_claim="ops.governed_productive_account_equity_authority_producer_v1",
        revival_equivalent=False,
        new_generation_identity=True,
        contradiction=False,
    )
    assert minted.acceptance_status == "ACCEPTANCE_FAILED"
    assert "OBSERVATION_CANNOT_MINT_AUTHORITY" in minted.reason_codes
    with pytest.raises(GovernedAccountEquitySourceCandidateError) as err:
        build_governed_account_equity_source_candidate_v1(
            **{
                **_synthetic_candidate_kwargs(),
                "observation_authority_class": "AUTHORITY",
            }
        )
    assert "OBSERVATION_CANNOT_MINT_AUTHORITY" in str(err.value)


def test_owner_ratification_is_separate_gate_and_pr1_cannot_open_mapping() -> None:
    with pytest.raises(SourcePromotionStateMachineError):
        assert_owner_ratification_gate_v1(
            current=STATE_ACCEPTABLE_FOR_OWNER_RATIFICATION,
            nxt=STATE_OWNER_RATIFIED,
            owner_explicitly_ratifies_exact_candidate_id=False,
        )
    closed = evaluate_mapping_boundary_reopen_v1(
        reopen_contract_id="PR1_REOPEN_CLOSED",
        new_candidate_acceptable_for_owner_ratification=False,
        owner_explicitly_ratifies_exact_candidate_id=False,
        exact_candidate_id="NONE",
    )
    assert closed.mapping_boundary_currently_open == "false"
    assert closed.mapping_proven == "false"
    assert closed.governed_producer_created == "false"
    with pytest.raises(MappingBoundaryReopenContractError):
        evaluate_mapping_boundary_reopen_v1(
            reopen_contract_id="PR1_REOPEN_OWNER",
            new_candidate_acceptable_for_owner_ratification=True,
            owner_explicitly_ratifies_exact_candidate_id=True,
            exact_candidate_id="C17_SYNTHETIC_TEST_ONLY",
        )
    with pytest.raises(MappingBoundaryReopenContractError):
        evaluate_mapping_boundary_reopen_v1(
            reopen_contract_id="PR1_REOPEN_FORCE_OPEN",
            new_candidate_acceptable_for_owner_ratification=False,
            owner_explicitly_ratifies_exact_candidate_id=False,
            exact_candidate_id="NONE",
            persist_currently_open=True,
        )
    assert future_reopen_predicate_v1(
        new_candidate_acceptable_for_owner_ratification=True,
        owner_explicitly_ratifies_exact_candidate_id=True,
    )
    assert not future_reopen_predicate_v1(
        new_candidate_acceptable_for_owner_ratification=True,
        owner_explicitly_ratifies_exact_candidate_id=False,
    )


def test_census_finds_no_genuine_c17_and_does_not_invent_candidates() -> None:
    report = build_source_candidate_census_report_v1()
    created = materialize_c17_plus_candidates_v1()
    assert report.census_complete == "true"
    assert report.c17_created == "false"
    assert report.genuinely_new_candidate_count == "0"
    assert report.candidate_ids_created == "NONE"
    assert report.acceptable_for_owner_ratification_count == "0"
    assert report.mapping_proven == "false"
    assert created == ()
    assert CANDIDATE_CENSUS_COMPLETE is True
    assert C17_CREATED is False
    assert report.next_evidence_generation_blocker == NEXT_EVIDENCE_GENERATION_BLOCKER
    finding_ids = {item.finding_id for item in report.findings}
    assert "F01_C01_C16_BASELINE_REJECTION" in finding_ids
    assert "F09_P08_POS_C17_DIFFERENT_DIMENSION" in finding_ids
    assert all(item.c17_plus_materialized == "false" for item in report.findings)
    assert all(item.genuinely_new_source_generation == "false" for item in report.findings)


def test_no_mapping_producer_binding_or_live_unlock() -> None:
    dag = live_admission_gap_dag_v1()
    assert NEW_SOURCE_GENERATION_MECHANISM_RATIFIED is True
    assert SOURCE_ACCEPTANCE_CONJUNCTION_RATIFIED is True
    assert SOURCE_PROMOTION_STATE_MACHINE_RATIFIED is True
    assert MAPPING_REOPEN_MECHANISM_EXISTS is True
    assert MAPPING_BOUNDARY_CURRENTLY_OPEN is False
    assert CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is False
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert dag["MAPPING_BOUNDARY_CURRENTLY_OPEN"] is False
    assert dag["C17_CREATED"] is False
    assert dag["EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY"] == (
        EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY
    )
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_runbook_aq_consumes_owner_go_without_rewriting_ap_or_protected_surfaces() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    aq_section = _aq_section()
    ap_start = runbook.index(AP_HEADING)
    ap_section = runbook[ap_start : runbook.index(AQ_HEADING, ap_start)]
    assert "THIS_SLICE=11.2.1.AP" in ap_section
    assert "THIS_SLICE=11.2.1.AQ" not in ap_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_EQUITY_RECOVERY_PR1_GOVERNANCE_REOPEN_AND_CANDIDATE_CENSUS_V1"
        in aq_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in aq_section
    assert "C01_C16_REJECTION_STILL_BINDING=true" in aq_section
    assert "C01_C16_REVIVAL_ALLOWED=false" in aq_section
    assert "NEW_CANDIDATE_NAMESPACE_START=C17" in aq_section
    assert "MAPPING_BOUNDARY_CURRENTLY_OPEN=false" in aq_section
    assert "C17_CREATED=false" in aq_section
    assert "MAPPING_PROVEN=false" in aq_section
    assert "GOVERNED_PRODUCER_CREATED=false" in aq_section
    assert "LIVE_ENABLED=false" in aq_section
    assert "LIVE_ARMED=false" in aq_section
    assert "WIRE_SEND_PERMITTED=false" in aq_section
    assert "MASTER_V2_UNCHANGED=true" in aq_section
    assert "DOUBLE_PLAY_UNCHANGED=true" in aq_section
    assert "TOP20_RANKING_UNIVERSE_UNCHANGED=true" in aq_section
    assert "SELF_LEARNING_UNCHANGED=true" in aq_section
    assert "LEARNING_DDO_AUTHORITY_EFFECT=NONE" in aq_section
    assert "FULL_CORE_AUTONOMY_UNCHANGED=true" in aq_section
    assert "CONSTRUCT_LIVE_EXECUTION_PORT_V1=FORBIDDEN_IN_CAP_11_1" in aq_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in aq_section
    assert "P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_RESOLVED=false" in aq_section
    assert (
        "DOCS_TOKEN_FULL_CORE_EQUITY_RECOVERY_PR1_GOVERNANCE_REOPEN_AND_CANDIDATE_CENSUS_V1" in spec
    )
    assert "CORE_LOGIC_CHANGE=false" in aq_section
    assert "PROTECTED_SURFACES_UNCHANGED=true" in aq_section
    assert STATE_PRODUCER_AUTHORIZED not in (
        build_source_candidate_census_report_v1().candidate_ids_created
    )
    assert STATE_RUNTIME_BINDING_AUTHORIZED != "true"
