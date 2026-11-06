"""Definition-only contract tests for CS momentum backlog v1 (closed lane)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.material_different_cross_sectional_momentum_hypothesis_backlog_v1 import (
    BACKLOG_REL_PATH,
    GOVERNANCE_REL_PATH,
    BacklogValidationError,
    load_and_validate_repo_backlog,
    validate_backlog_contract,
)

REPO = Path(__file__).resolve().parents[2]
BACKLOG_PATH = REPO / BACKLOG_REL_PATH
GOVERNANCE = REPO / GOVERNANCE_REL_PATH
OWNER_MAP = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
ENTRY_BACKLOG = (
    REPO / "config/research/canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.json"
)
EXIT_BACKLOG = REPO / "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_backlog_closed_terminal_no_successor() -> None:
    report = load_and_validate_repo_backlog(REPO)
    assert report["valid"] is True
    assert report["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert report["preregistered_count"] == 0
    assert report["terminal_count"] == 1
    assert (
        report["hypothesis_id"]
        == "CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_NON_BITCOIN_PERPETUALS_V1"
    )
    assert report["terminal_strategy_id"] == "CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1"
    assert report["terminal_result"] == "FAIL_CLOSED_NO_RETRY"
    assert report["development_run_count"] == 1
    assert report["runner_start_count"] == 1
    assert report["run_budget_consumed"] is True
    assert report["successor_found"] is False
    assert report["next_eligible"] == "NONE"
    assert report["retry_allowed"] is False
    assert report["reopen_allowed"] is False
    assert report["evaluation_authorized"] is False
    assert report["holdout_forbidden"] is True
    assert report["promotion_eligible"] is False


def test_sibling_closed_lanes_and_terminal_inventory() -> None:
    backlog = _load(BACKLOG_PATH)
    siblings = backlog["closed_sibling_lanes"]
    assert siblings["entry_eligibility_lane_status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["exit_efficiency_lane_status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["reopen_forbidden"] is True
    assert _load(ENTRY_BACKLOG)["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert _load(EXIT_BACKLOG)["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert backlog["preregistered_hypotheses"] == []
    assert backlog["open_unpreregistered_candidates"] == []
    assert backlog["explicit_closeout_decision"] is True
    assert backlog["create_successor_hypothesis"] is False
    assert backlog["automatic_successor_creation"] is False
    hyp = backlog["terminal_hypotheses"][0]
    assert hyp["implementation_present"] is True
    assert hyp["holdout_allowed"] is False
    assert hyp["development_run_count"] == 1
    assert hyp["run_slot_consumed"] is True
    assert hyp["terminal_result"] == "FAIL_CLOSED_NO_RETRY"
    assert hyp["rerun_allowed"] is False


def test_fail_closed_mutations() -> None:
    payload = _load(BACKLOG_PATH)
    bad = copy.deepcopy(payload)
    bad["evaluation_authorized"] = True
    with pytest.raises(BacklogValidationError, match="EVALUATION_AUTHORIZED"):
        validate_backlog_contract(bad)
    bad2 = copy.deepcopy(payload)
    bad2["retry_allowed"] = True
    with pytest.raises(BacklogValidationError, match="RETRY_ALLOWED"):
        validate_backlog_contract(bad2)
    bad3 = copy.deepcopy(payload)
    bad3["create_successor_hypothesis"] = True
    with pytest.raises(BacklogValidationError, match="CREATE_SUCCESSOR_TRUE"):
        validate_backlog_contract(bad3)
    bad4 = copy.deepcopy(payload)
    bad4["development_run_count"] = 0
    with pytest.raises(BacklogValidationError, match="DEVELOPMENT_RUN_COUNT_NOT_ONE"):
        validate_backlog_contract(bad4)
    bad5 = copy.deepcopy(payload)
    bad5["closed_sibling_lanes"]["reopen_forbidden"] = False
    with pytest.raises(BacklogValidationError, match="SIBLING_REOPEN_NOT_FORBIDDEN"):
        validate_backlog_contract(bad5)


def test_governance_and_owner_map() -> None:
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_HYPOTHESIS_BACKLOG_V1" in text
    assert "LANE_CLOSED_NO_FURTHER_RESEARCH" in text
    assert "FAIL_CLOSED_NO_RETRY" in text
    owners = _load(OWNER_MAP)["allowed_optimization_surfaces"]
    assert "MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_HYPOTHESIS_BACKLOG_V1" in owners
