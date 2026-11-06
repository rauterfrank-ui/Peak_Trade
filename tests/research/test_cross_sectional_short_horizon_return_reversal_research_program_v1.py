"""Contract tests for CSRHR program after terminal retirement closeout."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.cross_sectional_short_horizon_return_reversal_research_program_v1 import (
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


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_program_closed_after_development_fail() -> None:
    report = load_and_validate_repo_program(REPO)
    assert report["valid"] is True
    assert report["program_closed"] is True
    assert (
        report["program_id"] == "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1"
    )
    assert report["status"] == "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"
    assert report["evaluation_authorized"] is False
    assert report["development_evaluation_authorized"] is False
    assert report["development_run_count"] == 1
    assert report["holdout_forbidden"] is True
    assert report["next_eligible"] == "NONE"
    assert GOVERNANCE.is_file()


def test_causal_independence_and_closed_gates_preserved() -> None:
    payload = _load(PROGRAM_PATH)
    independence = payload["causal_independence"]
    assert independence["independent_from_closed_volatility_regime_program"] is True
    assert independence["independent_from_closed_cross_sectional_momentum_lane"] is True
    assert independence["not_a_volatility_regime_reopen"] is True
    assert (
        independence["not_a_retry_of_terminal_cross_sectional_relative_strength_momentum_v1"]
        is True
    )
    assert independence["polarity_vs_cs_momentum"] == "OPPOSITE_REVERSAL_NOT_PERSISTENCE"
    assert payload["strategy_implementation_present"] is True
    assert payload["explicit_closeout_decision"] is True
    assert payload["create_successor_hypothesis"] is False
    assert payload["runtime_policy"]["live_authorized"] is False
    assert payload["promotion_and_economic_gate_policy"]["economic_gate_open"] is False
    assert payload["promotion_and_economic_gate_policy"]["promotion_eligible"] is False


def test_fail_closed_on_authorization_and_status_mutation() -> None:
    payload = _load(PROGRAM_PATH)
    bad = copy.deepcopy(payload)
    bad["evaluation_authorized"] = True
    with pytest.raises(ProgramValidationError, match="EVALUATION_AUTHORIZED_TRUE"):
        validate_program_contract(bad)
    bad2 = copy.deepcopy(payload)
    bad2["development_evaluation_authorized"] = True
    with pytest.raises(ProgramValidationError, match="DEVELOPMENT_EVALUATION_AUTHORIZED_TRUE"):
        validate_program_contract(bad2)
    bad3 = copy.deepcopy(payload)
    bad3["status"] = "DEFINITION_ONLY"
    with pytest.raises(ProgramValidationError, match="STATUS_NOT_PROGRAM_CLOSED"):
        validate_program_contract(bad3)
    bad4 = copy.deepcopy(payload)
    bad4["development_run_count"] = 2
    with pytest.raises(ProgramValidationError, match="DEVELOPMENT_RUN_COUNT_NOT_ONE"):
        validate_program_contract(bad4)


def test_owner_map_registers_program_surface() -> None:
    owner = _load(OWNER_MAP)
    surfaces = owner["allowed_optimization_surfaces"]
    assert "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1" in surfaces
    paths = surfaces["CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1"][
        "path_prefixes"
    ]
    assert PROGRAM_REL_PATH in paths
