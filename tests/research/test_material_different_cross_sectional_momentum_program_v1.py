"""Definition-only contract tests for CS momentum program v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.material_different_cross_sectional_momentum_program_v1 import (
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
HOLDOUT_SUMMARY = (
    REPO
    / "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_v1/summary.json"
)
HOLDOUT_MANIFEST = (
    REPO
    / "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_v1/run_manifest.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_program_definition_only() -> None:
    report = load_and_validate_repo_program(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is True
    assert report["program_id"] == "MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_PROGRAM_V1"
    assert report["strategy_identity"] == "CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1"
    assert report["holdout_authorized"] is False
    assert report["evaluation_authorized"] is False
    assert report["promotion_eligible"] is False
    assert report["development_run_count"] == 0
    assert report["runner_start_count"] == 0


def test_causal_independence_and_no_core_mutation_flags() -> None:
    payload = _load(PROGRAM_PATH)
    assert payload["strategy_implementation_present"] is False
    assert payload["strategy_implementation_authorized_in_this_slice"] is False
    assert payload["run_slot_consumed"] is False
    assert payload["holdout_forbidden"] is True
    assert payload["runtime_authorized"] is False
    independence = payload["causal_independence"]
    assert independence["independent_from_closed_entry_eligibility_lane"] is True
    assert independence["independent_from_closed_exit_efficiency_lane"] is True
    assert independence["prior_terminal_relative_strength_v0_retry_forbidden"] is True
    for forbidden in (
        "bollinger_bands_mean_reversion",
        "midband_exit_logic",
        "reentry_cooldown",
        "adx_di_direction_confirmation",
        "regime_gated_standaside",
        "ma_trend_alignment_entry_filter",
        "macd_histogram_countertrend_entry_filter",
        "rsi_exhaustion_entry_filter",
    ):
        assert forbidden in independence["forbidden_lineage_refs"]


def test_closed_lanes_and_terminal_holdout_immutable() -> None:
    entry = _load(ENTRY_BACKLOG)
    exitb = _load(EXIT_BACKLOG)
    assert entry["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert exitb["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert entry["explicit_closeout_decision"] is True
    assert exitb["explicit_closeout_decision"] is True
    summary = _load(HOLDOUT_SUMMARY)
    manifest = _load(HOLDOUT_MANIFEST)
    assert summary["holdout_run_count"] == 1
    assert summary["runner_start_count"] == 1
    assert summary["result_class"] == "FAIL"
    assert manifest["holdout_run_count"] == 1
    assert manifest["reason"] == "NET_PROFIT_FACTOR_NOT_IMPROVED"


def test_fail_closed_on_authorization_mutation() -> None:
    payload = _load(PROGRAM_PATH)
    bad = copy.deepcopy(payload)
    bad["evaluation_authorized"] = True
    with pytest.raises(ProgramValidationError, match="EVALUATION_AUTHORIZED_TRUE"):
        validate_program_contract(bad)
    bad2 = copy.deepcopy(payload)
    bad2["development_run_count"] = 1
    with pytest.raises(ProgramValidationError, match="DEVELOPMENT_RUN_COUNT_NONZERO"):
        validate_program_contract(bad2)
    bad3 = copy.deepcopy(payload)
    bad3["strategy_implementation_present"] = True
    with pytest.raises(ProgramValidationError, match="STRATEGY_IMPLEMENTATION_PRESENT"):
        validate_program_contract(bad3)


def test_governance_and_owner_map() -> None:
    assert GOVERNANCE.is_file()
    assert "DOCS_TOKEN_MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_PROGRAM_V1" in (
        GOVERNANCE.read_text(encoding="utf-8")
    )
    owners = _load(OWNER_MAP)["allowed_optimization_surfaces"]
    assert "MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_PROGRAM_V1" in owners
