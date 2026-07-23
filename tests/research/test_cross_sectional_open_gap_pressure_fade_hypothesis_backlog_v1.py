"""Definition-only contract tests for CS open-gap pressure fade backlog v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.cross_sectional_open_gap_pressure_fade_hypothesis_backlog_v1 import (
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


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_backlog_open_one_preregistered_definition_only() -> None:
    report = load_and_validate_repo_backlog(REPO)
    assert report["valid"] is True
    assert report["status"] == "OPEN_BACKLOG"
    assert report["preregistered_count"] == 1
    assert report["evaluation_authorized"] is False
    assert (
        report["next_eligible"]
        == "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_NON_BITCOIN_PERPETUALS_V1"
    )


def test_sibling_lanes_remain_closed_or_open_as_required() -> None:
    payload = _load(BACKLOG_PATH)
    siblings = payload["closed_sibling_lanes"]
    assert siblings["volatility_regime_lane_status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["cross_sectional_momentum_lane_status"] == "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["entry_eligibility_lane_status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["exit_efficiency_lane_status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert (
        siblings["path_efficiency_continuation_status"] == "DEVELOPMENT_FAIL_SLOT_CONSUMED_NO_RETRY"
    )
    assert siblings["clv_pressure_continuation_status"] == "DEVELOPMENT_FAIL_SLOT_CONSUMED_NO_RETRY"
    assert siblings["reopen_forbidden"] is True
    open_sib = payload["open_sibling_lanes"]
    assert open_sib["cross_sectional_short_horizon_return_reversal_lane_status"] == "OPEN_BACKLOG"
    assert open_sib["mutation_forbidden"] is True


def test_fail_closed_on_evaluation_authorization() -> None:
    payload = _load(BACKLOG_PATH)
    bad = copy.deepcopy(payload)
    bad["evaluation_authorized"] = True
    with pytest.raises(BacklogValidationError, match="EVALUATION_AUTHORIZED"):
        validate_backlog_contract(bad)


def test_owner_map_registers_backlog_surface() -> None:
    owner = _load(OWNER_MAP)
    surfaces = owner["allowed_optimization_surfaces"]
    assert "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_HYPOTHESIS_BACKLOG_V1" in surfaces
    paths = surfaces["CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_HYPOTHESIS_BACKLOG_V1"][
        "path_prefixes"
    ]
    assert BACKLOG_REL_PATH in paths
