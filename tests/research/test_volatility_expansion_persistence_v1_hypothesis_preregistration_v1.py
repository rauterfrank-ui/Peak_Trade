"""Definition-only contract tests for volatility expansion persistence preregistration v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.volatility_expansion_persistence_v1_hypothesis_preregistration_v1 import (
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
ENTRY_BACKLOG = (
    REPO / "config/research/canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.json"
)
EXIT_BACKLOG = REPO / "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
CS_PROGRAM = REPO / "config/research/material_different_cross_sectional_momentum_program_v1.json"
PROGRAM_PATH = REPO / "config/research/volatility_regime_research_program_v1.json"
BACKLOG_PATH = REPO / "config/research/volatility_regime_hypothesis_backlog_v1.json"
COILED_SPRING_BINDING = REPO / "config/research/vol_breakout_v1_versioned_research_binding_v0.json"
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
    assert report["material_difference_explicit"] is True
    assert report["material_difference_from_vcb_v1"] is True
    assert report["exit_semantics_frozen"] is True
    assert report["event_sufficiency_frozen"] is True
    assert report["productive_pnl_evaluator_referenced"] is True
    assert report["second_pnl_truth_created"] is False
    assert report["pending_threshold_keys"] == []
    assert report["time_segment_definition_id"] == REQUIRED_TIME_SEGMENT_DEFINITION_ID
    contract = _load(CONTRACT_PATH)
    assert compute_contract_digest(contract) == contract["contract_digest"]


def test_frozen_mechanism_and_baseline_isolation() -> None:
    contract = _load(CONTRACT_PATH)
    adm = contract["admission_mechanism"]
    assert adm["vol_estimator"]["period"] == 14
    assert adm["vol_estimator"]["normalization"] == "ATR_DIV_CLOSE"
    pct = adm["vol_estimator"]["percentile_metric"]
    assert pct["rolling_lookback_bars"] == 120
    assert pct["percentile_tie_method"] == "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
    assert pct["percentile_rank_window_includes_current_value"] is True
    assert adm["expansion_confirmation"]["threshold_inclusive_min"] == 0.80
    assert adm["expansion_confirmation"]["bars_required_at_or_above_threshold"] == 2
    life = adm["expansion_event_lifecycle"]
    assert life["compression_regime_not_required"] is True
    assert life["persistence_window_bars"] == [1, 2, 3, 4, 5, 6]
    assert life["event_consumption"] == "SINGLE_USE"
    assert adm["directional_entry"]["channel_lookback_completed_bars"] == 20
    assert adm["directional_entry"]["entry_on_expansion_confirmation_bar_t_forbidden"] is True
    assert contract["exit_semantics"]["initial_stop_atr_multiple"] == 1.5
    assert contract["exit_semantics"]["trailing_stop_atr_multiple"] == 2.0
    assert contract["exit_semantics"]["time_exit_max_bars"] == 48
    assert (
        contract["exit_semantics"]["productive_exit_pnl_evaluator_ref"]
        == REQUIRED_PRODUCTIVE_PNL_REF
    )
    assert PRODUCTIVE_PNL.is_file()
    assert contract["baseline"]["baseline_id"] == REQUIRED_BASELINE_ID
    assert contract["baseline"]["sole_difference_vs_treatment"] == "EXPANSION_PERSISTENCE_ADMISSION"
    events = contract["event_sufficiency_gates"]
    assert events["min_evaluable_treatment_breakout_events"] == 50
    assert events["min_executed_treatment_trades"] == 30
    assert events["min_evaluable_treatment_events_per_time_segment"] == 10
    assert contract["costs"]["fee_bps_per_side"] == 10.0
    assert contract["costs"]["slippage_bps_per_side"] == 5.0
    assert contract["strategy_implementation_present"] is False
    assert contract["parameter_governance"]["open_parameters_remaining"] is False
    assert contract["development_run_count"] == 1
    assert contract["runner_start_count"] == 1
    assert contract["run_slot_consumed"] is True


def test_definition_semantics_complete_bindings() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["definition_semantics_complete"] is True
    assert report["percentile_tie_method"] == "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
    assert report["percentile_current_value_included"] is True
    assert report["expansion_event_consumption"] == "SINGLE_USE"
    assert report["persistence_window_bars"] == [1, 2, 3, 4, 5, 6]

    contract = _load(CONTRACT_PATH)
    life = contract["admission_mechanism"]["expansion_event_lifecycle"]
    assert (
        life[
            "rearm_requires_normalized_atr_percentile_below_threshold_for_at_least_one_completed_bar"
        ]
        is True
    )
    assert life["rearm_threshold_exclusive_max"] == 0.80
    assert life["no_entry_on_initial_compression_release_or_breakout_bar"] is True
    frozen = contract["parameter_governance"]["frozen_parameters"]
    assert frozen["atr_period"] == 14
    assert frozen["expansion_confirmation_threshold"] == 0.80
    assert frozen["persistence_window_start_offset"] == 1
    assert frozen["persistence_window_end_offset"] == 6
    assert contract["parameter_governance"]["definition_semantics_complete"] is True


def test_fail_closed_on_semantics_mutation() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["admission_mechanism"]["vol_estimator"]["percentile_metric"]["percentile_tie_method"] = (
        "AVERAGE_RANK"
    )
    with pytest.raises(PreregistrationValidationError, match="PERCENTILE_TIE_METHOD"):
        validate_measurement_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["admission_mechanism"]["expansion_confirmation"]["threshold_inclusive_min"] = 0.75
    with pytest.raises(PreregistrationValidationError, match="EXPANSION_THR"):
        validate_measurement_contract(bad2)
    bad3 = copy.deepcopy(contract)
    bad3["admission_mechanism"]["expansion_event_lifecycle"][
        "persistence_window_start_offset_after_confirmation_bar"
    ] = 0
    with pytest.raises(PreregistrationValidationError, match="PERSISTENCE_START"):
        validate_measurement_contract(bad3)
    bad4 = copy.deepcopy(contract)
    bad4["admission_mechanism"]["expansion_event_lifecycle"]["compression_regime_not_required"] = (
        False
    )
    with pytest.raises(PreregistrationValidationError, match="COMPRESSION_REQUIRED"):
        validate_measurement_contract(bad4)
    bad5 = copy.deepcopy(contract)
    bad5["parameter_governance"]["definition_semantics_complete"] = False
    with pytest.raises(PreregistrationValidationError, match="SEMANTICS_INCOMPLETE"):
        validate_measurement_contract(bad5)
    bad6 = copy.deepcopy(contract)
    bad6["exit_semantics"]["second_pnl_truth_forbidden"] = False
    with pytest.raises(PreregistrationValidationError, match="SECOND_PNL_TRUTH"):
        validate_measurement_contract(bad6)


def test_material_difference_vs_vcb_and_coiled_spring() -> None:
    contract = _load(CONTRACT_PATH)
    md = contract["material_difference_vs_terminal_coiled_spring"]
    assert md["prior_terminal_hypothesis_id"] == "VOL_BREAKOUT_COILED_SPRING_NON_BITCOIN_FUTURES_V1"
    assert md["unchanged_binding_retry_forbidden"] is True
    prior = _load(COILED_SPRING_BINDING)
    assert prior["hypothesis_id"] == "VOL_BREAKOUT_COILED_SPRING_NON_BITCOIN_FUTURES_V1"
    md_vcb = contract["material_difference_vs_volatility_compression_breakout_v1"]
    assert md_vcb["prior_strategy_identity"] == "VOLATILITY_COMPRESSION_BREAKOUT_V1"
    assert md_vcb["vcb_retry_forbidden"] is True
    assert md_vcb["not_a_parameter_change_of_vcb_v1"] is True
    assert contract["admission_mechanism"]["vol_estimator"]["period"] == 14
    program = _load(PROGRAM_PATH)
    forbidden = program["causal_independence"]["forbidden_lineage_refs"]
    assert "VOL_BREAKOUT_COILED_SPRING_NON_BITCOIN_FUTURES_V1" in forbidden
    assert "VOLATILITY_COMPRESSION_BREAKOUT_V1" in forbidden
    backlog = _load(BACKLOG_PATH)
    terminals = {t["strategy_identity"] for t in backlog["terminal_hypotheses"]}
    assert "VOLATILITY_EXPANSION_PERSISTENCE_V1" in terminals
    assert "VOLATILITY_COMPRESSION_BREAKOUT_V1" in terminals
    assert backlog["preregistered_hypotheses"][0]["strategy_identity"] == (
        "VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1"
    )
    assert "VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1" in terminals


def test_holdout_rejected_and_prior_lanes_unchanged() -> None:
    with pytest.raises(PreregistrationValidationError, match="HOLDOUT"):
        reject_holdout_dataset_or_path("offline_economic_reevaluation_sealed_long_panel_v1")
    with pytest.raises(PreregistrationValidationError, match="HOLDOUT"):
        reject_holdout_dataset_or_path(
            "docs/evidence/offline_economic_reevaluation_sealed_long_panel_v1/summary.json"
        )
    assert _load(ENTRY_BACKLOG)["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert _load(EXIT_BACKLOG)["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert _load(CS_PROGRAM)["status"] == "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"


def test_fail_closed_on_digest_or_runtime_mutation() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["contract_digest"] = "0" * 64
    with pytest.raises(PreregistrationValidationError, match="CONTRACT_DIGEST_MISMATCH"):
        validate_measurement_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["runtime_policy"]["orders_allowed"] = True
    with pytest.raises(PreregistrationValidationError, match="RUNTIME_FLAG_ORDERS_ALLOWED"):
        validate_measurement_contract(bad2)
    bad3 = copy.deepcopy(contract)
    bad3["evaluation_authorized"] = True
    with pytest.raises(PreregistrationValidationError, match="EVALUATION_AUTHORIZED"):
        validate_measurement_contract(bad3)
    bad4 = copy.deepcopy(contract)
    bad4["parameter_governance"]["open_parameters_remaining"] = True
    with pytest.raises(PreregistrationValidationError, match="OPEN_PARAMETERS"):
        validate_measurement_contract(bad4)
    bad5 = copy.deepcopy(contract)
    bad5["exit_semantics"]["frozen"] = False
    with pytest.raises(PreregistrationValidationError, match="EXIT_NOT_FROZEN"):
        validate_measurement_contract(bad5)
    bad6 = copy.deepcopy(contract)
    bad6["development_run_count"] = 0
    with pytest.raises(PreregistrationValidationError, match="DEVELOPMENT_RUN_COUNT"):
        validate_measurement_contract(bad6)


def test_governance_evidence_owner_map() -> None:
    assert GOVERNANCE.is_file()
    assert (
        "DOCS_TOKEN_VOLATILITY_EXPANSION_PERSISTENCE_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1"
        in GOVERNANCE.read_text(encoding="utf-8")
    )
    assert (EVIDENCE / "README.md").is_file()
    assert (EVIDENCE / "summary.json").is_file()
    assert (EVIDENCE / "safety_attestation.md").is_file()
    assert (EVIDENCE / "split_manifest.json").is_file()
    assert (EVIDENCE / "timing_proof.txt").is_file()
    summary = _load(EVIDENCE / "summary.json")
    assert summary["evaluation_executed"] is False
    assert summary["holdout_accessed"] is False
    assert summary["dataset_loaded"] is False
    assert summary["development_run_count"] == 1
    assert summary["runner_start_count"] == 1
    assert summary["open_parameters_remaining"] is False
    assert summary["material_difference_from_vcb_v1_explicit"] is True
    assert summary["definition_semantics_complete"] is True
    assert summary["second_pnl_truth_created"] is False
    assert summary["contract_digest"] == _load(CONTRACT_PATH)["contract_digest"]
    owners = _load(OWNER_MAP)["allowed_optimization_surfaces"]
    assert (
        "VOLATILITY_EXPANSION_PERSISTENCE_V1_HYPOTHESIS_PREREGISTRATION_DEFINITION_ONLY_V1"
        in owners
    )
    split = _load(EVIDENCE / "split_manifest.json")
    assert split["method"] == "CHRONOLOGICAL_60_20_20_FLOOR_HOUR"
    assert (
        split["split_intervals_sha256"]
        == "a35783bf0268c174dfe585c9839ba45cc6e3835021699786f4490a0d8c9b33db"
    )
