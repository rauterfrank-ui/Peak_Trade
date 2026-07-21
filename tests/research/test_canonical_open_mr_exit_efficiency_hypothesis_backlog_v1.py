"""Contract tests for canonical open MR exit-efficiency hypothesis backlog after terminal closeout."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.canonical_open_mr_exit_efficiency_hypothesis_backlog_v1 import (
    BACKLOG_REL_PATH,
    GOVERNANCE_REL_PATH,
    REQUIRED_HYPOTHESIS_ID,
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


def test_repo_backlog_terminal_inconclusive() -> None:
    report = load_and_validate_repo_backlog(REPO)
    assert report["valid"] is True
    assert report["preregistered_count"] == 0
    assert report["terminal_count"] == 1
    assert report["open_unpreregistered_count"] == 0
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["development_run_count"] == 1
    assert report["evaluation_authorized"] is False
    assert report["holdout_forbidden"] is True
    assert report["result_class"] == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert report["economic_verdict"] == "NOT_EVALUATED"
    assert report["rerun_allowed"] is False
    assert report["runtime_locked"] is True


def test_terminal_entry_shape() -> None:
    backlog = _load(BACKLOG_PATH)
    assert backlog["preregistered_hypotheses"] == []
    assert backlog["open_unpreregistered_candidates"] == []
    assert len(backlog["terminal_hypotheses"]) == 1
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


def test_governance_doc_present() -> None:
    text = GOVERNANCE_PATH.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_CANONICAL_OPEN_MR_EXIT_EFFICIENCY_HYPOTHESIS_BACKLOG_V1" in text
    assert REQUIRED_HYPOTHESIS_ID in text
