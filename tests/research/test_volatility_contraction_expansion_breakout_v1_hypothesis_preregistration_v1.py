"""Definition-only contract tests for VCEB preregistration v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.volatility_contraction_expansion_breakout_v1_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    EVIDENCE_REL_PATH,
    GOVERNANCE_REL_PATH,
    REQUIRED_BASELINE_ID,
    REQUIRED_DIRECTIONAL_FORM,
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
    assert report["material_difference_from_vcb_v1"] is True
    assert report["material_difference_from_vdbx_v1"] is True
    assert report["productive_pnl_evaluator_referenced"] is True
    assert report["second_pnl_truth_created"] is False
    assert report["portfolio_aggregation_id"] == REQUIRED_PORTFOLIO
    assert report["time_segment_definition_id"] == REQUIRED_TIME_SEGMENT_DEFINITION_ID
    contract = _load(CONTRACT_PATH)
    assert compute_contract_digest(contract) == contract["contract_digest"]


def test_frozen_joint_transition_mechanism_and_exit_pairability() -> None:
    contract = _load(CONTRACT_PATH)
    adm = contract["admission_mechanism"]
    assert adm["vol_estimator"]["family"] == "REALIZED_VOLATILITY"
    assert adm["vol_estimator"]["period"] == 24
    assert adm["contraction_state"]["percentile_inclusive_max"] == 0.30
    assert adm["contraction_state"]["min_consecutive_completed_bars"] == 8
    assert adm["expansion_trigger"]["absolute_percentile_inclusive_min"] == 0.65
    assert adm["expansion_trigger"]["relative_percentile_rise_inclusive_min"] == 0.25
    life = adm["transition_event_lifecycle"]
    assert life["entry_window_bars"] == [1]
    assert life["joint_price_break_required_on_confirmation_bar_t"] is True
    assert life["vcb_style_multi_bar_release_window_forbidden"] is True
    assert life["decay_admission_not_required"] is True
    entry = adm["directional_entry"]
    assert entry["joint_coincidence_required"] is True
    assert entry["ex_ante_exit_reachability_required"] is True
    assert entry["min_post_fill_bars_required_inclusive"] == 48
    exits = contract["exit_semantics"]
    assert exits["precedence_ascending_wins_first"] == REQUIRED_PRECEDENCE
    assert exits["trailing_stop_forbidden"] is True
    assert exits["opposite_break_invalidation"]["authorized"] is True
    assert exits["every_admitted_entry_must_have_reachable_exit"] is True
    assert exits["productive_exit_pnl_evaluator_ref"] == REQUIRED_PRODUCTIVE_PNL_REF
    assert PRODUCTIVE_PNL.is_file()
    assert contract["strategy_implementation_present"] is False
    assert contract["development_run_count"] == 1
    assert contract["run_slot_consumed"] is True
    assert contract["baseline"]["sole_difference_vs_treatment"] == (
        "VOLATILITY_CONTRACTION_EXPANSION_JOINT_ADMISSION"
    )


def test_material_difference_vs_terminals_and_bindings() -> None:
    contract = _load(CONTRACT_PATH)
    md_vcb = contract["material_difference_vs_volatility_compression_breakout_v1"]
    assert md_vcb["vcb_retry_forbidden"] is True
    assert md_vcb["not_a_parameter_change_of_vcb_v1"] is True
    md_vdbx = contract[
        "material_difference_vs_volatility_decay_breakout_with_explicit_decay_exit_v1"
    ]
    assert md_vdbx["vdbx_retry_forbidden"] is True
    assert md_vdbx["not_a_repair_or_retry_of_vdbx_v1"] is True
    backlog = _load(BACKLOG_PATH)
    assert backlog["status"] == "OPEN_BACKLOG"
    assert len(backlog["preregistered_hypotheses"]) == 1
    assert backlog["preregistered_hypotheses"][0]["strategy_identity"] == (
        "VOLATILITY_TERM_STRUCTURE_REVERSION_V1"
    )
    terminals = {t["strategy_identity"] for t in backlog["terminal_hypotheses"]}
    assert REQUIRED_STRATEGY_IDENTITY in terminals
    assert "VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1" in terminals
    assert terminals == {
        "VOLATILITY_COMPRESSION_BREAKOUT_V1",
        "VOLATILITY_EXPANSION_PERSISTENCE_V1",
        "VOLATILITY_DECAY_BREAKOUT_V1",
        "VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1",
        "VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1",
        "VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1",
        "VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1",
    }
    program = _load(PROGRAM_PATH)
    assert program["strategy_identity"] == ("VOLATILITY_TERM_STRUCTURE_REVERSION_V1")
    assert REQUIRED_STRATEGY_IDENTITY in program["causal_independence"]["forbidden_lineage_refs"]


def test_fail_closed_on_semantics_mutation() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["admission_mechanism"]["contraction_state"]["percentile_inclusive_max"] = 0.20
    with pytest.raises(PreregistrationValidationError, match="CONTRACTION_THR"):
        validate_measurement_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["exit_semantics"]["trailing_stop_forbidden"] = False
    with pytest.raises(PreregistrationValidationError, match="TRAILING_ALLOWED"):
        validate_measurement_contract(bad2)
    bad3 = copy.deepcopy(contract)
    bad3["material_difference_vs_volatility_compression_breakout_v1"]["vcb_retry_forbidden"] = False
    with pytest.raises(PreregistrationValidationError, match="VCB_RETRY_ALLOWED"):
        validate_measurement_contract(bad3)
    bad4 = copy.deepcopy(contract)
    bad4["development_run_count"] = 2
    with pytest.raises(PreregistrationValidationError, match="DEVELOPMENT_RUN_COUNT"):
        validate_measurement_contract(bad4)
    bad5 = copy.deepcopy(contract)
    bad5["exit_semantics"]["second_pnl_truth_forbidden"] = False
    with pytest.raises(PreregistrationValidationError, match="SECOND_PNL_TRUTH"):
        validate_measurement_contract(bad5)


def test_holdout_rejected() -> None:
    with pytest.raises(PreregistrationValidationError, match="HOLDOUT"):
        reject_holdout_dataset_or_path("offline_economic_reevaluation_sealed_long_panel_v1")


def test_governance_evidence_owner_map() -> None:
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1_"
        "PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1"
    ) in text
    assert (EVIDENCE / "README.md").is_file()
    assert (EVIDENCE / "summary.json").is_file()
    assert (EVIDENCE / "safety_attestation.md").is_file()
    assert (EVIDENCE / "split_manifest.json").is_file()
    assert (EVIDENCE / "timing_proof.txt").is_file()
    summary = _load(EVIDENCE / "summary.json")
    assert summary["evaluation_executed"] is False
    assert summary["holdout_accessed"] is False
    assert summary["development_run_count"] == 1
    assert summary["runner_start_count"] == 1
    assert summary["development_evaluation_executed"] is True
    owners = _load(OWNER_MAP)["allowed_optimization_surfaces"]
    assert (
        "VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1_HYPOTHESIS_PREREGISTRATION_DEFINITION_ONLY_V1"
    ) in owners
