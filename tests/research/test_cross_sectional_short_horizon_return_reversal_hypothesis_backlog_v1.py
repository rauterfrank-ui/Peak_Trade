"""Contract tests for CSRHR backlog after terminal retirement closeout."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1 import (
    BACKLOG_REL_PATH,
    BacklogValidationError,
    load_and_validate_repo_backlog,
    validate_backlog_contract,
)

REPO = Path(__file__).resolve().parents[2]
BACKLOG_PATH = REPO / BACKLOG_REL_PATH
OWNER_MAP = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
UNRELATED_OPEN_GAP = (
    REPO / "config/research/cross_sectional_open_gap_pressure_fade_hypothesis_backlog_v1.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_backlog_terminally_retired_no_selectable_inventory() -> None:
    report = load_and_validate_repo_backlog(REPO)
    assert report["valid"] is True
    assert report["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert report["preregistered_count"] == 0
    assert report["terminal_count"] == 1
    assert report["next_eligible"] == "NONE"
    assert report["evaluation_authorized"] is False
    assert report["development_reevaluation_eligible"] is False
    assert report["holdout_eligible"] is False
    assert report["sealed_eligible"] is False
    assert report["promotion_eligible"] is False
    assert report["activation_eligible"] is False
    assert report["automatic_selection_enabled"] is False
    assert report["historical_evidence_preserved"] is True


def test_terminal_hypothesis_preserves_development_fail_truth() -> None:
    payload = _load(BACKLOG_PATH)
    hyp = payload["terminal_hypotheses"][0]
    assert hyp["strategy_identity"] == "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1"
    assert hyp["status"] == "TERMINAL_FAIL"
    assert hyp["terminal_result"] == "FAIL_CLOSED_NO_RETRY"
    assert hyp["run_slot_consumed"] is True
    assert hyp["retry_allowed"] is False
    assert hyp["rerun_allowed"] is False
    assert hyp["holdout_allowed"] is False
    assert payload["explicit_closeout_decision"] is True
    assert payload["create_successor_hypothesis"] is False


def test_sibling_lanes_remain_closed_and_unrelated_open_gap_untouched() -> None:
    payload = _load(BACKLOG_PATH)
    siblings = payload["closed_sibling_lanes"]
    assert siblings["volatility_regime_lane_status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["cross_sectional_momentum_lane_status"] == "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["entry_eligibility_lane_status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["exit_efficiency_lane_status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["reopen_forbidden"] is True
    open_gap = _load(UNRELATED_OPEN_GAP)
    assert open_gap["status"] == "OPEN_BACKLOG"
    assert open_gap["program_id"] == "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_RESEARCH_PROGRAM_V1"


def test_fail_closed_on_evaluation_authorization_and_reopen() -> None:
    payload = _load(BACKLOG_PATH)
    bad = copy.deepcopy(payload)
    bad["evaluation_authorized"] = True
    with pytest.raises(BacklogValidationError, match="EVALUATION_AUTHORIZED"):
        validate_backlog_contract(bad)
    bad2 = copy.deepcopy(payload)
    bad2["reopen_allowed"] = True
    with pytest.raises(BacklogValidationError, match="REOPEN_ALLOWED"):
        validate_backlog_contract(bad2)
    bad3 = copy.deepcopy(payload)
    bad3["next_eligible"] = (
        "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_NON_BITCOIN_PERPETUALS_V1"
    )
    with pytest.raises(BacklogValidationError, match="NEXT_ELIGIBLE_NOT_NONE"):
        validate_backlog_contract(bad3)


def test_owner_map_registers_backlog_surface() -> None:
    owner = _load(OWNER_MAP)
    surfaces = owner["allowed_optimization_surfaces"]
    assert "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_HYPOTHESIS_BACKLOG_V1" in surfaces
    paths = surfaces["CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_HYPOTHESIS_BACKLOG_V1"][
        "path_prefixes"
    ]
    assert BACKLOG_REL_PATH in paths
