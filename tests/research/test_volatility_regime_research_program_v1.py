"""Definition-only contract tests for volatility regime program v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.volatility_regime_research_program_v1 import (
    GOVERNANCE_REL_PATH,
    PROGRAM_REL_PATH,
    ProgramValidationError,
    load_and_validate_repo_program,
    validate_program_contract,
)

REPO = Path(__file__).resolve().parents[2]
PROGRAM_PATH = REPO / PROGRAM_REL_PATH
GOVERNANCE = REPO / GOVERNANCE_REL_PATH
OWNER_MAP = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
ENTRY_BACKLOG = (
    REPO / "config/research/canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.json"
)
EXIT_BACKLOG = REPO / "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
CS_PROGRAM = REPO / "config/research/material_different_cross_sectional_momentum_program_v1.json"
COILED_SPRING_CLOSEOUT = (
    REPO / "config/research/vol_breakout_v1_terminal_negative_economic_evidence_closeout_v0.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_program_definition_only_open() -> None:
    report = load_and_validate_repo_program(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is True
    assert report["strategy_implementation_present"] is False
    assert report["program_id"] == "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
    assert report["status"] == "DEFINITION_ONLY_PROGRAM_OPEN"
    assert report["strategy_identity"] == "VOLATILITY_COMPRESSION_BREAKOUT_V1"
    assert report["signal_family"] == "VOLATILITY_REGIME"
    assert report["holdout_authorized"] is False
    assert report["evaluation_authorized"] is False
    assert report["promotion_eligible"] is False
    assert report["development_run_count"] == 0
    assert report["runner_start_count"] == 0
    assert report["run_slot_consumed"] is False
    assert report["retry_allowed"] is False
    assert report["material_difference_explicit"] is True
    assert report["causally_independent_from_cs_momentum"] is True


def test_material_difference_and_closed_siblings_immutable() -> None:
    payload = _load(PROGRAM_PATH)
    md = payload["material_difference_vs_terminal_coiled_spring"]
    assert md["prior_terminal_hypothesis_id"] == "VOL_BREAKOUT_COILED_SPRING_NON_BITCOIN_FUTURES_V1"
    assert md["unchanged_binding_retry_forbidden"] is True
    assert md["reopen_of_terminal_vol_breakout_v1_forbidden"] is True
    closeout = _load(COILED_SPRING_CLOSEOUT)
    assert closeout["same_binding_retry_allowed"] is False
    assert closeout["current_research_generation_closed"] is True
    assert _load(ENTRY_BACKLOG)["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert _load(EXIT_BACKLOG)["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert _load(CS_PROGRAM)["status"] == "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"
    independence = payload["causal_independence"]
    assert independence["cross_sectional_momentum_dependency"] is False
    assert independence["independent_from_closed_cross_sectional_momentum_lane"] is True


def test_fail_closed_on_authorization_mutation() -> None:
    payload = _load(PROGRAM_PATH)
    bad = copy.deepcopy(payload)
    bad["evaluation_authorized"] = True
    with pytest.raises(ProgramValidationError, match="EVALUATION_AUTHORIZED_TRUE"):
        validate_program_contract(bad)
    bad2 = copy.deepcopy(payload)
    bad2["development_run_count"] = 1
    with pytest.raises(ProgramValidationError, match="DEVELOPMENT_RUN_COUNT_NOT_ZERO"):
        validate_program_contract(bad2)
    bad3 = copy.deepcopy(payload)
    bad3["strategy_implementation_present"] = True
    with pytest.raises(ProgramValidationError, match="STRATEGY_IMPLEMENTATION_PRESENT_TRUE"):
        validate_program_contract(bad3)
    bad4 = copy.deepcopy(payload)
    bad4["runtime_policy"]["orders_allowed"] = True
    with pytest.raises(ProgramValidationError, match="RUNTIME_POLICY_ORDERS_ALLOWED_TRUE"):
        validate_program_contract(bad4)


def test_governance_and_owner_map() -> None:
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_VOLATILITY_REGIME_RESEARCH_PROGRAM_V1" in text
    assert "DEFINITION_ONLY_PROGRAM_OPEN" in text
    assert "VOL_BREAKOUT_COILED_SPRING_NON_BITCOIN_FUTURES_V1" in text
    owners = _load(OWNER_MAP)["allowed_optimization_surfaces"]
    assert "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1" in owners
