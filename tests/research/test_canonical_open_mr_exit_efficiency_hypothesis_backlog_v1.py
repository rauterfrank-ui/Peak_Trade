"""Contract tests for canonical open MR exit-efficiency hypothesis backlog (V8 TERMINAL_PASS)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.canonical_open_mr_exit_efficiency_hypothesis_backlog_v1 import (
    BACKLOG_REL_PATH,
    GOVERNANCE_REL_PATH,
    REQUIRED_FALSY_ZERO_HYGIENE_SURFACE,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_OBSERVABILITY_SURFACE,
    REQUIRED_V2_HYPOTHESIS_ID,
    REQUIRED_V3_HYPOTHESIS_ID,
    REQUIRED_V4_HYPOTHESIS_ID,
    REQUIRED_V5_HYPOTHESIS_ID,
    REQUIRED_V6_HYPOTHESIS_ID,
    REQUIRED_V6_MECHANISM_ID,
    REQUIRED_V7_HYPOTHESIS_ID,
    REQUIRED_V8_HYPOTHESIS_ID,
    BacklogValidationError,
    assert_exactly_one_exit_efficiency_backlog_ssot,
    load_and_validate_repo_backlog,
    validate_backlog_contract,
)

REPO = Path(__file__).resolve().parents[2]
BACKLOG_PATH = REPO / BACKLOG_REL_PATH
GOVERNANCE_PATH = REPO / GOVERNANCE_REL_PATH


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_exactly_one_exit_efficiency_backlog_ssot() -> None:
    assert_exactly_one_exit_efficiency_backlog_ssot(REPO)
    assert BACKLOG_PATH.is_file()
    assert GOVERNANCE_PATH.is_file()


def test_repo_backlog_one_definition_only_v8_preregistered() -> None:
    report = load_and_validate_repo_backlog(REPO)
    assert report["valid"] is True
    assert report["status"] == "POST_TERMINAL_OPERATOR_DECISION_REQUIRED"
    assert report["lifecycle_contract_id"] == (
        "CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1"
    )
    assert report["lifecycle_authority"] == (
        "SHARED_POST_TERMINAL_LIFECYCLE_CONTRACT_V1_SOLE_AUTHORITY"
    )
    assert report["preregistered_count"] == 0
    assert report["terminal_count"] == 8
    assert report["open_unpreregistered_count"] == 0
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["preregistered_hypothesis_id"] is None
    assert report["development_run_count"] == 8
    assert report["evaluation_authorized"] is False
    assert report["v7_evaluation_run_count"] == 1
    assert report["v7_result_class"] == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert report["v8_evaluation_run_count"] == 1
    assert report["v8_result_class"] == "PASS"
    assert report["holdout_forbidden"] is True
    assert report["rerun_allowed"] is False
    assert report["runtime_locked"] is True
    assert report["v2_evaluation_run_count"] == 1
    assert report["v2_is_rerun_of_v1"] is False
    assert report["v3_evaluation_run_count"] == 1
    assert report["v3_result_class"] == "FAIL"
    assert report["v3_is_rerun_of_v2"] is False
    assert report["v4_evaluation_run_count"] == 1
    assert report["v4_result_class"] == "INFRASTRUCTURE_FAILURE"
    assert report["v4_is_rerun_of_v3"] is False
    assert report["observability_surface"] == REQUIRED_OBSERVABILITY_SURFACE
    assert report["falsy_zero_hygiene_surface"] == REQUIRED_FALSY_ZERO_HYGIENE_SURFACE
    assert set(report["terminal_hypothesis_ids"]) == {
        REQUIRED_HYPOTHESIS_ID,
        REQUIRED_V2_HYPOTHESIS_ID,
        REQUIRED_V3_HYPOTHESIS_ID,
        REQUIRED_V4_HYPOTHESIS_ID,
        REQUIRED_V5_HYPOTHESIS_ID,
        REQUIRED_V6_HYPOTHESIS_ID,
        REQUIRED_V7_HYPOTHESIS_ID,
        REQUIRED_V8_HYPOTHESIS_ID,
    }
    assert report["v5_evaluation_run_count"] == 1
    assert report["v5_result_class"] == "INFRASTRUCTURE_FAILURE"
    assert report["v5_is_rerun_of_v4"] is False


def test_one_preregistered_v8_and_v7_terminal_entry_shape() -> None:
    backlog = _load(BACKLOG_PATH)
    assert backlog["preregistered_hypotheses"] == []
    assert backlog["governance_rules"]["preregistered_count_exact"] == 0
    assert backlog["open_unpreregistered_candidates"] == []
    assert backlog["status"] == "POST_TERMINAL_OPERATOR_DECISION_REQUIRED"
    assert backlog["lifecycle_authority"] == (
        "SHARED_POST_TERMINAL_LIFECYCLE_CONTRACT_V1_SOLE_AUTHORITY"
    )
    assert backlog["explicit_closeout_decision"] is False
    assert backlog["explicit_waiting_decision"] is False
    assert backlog["lane_auto_closed"] is False
    assert backlog["entry_eligibility_lane_status"] == ("POST_TERMINAL_OPERATOR_DECISION_REQUIRED")
    assert "CLOSED_NO_OPEN_CANDIDATES" not in json.dumps(backlog)
    assert backlog["development_run_count"] == 8
    assert len(backlog["terminal_hypotheses"]) == 8
    by_id = {e["hypothesis_id"]: e for e in backlog["terminal_hypotheses"]}
    v1 = by_id[REQUIRED_HYPOTHESIS_ID]
    assert v1["status"] == "TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert v1["evaluation_run_count"] == 1
    v2 = by_id[REQUIRED_V2_HYPOTHESIS_ID]
    assert v2["status"] == "TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert v2["evaluation_run_count"] == 1
    v3 = by_id[REQUIRED_V3_HYPOTHESIS_ID]
    assert v3["status"] == "TERMINAL_FAIL"
    assert v3["evaluation_run_count"] == 1
    assert v3["result_class"] == "FAIL"
    assert v3["economic_verdict"] == "FAIL"
    assert v3["decision_reason"] == "identical_arms_no_exit_divergence"
    assert v3["acceptance_criteria_met"] is False
    assert v3["fail"] is True
    assert v3["pass"] is False
    assert v3["rerun_allowed"] is False
    assert v3["falsy_zero_hygiene_surface"] == REQUIRED_FALSY_ZERO_HYGIENE_SURFACE
    assert v3["observability_surface"] == REQUIRED_OBSERVABILITY_SURFACE
    v4 = by_id[REQUIRED_V4_HYPOTHESIS_ID]
    assert v4["status"] == "TERMINAL_INFRASTRUCTURE_FAILURE"
    assert v4["evaluation_run_count"] == 1
    assert v4["result_class"] == "INFRASTRUCTURE_FAILURE"
    assert v4["economic_verdict"] == "NOT_EVALUATED"
    assert v4["evaluation_completed"] is False
    assert v4["rerun_allowed"] is False
    assert "NO_V3_RERUN" in backlog["explicit_non_actions"]
    assert "NO_HOLDOUT_AFTER_FAIL" in backlog["explicit_non_actions"]
    assert "NO_RETUNING_AFTER_FAIL" in backlog["explicit_non_actions"]
    assert "NO_V4_RERUN" in backlog["explicit_non_actions"]
    v5 = by_id[REQUIRED_V5_HYPOTHESIS_ID]
    assert v5["status"] == "TERMINAL_INFRASTRUCTURE_FAILURE"
    assert v5["evaluation_run_count"] == 1
    assert v5["result_class"] == "INFRASTRUCTURE_FAILURE"
    assert v5["economic_verdict"] == "NOT_EVALUATED"
    assert v5["evaluation_completed"] is False
    assert v5["rerun_allowed"] is False
    assert v5["baseline_members_completed"] == "3/46"
    assert v5["treatment_members_completed"] == "0/46"
    assert "NO_V5_RERUN" in backlog["explicit_non_actions"]
    v6 = by_id[REQUIRED_V6_HYPOTHESIS_ID]
    assert v6["status"] == "TERMINAL_FAIL"
    assert v6["evaluation_run_count"] == 1
    assert v6["result_class"] == "FAIL"
    assert v6["economic_verdict"] == "FAIL"
    assert v6["decision_reason"] == "NET_PROFIT_FACTOR_NOT_IMPROVED"
    assert v6["acceptance_criteria_met"] is False
    assert v6["fail"] is True
    assert v6["pass"] is False
    assert v6["rerun_allowed"] is False
    assert v6["mechanism_id"] == REQUIRED_V6_MECHANISM_ID
    assert v6["identical_exit_mechanism_to_development_v5"] is False
    assert v6["economic_change_vs_development_v5"] is True
    assert v6["baseline_members_completed"] == "46/46"
    assert v6["treatment_members_completed"] == "46/46"
    assert "NO_V6_RERUN" in backlog["explicit_non_actions"]
    assert "NO_V6_EVALUATION_IN_THIS_SLICE" not in backlog["explicit_non_actions"]
    assert "NO_V7_EVALUATION_IN_THIS_SLICE" not in backlog["explicit_non_actions"]
    assert "NO_V7_RERUN" in backlog["explicit_non_actions"]
    assert "NO_V7_REOPEN" in backlog["explicit_non_actions"]
    assert "NO_V8_EVALUATION_IN_THIS_SLICE" not in backlog["explicit_non_actions"]
    assert "NO_V8_RERUN" in backlog["explicit_non_actions"]
    assert "NO_V8_REOPEN" in backlog["explicit_non_actions"]
    assert "NO_HOLDOUT_AFTER_PASS" in backlog["explicit_non_actions"]
    assert "NO_RUNTIME_PROMOTION_FROM_DEVELOPMENT_PASS" in backlog["explicit_non_actions"]
    assert "NO_V9_AUTO_CREATE" in backlog["explicit_non_actions"]
    assert "NO_V7_AUTO_CREATE" in backlog["explicit_non_actions"]
    assert "NO_V8_AUTO_CREATE" in backlog["explicit_non_actions"]
    v7 = by_id[REQUIRED_V7_HYPOTHESIS_ID]
    assert v7["status"] == "TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert v7["evaluation_run_count"] == 1
    assert v7["result_class"] == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert v7["economic_verdict"] == "NOT_EVALUATED"
    assert v7["panel_backtest_executed"] is False
    assert v7["rerun_allowed"] is False
    assert v7.get("failure_class") == "FROZEN_EXIT_PARAMETERS_MISMATCH"
    assert v7.get("failure_timing") == "BEFORE_PANEL_ACCESS"
    assert v7.get("v7_reopen_allowed") is False
    assert v7.get("strategy_fail") is False
    assert v7.get("economic_fail") is False
    assert v7.get("measurement_pass") is False
    v8 = by_id[REQUIRED_V8_HYPOTHESIS_ID]
    assert v8["status"] == "TERMINAL_PASS"
    assert v8["evaluation_run_count"] == 1
    assert v8["result_class"] == "PASS"
    assert v8["economic_verdict"] == "PASS"
    assert v8["decision_reason"] == "ALL_PASS_REQUIRES_MET"
    assert v8["acceptance_criteria_met"] is True
    assert v8["pass"] is True
    assert v8["fail"] is False
    assert v8["panel_backtest_executed"] is True
    assert v8["run_slot_consumed"] is True
    assert v8["rerun_allowed"] is False
    assert v8["v8_reopen_allowed"] is False
    assert v8["baseline_members_completed"] == "46/46"
    assert v8["treatment_members_completed"] == "46/46"
    assert backlog["next_canonical_step"] == (
        "OPERATOR_GO_REQUIRED_FOR_ANY_NEW_DEFINITION_ONLY_PREREGISTRATION"
    )
    assert "NO_V6_AUTO_CREATE" not in backlog["explicit_non_actions"]
    assert "NO_V5_AUTO_CREATE" not in backlog["explicit_non_actions"]
    assert "NO_V3_ECONOMIC_RESULT_IMPORT" in backlog["explicit_non_actions"]
    assert "NO_V4_AUTO_CREATE" not in backlog["explicit_non_actions"]


def test_governance_doc_mentions_v8_prereg_and_v7_terminal() -> None:
    text = (
        REPO / "docs/governance/CANONICAL_OPEN_MR_EXIT_EFFICIENCY_HYPOTHESIS_BACKLOG_V1.md"
    ).read_text(encoding="utf-8")
    assert "POST_TERMINAL_OPERATOR_DECISION_REQUIRED" in text
    assert "CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1" in text
    assert "OPEN_BACKLOG` is invalid" in text or "OPEN_BACKLOG is invalid" in text
    assert "CLOSED_NO_OPEN_CANDIDATES" in text  # mentioned as removed/non-canonical
    assert "V6" in text
    assert "TERMINAL_FAIL" in text or "FAIL" in text
    assert "NET_PROFIT_FACTOR_NOT_IMPROVED" in text
    assert "V7" in text
    assert "preregistered_count_exact=0" in text
    assert "V8" in text
    assert "TERMINAL_PASS" in text
    assert "ALL_PASS_REQUIRES_MET" in text
    assert "FROZEN_EXIT_PARAMETERS_MISMATCH" in text
    assert "BEFORE_PANEL_ACCESS" in text
    assert "OPERATOR_GO_REQUIRED_FOR_ANY_NEW_DEFINITION_ONLY_PREREGISTRATION" in text
    assert "V5" in text or "v5" in text.lower()
    assert "V4" in text
    assert "INFRASTRUCTURE_FAILURE" in text or "Infrastructure" in text
    assert "NO_V8" in text or "No V8" in text or "No V8 auto-create" in text


def test_rejects_open_backlog_with_empty_inventory() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["status"] = "OPEN_BACKLOG"
    with pytest.raises(
        BacklogValidationError, match="STATUS_NOT_POST_TERMINAL_OPERATOR_DECISION_REQUIRED"
    ):
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


def test_rejects_noncanonical_entry_eligibility_status_label() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["entry_eligibility_lane_status"] = "CLOSED_NO_OPEN_CANDIDATES"
    with pytest.raises(BacklogValidationError, match="ENTRY_ELIGIBILITY_LANE_STATUS_NOT_CANONICAL"):
        validate_backlog_contract(bad)
