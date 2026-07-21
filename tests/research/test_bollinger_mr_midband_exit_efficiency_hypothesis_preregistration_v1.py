"""Contract tests for Bollinger/MR midband exit-efficiency hypothesis preregistration v1.

Definition-only. No backtest. No economic metrics. No holdout content inspection.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    HOLDOUT_OPAQUE_ID,
    REQUIRED_FROZEN_EXIT_PARAMETERS,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_PRIMARY_METRICS,
    REQUIRED_RESEARCH_QUESTION,
    HypothesisPreregistrationError,
    load_and_validate_repo_contract,
    materialize_chronological_splits,
    reject_holdout_dataset_or_path,
    validate_preregistration_contract,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
EVIDENCE = REPO / "docs/evidence/preregister_bollinger_mr_midband_exit_efficiency_hypothesis_v1"
GOVERNANCE = (
    REPO
    / "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1.md"
)
FORBIDDEN_RESULT_ARTIFACTS = (
    "baseline_metrics.json",
    "treatment_metrics.json",
    "probe_summary.json",
    "comparison_decision.json",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_validates_against_seal_registry() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is True
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["multiple_testing_budget"] == 1
    assert report["evaluation_run_count"] == 0
    assert report["evaluation_run_count_authorized"] == 1
    assert report["treatment_type"] == "POST_ENTRY_EXIT_EFFICIENCY_MECHANISM"
    assert report["mechanism_id"] == "canonical_bollinger_side_aware_middle_band_exit_v1"
    assert report["development_only"] is True
    assert report["holdout_allowed"] is False
    assert report["pass_criteria_frozen"] is True
    assert report["cost_model_canonical"] is True


def test_definition_only_no_result_values_in_contract() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["slice_class"] == "DEFINITION_ONLY"
    assert contract["preregistration_state"] == "DEFINITION_ONLY_PREREGISTERED"
    assert contract["evaluation_authorized"] is False
    assert contract["backtest_authorized"] is False
    assert contract["evaluation_executed"] is False
    assert contract["evaluation_run_count"] == 0
    assert contract["exit_mechanism"]["frozen_parameters"] == REQUIRED_FROZEN_EXIT_PARAMETERS
    for banned_key in (
        "baseline_metrics",
        "treatment_metrics",
        "measured_net_return",
        "measured_profit_factor",
        "economic_metrics",
        "RESULT_CLASS",
        "result_class",
    ):
        assert banned_key not in contract


def test_exactly_one_hypothesis_and_one_development_run() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["hypothesis_count"] == 1
    assert contract["multiple_testing_budget"] == 1
    assert contract["evaluation_run_count_authorized"] == 1
    assert contract["development_evaluation_runs_allowed"] == 1
    bad = copy.deepcopy(contract)
    bad["hypothesis_count"] = 2
    with pytest.raises(HypothesisPreregistrationError, match="HYPOTHESIS_COUNT"):
        validate_preregistration_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["evaluation_run_count_authorized"] = 2
    with pytest.raises(HypothesisPreregistrationError, match="EVALUATION_RUN_COUNT"):
        validate_preregistration_contract(bad2)
    bad3 = copy.deepcopy(contract)
    bad3["evaluation_run_count"] = 1
    with pytest.raises(HypothesisPreregistrationError, match="EVALUATION_RUN_COUNT_MUST_BE_0"):
        validate_preregistration_contract(bad3)


def test_dataset_and_digest_binding() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["dataset_id"] == (
        "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
    )
    assert contract["dataset_class"] == "DEVELOPMENT_ONLY"
    assert contract["splits"]["split_intervals_sha256"] == (
        "a35783bf0268c174dfe585c9839ba45cc6e3835021699786f4490a0d8c9b33db"
    )
    digests = contract["baseline_binding_digests"]
    assert digests["binding_semantic_digest"].startswith("8a8fdbf2")
    assert contract["panel_seal"]["expected_manifest_sha256"].startswith("be953c55")
    bad = copy.deepcopy(contract)
    bad["baseline_binding_digests"]["config_digest"] = "deadbeef"
    with pytest.raises(HypothesisPreregistrationError, match="BASELINE_DIGEST_MISMATCH"):
        validate_preregistration_contract(bad)


def test_holdout_id_and_paths_fail_closed() -> None:
    with pytest.raises(HypothesisPreregistrationError, match="HOLDOUT"):
        reject_holdout_dataset_or_path(HOLDOUT_OPAQUE_ID)
    with pytest.raises(HypothesisPreregistrationError, match="HOLDOUT"):
        reject_holdout_dataset_or_path(
            "docs/evidence/offline_economic_reevaluation_sealed_long_panel_v1/summary.json"
        )
    contract = _load(CONTRACT_PATH)
    assert contract["holdout_allowed"] is False
    assert contract["holdout_forbidden"] is True
    assert contract["promotion_and_holdout_policy"]["holdout_preregistered"] is False
    bad = copy.deepcopy(contract)
    bad["allowed_data_sources"] = [HOLDOUT_OPAQUE_ID]
    with pytest.raises(HypothesisPreregistrationError, match="HOLDOUT"):
        validate_preregistration_contract(bad)


def test_research_question_and_exit_only_scope() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["research_question"] == REQUIRED_RESEARCH_QUESTION
    assert contract["research_question_scope_selected"] == "EXIT_EFFICIENCY_ONLY"
    assert "COST_STRUCTURE_REDUCTION" in contract["research_question_scope_excluded"]
    assert "SHORT_SIDE_FILTER" in contract["research_question_scope_excluded"]
    assert contract["short_side_hypothesis_preregistered"] is False
    assert contract["competing_open_hypothesis_count_allowed"] == 0


def test_exit_divergence_and_full_pass_fail_criteria() -> None:
    contract = _load(CONTRACT_PATH)
    div = contract["exit_divergence_requirement"]
    assert div["required"] is True
    assert div["if_absent_result_class"] == "FAIL"
    assert contract["metrics"]["primary"] == list(REQUIRED_PRIMARY_METRICS)
    pass_all = contract["decision_thresholds"]["pass_requires_all"]
    assert any("net_profit_factor_treatment >" in x for x in pass_all)
    assert any("net_pnl_treatment >" in x for x in pass_all)
    assert any("mean_realized_pnl_over_mfe_capture_ratio_treatment >" in x for x in pass_all)
    assert any("mean_mfe_to_exit_leakage_treatment <" in x for x in pass_all)
    assert any("improvement_not_solely_explained_by_reduced_trade_count" in x for x in pass_all)
    assert any("no_new_instrument_concentration" in x for x in pass_all)
    assert any("cost_multiplier_treatment == 1.0" in x for x in pass_all)
    assert contract["decision_thresholds"]["pass_criteria_frozen"] is True
    bad = copy.deepcopy(contract)
    bad["exit_divergence_requirement"]["required"] = False
    with pytest.raises(HypothesisPreregistrationError, match="EXIT_DIVERGENCE"):
        validate_preregistration_contract(bad)


def test_no_entry_side_instrument_or_cost_weakening() -> None:
    contract = _load(CONTRACT_PATH)
    treatment = contract["treatment"]
    assert treatment["acts_before_entry_decision"] is False
    assert treatment["no_new_entry_authority"] is True
    assert treatment["no_new_side_selection_authority"] is True
    assert contract["exit_mechanism"]["entry_effect"] == "NONE"
    assert contract["exit_mechanism"]["direction_or_side_effect"] == "NONE"
    assert contract["exit_mechanism"]["instrument_selection_effect"] == "NONE"
    assert contract["exit_mechanism"]["cost_model_effect"] == "NONE"
    assert contract["cost_model"]["cost_multiplier"] == 1.0
    assert contract["cost_model"]["cost_assumption_below_canonical_1x_forbidden"] is True
    assert contract["shared_trading_semantics"]["production_strategy_semantics_unchanged"] is True
    assert contract["shared_trading_semantics"]["double_play_authority_unchanged"] is True
    assert contract["shared_trading_semantics"]["risk_sizing_execution_semantics_unchanged"] is True


def test_chronological_splits_deterministic() -> None:
    splits = materialize_chronological_splits(
        panel_start="2022-06-01T03:55:17Z",
        panel_end_exclusive="2023-08-16T05:55:00Z",
        max_feature_lookback_hours=20,
        max_holding_horizon_hours=48,
    )
    assert splits["split_intervals_sha256"] == (
        "a35783bf0268c174dfe585c9839ba45cc6e3835021699786f4490a0d8c9b33db"
    )
    contract = _load(CONTRACT_PATH)
    assert (
        contract["splits"]["final_development_confirmation"]
        == splits["final_development_confirmation"]
    )


def test_evidence_and_governance_definition_only() -> None:
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert "DEFINITION_ONLY_PREREGISTERED" in text
    assert (
        "DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1"
        in text
    )
    assert EVIDENCE.is_dir()
    summary = _load(EVIDENCE / "summary.json")
    assert summary["evaluation_executed"] is False
    assert summary["evaluation_run_count"] == 0
    assert summary["holdout_accessed"] is False
    for name in FORBIDDEN_RESULT_ARTIFACTS:
        assert not (EVIDENCE / name).exists()


def test_competing_open_hypothesis_rejected() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["competing_open_hypothesis_count_allowed"] = 1
    with pytest.raises(HypothesisPreregistrationError, match="COMPETING_OPEN_COUNT"):
        validate_preregistration_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["short_side_hypothesis_preregistered"] = True
    with pytest.raises(HypothesisPreregistrationError, match="SHORT_SIDE"):
        validate_preregistration_contract(bad2)
