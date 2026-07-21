"""Contract tests for canonical open MR exit-efficiency hypothesis backlog with V2 preregistration."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.canonical_open_mr_exit_efficiency_hypothesis_backlog_v1 import (
    BACKLOG_REL_PATH,
    GOVERNANCE_REL_PATH,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_OBSERVABILITY_SURFACE,
    REQUIRED_V2_HYPOTHESIS_ID,
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


def test_repo_backlog_v2_preregistered_and_v1_terminal() -> None:
    report = load_and_validate_repo_backlog(REPO)
    assert report["valid"] is True
    assert report["preregistered_count"] == 1
    assert report["terminal_count"] == 1
    assert report["open_unpreregistered_count"] == 0
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["preregistered_hypothesis_id"] == REQUIRED_V2_HYPOTHESIS_ID
    assert report["development_run_count"] == 1
    assert report["evaluation_authorized"] is False
    assert report["holdout_forbidden"] is True
    assert report["result_class"] == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert report["economic_verdict"] == "NOT_EVALUATED"
    assert report["rerun_allowed"] is False
    assert report["runtime_locked"] is True
    assert report["v2_evaluation_run_count"] == 0
    assert report["v2_is_rerun_of_v1"] is False
    assert report["observability_surface"] == REQUIRED_OBSERVABILITY_SURFACE


def test_terminal_and_preregistered_entry_shape() -> None:
    backlog = _load(BACKLOG_PATH)
    assert len(backlog["preregistered_hypotheses"]) == 1
    assert backlog["open_unpreregistered_candidates"] == []
    assert len(backlog["terminal_hypotheses"]) == 1
    prereg = backlog["preregistered_hypotheses"][0]
    assert prereg["hypothesis_id"] == REQUIRED_V2_HYPOTHESIS_ID
    assert prereg["status"] == "DEFINITION_ONLY_PREREGISTERED"
    assert prereg["evaluation_run_count"] == 0
    assert prereg["evaluation_started"] is False
    assert prereg["evaluation_executed"] is False
    assert prereg["new_evaluation_not_rerun"] is True
    assert prereg["v1_partial_results_reused"] is False
    assert prereg["observability_surface"] == REQUIRED_OBSERVABILITY_SURFACE
    entry = backlog["terminal_hypotheses"][0]
    assert entry["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert entry["status"] == "TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert entry["evaluation_run_count"] == 1
    assert entry["evaluation_started"] is True
    assert entry["evaluation_completed"] is False
    assert entry["pass"] is False
    assert entry["fail"] is False
    assert entry["rerun_allowed"] is False
    assert entry["baseline_members_completed"] == "2/46"
    assert entry["treatment_members_completed"] == "0/46"
    assert "NO_V2_PREREGISTRATION_IN_THIS_SLICE" not in backlog["explicit_non_actions"]


def test_governance_doc_present() -> None:
    text = GOVERNANCE_PATH.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_CANONICAL_OPEN_MR_EXIT_EFFICIENCY_HYPOTHESIS_BACKLOG_V1" in text
    assert REQUIRED_HYPOTHESIS_ID in text
    assert REQUIRED_V2_HYPOTHESIS_ID in text
