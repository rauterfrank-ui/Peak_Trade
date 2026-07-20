"""Contract tests for entry-effective MR eligibility hypothesis preregistration v1.

Definition-only. No backtest. No economic metrics. No holdout content inspection.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.entry_effective_mr_eligibility_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    HOLDOUT_OPAQUE_ID,
    HypothesisPreregistrationError,
    REQUIRED_FROZEN_FILTER_PARAMETERS,
    load_and_validate_repo_contract,
    materialize_chronological_splits,
    reject_holdout_dataset_or_path,
    validate_preregistration_contract,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
EVIDENCE = REPO / "docs/evidence/preregister_entry_effective_mr_eligibility_hypothesis_v1"
GOVERNANCE = (
    REPO
    / "docs/governance/ENTRY_EFFECTIVE_MR_ELIGIBILITY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1.md"
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
    assert report["multiple_testing_budget"] == 1
    assert report["evaluation_run_count_authorized"] == 1
    assert report["treatment_type"] == "ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER"
    assert report["entry_eligibility_divergence_required"] is True
    assert report["filter_id"] == "canonical_vol_regime_filter_atr_percentile_midband_v1"


def test_definition_only_no_result_values_in_contract() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["slice_class"] == "DEFINITION_ONLY"
    assert contract["evaluation_authorized"] is False
    assert contract["backtest_authorized"] is False
    assert contract["eligibility_filter"]["frozen_parameters"] == REQUIRED_FROZEN_FILTER_PARAMETERS
    # No evaluated metric payloads — only future decision predicates may name metrics.
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
    assert "if_absent_result_class" in contract["entry_eligibility_divergence_requirement"]


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
    bad3["development_evaluation_runs_allowed"] = 0
    with pytest.raises(HypothesisPreregistrationError, match="DEVELOPMENT_RUNS_ALLOWED"):
        validate_preregistration_contract(bad3)


def test_holdout_id_and_paths_fail_closed() -> None:
    with pytest.raises(HypothesisPreregistrationError, match="HOLDOUT"):
        reject_holdout_dataset_or_path(HOLDOUT_OPAQUE_ID)
    with pytest.raises(HypothesisPreregistrationError, match="HOLDOUT"):
        reject_holdout_dataset_or_path(
            "docs/evidence/offline_economic_reevaluation_sealed_long_panel_v1/summary.json"
        )
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["allowed_data_sources"] = [HOLDOUT_OPAQUE_ID]
    with pytest.raises(HypothesisPreregistrationError, match="HOLDOUT"):
        validate_preregistration_contract(bad)
    assert contract["sealed_holdout_content_inspection_authorized"] is False
    assert "offline_economic_reevaluation_sealed_long_panel_v1" not in json.dumps(
        contract["allowed_data_sources"]
    )


def test_entry_eligibility_divergence_is_mandatory_measurement_condition() -> None:
    contract = _load(CONTRACT_PATH)
    div = contract["entry_eligibility_divergence_requirement"]
    assert div["required"] is True
    assert div["if_absent_result_class"] == "FAIL"
    assert any(
        "entry_eligibility_divergence_observed" in str(x)
        for x in contract["decision_thresholds"]["pass_requires_all"]
    )
    bad = copy.deepcopy(contract)
    bad["entry_eligibility_divergence_requirement"]["required"] = False
    with pytest.raises(HypothesisPreregistrationError, match="ENTRY_ELIGIBILITY_DIVERGENCE"):
        validate_preregistration_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["decision_thresholds"]["pass_requires_all"] = ["net_return_treatment > net_return_control"]
    with pytest.raises(HypothesisPreregistrationError, match="PASS_MUST_REQUIRE_ENTRY_DIVERGENCE"):
        validate_preregistration_contract(bad2)


def test_prior_failed_regime_features_may_not_be_reused() -> None:
    contract = _load(CONTRACT_PATH)
    feature_ids = {f["feature_id"] for f in contract["eligibility_filter"]["features"]}
    assert "realized_vol_168h" not in feature_ids
    assert "range_compression_72h" not in feature_ids
    assert "trend_strength_168h" not in feature_ids
    bad = copy.deepcopy(contract)
    bad["eligibility_filter"]["features"].append(
        {"feature_id": "realized_vol_168h", "lookback_hours": 168, "causal": True}
    )
    with pytest.raises(HypothesisPreregistrationError, match="PRIOR_FAILED_FEATURE_REUSE"):
        validate_preregistration_contract(bad)


def test_baseline_treatment_authority_and_promotion_forbidden() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["baseline_immutable"] is True
    treatment = contract["treatment"]
    assert treatment["treatment_type"] == "ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER"
    assert treatment["acts_before_entry_decision"] is True
    assert treatment["reporting_or_attribution_only"] is False
    assert treatment["no_new_direction_authority"] is True
    assert treatment["no_new_switch_authority"] is True
    assert treatment["no_new_risk_authority"] is True
    assert treatment["no_new_sizing_authority"] is True
    assert treatment["no_new_execution_authority"] is True
    assert treatment["runtime_implementation_in_this_slice"] is False
    assert contract["promotion_and_holdout_policy"]["promotion_eligible"] is False
    assert (
        contract["promotion_and_holdout_policy"]["economic_validity_offline_gate_changed"] is False
    )
    for key in (
        "runtime_activated",
        "shadow_activated",
        "testnet_activated",
        "live_authorized",
        "orders_allowed",
        "scheduler_authorized",
    ):
        assert contract["runtime_policy"][key] is False
    bad = copy.deepcopy(contract)
    bad["promotion_and_holdout_policy"]["promotion_eligible"] = True
    with pytest.raises(HypothesisPreregistrationError, match="PROMOTION"):
        validate_preregistration_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["runtime_policy"]["orders_allowed"] = True
    with pytest.raises(HypothesisPreregistrationError, match="RUNTIME_FLAG"):
        validate_preregistration_contract(bad2)


def test_chronological_splits_no_overlap_and_purge_embargo() -> None:
    splits = materialize_chronological_splits(
        panel_start="2022-06-01T03:55:17Z",
        panel_end_exclusive="2023-08-16T05:55:00Z",
    )
    assert splits["train_definition"]["end_exclusive"] == splits["validation"]["start"]
    assert (
        splits["validation"]["end_exclusive"] == splits["final_development_confirmation"]["start"]
    )
    assert splits["purge_hours"] == 216
    assert splits["embargo_hours"] == 168
    contract = _load(CONTRACT_PATH)
    assert contract["splits"]["split_intervals_sha256"] == splits["split_intervals_sha256"]


def test_costs_stops_thresholds_and_inconclusive_guard() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["cost_model"]["fee_bps"] == 10.0
    assert contract["cost_model"]["slippage_bps"] == 5.0
    assert contract["cost_model"]["cost_drag_fully_included_in_net_metrics"] is True
    assert contract["stop_and_ledger_semantics"]["stop_pct"] == 0.025
    assert contract["decision_thresholds"]["minimum_trade_count"] == 50
    assert contract["decision_thresholds"]["max_trade_count_reduction_fraction_vs_control"] == 0.5
    assert contract["decision_thresholds"]["inconclusive_never_for_poor_economic_results"] is True
    bad = copy.deepcopy(contract)
    del bad["cost_model"]["fee_bps"]
    with pytest.raises(HypothesisPreregistrationError, match="COST_MODEL_MISSING"):
        validate_preregistration_contract(bad)


def test_evidence_and_governance_definition_only() -> None:
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert "PROMOTION_ELIGIBLE=false" in text
    assert "DEFINITION_ONLY" in text
    assert "ENTRY_ELIGIBILITY_DIVERGENCE_REQUIRED=true" in text
    for name in ("README.md", "summary.json", "safety_attestation.md", "split_manifest.json"):
        assert (EVIDENCE / name).is_file()
    summary = _load(EVIDENCE / "summary.json")
    assert summary["slice_class"] == "DEFINITION_ONLY"
    assert summary["hypothesis_count"] == 1
    assert summary["evaluation_run_count_authorized"] == 1
    assert summary["backtest_executed"] is False
    assert summary["economic_metrics_computed"] is False
    assert summary["development_panel_accessed"] is False
    assert summary["holdout_accessed"] is False
    assert summary["sealed_holdout_content_inspected"] is False
    assert summary["productive_trading_logic_changed"] is False
    assert summary["authority_changed"] is False
    assert summary["promotion_eligible"] is False
    assert summary["entry_eligibility_divergence_required"] is True
    evidence_names = {path.name for path in EVIDENCE.iterdir()}
    for banned in FORBIDDEN_RESULT_ARTIFACTS:
        assert banned not in evidence_names
