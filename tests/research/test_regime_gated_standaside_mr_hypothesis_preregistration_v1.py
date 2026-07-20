"""Contract tests for regime-gated standaside MR hypothesis preregistration v1.

Definition-only. No backtest. No economic metrics. No holdout content inspection.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.regime_gated_standaside_mr_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    HOLDOUT_OPAQUE_ID,
    HypothesisPreregistrationError,
    load_and_validate_repo_contract,
    materialize_chronological_splits,
    reject_holdout_dataset_or_path,
    validate_preregistration_contract,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
EVIDENCE = REPO / "docs/evidence/preregister_regime_gated_standaside_mr_hypothesis_v1"
GOVERNANCE = (
    REPO / "docs/governance/REGIME_GATED_STANDASIDE_MR_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1.md"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_validates_against_seal_registry() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["multiple_testing_budget"] == 1
    assert report["treatment_type"] == "ENTRY_ELIGIBILITY_STANDASIDE_GATE"


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


def test_development_only_and_budget_exactly_one() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["dataset_class"] == "DEVELOPMENT_ONLY"
    assert contract["hypothesis_count"] == 1
    assert contract["multiple_testing_budget"] == 1
    bad = copy.deepcopy(contract)
    bad["dataset_class"] = "HOLDOUT"
    with pytest.raises(HypothesisPreregistrationError, match="DEVELOPMENT_ONLY"):
        validate_preregistration_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["multiple_testing_budget"] = 2
    with pytest.raises(HypothesisPreregistrationError, match="MULTIPLE_TESTING_BUDGET"):
        validate_preregistration_contract(bad2)


def test_baseline_and_treatment_fully_specified() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["baseline_config_id"]
    assert contract["baseline_immutable"] is True
    treatment = contract["treatment"]
    assert treatment["treatment_type"] == "ENTRY_ELIGIBILITY_STANDASIDE_GATE"
    assert treatment["treatment_count"] == 1
    assert treatment["no_new_direction_authority"] is True
    assert treatment["no_new_switch_authority"] is True
    assert treatment["no_new_risk_authority"] is True
    assert treatment["no_new_sizing_authority"] is True
    assert treatment["no_new_execution_authority"] is True
    assert treatment["runtime_implementation_in_this_slice"] is False


def test_chronological_splits_no_overlap_and_purge_embargo() -> None:
    splits = materialize_chronological_splits(
        panel_start="2022-06-01T03:55:17Z",
        panel_end_exclusive="2023-08-16T05:55:00Z",
    )
    assert splits["train_definition"]["end_exclusive"] == splits["validation"]["start"]
    assert (
        splits["validation"]["end_exclusive"] == splits["final_development_confirmation"]["start"]
    )
    assert splits["train_definition"]["start"] < splits["train_definition"]["end_exclusive"]
    assert splits["validation"]["start"] < splits["validation"]["end_exclusive"]
    assert (
        splits["final_development_confirmation"]["start"]
        < splits["final_development_confirmation"]["end_exclusive"]
    )
    assert splits["purge_hours"] == 216
    assert splits["embargo_hours"] == 168
    assert splits["validation_label_eligible_from"] > splits["validation"]["start"]
    assert splits["final_label_eligible_from"] > splits["final_development_confirmation"]["start"]
    contract = _load(CONTRACT_PATH)
    assert contract["splits"]["split_intervals_sha256"] == splits["split_intervals_sha256"]


def test_features_past_only_costs_and_thresholds_required() -> None:
    contract = _load(CONTRACT_PATH)
    for feat in contract["regime_features"]["features"]:
        assert feat["causal"] is True
        assert int(feat["lookback_hours"]) > 0
    assert contract["regime_features"]["lookahead_forbidden"] is True
    bad = copy.deepcopy(contract)
    del bad["cost_model"]["fee_bps"]
    with pytest.raises(HypothesisPreregistrationError, match="COST_MODEL_MISSING"):
        validate_preregistration_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["decision_thresholds"]["pass_requires_all"] = []
    with pytest.raises(HypothesisPreregistrationError, match="THRESHOLD_MISSING"):
        validate_preregistration_contract(bad2)


def test_runtime_and_promotion_forbidden() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["promotion_and_holdout_policy"]["promotion_eligible"] is False
    assert contract["promotion_and_holdout_policy"]["economic_validity_offline_gate_pass"] is False
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
    bad["runtime_policy"]["runtime_activated"] = True
    with pytest.raises(HypothesisPreregistrationError, match="RUNTIME_FLAG"):
        validate_preregistration_contract(bad)


def test_evidence_and_governance_exist() -> None:
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert "PROMOTION_ELIGIBLE=false" in text
    assert "DEFINITION_ONLY" in text
    for name in ("README.md", "summary.json", "safety_attestation.md", "split_manifest.json"):
        assert (EVIDENCE / name).is_file()
    summary = _load(EVIDENCE / "summary.json")
    assert summary["backtest_executed"] is False
    assert summary["economic_metrics_computed"] is False
    assert summary["sealed_holdout_content_inspected"] is False
    evidence_names = {path.name for path in EVIDENCE.iterdir()}
    assert "baseline_metrics.json" not in evidence_names
    assert "probe_summary.json" not in evidence_names
