"""Definition-only contract tests for volatility compression breakout preregistration v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.volatility_compression_breakout_v1_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    EVIDENCE_REL_PATH,
    GOVERNANCE_REL_PATH,
    REQUIRED_BASELINE_ID,
    REQUIRED_DIRECTIONAL_FORM,
    REQUIRED_HYPOTHESIS_ID,
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
COILED_SPRING_BINDING = REPO / "config/research/vol_breakout_v1_versioned_research_binding_v0.json"


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
    assert report["development_run_count"] == 0
    assert report["runner_start_count"] == 0
    assert report["open_parameters_remaining"] is False
    assert report["material_difference_explicit"] is True
    assert report["exit_semantics_frozen"] is True
    assert report["event_sufficiency_frozen"] is True
    assert report["pending_threshold_keys"] == []
    assert report["time_segment_definition_id"] == REQUIRED_TIME_SEGMENT_DEFINITION_ID
    contract = _load(CONTRACT_PATH)
    assert compute_contract_digest(contract) == contract["contract_digest"]


def test_frozen_mechanism_and_baseline_isolation() -> None:
    contract = _load(CONTRACT_PATH)
    adm = contract["admission_mechanism"]
    assert adm["vol_estimator"]["period"] == 20
    assert adm["vol_estimator"]["normalization"] == "ATR_DIV_CLOSE"
    assert adm["compression_metric"]["rolling_lookback_bars"] == 120
    assert adm["compression_metric"]["compression_threshold_inclusive_max"] == 0.20
    assert adm["min_compression_duration"]["bars"] == 12
    assert adm["expansion_release"]["threshold_inclusive_min"] == 0.75
    assert adm["expansion_release"]["max_bars_after_last_compression_bar"] == 6
    assert adm["directional_entry"]["channel_lookback_completed_bars"] == 20
    assert contract["exit_semantics"]["initial_stop_atr_multiple"] == 1.5
    assert contract["exit_semantics"]["trailing_stop_atr_multiple"] == 2.0
    assert contract["exit_semantics"]["time_exit_max_bars"] == 48
    assert contract["baseline"]["baseline_id"] == REQUIRED_BASELINE_ID
    assert (
        contract["baseline"]["sole_difference_vs_treatment"] == "COMPRESSION_TO_EXPANSION_ADMISSION"
    )
    events = contract["event_sufficiency_gates"]
    assert events["min_evaluable_treatment_breakout_events"] == 50
    assert events["min_executed_treatment_trades"] == 20
    assert events["min_evaluable_treatment_events_per_time_segment"] == 10
    assert contract["costs"]["fee_bps_per_side"] == 10.0
    assert contract["costs"]["slippage_bps_per_side"] == 5.0
    assert contract["strategy_implementation_present"] is False
    assert contract["parameter_governance"]["open_parameters_remaining"] is False


def test_definition_semantics_complete_bindings() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["definition_semantics_complete"] is True
    assert report["percentile_tie_method"] == "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
    assert report["percentile_current_value_included"] is True
    assert report["compression_cycle_consumption"] == "SINGLE_USE"
    assert report["release_window_offsets"] == [1, 2, 3, 4, 5, 6]
    assert report["max_expansion_triggers_per_release_cycle"] == 1

    contract = _load(CONTRACT_PATH)
    metric = contract["admission_mechanism"]["compression_metric"]
    assert metric["percentile_tie_method"] == "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
    assert (
        metric["percentile_rank_formula"]
        == "count(window_values <= current_value) / count(window_values)"
    )
    assert metric["percentile_rank_window_includes_current_value"] is True
    assert metric["percentile_rank_min_valid_observations"] == 120
    assert metric["percentile_rank_requires_exact_lookback_observations"] is True
    assert metric["midrank_forbidden"] is True
    assert metric["average_rank_forbidden"] is True
    assert metric["strict_less_than_tie_method_forbidden"] is True
    assert metric["vol_breakout_rolling_last_pct_rank_not_authority"] is True
    assert metric["lookahead_forbidden"] is True
    assert metric["current_value_shift_to_exclusively_historical_window_forbidden"] is True

    release = contract["admission_mechanism"]["expansion_release"]
    assert release["release_window_start_offset_after_last_compression_bar"] == 1
    assert release["release_window_end_offset_after_last_compression_bar"] == 6
    assert release["release_window_offsets_inclusive"] is True
    assert release["last_compression_bar_is_not_a_release_bar"] is True
    assert release["multiple_expansion_triggers_per_release_window_allowed"] is False
    assert release["max_expansion_triggers_per_release_cycle"] == 1

    cycle = contract["admission_mechanism"]["compression_cycle_lifecycle"]
    assert cycle["compression_cycle_consumption"] == "SINGLE_USE"
    assert cycle["compression_state_reset_on_successful_entry"] is True
    assert cycle["compression_state_reset_on_channel_miss_at_expansion_trigger"] is True
    assert cycle["compression_state_reset_on_release_window_expiry"] is True
    assert cycle["first_qualifying_expansion_trigger_consumes_cycle"] is True
    assert cycle["channel_miss_at_first_expansion_trigger_discards_cycle_immediately"] is True
    assert cycle["no_expansion_trigger_within_offsets_1_to_6_expires_cycle_after_offset_6"] is True
    assert cycle["overlapping_or_parallel_cycles_forbidden"] is True
    assert cycle["release_cycle_offsets"] == [1, 2, 3, 4, 5, 6]
    assert (
        cycle["further_expansion_triggers_in_same_cycle_forbidden_even_after_channel_miss"] is True
    )

    frozen = contract["parameter_governance"]["frozen_parameters"]
    assert frozen["percentile_tie_method"] == "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
    assert frozen["percentile_rank_window_includes_current_value"] is True
    assert frozen["compression_cycle_consumption"] == "SINGLE_USE"
    assert frozen["release_window_start_offset_after_last_compression_bar"] == 1
    assert frozen["release_window_end_offset_after_last_compression_bar"] == 6
    assert frozen["max_expansion_triggers_per_release_cycle"] == 1
    assert contract["parameter_governance"]["definition_semantics_complete"] is True
    assert contract["evaluation_authorized"] is False
    assert contract["development_evaluation_authorized"] is False
    assert contract["strategy_implementation_present"] is False
    assert contract["implementation_authorized"] is False
    assert contract["development_run_count"] == 0
    assert contract["runner_start_count"] == 0


def test_fail_closed_on_semantics_mutation() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["admission_mechanism"]["compression_metric"]["percentile_tie_method"] = "AVERAGE_RANK"
    with pytest.raises(PreregistrationValidationError, match="PERCENTILE_TIE_METHOD"):
        validate_measurement_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["admission_mechanism"]["compression_metric"][
        "percentile_rank_window_includes_current_value"
    ] = False
    with pytest.raises(PreregistrationValidationError, match="PERCENTILE_CURRENT_NOT_INCLUDED"):
        validate_measurement_contract(bad2)
    bad3 = copy.deepcopy(contract)
    bad3["admission_mechanism"]["expansion_release"][
        "release_window_start_offset_after_last_compression_bar"
    ] = 0
    with pytest.raises(PreregistrationValidationError, match="RELEASE_START_OFFSET"):
        validate_measurement_contract(bad3)
    bad4 = copy.deepcopy(contract)
    bad4["admission_mechanism"]["compression_cycle_lifecycle"][
        "compression_state_reset_on_channel_miss_at_expansion_trigger"
    ] = False
    with pytest.raises(PreregistrationValidationError, match="RESET_ON_CHANNEL_MISS_FALSE"):
        validate_measurement_contract(bad4)
    bad5 = copy.deepcopy(contract)
    bad5["admission_mechanism"]["expansion_release"][
        "multiple_expansion_triggers_per_release_window_allowed"
    ] = True
    with pytest.raises(PreregistrationValidationError, match="MULTI_TRIGGER_ALLOWED"):
        validate_measurement_contract(bad5)
    bad6 = copy.deepcopy(contract)
    bad6["parameter_governance"]["definition_semantics_complete"] = False
    with pytest.raises(PreregistrationValidationError, match="SEMANTICS_INCOMPLETE"):
        validate_measurement_contract(bad6)


def test_material_difference_vs_terminal_coiled_spring() -> None:
    contract = _load(CONTRACT_PATH)
    md = contract["material_difference_vs_terminal_coiled_spring"]
    assert md["prior_terminal_hypothesis_id"] == "VOL_BREAKOUT_COILED_SPRING_NON_BITCOIN_FUTURES_V1"
    assert md["unchanged_binding_retry_forbidden"] is True
    prior = _load(COILED_SPRING_BINDING)
    assert prior["hypothesis_id"] == "VOL_BREAKOUT_COILED_SPRING_NON_BITCOIN_FUTURES_V1"
    params = prior["binding"]["parameter_binding"]["parameters"]
    assert params["vol_window"] == 14
    assert params["vol_percentile"] == 50.0
    assert params["lookback_breakout"] == 20
    # New contract must not reuse the terminal ATR14 / vol_percentile=50 binding.
    assert contract["admission_mechanism"]["vol_estimator"]["period"] == 20
    assert (
        contract["admission_mechanism"]["compression_metric"]["compression_threshold_inclusive_max"]
        == 0.20
    )
    program = _load(PROGRAM_PATH)
    assert (
        "VOL_BREAKOUT_COILED_SPRING_NON_BITCOIN_FUTURES_V1"
        in program["causal_independence"]["forbidden_lineage_refs"]
    )


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


def test_governance_evidence_owner_map() -> None:
    assert GOVERNANCE.is_file()
    assert (
        "DOCS_TOKEN_VOLATILITY_COMPRESSION_BREAKOUT_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1"
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
    assert summary["development_run_count"] == 0
    assert summary["runner_start_count"] == 0
    assert summary["open_parameters_remaining"] is False
    assert summary["material_difference_from_terminal_coiled_spring_explicit"] is True
    assert summary["definition_semantics_complete"] is True
    assert summary["contract_digest"] == _load(CONTRACT_PATH)["contract_digest"]
    owners = _load(OWNER_MAP)["allowed_optimization_surfaces"]
    assert (
        "VOLATILITY_COMPRESSION_BREAKOUT_V1_HYPOTHESIS_PREREGISTRATION_DEFINITION_ONLY_V1" in owners
    )
    split = _load(EVIDENCE / "split_manifest.json")
    assert split["method"] == "CHRONOLOGICAL_60_20_20_FLOOR_HOUR"
    assert (
        split["split_intervals_sha256"]
        == "a35783bf0268c174dfe585c9839ba45cc6e3835021699786f4490a0d8c9b33db"
    )
