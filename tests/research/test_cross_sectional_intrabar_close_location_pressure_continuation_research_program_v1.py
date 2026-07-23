"""Definition-only contract tests for CS intrabar close-location pressure continuation program v1."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from src.research.cross_sectional_intrabar_close_location_pressure_continuation_research_program_v1 import (
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
CSRHR_PROGRAM = (
    REPO / "config/research/cross_sectional_short_horizon_return_reversal_research_program_v1.json"
)
CSRHR_BACKLOG = (
    REPO
    / "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
)
CSRHR_PROGRAM_SHA256_PREFIX = "9520e0cf1d4d4b4a"
CSRHR_BACKLOG_SHA256_PREFIX = "04059ed471484912"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha_prefix(path: Path, n: int = 16) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:n]


def test_repo_program_definition_only_evaluation_unauthorized() -> None:
    report = load_and_validate_repo_program(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is True
    assert (
        report["program_id"]
        == "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_RESEARCH_PROGRAM_V1"
    )
    assert (
        report["workstream_id"]
        == "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_WORKSTREAM_V1"
    )
    assert report["status"] == "DEFINITION_ONLY"
    assert report["evaluation_authorized"] is False
    assert report["development_run_count"] == 0
    assert report["holdout_forbidden"] is True
    assert GOVERNANCE.is_file()


def test_causal_independence_and_frozen_identities() -> None:
    payload = _load(PROGRAM_PATH)
    independence = payload["causal_independence"]
    assert independence["independent_from_closed_volatility_regime_program"] is True
    assert independence["independent_from_closed_cross_sectional_momentum_lane"] is True
    assert independence["independent_from_open_csrhr_program"] is True
    assert independence["independent_from_terminal_path_efficiency_continuation"] is True
    assert independence["not_a_csrhr_continuation_or_semantic_reuse"] is True
    assert independence["not_a_path_efficiency_retry_or_rename"] is True
    assert payload["signal_family"] == "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE"
    assert (
        payload["target_phenomenon"]
        == "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION"
    )
    assert payload["development_run_limit"] == 1
    assert payload["retry_policy"]["after_development_fail"] == "FAIL_CLOSED_NO_RETRY"
    assert payload["strategy_implementation_present"] is True
    assert payload["implementation_authorized"] is True
    assert payload["runtime_policy"]["live_authorized"] is False
    assert payload["promotion_and_economic_gate_policy"]["economic_gate_open"] is False
    assert payload["development_run_count"] == 0
    assert payload["evaluation_authorized"] is False


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


def test_csrhr_sibling_unchanged() -> None:
    assert _sha_prefix(CSRHR_PROGRAM) == CSRHR_PROGRAM_SHA256_PREFIX
    assert _sha_prefix(CSRHR_BACKLOG) == CSRHR_BACKLOG_SHA256_PREFIX
    csrhr_bl = _load(CSRHR_BACKLOG)
    assert csrhr_bl["status"] == "OPEN_BACKLOG"
    assert csrhr_bl["development_run_count"] == 0
    assert csrhr_bl["evaluation_authorized"] is False


def test_owner_map_registers_program_surface() -> None:
    owner = _load(OWNER_MAP)
    surfaces = owner["allowed_optimization_surfaces"]
    assert (
        "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_RESEARCH_PROGRAM_V1"
        in surfaces
    )
    paths = surfaces[
        "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_RESEARCH_PROGRAM_V1"
    ]["path_prefixes"]
    assert PROGRAM_REL_PATH in paths
