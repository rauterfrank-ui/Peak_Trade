"""Definition-only contract tests for VTSR preregistration v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.volatility_term_structure_reversion_v1_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    EVIDENCE_REL_PATH,
    GOVERNANCE_REL_PATH,
    REQUIRED_BASELINE_ID,
    REQUIRED_DIRECTIONAL_FORM,
    REQUIRED_ENTRY_POINT_SCRIPT,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_PORTFOLIO,
    REQUIRED_PREDECESSOR,
    REQUIRED_PRECEDENCE,
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
ENTRY_POINT_BINDING = (
    REPO
    / "config/research/volatility_term_structure_reversion_v1_development_evaluation_entry_point_binding_v1.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_definition_only_digest() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is True
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["strategy_identity"] == REQUIRED_STRATEGY_IDENTITY
    assert report["predecessor_strategy_id"] == REQUIRED_PREDECESSOR
    assert report["directional_form"] == REQUIRED_DIRECTIONAL_FORM
    assert report["baseline_id"] == REQUIRED_BASELINE_ID
    assert report["evaluation_authorized"] is False
    assert report["development_evaluation_authorized"] is True
    assert report["development_evaluation_executed"] is True
    assert report["holdout_authorized"] is False
    assert report["dataset_bound"] is True
    assert report["development_run_count"] == 1
    assert report["runner_start_count"] == 1
    assert report["run_slot_consumed"] is True
    assert report["open_parameters_remaining"] is False
    assert report["entry_semantics_complete"] is True
    assert report["exit_semantics_complete"] is True
    assert report["entry_exit_pairable"] is True
    assert report["material_difference_from_vefcf_v1"] is True
    assert report["productive_pnl_evaluator_referenced"] is True
    assert report["second_pnl_truth_created"] is False
    assert report["canonical_entry_point"] == REQUIRED_ENTRY_POINT_SCRIPT
    assert report["portfolio_aggregation_id"] == REQUIRED_PORTFOLIO
    assert report["time_segment_definition_id"] == REQUIRED_TIME_SEGMENT_DEFINITION_ID
    contract = _load(CONTRACT_PATH)
    assert compute_contract_digest(contract) == contract["contract_digest"]


def test_frozen_term_structure_reversion_mechanism_and_exit_pairability() -> None:
    contract = _load(CONTRACT_PATH)
    adm = contract["admission_mechanism"]
    assert adm["vol_estimator"]["family"] == "REALIZED_VOLATILITY_TERM_STRUCTURE"
    assert adm["vol_estimator"]["short_horizon_completed_bars"] == 8
    assert adm["vol_estimator"]["long_horizon_completed_bars"] == 48
    ts = adm["term_structure_state"]
    assert ts["elevated_ratio_percentile_inclusive_min"] == 0.80
    assert ts["min_consecutive_elevated_bars"] == 2
    assert ts["depressed_entry_forbidden_in_v1"] is True
    fade = adm["reversion_fade_entry"]
    assert fade["entry_only_after_elevated_term_structure_state"] is True
    assert fade["vefcf_failed_continuation_fade_entry_forbidden"] is True
    assert fade["direction_rule"] == "opposite_to_signed_return_over_short_horizon_window"
    exits = contract["exit_semantics"]
    assert exits["precedence_ascending_wins_first"] == REQUIRED_PRECEDENCE
    assert exits["trailing_stop_forbidden"] is True
    assert exits["term_structure_normalization_invalidation"]["authorized"] is True
    assert exits["productive_exit_pnl_evaluator_ref"] == REQUIRED_PRODUCTIVE_PNL_REF
    assert PRODUCTIVE_PNL.is_file()
    assert contract["strategy_implementation_present"] is False
    assert contract["development_run_count"] == 1
    assert contract["run_slot_consumed"] is True
    ep = contract["canonical_development_evaluation_entry_point"]
    assert ep["definition_only"] is True
    assert ep["evaluation_authorized_in_this_slice"] is False
    assert ep["script_ref"] == REQUIRED_ENTRY_POINT_SCRIPT
    assert ep["status"] == "RUN_SLOT_CONSUMED_DEVELOPMENT_FAIL"
    assert ENTRY_POINT_BINDING.is_file()
    binding = _load(ENTRY_POINT_BINDING)
    assert binding["status"] == "RUN_SLOT_CONSUMED_DEVELOPMENT_FAIL"
    assert binding["development_evaluation_executed"] is True
    assert binding["development_run_count"] == 1
    assert binding["runner_start_count"] == 1
    assert binding["holdout_forbidden"] is True


def test_material_difference_vs_terminals_and_bindings() -> None:
    contract = _load(CONTRACT_PATH)
    md = contract["material_difference_vs_volatility_expansion_failed_continuation_fade_v1"]
    assert md["vefcf_retry_forbidden"] is True
    assert md["not_a_repair_or_retry_of_vefcf_v1"] is True
    backlog = _load(BACKLOG_PATH)
    assert len(backlog["preregistered_hypotheses"]) == 1
    assert backlog["status"] == "OPEN_BACKLOG"
    assert backlog["preregistered_hypotheses"][0]["strategy_identity"] == REQUIRED_STRATEGY_IDENTITY
    terminals = {t["strategy_identity"] for t in backlog["terminal_hypotheses"]}
    assert REQUIRED_PREDECESSOR in terminals
    assert REQUIRED_STRATEGY_IDENTITY not in terminals
    program = _load(PROGRAM_PATH)
    assert program["strategy_identity"] == REQUIRED_STRATEGY_IDENTITY
    assert REQUIRED_PREDECESSOR in program["causal_independence"]["forbidden_lineage_refs"]


def test_fail_closed_on_semantics_mutation() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["admission_mechanism"]["reversion_fade_entry"][
        "entry_only_after_elevated_term_structure_state"
    ] = False
    with pytest.raises(PreregistrationValidationError, match="FADE_ORDER"):
        validate_measurement_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["exit_semantics"]["trailing_stop_forbidden"] = False
    with pytest.raises(PreregistrationValidationError, match="TRAILING_ALLOWED"):
        validate_measurement_contract(bad2)
    bad3 = copy.deepcopy(contract)
    bad3["development_run_count"] = 0
    with pytest.raises(PreregistrationValidationError, match="DEVELOPMENT_RUN_COUNT"):
        validate_measurement_contract(bad3)
    bad4 = copy.deepcopy(contract)
    bad4["exit_semantics"]["second_pnl_truth_forbidden"] = False
    with pytest.raises(PreregistrationValidationError, match="SECOND_PNL_TRUTH"):
        validate_measurement_contract(bad4)


def test_holdout_rejected() -> None:
    with pytest.raises(PreregistrationValidationError, match="HOLDOUT_ACCESS_FORBIDDEN"):
        reject_holdout_dataset_or_path("offline_economic_reevaluation_sealed_long_panel_v1")


def test_governance_evidence_owner_map() -> None:
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert "docs_token:" in text
    assert (
        "DOCS_TOKEN_VOLATILITY_TERM_STRUCTURE_REVERSION_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1"
    ) in text
    required = {
        "README.md",
        "summary.json",
        "safety_attestation.md",
        "split_manifest.json",
        "timing_proof.txt",
    }
    assert required.issubset({p.name for p in EVIDENCE.iterdir() if p.is_file()})
    summary = _load(EVIDENCE / "summary.json")
    assert summary["development_run_count"] == 1
    assert summary["run_slot_consumed"] is True
    assert summary["runner_start_count"] == 1
    assert summary["development_evaluation_executed"] is True
    assert summary["holdout_accessed"] is False
    assert summary["orders"] is False
    assert summary["live_authorized"] is False
    assert summary["second_pnl_truth_created"] is False
    assert summary["contract_digest"] == _load(CONTRACT_PATH)["contract_digest"]
    owner = _load(OWNER_MAP)
    key = "VOLATILITY_TERM_STRUCTURE_REVERSION_V1_HYPOTHESIS_PREREGISTRATION_DEFINITION_ONLY_V1"
    assert key in owner["allowed_optimization_surfaces"]
