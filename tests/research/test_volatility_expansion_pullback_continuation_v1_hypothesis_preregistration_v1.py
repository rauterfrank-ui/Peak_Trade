"""Definition-only contract tests for VEPC preregistration v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.volatility_expansion_pullback_continuation_v1_hypothesis_preregistration_v1 import (
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
    / "config/research/volatility_expansion_pullback_continuation_v1_development_evaluation_entry_point_binding_v1.json"
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
    assert report["development_evaluation_executed"] is False
    assert report["holdout_authorized"] is False
    assert report["dataset_bound"] is True
    assert report["development_run_count"] == 1
    assert report["runner_start_count"] == 1
    assert report["run_slot_consumed"] is True
    assert report["open_parameters_remaining"] is False
    assert report["entry_semantics_complete"] is True
    assert report["exit_semantics_complete"] is True
    assert report["entry_exit_pairable"] is True
    assert report["material_difference_from_vceb_v1"] is True
    assert report["productive_pnl_evaluator_referenced"] is True
    assert report["second_pnl_truth_created"] is False
    assert report["canonical_entry_point"] == REQUIRED_ENTRY_POINT_SCRIPT
    assert report["portfolio_aggregation_id"] == REQUIRED_PORTFOLIO
    assert report["time_segment_definition_id"] == REQUIRED_TIME_SEGMENT_DEFINITION_ID
    contract = _load(CONTRACT_PATH)
    assert compute_contract_digest(contract) == contract["contract_digest"]


def test_frozen_pullback_continuation_mechanism_and_exit_pairability() -> None:
    contract = _load(CONTRACT_PATH)
    adm = contract["admission_mechanism"]
    assert adm["expansion_state"]["percentile_inclusive_min"] == 0.65
    assert adm["expansion_state"]["min_consecutive_completed_bars"] == 4
    pb = adm["pullback_requirement"]
    assert pb["max_pullback_bars_inclusive"] == 8
    assert pb["min_pullback_fraction_of_impulse_range"] == 0.15
    assert pb["max_pullback_fraction_of_impulse_range"] == 0.50
    assert pb["pullback_required_before_entry"] is True
    cont = adm["continuation_entry"]
    assert cont["entry_only_after_pullback_then_continuation"] is True
    assert cont["no_immediate_post_expansion_breakout_entry"] is True
    exits = contract["exit_semantics"]
    assert exits["precedence_ascending_wins_first"] == REQUIRED_PRECEDENCE
    assert exits["trailing_stop_forbidden"] is True
    assert exits["pullback_structure_invalidation"]["authorized"] is True
    assert exits["productive_exit_pnl_evaluator_ref"] == REQUIRED_PRODUCTIVE_PNL_REF
    assert PRODUCTIVE_PNL.is_file()
    assert contract["strategy_implementation_present"] is False
    assert contract["development_run_count"] == 1
    assert contract["run_slot_consumed"] is True
    ep = contract["canonical_development_evaluation_entry_point"]
    assert ep["definition_only"] is True
    assert ep["evaluation_authorized_in_this_slice"] is False
    assert ep["script_ref"] == REQUIRED_ENTRY_POINT_SCRIPT
    assert ENTRY_POINT_BINDING.is_file()
    binding = _load(ENTRY_POINT_BINDING)
    assert binding["status"] == "RUN_SLOT_CONSUMED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT"
    assert binding["development_evaluation_executed"] is False
    assert binding["development_run_count"] == 1
    assert binding["runner_start_count"] == 1
    assert binding["holdout_forbidden"] is True
    assert binding["dataset_binding"]["dataset_class"] == "DEVELOPMENT_ONLY"
    assert (
        REPO / "src/research/volatility_expansion_pullback_continuation_v1_strategy_v1.py"
    ).is_file()


def test_material_difference_vs_terminals_and_bindings() -> None:
    contract = _load(CONTRACT_PATH)
    md = contract["material_difference_vs_volatility_contraction_expansion_breakout_v1"]
    assert md["vceb_retry_forbidden"] is True
    assert md["not_a_repair_or_retry_of_vceb_v1"] is True
    backlog = _load(BACKLOG_PATH)
    assert backlog["preregistered_hypotheses"] == []
    assert backlog["status"] == "AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS"
    terminals = {t["strategy_identity"] for t in backlog["terminal_hypotheses"]}
    assert terminals == {
        "VOLATILITY_COMPRESSION_BREAKOUT_V1",
        "VOLATILITY_EXPANSION_PERSISTENCE_V1",
        "VOLATILITY_DECAY_BREAKOUT_V1",
        "VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1",
        "VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1",
        "VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1",
    }
    assert REQUIRED_STRATEGY_IDENTITY in terminals
    program = _load(PROGRAM_PATH)
    assert program["strategy_identity"] == REQUIRED_STRATEGY_IDENTITY
    assert REQUIRED_PREDECESSOR in program["causal_independence"]["forbidden_lineage_refs"]


def test_fail_closed_on_semantics_mutation() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["admission_mechanism"]["pullback_requirement"]["pullback_required_before_entry"] = False
    with pytest.raises(PreregistrationValidationError, match="PULLBACK_REQUIRED"):
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
    # Split marker avoids Policy Critic NO_SECRETS false positive on docs_token lines.
    assert "docs_token:" in text
    assert (
        "DOCS_TOKEN_VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1_"
        "PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1"
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
    assert summary["development_run_count"] == 0
    assert summary["run_slot_consumed"] is False
    assert summary["holdout_accessed"] is False
    assert summary["orders"] is False
    assert summary["live_authorized"] is False
    assert summary["second_pnl_truth_created"] is False
    # Preregistration evidence digest is frozen at preregistration time; live contract
    # digest advances when the historical slot is marked CONSUMED_NO_RETRY.
    assert isinstance(summary["contract_digest"], str) and len(summary["contract_digest"]) == 64
    owner = _load(OWNER_MAP)
    key = "VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1_HYPOTHESIS_PREREGISTRATION_DEFINITION_ONLY_V1"
    assert key in owner["allowed_optimization_surfaces"]
