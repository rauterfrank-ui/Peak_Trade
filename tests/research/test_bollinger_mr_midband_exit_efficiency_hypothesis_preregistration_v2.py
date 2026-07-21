"""Contract tests for Bollinger/MR midband exit-efficiency hypothesis preregistration v2.

After terminal closeout: V2 is DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL /
INCONCLUSIVE_INFRASTRUCTURE_FAILURE with run count 1. V1 remains terminal and
must not be rerun or partially reused. Observability surface remains bound.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v1 import (
    load_and_validate_repo_contract as load_v1,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v2 import (
    CONTRACT_REL_PATH,
    EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST,
    REQUIRED_FROZEN_EXIT_PARAMETERS,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_OBSERVABILITY_SURFACE,
    REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
    HypothesisPreregistrationError,
    load_and_validate_repo_contract,
    reject_holdout_dataset_or_path,
    validate_preregistration_contract,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
V1_CONTRACT_PATH = (
    REPO
    / "config/research/bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v1.json"
)
GOVERNANCE = (
    REPO
    / "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V2.md"
)
EVIDENCE = REPO / "docs/evidence/preregister_bollinger_mr_midband_exit_efficiency_hypothesis_v2"
EVAL_EVIDENCE = REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v2"
BACKLOG = REPO / "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_terminal_inconclusive() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is False
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["predecessor_hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert report["evaluation_run_count"] == 1
    assert report["evaluation_started"] is True
    assert report["evaluation_completed"] is False
    assert report["evaluation_executed"] is True
    assert report["result_class"] == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert report["economic_verdict"] == "NOT_EVALUATED"
    assert report["new_evaluation_not_rerun"] is True
    assert report["v1_partial_results_reused"] is False
    assert report["definition_semantics_identical"] is True
    assert report["observability_surface_bound"] is True
    assert report["observability_surface"] == REQUIRED_OBSERVABILITY_SURFACE
    assert report["development_preregistration_digest"] == (
        EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST
    )
    assert report["rerun_allowed"] is False


def test_hypothesis_id_unique_and_not_v1_rerun() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert contract["hypothesis_id"] != REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert contract["new_evaluation_not_rerun"] is True
    assert contract["v1_rerun_forbidden"] is True
    assert contract["evaluation_run_count"] == 1
    assert (
        contract["preregistration_state"]
        == "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    )
    assert contract["status"] == contract["preregistration_state"]


def test_v1_terminal_unchanged_and_not_rerun() -> None:
    v1_report = load_v1(REPO)
    assert v1_report["hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert v1_report["evaluation_run_count"] == 1
    assert v1_report["result_class"] == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert v1_report["rerun_allowed"] is False
    v1 = _load(V1_CONTRACT_PATH)
    assert (
        v1["status"]
        == "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    )
    assert v1["evaluation_run_count"] == 1


def test_no_v1_partial_result_or_checkpoint_reuse() -> None:
    contract = _load(CONTRACT_PATH)
    for banned in (
        "baseline_members_completed",
        "treatment_members_completed",
        "partial_baseline_metrics",
        "partial_treatment_metrics",
        "checkpoint_reuse",
        "v1_checkpoint_ref",
        "v1_partial_result_ref",
    ):
        assert banned not in contract
    assert contract["predecessor_development_v1"]["partial_results_reused"] is False
    assert contract["predecessor_development_v1"]["historical_process_death_cause"] == "UNKNOWN"
    summary = _load(EVIDENCE / "summary.json")
    assert summary["v1_partial_results_reused"] is False
    eval_summary = _load(EVAL_EVIDENCE / "summary.json")
    assert eval_summary["v1_partial_results_reused"] is False
    assert eval_summary["v1_rerun"] is False


def test_definition_semantics_identical_to_v1() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["definition_semantics_identical"] is True
    contract = _load(CONTRACT_PATH)
    assert contract["identical_measurement_rules_to_development_v1"] is True
    assert contract["exit_mechanism"]["frozen_parameters"] == REQUIRED_FROZEN_EXIT_PARAMETERS
    assert float(contract["cost_model"]["cost_multiplier"]) == 1.0


def test_observability_surface_bound() -> None:
    contract = _load(CONTRACT_PATH)
    obs = contract["infrastructure_bindings"]["evaluation_runner_lifecycle_observability_v1"]
    assert obs["surface_id"] == REQUIRED_OBSERVABILITY_SURFACE
    assert obs["auto_resume_forbidden"] is True
    assert obs["auto_rerun_on_infrastructure_failure_forbidden"] is True
    assert obs["required_result_class_on_incomplete_run"] == ("INCONCLUSIVE_INFRASTRUCTURE_FAILURE")
    for key in (
        "phase",
        "last_confirmed_member",
        "heartbeat_progress",
        "exit_code",
        "signal",
        "exception_class_and_truncated_traceback",
        "atomic_lifecycle_checkpoint",
    ):
        assert key in obs["required_durable_diagnostics"]


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
    assert len(backlog["terminal_hypotheses"]) == 3
    ids = {e["hypothesis_id"] for e in backlog["terminal_hypotheses"]}
    assert REQUIRED_HYPOTHESIS_ID in ids
    assert REQUIRED_PREDECESSOR_HYPOTHESIS_ID in ids
    assert "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V3" in ids
    v2 = next(
        e for e in backlog["terminal_hypotheses"] if e["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    )
    assert v2["status"] == "TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert v2["evaluation_run_count"] == 1
    assert v2["evaluation_started"] is True
    assert v2["evaluation_executed"] is True
    assert "NO_V2_RERUN" in backlog["explicit_non_actions"]
    v3 = next(
        e
        for e in backlog["terminal_hypotheses"]
        if e["hypothesis_id"]
        == "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V3"
    )
    assert v3["status"] == "TERMINAL_FAIL"
    assert v3["evaluation_run_count"] == 1
    assert v3["result_class"] == "FAIL"


def test_validation_does_not_authorize_rerun() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["evaluation_executed"] is True
    assert report["evaluation_run_count"] == 1
    assert report["rerun_allowed"] is False
    contract = _load(CONTRACT_PATH)
    assert contract["evaluation_authorized"] is False
    assert contract["backtest_authorized"] is False
    assert contract["rerun_allowed"] is False


def test_mutated_run_count_fails_closed() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["evaluation_run_count"] = 0
    with pytest.raises(HypothesisPreregistrationError, match="EVALUATION_RUN_COUNT_MUST_BE_1"):
        validate_preregistration_contract(bad)


def test_governance_and_evidence_present() -> None:
    assert GOVERNANCE.is_file()
    assert (
        "DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V2"
        in (GOVERNANCE.read_text(encoding="utf-8"))
    )
    assert (EVIDENCE / "README.md").is_file()
    assert (EVIDENCE / "summary.json").is_file()
    assert (EVIDENCE / "safety_attestation.md").is_file()
    assert (EVIDENCE / "split_manifest.json").is_file()
    assert (EVAL_EVIDENCE / "summary.json").is_file()
