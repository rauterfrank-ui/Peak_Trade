"""Definition-only contract tests for volatility regime backlog v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.volatility_regime_hypothesis_backlog_v1 import (
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
CS_PROGRAM = REPO / "config/research/material_different_cross_sectional_momentum_program_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_backlog_open_with_one_preregistration() -> None:
    report = load_and_validate_repo_backlog(REPO)
    assert report["valid"] is True
    assert report["status"] == "OPEN_BACKLOG"
    assert report["preregistered_count"] == 1
    assert report["terminal_count"] == 4
    assert (
        report["hypothesis_id"]
        == "VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_NON_BITCOIN_PERPETUALS_V1"
    )
    assert report["strategy_identity"] == "VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1"
    assert report["development_run_count"] == 0
    assert (
        report["dataset_id"]
        == "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
    )
    assert report["evaluation_authorized"] is False
    assert report["holdout_forbidden"] is True
    assert report["promotion_eligible"] is False
    assert report["retry_allowed"] is False


def test_sibling_closed_lanes_and_inventory() -> None:
    backlog = _load(BACKLOG_PATH)
    siblings = backlog["closed_sibling_lanes"]
    assert siblings["entry_eligibility_lane_status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["exit_efficiency_lane_status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["cross_sectional_momentum_lane_status"] == "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["reopen_forbidden"] is True
    assert _load(ENTRY_BACKLOG)["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert _load(EXIT_BACKLOG)["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert _load(CS_PROGRAM)["status"] == "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"
    assert backlog["open_unpreregistered_candidates"] == []
    assert len(backlog["terminal_hypotheses"]) == 4
    terminals = {t["strategy_identity"]: t for t in backlog["terminal_hypotheses"]}
    assert terminals["VOLATILITY_COMPRESSION_BREAKOUT_V1"]["terminal_result"] == (
        "FAIL_CLOSED_NO_RETRY"
    )
    assert terminals["VOLATILITY_EXPANSION_PERSISTENCE_V1"]["fail_reason"].endswith(
        "UNPAIRABLE_ENTRY_NO_EXIT"
    )
    assert terminals["VOLATILITY_DECAY_BREAKOUT_V1"]["fail_reason"].endswith(
        "UNPAIRABLE_ENTRY_NO_EXIT"
    )
    assert terminals["VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1"][
        "fail_reason"
    ].endswith("UNPAIRABLE_ENTRY_NO_EXIT")
    assert backlog["sealed_holdout_binding_status"] == "UNBOUND_UNTOUCHED"
    hyp = backlog["preregistered_hypotheses"][0]
    assert hyp["implementation_present"] is False
    assert hyp["holdout_allowed"] is False
    assert hyp["development_run_limit"] == 1
    assert hyp["development_run_count"] == 0
    assert hyp["runner_start_count"] == 0
    assert hyp["run_slot_consumed"] is False
    assert hyp["status"] == "DEFINITION_ONLY_PREREGISTERED"
    assert hyp["baseline_id"] == "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
    assert hyp["strategy_identity"] == "VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1"


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
    bad3["development_run_count"] = 1
    with pytest.raises(BacklogValidationError, match="DEVELOPMENT_RUN_COUNT_NOT_ZERO"):
        validate_backlog_contract(bad3)
    bad4 = copy.deepcopy(payload)
    bad4["closed_sibling_lanes"]["reopen_forbidden"] = False
    with pytest.raises(BacklogValidationError, match="SIBLING_REOPEN_NOT_FORBIDDEN"):
        validate_backlog_contract(bad4)


def test_governance_and_owner_map() -> None:
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_VOLATILITY_REGIME_HYPOTHESIS_BACKLOG_V1" in text
    assert "OPEN_BACKLOG" in text
    assert "VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1" in text
    assert "VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1" in text
    owners = _load(OWNER_MAP)["allowed_optimization_surfaces"]
    assert "VOLATILITY_REGIME_HYPOTHESIS_BACKLOG_V1" in owners
