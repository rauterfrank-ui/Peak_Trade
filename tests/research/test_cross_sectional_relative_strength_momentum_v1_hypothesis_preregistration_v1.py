"""Definition-only contract tests for CS RS momentum preregistration v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.cross_sectional_relative_strength_momentum_v1_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    GOVERNANCE_REL_PATH,
    EVIDENCE_REL_PATH,
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
HOLDOUT_SUMMARY = (
    REPO
    / "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_v1/summary.json"
)
PROGRAM_PATH = REPO / "config/research/material_different_cross_sectional_momentum_program_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_definition_only_digest() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is True
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["directional_form"] == REQUIRED_DIRECTIONAL_FORM
    assert report["evaluation_authorized"] is False
    assert report["holdout_authorized"] is False
    assert report["development_run_count"] == 0
    assert report["runner_start_count"] == 0
    assert report["evaluation_blocked_while_pending"] is False
    assert report["pending_threshold_keys"] == []
    assert report["time_segment_definition_id"] == REQUIRED_TIME_SEGMENT_DEFINITION_ID
    contract = _load(CONTRACT_PATH)
    assert compute_contract_digest(contract) == contract["contract_digest"]


def test_directional_form_d_and_independence() -> None:
    contract = _load(CONTRACT_PATH)
    directional = contract["directional_form"]
    assert directional["selected"] == REQUIRED_DIRECTIONAL_FORM
    assert directional["double_play_remains_sole_authority"] is True
    assert "A_TOP_RANKED_LONG_ONLY" in directional["rejected_forms"]
    assert "B_BOTTOM_RANKED_SHORT_ONLY" in directional["rejected_forms"]
    assert "C_MARKET_NEUTRAL_TOP_VS_BOTTOM" in directional["rejected_forms"]
    assert contract["score_and_selection"]["selection_mode"] == "single_top1_by_score_desc"
    assert contract["score_and_selection"]["not_volatility_normalized_relative_strength_v0"] is True
    assert contract["strategy_implementation_present"] is False
    assert contract["portfolio"]["preserve_canonical_equal_weight"] is True
    assert contract["costs"]["fee_bps_per_side"] == 10.0
    assert contract["costs"]["slippage_bps_per_side"] == 5.0
    program = _load(PROGRAM_PATH)
    for forbidden in (
        "bollinger_bands_mean_reversion",
        "midband_exit_logic",
        "reentry_cooldown",
        "adx_di_direction_confirmation",
        "regime_gated_standaside",
    ):
        assert forbidden in program["causal_independence"]["forbidden_lineage_refs"]


def test_operator_authorized_thresholds_and_time_segments_complete() -> None:
    contract = _load(CONTRACT_PATH)
    admission = contract["economic_admission_contract"]
    assert admission["evaluation_blocked_while_any_threshold_pending"] is False
    assert admission["pending_threshold_keys"] == []
    assert admission["thresholds"]["minimum_rebalance_observations"]["value"] == 30
    assert admission["thresholds"]["minimum_rebalance_observations"]["status"] == "CONFIGURED"
    assert (
        admission["thresholds"]["minimum_rebalance_observations"]["authority"]
        == "EXPLICIT_OPERATOR_AUTHORIZATION"
    )
    assert (
        admission["thresholds"]["minimum_rebalance_observations"]["not_result_calibrated"] is True
    )
    assert admission["thresholds"]["time_segment_robustness_pass_ratio"]["value"] == 0.5
    assert admission["thresholds"]["time_segment_robustness_pass_ratio"]["status"] == "CONFIGURED"
    assert (
        admission["thresholds"]["time_segment_robustness_pass_ratio"]["authority"]
        == "EXPLICIT_OPERATOR_AUTHORIZATION"
    )
    assert (
        admission["thresholds"]["time_segment_robustness_pass_ratio"]["not_result_calibrated"]
        is True
    )
    tsd = contract["time_segment_definition"]
    assert tsd["time_segment_definition_id"] == REQUIRED_TIME_SEGMENT_DEFINITION_ID
    assert tsd["total_time_segments"] == 4
    assert tsd["denominator"] == 4
    assert tsd["expected_minimum_passing_segments"] == 2
    assert tsd["all_segments_must_be_evaluable"] is True
    assert tsd["non_evaluable_segments_are_pass"] is False
    assert tsd["non_evaluable_segments_removed_from_denominator"] is False
    assert tsd["generic_walk_forward_v1_bound"] is False
    assert tsd["illustrative_60_20_20_partition_is_not_authority"] is True
    assert contract["evaluation_authorized"] is False
    assert contract["development_evaluation_authorized"] is True


def test_bounded_development_grid_governance() -> None:
    contract = _load(CONTRACT_PATH)
    grid = contract["parameter_governance"]["development_only_bounded_grid"]
    assert grid["authorized"] is True
    assert grid["lookback_N_candidates"] == [10, 20, 48]
    assert grid["rebalance_interval_bars_candidates"] == [1, 4, 24]
    assert grid["holdout_forbidden_for_grid_selection"] is True
    assert grid["post_result_grid_alteration_forbidden"] is True
    assert contract["holdout_based_parameter_selection_forbidden"] is True
    assert contract["optimization_forbidden"] is True


def test_holdout_rejected_and_prior_lanes_unchanged() -> None:
    with pytest.raises(PreregistrationValidationError, match="HOLDOUT"):
        reject_holdout_dataset_or_path("offline_economic_reevaluation_sealed_long_panel_v1")
    with pytest.raises(PreregistrationValidationError, match="HOLDOUT"):
        reject_holdout_dataset_or_path(
            "docs/evidence/offline_economic_reevaluation_sealed_long_panel_v1/summary.json"
        )
    assert _load(ENTRY_BACKLOG)["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert _load(EXIT_BACKLOG)["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    holdout = _load(HOLDOUT_SUMMARY)
    assert holdout["holdout_run_count"] == 1
    assert holdout["runner_start_count"] == 1
    assert holdout["result_class"] == "FAIL"


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
    bad2b = copy.deepcopy(contract)
    bad2b["evaluation_authorized"] = True
    with pytest.raises(PreregistrationValidationError, match="EVALUATION_AUTHORIZED"):
        validate_measurement_contract(bad2b)
    bad3 = copy.deepcopy(contract)
    bad3["directional_form"]["selected"] = "A_TOP_RANKED_LONG_ONLY"
    with pytest.raises(PreregistrationValidationError, match="DIRECTIONAL_FORM_NOT_D"):
        validate_measurement_contract(bad3)
    bad4 = copy.deepcopy(contract)
    bad4["time_segment_definition"]["generic_walk_forward_v1_bound"] = True
    with pytest.raises(PreregistrationValidationError, match="WALK_FORWARD_BOUND"):
        validate_measurement_contract(bad4)


def test_governance_evidence_owner_map() -> None:
    assert GOVERNANCE.is_file()
    assert (
        "DOCS_TOKEN_CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1"
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
    assert summary["development_run_count"] == 0
    assert summary["runner_start_count"] == 0
    owners = _load(OWNER_MAP)["allowed_optimization_surfaces"]
    assert (
        "CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1_HYPOTHESIS_PREREGISTRATION_DEFINITION_ONLY_V1"
        in owners
    )
    # illustrative 60/20/20 evidence partition remains present and unchanged as non-authority
    split = _load(EVIDENCE / "split_manifest.json")
    assert split["method"] == "CHRONOLOGICAL_60_20_20_FLOOR_HOUR"
    assert (
        split["split_intervals_sha256"]
        == "a35783bf0268c174dfe585c9839ba45cc6e3835021699786f4490a0d8c9b33db"
    )
