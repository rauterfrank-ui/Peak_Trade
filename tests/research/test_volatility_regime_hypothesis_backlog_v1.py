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


def test_repo_backlog_open_with_cslrvc_preregistered() -> None:
    report = load_and_validate_repo_backlog(REPO)
    assert report["valid"] is True
    assert report["status"] == "OPEN_BACKLOG"
    assert report["preregistered_count"] == 1
    assert report["terminal_count"] == 10
    assert report["hypothesis_id"] == (
        "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
    )
    assert report["strategy_identity"] == (
        "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1"
    )
    assert report["development_run_count"] == 0
    assert (
        report["dataset_id"]
        == "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
    )
    assert report["evaluation_authorized"] is False
    assert report["holdout_forbidden"] is True
    assert report["promotion_eligible"] is False
    assert report["retry_allowed"] is False
    assert report["explicit_closeout_decision"] is False
    assert report["explicit_waiting_decision"] is False


def test_sibling_closed_lanes_and_terminal_inventory() -> None:
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
    assert len(backlog["preregistered_hypotheses"]) == 1
    hyp = backlog["preregistered_hypotheses"][0]
    assert hyp["strategy_identity"] == "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1"
    assert hyp["status"] == "STRATEGY_IMPLEMENTATION_PRESENT_EVALUATION_UNAUTHORIZED"
    assert hyp["implementation_present"] is True
    assert hyp["run_slot_consumed"] is False
    assert hyp["development_run_count"] == 0
    assert len(backlog["terminal_hypotheses"]) == 10
    terminals = {t["strategy_identity"]: t for t in backlog["terminal_hypotheses"]}
    assert terminals["VOLATILITY_COMPRESSION_BREAKOUT_V1"]["terminal_result"] == (
        "FAIL_CLOSED_NO_RETRY"
    )
    vepc = terminals["VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1"]
    assert vepc["status"] == "TERMINAL_FAIL"
    assert vepc["terminal_result"] == "FAIL_CLOSED_NO_RETRY"
    assert vepc["historical_slot_status"] == "CONSUMED_NO_RETRY"
    assert vepc["retry_allowed"] is False
    assert vepc["reopen_allowed"] is False
    vefcf = terminals["VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1"]
    assert vefcf["status"] == "TERMINAL_FAIL"
    assert vefcf["terminal_result"] == "FAIL_CLOSED_NO_RETRY"
    assert vefcf["run_slot_consumed"] is True
    assert vefcf["retry_allowed"] is False
    vtsr = terminals["VOLATILITY_TERM_STRUCTURE_REVERSION_V1"]
    assert vtsr["status"] == "TERMINAL_FAIL"
    assert vtsr["terminal_result"] == "FAIL_CLOSED_NO_RETRY"
    assert vtsr["run_slot_consumed"] is True
    assert vtsr["retry_allowed"] is False
    vtdc = terminals["VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1"]
    assert vtdc["status"] == "TERMINAL_FAIL"
    assert vtdc["terminal_result"] == "FAIL_CLOSED_NO_RETRY"
    assert vtdc["run_slot_consumed"] is True
    assert vtdc["retry_allowed"] is False
    assert backlog["sealed_holdout_binding_status"] == "UNBOUND_UNTOUCHED"
    assert backlog["required_treatment_type"] == (
        "OWN_INSTRUMENT_CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_ADMISSION"
    )
    assert backlog["next_canonical_step"] == (
        "AWAIT_SEPARATE_OPERATOR_GO_FOR_BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION"
    )
    assert backlog["implementation_authorized"] is True
    terminals = {t["strategy_identity"]: t for t in backlog["terminal_hypotheses"]}
    cshrvf = terminals["CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1"]
    assert cshrvf["status"] == "TERMINAL_FAIL"
    assert cshrvf["terminal_result"] == "FAIL_CLOSED_NO_RETRY"
    assert cshrvf["run_slot_consumed"] is True
    assert cshrvf["development_run_count"] == 1
    assert cshrvf["runner_start_count"] == 1
    assert cshrvf["retry_allowed"] is False
    assert cshrvf["rerun_allowed"] is False
    assert cshrvf["reopen_allowed"] is False
    assert hyp["runner_start_count"] == 0
    assert hyp["development_run_count"] == 0
    assert hyp["run_slot_consumed"] is False


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
    bad5 = copy.deepcopy(payload)
    bad5["status"] = "AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS"
    with pytest.raises(BacklogValidationError, match="STATUS_NOT_OPEN_BACKLOG"):
        validate_backlog_contract(bad5)
    bad6 = copy.deepcopy(payload)
    bad6["explicit_waiting_decision"] = True
    with pytest.raises(BacklogValidationError, match="WAITING_DECISION_TRUE"):
        validate_backlog_contract(bad6)


def test_governance_and_owner_map() -> None:
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_VOLATILITY_REGIME_HYPOTHESIS_BACKLOG_V1" in text
    assert "OPEN_BACKLOG" in text
    assert "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1" in text
    assert "CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1" in text
    assert "VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1" in text
    assert "VOLATILITY_TERM_STRUCTURE_REVERSION_V1" in text
    assert "VEFCF" in text or "VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE" in text
    owners = _load(OWNER_MAP)["allowed_optimization_surfaces"]
    assert "VOLATILITY_REGIME_HYPOTHESIS_BACKLOG_V1" in owners
