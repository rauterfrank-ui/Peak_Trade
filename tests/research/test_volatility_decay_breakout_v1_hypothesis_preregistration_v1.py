"""Definition-only contract tests for volatility decay breakout preregistration v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.volatility_decay_breakout_v1_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    EVIDENCE_REL_PATH,
    GOVERNANCE_REL_PATH,
    REQUIRED_BASELINE_ID,
    REQUIRED_DIRECTIONAL_FORM,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_PRODUCTIVE_PNL_REF,
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
    assert report["directional_form"] == REQUIRED_DIRECTIONAL_FORM
    assert report["baseline_id"] == REQUIRED_BASELINE_ID
    assert report["evaluation_authorized"] is False
    assert report["holdout_authorized"] is False
    assert report["dataset_bound"] is True
    assert report["development_run_count"] == 1
    assert report["runner_start_count"] == 1
    assert report["open_parameters_remaining"] is False
    assert report["material_difference_from_vcb_v1"] is True
    assert report["material_difference_from_vep_v1"] is True
    assert report["productive_pnl_evaluator_referenced"] is True
    assert report["second_pnl_truth_created"] is False
    assert report["time_segment_definition_id"] == REQUIRED_TIME_SEGMENT_DEFINITION_ID
    contract = _load(CONTRACT_PATH)
    assert compute_contract_digest(contract) == contract["contract_digest"]


def test_frozen_decay_mechanism_and_baseline_isolation() -> None:
    contract = _load(CONTRACT_PATH)
    adm = contract["admission_mechanism"]
    assert adm["vol_estimator"]["period"] == 14
    decay = adm["decay_confirmation"]
    assert decay["threshold_exclusive_max"] == 0.40
    assert decay["high_vol_prior_threshold_inclusive_min"] == 0.70
    life = adm["decay_event_lifecycle"]
    assert life["decay_window_bars"] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert life["event_consumption"] == "SINGLE_USE"
    assert life["expansion_persistence_not_required"] is True
    assert contract["baseline"]["sole_difference_vs_treatment"] == "VOLATILITY_DECAY_ADMISSION"
    assert (
        contract["exit_semantics"]["productive_exit_pnl_evaluator_ref"]
        == REQUIRED_PRODUCTIVE_PNL_REF
    )
    assert PRODUCTIVE_PNL.is_file()
    assert contract["strategy_implementation_present"] is False
    assert contract["development_run_count"] == 1
    assert contract["run_slot_consumed"] is True


def test_material_difference_vs_vep_vcb() -> None:
    contract = _load(CONTRACT_PATH)
    md_vep = contract["material_difference_vs_volatility_expansion_persistence_v1"]
    assert md_vep["prior_strategy_identity"] == "VOLATILITY_EXPANSION_PERSISTENCE_V1"
    assert md_vep["vep_retry_forbidden"] is True
    assert md_vep["not_a_repair_or_retry_of_vep_v1"] is True
    assert "not_an_exit_repair" in md_vep["differences"]
    md_vcb = contract["material_difference_vs_volatility_compression_breakout_v1"]
    assert md_vcb["vcb_retry_forbidden"] is True
    backlog = _load(BACKLOG_PATH)
    assert backlog["preregistered_hypotheses"][0]["strategy_identity"] == (
        "VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1"
    )
    terminals = {t["strategy_identity"] for t in backlog["terminal_hypotheses"]}
    assert "VOLATILITY_DECAY_BREAKOUT_V1" in terminals
    assert "VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1" in terminals
    program = _load(PROGRAM_PATH)
    assert (
        "VOLATILITY_EXPANSION_PERSISTENCE_V1"
        in program["causal_independence"]["forbidden_lineage_refs"]
    )
    assert program["strategy_identity"] == ("VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1")


def test_fail_closed_on_semantics_mutation() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["admission_mechanism"]["decay_confirmation"]["threshold_exclusive_max"] = 0.50
    with pytest.raises(PreregistrationValidationError, match="DECAY_THR"):
        validate_measurement_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["material_difference_vs_volatility_expansion_persistence_v1"]["vep_retry_forbidden"] = (
        False
    )
    with pytest.raises(PreregistrationValidationError, match="VEP_RETRY_ALLOWED"):
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
    with pytest.raises(PreregistrationValidationError, match="HOLDOUT"):
        reject_holdout_dataset_or_path("offline_economic_reevaluation_sealed_long_panel_v1")


def test_governance_evidence_owner_map() -> None:
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_VOLATILITY_DECAY_BREAKOUT_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1" in text
    assert (EVIDENCE / "README.md").is_file()
    assert (EVIDENCE / "summary.json").is_file()
    assert (EVIDENCE / "safety_attestation.md").is_file()
    assert (EVIDENCE / "split_manifest.json").is_file()
    summary = _load(EVIDENCE / "summary.json")
    assert summary["evaluation_executed"] is False
    assert summary["holdout_accessed"] is False
    assert summary["forensic_class"] == "HYPOTHESIS_TERMINAL"
    owners = _load(OWNER_MAP)["allowed_optimization_surfaces"]
    assert "VOLATILITY_DECAY_BREAKOUT_V1_HYPOTHESIS_PREREGISTRATION_DEFINITION_ONLY_V1" in owners
