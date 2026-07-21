"""Contract tests for canonical open MR exit-efficiency hypothesis backlog (V4 terminal)."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.canonical_open_mr_exit_efficiency_hypothesis_backlog_v1 import (
    BACKLOG_REL_PATH,
    GOVERNANCE_REL_PATH,
    REQUIRED_FALSY_ZERO_HYGIENE_SURFACE,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_OBSERVABILITY_SURFACE,
    REQUIRED_V2_HYPOTHESIS_ID,
    REQUIRED_V3_HYPOTHESIS_ID,
    REQUIRED_V4_HYPOTHESIS_ID,
    assert_exactly_one_exit_efficiency_backlog_ssot,
    load_and_validate_repo_backlog,
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


def test_repo_backlog_no_open_preregistration_v4_terminal() -> None:
    report = load_and_validate_repo_backlog(REPO)
    assert report["valid"] is True
    assert report["preregistered_count"] == 0
    assert report["terminal_count"] == 4
    assert report["open_unpreregistered_count"] == 0
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["preregistered_hypothesis_id"] is None
    assert report["development_run_count"] == 4
    assert report["evaluation_authorized"] is False
    assert report["holdout_forbidden"] is True
    assert report["result_class"] == "INFRASTRUCTURE_FAILURE"
    assert report["economic_verdict"] == "NOT_EVALUATED"
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
    }


def test_terminal_v4_and_terminal_entry_shape() -> None:
    backlog = _load(BACKLOG_PATH)
    assert len(backlog["preregistered_hypotheses"]) == 0
    assert backlog["governance_rules"]["preregistered_count_exact"] == 0
    assert backlog["open_unpreregistered_candidates"] == []
    assert len(backlog["terminal_hypotheses"]) == 4
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
    assert "NO_V5_AUTO_CREATE" in backlog["explicit_non_actions"]
    assert "NO_V3_ECONOMIC_RESULT_IMPORT" in backlog["explicit_non_actions"]
    assert "NO_V4_AUTO_CREATE" not in backlog["explicit_non_actions"]


def test_governance_doc_mentions_v4_terminal() -> None:
    text = GOVERNANCE_PATH.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_CANONICAL_OPEN_MR_EXIT_EFFICIENCY_HYPOTHESIS_BACKLOG_V1" in text
    assert "TERMINAL_INFRASTRUCTURE_FAILURE" in text
    assert "identical_arms_no_exit_divergence" in text
    assert REQUIRED_V3_HYPOTHESIS_ID in text
    assert REQUIRED_V4_HYPOTHESIS_ID in text
