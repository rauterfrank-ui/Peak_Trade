"""Definition-only contract tests for VDBX explicit-decay-exit preregistration v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    EVIDENCE_REL_PATH,
    GOVERNANCE_REL_PATH,
    REQUIRED_BASELINE_ID,
    REQUIRED_DIRECTIONAL_FORM,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_PORTFOLIO,
    REQUIRED_PREDECESSOR,
    REQUIRED_PRODUCTIVE_PNL_REF,
    REQUIRED_STRATEGY_IDENTITY,
    REQUIRED_TIME_SEGMENT_DEFINITION_ID,
    PreregistrationValidationError,
    compute_contract_digest,
    load_and_validate_repo_contract,
    reject_holdout_dataset_or_path,
    validate_measurement_contract,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
GOVERNANCE = REPO / GOVERNANCE_REL_PATH
EVIDENCE = REPO / EVIDENCE_REL_PATH
OWNER_MAP = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
PROGRAM_PATH = REPO / "config/research/volatility_regime_research_program_v1.json"
BACKLOG_PATH = REPO / "config/research/volatility_regime_hypothesis_backlog_v1.json"
PRODUCTIVE_PNL = REPO / REQUIRED_PRODUCTIVE_PNL_REF


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_definition_only_digest() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["strategy_identity"] == REQUIRED_STRATEGY_IDENTITY
    assert report["predecessor_strategy_id"] == REQUIRED_PREDECESSOR
    assert report["directional_form"] == REQUIRED_DIRECTIONAL_FORM
    assert report["baseline_id"] == REQUIRED_BASELINE_ID
    assert report["evaluation_authorized"] is False
    assert report["development_evaluation_authorized"] is False
    assert report["development_evaluation_executed"] is False
    assert report["holdout_authorized"] is False
    assert report["dataset_bound"] is True
    assert report["development_run_count"] == 0
    assert report["open_parameters_remaining"] is False
    assert report["exit_state_machine_complete"] is True
    assert report["exit_precedence_complete"] is True
    assert report["materially_distinct_from_predecessor"] is True
    assert report["productive_pnl_evaluator_referenced"] is True
    assert report["second_pnl_truth_created"] is False
    assert report["second_equity_truth_created"] is False
    assert report["second_stats_truth_created"] is False
    assert report["portfolio_aggregation_id"] == REQUIRED_PORTFOLIO
    assert report["time_segment_definition_id"] == REQUIRED_TIME_SEGMENT_DEFINITION_ID
    contract = _load(CONTRACT_PATH)
    assert compute_contract_digest(contract) == contract["contract_digest"]


def test_exit_semantics_and_material_difference() -> None:
    contract = _load(CONTRACT_PATH)
    exits = contract["exit_semantics"]
    assert exits["exit_state_machine_implemented"] is True
    assert exits["every_admitted_entry_must_have_reachable_exit"] is True
    assert exits["evaluator_side_reconstruction_of_missing_strategy_exits_forbidden"] is True
    assert exits["synthetic_fills_solely_to_pair_trades_forbidden"] is True
    assert exits["precedence_ascending_wins_first"][0] == "INITIAL_STOP"
    assert exits["precedence_ascending_wins_first"][-1] == "END_OF_PANEL_LIQUIDATION"
    assert exits["signal_exit"]["threshold_inclusive_min"] == 0.70
    assert PRODUCTIVE_PNL.is_file()
    md = contract["material_difference_vs_volatility_decay_breakout_v1"]
    assert md["vdb_retry_forbidden"] is True
    assert md["not_a_corrective_retry_of_vdb_v1"] is True
    assert contract["predecessor_strategy_id"] == REQUIRED_PREDECESSOR
    backlog = _load(BACKLOG_PATH)
    assert backlog["preregistered_hypotheses"][0]["strategy_identity"] == REQUIRED_STRATEGY_IDENTITY
    terminals = {t["strategy_identity"] for t in backlog["terminal_hypotheses"]}
    assert "VOLATILITY_DECAY_BREAKOUT_V1" in terminals
    program = _load(PROGRAM_PATH)
    assert program["strategy_identity"] == REQUIRED_STRATEGY_IDENTITY


def test_fail_closed_on_semantics_mutation() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["exit_semantics"]["exit_state_machine_implemented"] = False
    with pytest.raises(PreregistrationValidationError, match="EXIT_SM_MISSING"):
        validate_measurement_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["material_difference_vs_volatility_decay_breakout_v1"]["vdb_retry_forbidden"] = False
    with pytest.raises(PreregistrationValidationError, match="VDB_RETRY_ALLOWED"):
        validate_measurement_contract(bad2)
    bad3 = copy.deepcopy(contract)
    bad3["development_evaluation_authorized"] = True
    with pytest.raises(PreregistrationValidationError, match="DEV_EVAL_AUTHORIZED"):
        validate_measurement_contract(bad3)


def test_holdout_rejected() -> None:
    with pytest.raises(PreregistrationValidationError, match="HOLDOUT"):
        reject_holdout_dataset_or_path("offline_economic_reevaluation_sealed_long_panel_v1")


def test_governance_evidence_owner_map() -> None:
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1_"
        "PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1"
    ) in text
    assert (EVIDENCE / "README.md").is_file()
    assert (EVIDENCE / "summary.json").is_file()
    summary = _load(EVIDENCE / "summary.json")
    assert summary["evaluation_executed"] is False
    assert summary["holdout_accessed"] is False
    owner = _load(OWNER_MAP)
    surfaces = owner["allowed_optimization_surfaces"]
    assert (
        "VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1_HYPOTHESIS_PREREGISTRATION_"
        "DEFINITION_ONLY_V1"
    ) in surfaces
