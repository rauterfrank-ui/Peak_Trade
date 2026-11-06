"""Contract tests for Momentum V2 vol-scaled backlog after terminal retirement."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_hypothesis_backlog_v1 import (
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
CSRHR_BACKLOG = (
    REPO
    / "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
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
    assert hyp["strategy_identity"] == (
        "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1"
    )
    assert hyp["status"] == "TERMINAL_FAIL"
    assert hyp["terminal_result"] == "FAIL_CLOSED_NO_RETRY"
    assert hyp["economic_validity"] == "FAIL"
    assert hyp["run_slot_consumed"] is True
    assert hyp["retry_allowed"] is False
    assert hyp["rerun_allowed"] is False
    assert hyp["holdout_allowed"] is False
    assert payload["explicit_closeout_decision"] is True
    assert payload["create_successor_hypothesis"] is False
    assert payload["successor_found"] is False


def test_closed_sibling_csrhr_remains_closed() -> None:
    payload = _load(BACKLOG_PATH)
    siblings = payload["closed_sibling_lanes"]
    assert siblings["cross_sectional_momentum_lane_status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["reopen_forbidden"] is True
    csrhr = _load(CSRHR_BACKLOG)
    assert csrhr["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"


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
        "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
    )
    with pytest.raises(BacklogValidationError, match="NEXT_ELIGIBLE_NOT_NONE"):
        validate_backlog_contract(bad3)
    bad4 = copy.deepcopy(payload)
    bad4["preregistered_hypotheses"] = payload["terminal_hypotheses"]
    bad4["terminal_hypotheses"] = []
    with pytest.raises(BacklogValidationError, match="PREREGISTERED_LEN_NOT_0"):
        validate_backlog_contract(bad4)


def test_owner_map_registers_backlog_surface() -> None:
    owner = _load(OWNER_MAP)
    surfaces = owner["allowed_optimization_surfaces"]
    key = "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_HYPOTHESIS_BACKLOG_V1"
    assert key in surfaces
    paths = surfaces[key]["path_prefixes"]
    assert BACKLOG_REL_PATH in paths
