"""F1/M9 selection policy + prospective preregistration (no campaign execution)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.governance.explicit_productive_authorization_v1 import AUTHORIZED_FOR_PRODUCTIVE_APPLY
from src.governance.f1_m9_canonical_productive_candidate_adjudication_v1 import (
    adjudicate_canonical_f1_m9_productive_candidate_v1,
)
from src.governance.f1_m9_canonical_productive_candidate_evidence_census_v1 import (
    CAMPAIGN_EXECUTION_BLOCKER,
    EVIDENCE_CLASS_COUNTERFACTUAL,
    run_f1_m9_canonical_productive_candidate_evidence_census_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_preregistration_v1 import (
    assert_historical_preregistration_unchanged_v1,
    load_prospective_candidate_selection_campaign_preregistration_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_evidence_leakage_guard_v1 import (
    assert_decision_evidence_downstream_of_new_preregistration_v1,
    historical_evidence_cannot_select_v1,
)
from src.governance.f1_m9_productive_candidate_selection_policy_closure_v1 import (
    EARLIEST_REMAINING_BLOCKER,
    prove_f1_m9_productive_candidate_selection_policy_and_prospective_campaign_v1,
)
from src.governance.f1_m9_productive_candidate_selection_policy_v1 import (
    HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID,
    HISTORICAL_PREREGISTRATION_DIGEST,
    OUTCOME_NO_SELECTION,
    OUTCOME_SELECTED,
    RESEARCH_CONCLUSION_INSUFFICIENT,
    RESEARCH_CONCLUSION_REGION_PENDING,
    apply_f1_m9_selection_rule_v1,
    load_owner_selection_policy_v1,
    resolve_f1_m9_selection_policy_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_preregistration_v1 import (
    resolve_prospective_preregistration_v1,
)
from src.governance.f1_m9_real_productive_apply_preparation_closure_v1 import (
    prove_f1_m9_real_productive_apply_governed_preparation_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)
from src.research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    RESEARCH_CONCLUSION_NO_ROBUST,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_historical_preregistration_immutable_and_counterfactual() -> None:
    assert assert_historical_preregistration_unchanged_v1(repo_root=REPO_ROOT)
    historical = json.loads(
        (
            REPO_ROOT
            / "config/research/canonical_volatility_numeric_max_age_productive_evidence_session_"
            "preregistration_r1_active_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert "THRESHOLD_SELECTION" in historical["abort_block_criteria"]
    assert historical["non_promotion_invariants"]["COUNTERFACTUAL_ONLY"] is True
    assert historical["preregistration_digest"] == HISTORICAL_PREREGISTRATION_DIGEST


def test_historical_campaign_cannot_select() -> None:
    assert historical_evidence_cannot_select_v1(
        historical_campaign_id=HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID,
        historical_preregistration_digest=HISTORICAL_PREREGISTRATION_DIGEST,
    )
    guard = assert_decision_evidence_downstream_of_new_preregistration_v1(
        {
            "campaign_id": HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID,
            "preregistration_digest": HISTORICAL_PREREGISTRATION_DIGEST,
            "decision_making_evidence_timestamp_utc": "2026-09-24T18:00:00Z",
        },
        repo_root=REPO_ROOT,
    )
    assert guard["historical_evidence_decision_leakage"] is True
    assert guard["selection_permitted"] is False
    assert guard["forced_outcome"] == OUTCOME_NO_SELECTION


def test_owner_selection_policy_frozen_and_complete() -> None:
    resolved = resolve_f1_m9_selection_policy_v1(repo_root=REPO_ROOT)
    assert resolved.owner_selection_policy_resolved is True
    assert resolved.f1_m9_scoped_candidate_selection_policy_created is True
    assert resolved.admissible_parameter_space_resolved is True
    assert resolved.objective_semantics_resolved is True
    assert resolved.evidence_requirements_resolved is True
    policy = load_owner_selection_policy_v1(repo_root=REPO_ROOT)
    assert (
        policy["candidate_selection_authority"]
        == "F1_M9_SCOPED_RESEARCH_TO_PROPOSAL_SELECTION_ONLY"
    )
    assert "TRADING_DECISION_AUTHORITY" in policy["forbidden_authorities"]


def test_new_preregistration_authorizes_selection_only_within_campaign() -> None:
    prereg = load_prospective_candidate_selection_campaign_preregistration_v1(repo_root=REPO_ROOT)
    assert prereg["threshold_selection_authorized"] is True
    assert prereg["campaign_execution_authorized"] is False
    assert prereg["productive_apply_authorized"] is False
    state = resolve_prospective_preregistration_v1(repo_root=REPO_ROOT)
    assert state.new_prospective_campaign_preregistered is True
    assert state.new_prospective_campaign_executed is False
    assert state.new_decision_making_evidence_generated is False
    assert state.threshold_selection_authorized_within_new_campaign is True


def test_pre_preregistration_evidence_cannot_decide_candidate() -> None:
    prereg = load_prospective_candidate_selection_campaign_preregistration_v1(repo_root=REPO_ROOT)
    guard = assert_decision_evidence_downstream_of_new_preregistration_v1(
        {
            "campaign_id": prereg["campaign_id"],
            "preregistration_digest": prereg["preregistration_digest"],
            "decision_making_evidence_timestamp_utc": "2026-09-24T20:00:00Z",
        },
        repo_root=REPO_ROOT,
    )
    assert guard["historical_evidence_decision_leakage"] is True


def test_selection_rule_fail_closed_paths() -> None:
    base_rejection = [
        {"candidate_id": "CANDIDATE_300_S", "rejected": False},
        {"candidate_id": "CANDIDATE_600_S", "rejected": False},
    ]
    assert (
        apply_f1_m9_selection_rule_v1(
            research_conclusion=RESEARCH_CONCLUSION_INSUFFICIENT,
            robust_candidate_region=[300, 600],
            rejection_matrix=base_rejection,
        )["outcome"]
        == OUTCOME_NO_SELECTION
    )
    assert (
        apply_f1_m9_selection_rule_v1(
            research_conclusion=RESEARCH_CONCLUSION_NO_ROBUST,
            robust_candidate_region=[300],
            rejection_matrix=[{"candidate_id": "CANDIDATE_300_S", "rejected": False}],
        )["outcome"]
        == OUTCOME_NO_SELECTION
    )
    tie = apply_f1_m9_selection_rule_v1(
        research_conclusion=RESEARCH_CONCLUSION_REGION_PENDING,
        robust_candidate_region=[300, 600],
        rejection_matrix=base_rejection,
    )
    assert tie["outcome"] == OUTCOME_NO_SELECTION
    oos_fail = apply_f1_m9_selection_rule_v1(
        research_conclusion=RESEARCH_CONCLUSION_REGION_PENDING,
        robust_candidate_region=[300],
        rejection_matrix=[{"candidate_id": "CANDIDATE_300_S", "rejected": True}],
    )
    assert oos_fail["outcome"] == OUTCOME_NO_SELECTION


def test_unique_survivor_selects_proposal_without_productive_authority() -> None:
    selected = apply_f1_m9_selection_rule_v1(
        research_conclusion=RESEARCH_CONCLUSION_REGION_PENDING,
        robust_candidate_region=[600],
        rejection_matrix=[{"candidate_id": "CANDIDATE_600_S", "rejected": False}],
    )
    assert selected["outcome"] == OUTCOME_SELECTED
    assert selected["selected_max_age_seconds"] == 600
    assert selected["productive_authorization"] is False
    assert selected["owner_apply_record_materialization"] is False
    assert selected["productive_apply"] is False


def test_census_and_adjudication_remain_unresolved() -> None:
    census = run_f1_m9_canonical_productive_candidate_evidence_census_v1(repo_root=REPO_ROOT)
    assert census.existing_campaign_evidence_class == EVIDENCE_CLASS_COUNTERFACTUAL
    assert census.existing_campaign_can_select_productive_candidate is False
    assert census.owner_policy_required is False
    assert census.candidate_selection_rule_id == "F1_M9_ROBUST_REGION_UNIQUE_SURVIVOR_POINT_V1"
    assert census.earliest_blocker == CAMPAIGN_EXECUTION_BLOCKER
    adj = adjudicate_canonical_f1_m9_productive_candidate_v1(repo_root=REPO_ROOT)
    assert adj.resolved is False
    assert adj.candidate_id is None
    assert adj.explicit_productive_authorization_resolved is False
    assert adj.earliest_blocker == CAMPAIGN_EXECUTION_BLOCKER


def test_closure_and_predecessor_regressions() -> None:
    assert prove_f1_m9_real_productive_apply_governed_preparation_v1(repo_root=REPO_ROOT)
    assert prove_f1_m9_productive_candidate_selection_policy_and_prospective_campaign_v1(
        repo_root=REPO_ROOT
    )
    assert EARLIEST_REMAINING_BLOCKER == CAMPAIGN_EXECUTION_BLOCKER
    assert AUTHORIZED_FOR_PRODUCTIVE_APPLY is False
    assert int(PRODUCTIVE_NUMERIC_VALUES_SET) == 0


def test_policy_digest_mutates_on_body_change() -> None:
    policy = load_owner_selection_policy_v1(repo_root=REPO_ROOT)
    mutated = copy.deepcopy(policy)
    mutated["objective_semantics"]["research_question"] = "mutated"
    from src.governance.f1_m9_productive_candidate_selection_policy_v1 import (
        verify_owner_selection_policy_v1,
    )

    with pytest.raises(ValueError):
        verify_owner_selection_policy_v1(mutated, repo_root=REPO_ROOT)
