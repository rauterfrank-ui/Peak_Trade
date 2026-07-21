"""Contract tests for Bollinger/MR midband exit-efficiency hypothesis preregistration v3.

Terminal closeout: V3 is DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL with run count 1.
V2 remains terminal INCONCLUSIVE_INFRASTRUCTURE_FAILURE (run count 1; no rerun).
V1 remains terminal. No second evaluation / no rerun under this preregistration.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v2 import (
    load_and_validate_repo_contract as load_v2,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v3 import (
    CONTRACT_REL_PATH,
    EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST,
    REQUIRED_FALSY_ZERO_HYGIENE_SURFACE,
    REQUIRED_FROZEN_EXIT_PARAMETERS,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_OBSERVABILITY_SURFACE,
    REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
    REQUIRED_V1_HYPOTHESIS_ID,
    V2_TERMINAL_ROOT_CAUSE,
    HypothesisPreregistrationError,
    load_and_validate_repo_contract,
    reject_holdout_dataset_or_path,
    validate_preregistration_contract,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
V2_CONTRACT_PATH = (
    REPO
    / "config/research/bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v2.json"
)
GOVERNANCE = (
    REPO
    / "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V3.md"
)
EVIDENCE = REPO / "docs/evidence/preregister_bollinger_mr_midband_exit_efficiency_hypothesis_v3"
V2_EVAL_EVIDENCE = (
    REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v2"
)
V3_EVAL_EVIDENCE = (
    REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v3"
)
BACKLOG = REPO / "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_terminal_fail() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is False
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["predecessor_hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert report["evaluation_run_count"] == 1
    assert report["evaluation_started"] is True
    assert report["evaluation_completed"] is True
    assert report["evaluation_executed"] is True
    assert report["result_class"] == "FAIL"
    assert report["economic_verdict"] == "FAIL"
    assert report["new_evaluation_not_rerun"] is True
    assert report["v2_partial_results_reused"] is False
    assert report["definition_semantics_identical"] is True
    assert report["observability_surface_bound"] is True
    assert report["observability_surface"] == REQUIRED_OBSERVABILITY_SURFACE
    assert report["falsy_zero_hygiene_bound"] is True
    assert report["development_preregistration_digest"] == (
        EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST
    )
    assert report["rerun_allowed"] is False


def test_hypothesis_id_unique_and_not_v2_rerun() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert contract["hypothesis_id"] != REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert contract["hypothesis_id"] != REQUIRED_V1_HYPOTHESIS_ID
    assert contract["new_evaluation_not_rerun"] is True
    assert contract["v1_rerun_forbidden"] is True
    assert contract["v2_rerun_forbidden"] is True
    assert contract["evaluation_run_count"] == 1
    assert contract["preregistration_state"] == ("DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL")
    assert contract["status"] == "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL"
    assert contract["pass"] is False
    assert contract["fail"] is True


def test_v2_terminal_unchanged_and_not_rerun() -> None:
    v2_report = load_v2(REPO)
    assert v2_report["hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert v2_report["evaluation_run_count"] == 1
    assert v2_report["result_class"] == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert v2_report["rerun_allowed"] is False
    v2 = _load(V2_CONTRACT_PATH)
    assert (
        v2["status"]
        == "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    )
    assert v2["evaluation_run_count"] == 1


def test_no_v2_partial_result_or_economic_import() -> None:
    contract = _load(CONTRACT_PATH)
    for banned in (
        "baseline_members_completed",
        "treatment_members_completed",
        "partial_baseline_metrics",
        "partial_treatment_metrics",
        "checkpoint_reuse",
        "v1_checkpoint_ref",
        "v1_partial_result_ref",
        "v2_checkpoint_ref",
        "v2_partial_result_ref",
    ):
        assert banned not in contract
    pred = contract["predecessor_development_v2"]
    assert pred["partial_results_reused"] is False
    assert pred["process_death_root_cause"] == V2_TERMINAL_ROOT_CAUSE
    assert pred["panel_backtest_executed"] is False
    assert pred["economic_metrics_produced"] is False
    summary = _load(EVIDENCE / "summary.json")
    assert summary["v2_partial_results_reused"] is False
    assert summary["v2_economic_result_imported"] is False
    eval_summary = _load(V2_EVAL_EVIDENCE / "summary.json")
    assert eval_summary["evaluation_run_count"] == 1
    assert eval_summary["result_class"] == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    v3_eval = _load(V3_EVAL_EVIDENCE / "summary.json")
    assert v3_eval["evaluation_run_count"] == 1
    assert v3_eval["result_class"] == "FAIL"
    assert v3_eval["v2_partial_results_reused"] is False


def test_definition_semantics_identical_to_v2() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["definition_semantics_identical"] is True
    contract = _load(CONTRACT_PATH)
    assert contract["identical_measurement_rules_to_development_v2"] is True
    assert contract["identical_measurement_rules_to_development_v1"] is True
    assert contract["exit_mechanism"]["frozen_parameters"] == REQUIRED_FROZEN_EXIT_PARAMETERS
    assert float(contract["cost_model"]["cost_multiplier"]) == 1.0


def test_lifecycle_and_falsy_zero_bindings() -> None:
    contract = _load(CONTRACT_PATH)
    life = contract["lifecycle_contract"]
    assert life["one_run_only"] is True
    assert life["runner_start_persistence_required"] is True
    assert life["terminal_state_persistence_required"] is True
    assert life["no_rerun_after_runner_start"] is True
    assert life["infrastructure_failure_distinct_from_economic_failure"] is True
    obs = contract["infrastructure_bindings"]["evaluation_runner_lifecycle_observability_v1"]
    assert obs["surface_id"] == REQUIRED_OBSERVABILITY_SURFACE
    hygiene = contract["infrastructure_bindings"]["panel_runner_falsy_zero_premeasurement_hygiene"]
    assert hygiene["surface_id"] == REQUIRED_FALSY_ZERO_HYGIENE_SURFACE
    assert hygiene["root_cause_addressed"] == V2_TERMINAL_ROOT_CAUSE
    assert hygiene["does_not_authorize_v2_rerun"] is True
    assert hygiene["v2_terminal_unchanged"] is True


def test_holdout_untouched() -> None:
    with pytest.raises(HypothesisPreregistrationError):
        reject_holdout_dataset_or_path("offline_economic_reevaluation_sealed_long_panel_v1")
    contract = _load(CONTRACT_PATH)
    assert contract["holdout_allowed"] is False
    assert contract["holdout_forbidden"] is True
    assert contract["holdout_data_accessed"] is False
    assert contract["sealed_holdout_content_inspection_authorized"] is False


def test_registry_backlog_consistency() -> None:
    backlog = _load(BACKLOG)
    assert backlog["governance_rules"]["preregistered_count_exact"] == 0
    assert backlog["preregistered_hypotheses"] == []
    assert any(e["hypothesis_id"].endswith("_V6") for e in backlog["terminal_hypotheses"])
    assert len(backlog["terminal_hypotheses"]) == 6
    ids = {e["hypothesis_id"] for e in backlog["terminal_hypotheses"]}
    assert REQUIRED_HYPOTHESIS_ID in ids
    assert REQUIRED_PREDECESSOR_HYPOTHESIS_ID in ids
    assert REQUIRED_V1_HYPOTHESIS_ID in ids
    assert "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V4" in ids
    assert "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V5" in ids
    v3 = next(
        e for e in backlog["terminal_hypotheses"] if e["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    )
    assert v3["status"] == "TERMINAL_FAIL"
    assert v3["evaluation_run_count"] == 1
    assert v3["result_class"] == "FAIL"
    assert "NO_V2_RERUN" in backlog["explicit_non_actions"]
    assert "NO_V3_RERUN" in backlog["explicit_non_actions"]
    assert "NO_HOLDOUT_AFTER_FAIL" in backlog["explicit_non_actions"]
    assert "NO_V4_RERUN" in backlog["explicit_non_actions"]
    assert "NO_V6_RERUN" in backlog["explicit_non_actions"]
    assert "NO_V7_AUTO_CREATE" in backlog["explicit_non_actions"]


def test_validation_does_not_authorize_rerun() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["evaluation_executed"] is True
    assert report["evaluation_run_count"] == 1
    assert report["rerun_allowed"] is False
    contract = _load(CONTRACT_PATH)
    assert contract["evaluation_authorized"] is False
    assert contract["backtest_authorized"] is False
    assert contract["rerun_allowed"] is False


def test_mutated_run_count_zero_fails_closed() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["evaluation_run_count"] = 0
    with pytest.raises(HypothesisPreregistrationError, match="EVALUATION_RUN_COUNT_MUST_BE_1"):
        validate_preregistration_contract(bad)


def test_governance_and_evidence_present() -> None:
    assert GOVERNANCE.is_file()
    assert (
        "DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V3"
        in (GOVERNANCE.read_text(encoding="utf-8"))
    )
    assert (EVIDENCE / "README.md").is_file()
    assert (EVIDENCE / "summary.json").is_file()
    assert (EVIDENCE / "safety_attestation.md").is_file()
    assert (EVIDENCE / "split_manifest.json").is_file()
    assert (V3_EVAL_EVIDENCE / "summary.json").is_file()
