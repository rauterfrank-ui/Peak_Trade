"""Contract tests for canonical open MR exit-efficiency hypothesis backlog v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.canonical_open_mr_exit_efficiency_hypothesis_backlog_v1 import (
    BACKLOG_REL_PATH,
    GOVERNANCE_REL_PATH,
    REQUIRED_HYPOTHESIS_ID,
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


def test_repo_backlog_validates() -> None:
    report = load_and_validate_repo_backlog(REPO)
    assert report["valid"] is True
    assert report["preregistered_count"] == 1
    assert report["open_unpreregistered_count"] == 0
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["development_run_count"] == 0
    assert report["evaluation_authorized"] is False
    assert report["holdout_forbidden"] is True
    assert report["short_side_hypothesis_preregistered"] is False
    assert report["holdout_candidate_preregistered"] is False
    assert report["runtime_locked"] is True


def test_exactly_one_preregistered_exit_efficiency_candidate() -> None:
    backlog = _load(BACKLOG_PATH)
    assert backlog["open_unpreregistered_candidates"] == []
    assert backlog["competing_open_hypotheses"] == []
    assert len(backlog["preregistered_hypotheses"]) == 1
    entry = backlog["preregistered_hypotheses"][0]
    assert entry["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert entry["status"] == "DEFINITION_ONLY_PREREGISTERED"
    assert entry["evaluation_run_count"] == 0
    assert entry["evaluation_run_limit"] == 1
    assert entry["development_only"] is True
    assert entry["holdout_allowed"] is False
    assert backlog["short_side_hypothesis_preregistered"] is False
    assert backlog["holdout_candidate_preregistered"] is False
    assert backlog["cost_structure_hypothesis_preregistered"] is False


def test_second_preregistered_rejected() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["preregistered_hypotheses"].append(copy.deepcopy(bad["preregistered_hypotheses"][0]))
    with pytest.raises(BacklogValidationError, match="PREREGISTERED_COUNT"):
        validate_backlog_contract(bad)


def test_governance_doc_present() -> None:
    text = GOVERNANCE_PATH.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_CANONICAL_OPEN_MR_EXIT_EFFICIENCY_HYPOTHESIS_BACKLOG_V1" in text
    assert "DEFINITION_ONLY_PREREGISTERED" in text
    assert REQUIRED_HYPOTHESIS_ID in text
