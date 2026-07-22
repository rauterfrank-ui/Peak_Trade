"""Contract tests for canonical open MR entry-eligibility hypothesis backlog v1.

Definition-only governance. No backtest. No economic metrics. No holdout access.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.canonical_open_mr_entry_eligibility_hypothesis_backlog_v1 import (
    ADX_DI_DIRECTION_CONFIRMATION_HYPOTHESIS_ID,
    ADX_DI_DIRECTION_CONFIRMATION_HOLDOUT_V2_HYPOTHESIS_ID,
    BACKLOG_REL_PATH,
    FORBIDDEN_FEATURE_FAMILIES,
    GOVERNANCE_REL_PATH,
    HOLDOUT_OPAQUE_ID,
    NEXT_ELIGIBLE,
    QUEUED,
    REQUIRED_TERMINAL_FAIL_HYPOTHESIS_IDS,
    REQUIRED_TERMINAL_HYPOTHESIS_IDS,
    REQUIRED_TERMINAL_PASS_HYPOTHESIS_IDS,
    BacklogValidationError,
    assert_exactly_one_backlog_ssot,
    load_and_validate_repo_backlog,
    validate_backlog_contract,
)

REPO = Path(__file__).resolve().parents[2]
BACKLOG_PATH = REPO / BACKLOG_REL_PATH
GOVERNANCE_PATH = REPO / GOVERNANCE_REL_PATH


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_exactly_one_backlog_ssot_exists() -> None:
    assert_exactly_one_backlog_ssot(REPO)
    assert BACKLOG_PATH.is_file()
    assert GOVERNANCE_PATH.is_file()


def test_repo_backlog_validates() -> None:
    report = load_and_validate_repo_backlog(REPO)
    assert report["valid"] is True
    assert report["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert report["explicit_waiting_decision"] is False
    assert report["explicit_closeout_decision"] is True
    assert report["lane_auto_closed"] is False
    assert report["operator_decision"] == "CLOSE_LANE_NO_FURTHER_RESEARCH"
    assert report["lifecycle_contract_id"] == (
        "CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1"
    )
    assert report["lifecycle_authority"] == (
        "SHARED_POST_TERMINAL_LIFECYCLE_CONTRACT_V1_SOLE_AUTHORITY"
    )
    assert report["terminal_hypothesis_count"] == 7
    assert report["open_candidate_count"] == 0
    assert report["preregistered_count"] == 0
    assert report["development_run_count"] == 0
    assert report["evaluation_authorized"] is False
    assert report["holdout_forbidden"] is True
    assert report["runtime_locked"] is True
    assert report["next_eligible_hypothesis_id"] is None


def test_adx_di_terminal_pass_and_queue_empty() -> None:
    backlog = _load(BACKLOG_PATH)
    assert backlog["open_candidates"] == []
    assert backlog["preregistered_hypotheses"] == []
    terminals = {t["hypothesis_id"]: t for t in backlog["terminal_hypotheses"]}
    adx = terminals[ADX_DI_DIRECTION_CONFIRMATION_HYPOTHESIS_ID]
    assert adx["status"] == "TERMINAL_PASS"
    assert adx["pass_reason"] == "ALL_PASS_REQUIRES_MET"
    assert adx["feature_family"] == "adx_di_direction_confirmation"
    assert adx["holdout_run_count"] == 1
    assert adx["holdout_run_limit"] == 1
    assert adx["holdout_preregistration_status"] == "HOLDOUT_EVALUATION_EXECUTED_TERMINAL"
    assert adx["holdout_executed"] is True
    assert adx["holdout_result_class"] == "ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN"
    assert adx["successor_holdout_evaluation_hypothesis_id"] == (
        ADX_DI_DIRECTION_CONFIRMATION_HOLDOUT_V2_HYPOTHESIS_ID
    )
    assert adx["successor_holdout_run_count"] == 1
    assert adx["successor_holdout_run_limit"] == 1
    assert adx["successor_holdout_executed"] is True
    assert adx["successor_holdout_result_class"] == "FAIL"
    assert adx["successor_new_evaluation_not_rerun"] is True
    assert adx["evidence_ref"].endswith(
        "evaluate_adx_di_direction_confirmation_mr_eligibility_development_v1/"
    )
    macd = terminals["MACD_HISTOGRAM_COUNTERTREND_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1"]
    assert macd["status"] == "TERMINAL_FAIL"
    assert (
        "adx_di_direction_confirmation" in backlog["forbidden_feature_families_for_open_candidates"]
    )
    assert backlog["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert backlog["lifecycle_authority"] == (
        "SHARED_POST_TERMINAL_LIFECYCLE_CONTRACT_V1_SOLE_AUTHORITY"
    )
    assert backlog["explicit_closeout_decision"] is True
    assert backlog["explicit_waiting_decision"] is False
    assert backlog["lane_auto_closed"] is False
    assert backlog["verdict"] == (
        "CANONICAL_OPEN_MR_ENTRY_ELIGIBILITY_LANE_CLOSED_NO_FURTHER_RESEARCH_"
        "AFTER_EXPLICIT_OPERATOR_CLOSEOUT"
    )
    assert backlog["next_canonical_step"] == ("LANE_CLOSED_NO_FURTHER_RESEARCH_NO_EXECUTABLE_GO")
    assert (
        "REVIEW_DEFINITION_ONLY_EXIT_EFFICIENCY_PREREGISTRATION_NO_ENTRY_ELIGIBILITY_REOPEN"
        != backlog["next_canonical_step"]
    )


def test_all_terminal_hypotheses_captured() -> None:
    backlog = _load(BACKLOG_PATH)
    terminals = backlog["terminal_hypotheses"]
    assert [t["hypothesis_id"] for t in terminals] == list(REQUIRED_TERMINAL_HYPOTHESIS_IDS)
    fails = [t for t in terminals if t["status"] == "TERMINAL_FAIL"]
    passes = [t for t in terminals if t["status"] == "TERMINAL_PASS"]
    assert [t["hypothesis_id"] for t in fails] == list(REQUIRED_TERMINAL_FAIL_HYPOTHESIS_IDS)
    assert [t["hypothesis_id"] for t in passes] == list(REQUIRED_TERMINAL_PASS_HYPOTHESIS_IDS)
    assert len(fails) == 6
    assert len(passes) == 1


def test_open_candidate_count_empty() -> None:
    backlog = _load(BACKLOG_PATH)
    assert backlog["open_candidates"] == []


def test_priority_order_vacuous_when_empty() -> None:
    backlog = _load(BACKLOG_PATH)
    assert backlog["open_candidates"] == []


def test_no_next_eligible() -> None:
    backlog = _load(BACKLOG_PATH)
    next_ones = [c for c in backlog["open_candidates"] if c["queue_status"] == NEXT_ELIGIBLE]
    assert next_ones == []
    assert backlog["governance_rules"]["exactly_one_next_eligible_for_preregistration"] is False


def test_no_semantic_duplicate_feature_families() -> None:
    assert "adx_di_direction_confirmation" in FORBIDDEN_FEATURE_FAMILIES
    backlog = _load(BACKLOG_PATH)
    for candidate in backlog["open_candidates"]:
        assert candidate["feature_family"] not in FORBIDDEN_FEATURE_FAMILIES


def test_no_embedded_evaluation_results_or_runs() -> None:
    backlog = _load(BACKLOG_PATH)
    blob = json.dumps(backlog)
    for banned in (
        "baseline_metrics",
        "treatment_metrics",
        "measured_net_return",
        "measured_profit_factor",
        "economic_metrics",
        "comparison_decision",
        "probe_summary",
    ):
        assert banned not in backlog
        assert f'"{banned}"' not in blob
    assert backlog["development_run_count"] == 0
    assert backlog["evaluation_results_embedded"] is False
    assert backlog["evaluation_authorized"] is False
    assert backlog["backtest_authorized"] is False


def test_holdout_and_runtime_remain_locked() -> None:
    backlog = _load(BACKLOG_PATH)
    assert backlog["holdout_forbidden"] is True
    assert backlog["sealed_holdout_id"] == HOLDOUT_OPAQUE_ID
    assert backlog["sealed_holdout_content_inspection_authorized"] is False
    runtime = backlog["runtime_policy"]
    assert runtime["runtime_activated"] is False
    assert runtime["orders_allowed"] is False
    promo = backlog["promotion_and_economic_gate_policy"]
    assert promo["promotion_eligible"] is False
    assert promo["economic_validity_offline_gate_pass"] is False


def test_universe_and_governance_bindings() -> None:
    backlog = _load(BACKLOG_PATH)
    rules = backlog["governance_rules"]
    assert rules["open_candidate_count_min"] == 0
    assert rules["exactly_one_next_eligible_for_preregistration"] is False
    assert rules["economic_gate_closed"] is True
    assert rules["promotion_closed"] is True


def test_validator_rejects_second_next_eligible() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["governance_rules"]["open_candidate_count_min"] = 1
    bad["governance_rules"]["exactly_one_next_eligible_for_preregistration"] = True
    clone_a = {
        "hypothesis_id": "SYNTHETIC_FIRST_NEXT_ELIGIBLE_OPEN_CANDIDATE_V1",
        "status": "OPEN_UNPREREGISTERED",
        "queue_status": NEXT_ELIGIBLE,
        "feature_family": "synthetic_first_next_eligible_family",
        "priority_rank": 1,
        "priority_scores": {
            "semantic_distance": 5,
            "entry_effectiveness": 5,
            "measurability": 5,
            "low_additional_complexity": 5,
            "low_overfitting_risk": 5,
            "repo_support": 5,
        },
        "priority_score_total": 70,
        "causal_thesis": "synthetic",
        "independent_treatment_change": "synthetic",
        "expected_effect": "synthetic",
        "known_failure_modes": ["synthetic"],
        "repo_source_refs": ["synthetic"],
        "frozen_parameter_intent": {"x": 1},
        "not_a_parameter_retune_of": list(REQUIRED_TERMINAL_HYPOTHESIS_IDS),
        "semantic_distance_to_terminal": {
            tid: "synthetic" for tid in REQUIRED_TERMINAL_HYPOTHESIS_IDS
        },
    }
    clone_b = copy.deepcopy(clone_a)
    clone_b["hypothesis_id"] = "SYNTHETIC_SECOND_NEXT_ELIGIBLE_OPEN_CANDIDATE_V1"
    clone_b["feature_family"] = "synthetic_second_next_eligible_family"
    clone_b["priority_rank"] = 2
    clone_b["priority_scores"] = {
        "semantic_distance": 1,
        "entry_effectiveness": 1,
        "measurability": 1,
        "low_additional_complexity": 1,
        "low_overfitting_risk": 1,
        "repo_support": 1,
    }
    clone_b["priority_score_total"] = 14
    clone_b["queue_status"] = NEXT_ELIGIBLE
    bad["open_candidates"] = [clone_a, clone_b]
    with pytest.raises(BacklogValidationError, match="EXACTLY_ONE_NEXT_ELIGIBLE"):
        validate_backlog_contract(bad)


def test_validator_rejects_forbidden_feature_family_retune() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["governance_rules"]["open_candidate_count_min"] = 1
    bad["governance_rules"]["exactly_one_next_eligible_for_preregistration"] = True
    bad["open_candidates"] = [
        {
            "hypothesis_id": "SYNTHETIC_FORBIDDEN_FAMILY_OPEN_CANDIDATE_V1",
            "status": "OPEN_UNPREREGISTERED",
            "queue_status": NEXT_ELIGIBLE,
            "feature_family": "adx_di_direction_confirmation",
            "priority_rank": 1,
            "priority_scores": {
                "semantic_distance": 5,
                "entry_effectiveness": 5,
                "measurability": 5,
                "low_additional_complexity": 5,
                "low_overfitting_risk": 5,
                "repo_support": 5,
            },
            "priority_score_total": 70,
            "causal_thesis": "synthetic",
            "independent_treatment_change": "synthetic",
            "expected_effect": "synthetic",
            "known_failure_modes": ["synthetic"],
            "repo_source_refs": ["synthetic"],
            "frozen_parameter_intent": {"x": 1},
            "not_a_parameter_retune_of": list(REQUIRED_TERMINAL_HYPOTHESIS_IDS),
            "semantic_distance_to_terminal": {
                tid: "synthetic" for tid in REQUIRED_TERMINAL_HYPOTHESIS_IDS
            },
        }
    ]
    with pytest.raises(BacklogValidationError, match="SEMANTIC_DUPLICATE_FEATURE_FAMILY"):
        validate_backlog_contract(bad)


def test_validator_rejects_nonzero_development_run_count() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["development_run_count"] = 1
    with pytest.raises(BacklogValidationError, match="DEVELOPMENT_RUN_COUNT_NONZERO"):
        validate_backlog_contract(bad)


def test_governance_doc_marks_terminal_pass_and_closed_gate() -> None:
    text = GOVERNANCE_PATH.read_text(encoding="utf-8")
    assert "LANE_CLOSED_NO_FURTHER_RESEARCH" in text
    assert "CLOSE_LANE_NO_FURTHER_RESEARCH" in text
    assert "CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1" in text
    assert "OPEN_BACKLOG` is invalid" in text or "OPEN_BACKLOG is invalid" in text
    assert "PROMOTION_ELIGIBLE=false" in text
    assert ADX_DI_DIRECTION_CONFIRMATION_HYPOTHESIS_ID in text
    assert ADX_DI_DIRECTION_CONFIRMATION_HOLDOUT_V2_HYPOTHESIS_ID in text
    assert "TERMINAL_PASS" in text
    assert "HOLDOUT_EVALUATION_EXECUTED_TERMINAL" in text
    assert "LANE_CLOSED_NO_FURTHER_RESEARCH_NO_EXECUTABLE_GO" in text
    assert (
        "explicit_closeout_decision=true" in text
        or "explicit_closeout_decision`=true" in text
        or "explicit_closeout_decision=true" in text
    )
    assert "ALL_PASS_REQUIRES_MET" in text or "TERMINAL_PASS" in text
    assert "Economic offline gate remains closed" in text or "economic gate closed" in text.lower()
    assert "must not be re-run" in text or "Do **not** re-run" in text


def test_rejects_open_backlog_with_empty_inventory() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["status"] = "OPEN_BACKLOG"
    with pytest.raises(BacklogValidationError, match="STATUS_NOT_LANE_CLOSED_NO_FURTHER_RESEARCH"):
        validate_backlog_contract(bad)


def test_rejects_missing_shared_lifecycle_authority() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["lifecycle_authority"] = "LANE_LOCAL_STATUS_AUTHORITY"
    with pytest.raises(BacklogValidationError, match="LIFECYCLE_AUTHORITY_MISMATCH"):
        validate_backlog_contract(bad)


def test_rejects_auto_close_flag() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["lane_auto_closed"] = True
    with pytest.raises(BacklogValidationError, match="LANE_AUTO_CLOSED_FORBIDDEN"):
        validate_backlog_contract(bad)


def test_explicit_waiting_transition_invariants() -> None:
    backlog = _load(BACKLOG_PATH)
    assert backlog["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert backlog["explicit_waiting_decision"] is False
    assert backlog["explicit_closeout_decision"] is True
    assert backlog["lane_auto_closed"] is False
    assert backlog["open_candidates"] == []
    assert backlog["preregistered_hypotheses"] == []
    assert backlog["runtime_policy"]["runtime_activated"] is False
    assert backlog["runtime_policy"]["orders_allowed"] is False
    assert backlog["holdout_forbidden"] is True
    assert backlog["promotion_and_economic_gate_policy"]["promotion_eligible"] is False
    assert (
        "REVIEW_DEFINITION_ONLY_EXIT_EFFICIENCY_PREREGISTRATION_NO_ENTRY_ELIGIBILITY_REOPEN"
        != backlog["next_canonical_step"]
    )


def test_rejects_closed_lane_with_waiting_decision() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["explicit_waiting_decision"] = True
    with pytest.raises(BacklogValidationError, match="WAITING_DECISION_FORBIDDEN"):
        validate_backlog_contract(bad)
