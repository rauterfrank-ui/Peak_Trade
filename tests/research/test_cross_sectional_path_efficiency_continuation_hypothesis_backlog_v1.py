"""Definition-only contract tests for CS path-efficiency continuation backlog v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.cross_sectional_path_efficiency_continuation_hypothesis_backlog_v1 import (
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
    assert report["development_run_count"] == 1
    assert (
        report["next_eligible"]
        == "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
    )
    assert report["workstream_id"] == "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_WORKSTREAM_V1"


def test_sibling_lanes_closed_and_csrhr_open_protected() -> None:
    payload = _load(BACKLOG_PATH)
    siblings = payload["closed_sibling_lanes"]
    assert siblings["volatility_regime_lane_status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["cross_sectional_momentum_lane_status"] == "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["entry_eligibility_lane_status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["exit_efficiency_lane_status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert siblings["reopen_forbidden"] is True
    open_sib = payload["open_sibling_lanes"]
    assert open_sib["cross_sectional_short_horizon_return_reversal_lane_status"] == "OPEN_BACKLOG"
    assert open_sib["mutation_forbidden"] is True
    assert open_sib["semantic_reuse_forbidden"] is True
    assert open_sib["continuation_forbidden"] is True
    assert payload["sealed_holdout_binding_status"] == "UNBOUND_UNTOUCHED_ACCESS_FORBIDDEN"


def test_fail_closed_on_evaluation_authorization() -> None:
    payload = _load(BACKLOG_PATH)
    bad = copy.deepcopy(payload)
    bad["evaluation_authorized"] = True
    with pytest.raises(BacklogValidationError, match="EVALUATION_AUTHORIZED"):
        validate_backlog_contract(bad)
    bad2 = copy.deepcopy(payload)
    bad2["development_run_count"] = 0
    with pytest.raises(BacklogValidationError, match="DEVELOPMENT_RUN_COUNT"):
        validate_backlog_contract(bad2)


def test_owner_map_registers_backlog_surface() -> None:
    owner = _load(OWNER_MAP)
    surfaces = owner["allowed_optimization_surfaces"]
    assert "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_HYPOTHESIS_BACKLOG_V1" in surfaces
    paths = surfaces["CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_HYPOTHESIS_BACKLOG_V1"][
        "path_prefixes"
    ]
    assert BACKLOG_REL_PATH in paths
