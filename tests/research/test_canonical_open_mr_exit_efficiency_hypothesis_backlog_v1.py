"""Contract tests for canonical open MR exit-efficiency hypothesis backlog (V1+V2 terminal)."""

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


def test_repo_backlog_v1_and_v2_terminal() -> None:
    report = load_and_validate_repo_backlog(REPO)
    assert report["valid"] is True
    assert report["preregistered_count"] == 0
    assert report["terminal_count"] == 2
    assert report["open_unpreregistered_count"] == 0
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["preregistered_hypothesis_id"] is None
    assert report["development_run_count"] == 2
    assert report["evaluation_authorized"] is False
    assert report["holdout_forbidden"] is True
    assert report["result_class"] == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert report["economic_verdict"] == "NOT_EVALUATED"
    assert report["rerun_allowed"] is False
    assert report["runtime_locked"] is True
    assert report["v2_evaluation_run_count"] == 1
    assert report["v2_is_rerun_of_v1"] is False
    assert report["observability_surface"] == REQUIRED_OBSERVABILITY_SURFACE
    assert set(report["terminal_hypothesis_ids"]) == {
        REQUIRED_HYPOTHESIS_ID,
        REQUIRED_V2_HYPOTHESIS_ID,
    }


def test_terminal_entry_shape() -> None:
    backlog = _load(BACKLOG_PATH)
    assert backlog["preregistered_hypotheses"] == []
    assert backlog["open_unpreregistered_candidates"] == []
    assert len(backlog["terminal_hypotheses"]) == 2
    by_id = {e["hypothesis_id"]: e for e in backlog["terminal_hypotheses"]}
    v1 = by_id[REQUIRED_HYPOTHESIS_ID]
    assert v1["status"] == "TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert v1["evaluation_run_count"] == 1
    assert v1["evaluation_started"] is True
    assert v1["evaluation_completed"] is False
    assert v1["pass"] is False
    assert v1["fail"] is False
    assert v1["rerun_allowed"] is False
    assert v1["baseline_members_completed"] == "2/46"
    assert v1["treatment_members_completed"] == "0/46"
    v2 = by_id[REQUIRED_V2_HYPOTHESIS_ID]
    assert v2["status"] == "TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert v2["evaluation_run_count"] == 1
    assert v2["evaluation_started"] is True
    assert v2["evaluation_completed"] is False
    assert v2["pass"] is False
    assert v2["fail"] is False
    assert v2["rerun_allowed"] is False
    assert v2["baseline_members_completed"] == "0/46"
    assert v2["treatment_members_completed"] == "0/46"
    assert v2["new_evaluation_not_rerun"] is True
    assert v2["v1_partial_results_reused"] is False
    assert v2["observability_surface"] == REQUIRED_OBSERVABILITY_SURFACE
    assert "NO_V2_RERUN" in backlog["explicit_non_actions"]
    assert backlog["governance_rules"]["preregistered_count_exact"] == 0


def test_governance_doc_mentions_both_terminals() -> None:
    text = GOVERNANCE_PATH.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_CANONICAL_OPEN_MR_EXIT_EFFICIENCY_HYPOTHESIS_BACKLOG_V1" in text
    assert REQUIRED_HYPOTHESIS_ID in text
    assert REQUIRED_V2_HYPOTHESIS_ID in text
    assert "PREMEASUREMENT_GATE_FALSE_POSITIVE_ZERO_OR_SENTINEL" in text
