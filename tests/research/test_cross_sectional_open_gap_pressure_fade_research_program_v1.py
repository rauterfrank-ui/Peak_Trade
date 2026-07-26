"""Definition-only contract tests for CS open-gap pressure fade program v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.cross_sectional_open_gap_pressure_fade_research_program_v1 import (
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
CSRHR_BACKLOG = (
    REPO
    / "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_program_definition_only_evaluation_unauthorized() -> None:
    report = load_and_validate_repo_program(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is True
    assert report["program_id"] == "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_RESEARCH_PROGRAM_V1"
    assert report["status"] == "DEFINITION_ONLY"
    assert report["evaluation_authorized"] is False
    assert report["development_run_count"] == 1
    assert report["holdout_forbidden"] is True
    assert GOVERNANCE.is_file()


def test_causal_independence_from_closed_and_open_siblings() -> None:
    payload = _load(PROGRAM_PATH)
    independence = payload["causal_independence"]
    assert independence["independent_from_closed_volatility_regime_program"] is True
    assert independence["independent_from_closed_cross_sectional_momentum_lane"] is True
    assert independence["independent_from_open_csrhr_program"] is True
    assert independence["independent_from_terminal_path_efficiency_continuation"] is True
    assert independence["independent_from_terminal_clv_pressure_continuation"] is True
    assert independence["not_a_clv_pressure_retry_or_rename"] is True
    assert independence["volume_dependency"] is False
    assert payload["strategy_implementation_present"] is False
    assert payload["runtime_policy"]["live_authorized"] is False
    assert payload["promotion_and_economic_gate_policy"]["economic_gate_open"] is False
    csrhr = _load(CSRHR_BACKLOG)
    assert csrhr["status"] == "OPEN_BACKLOG"
    assert csrhr["development_run_count"] == 1


def test_fail_closed_on_authorization_mutation() -> None:
    payload = _load(PROGRAM_PATH)
    bad = copy.deepcopy(payload)
    bad["evaluation_authorized"] = True
    with pytest.raises(ProgramValidationError, match="EVALUATION_AUTHORIZED_TRUE"):
        validate_program_contract(bad)
    bad2 = copy.deepcopy(payload)
    bad2["development_run_count"] = 2
    with pytest.raises(ProgramValidationError, match="DEVELOPMENT_RUN_COUNT_NOT_ZERO"):
        validate_program_contract(bad2)
    bad3 = copy.deepcopy(payload)
    bad3["status"] = "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"
    with pytest.raises(ProgramValidationError, match="STATUS_NOT_DEFINITION_ONLY"):
        validate_program_contract(bad3)


def test_owner_map_registers_program_surface() -> None:
    owner = _load(OWNER_MAP)
    surfaces = owner["allowed_optimization_surfaces"]
    assert "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_RESEARCH_PROGRAM_V1" in surfaces
    paths = surfaces["CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_RESEARCH_PROGRAM_V1"]["path_prefixes"]
    assert PROGRAM_REL_PATH in paths
