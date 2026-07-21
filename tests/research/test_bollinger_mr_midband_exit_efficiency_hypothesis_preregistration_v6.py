"""Contract tests for Bollinger/MR midband exit-efficiency hypothesis preregistration v6.

Terminal closeout: V6 is DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL with run count 1.
V5 remains terminal INFRASTRUCTURE_FAILURE (run count 1; no rerun).
Genuine economic change vs V5: composite midband-cross OR max-holding-horizon=48h.
Exactly one authorized DEVELOPMENT evaluation executed; no rerun.
"""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest

from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v5 import (
    load_and_validate_repo_contract as load_v5,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v6 import (
    CONTRACT_REL_PATH,
    EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST,
    REQUIRED_BINDING_FIX_SURFACE,
    REQUIRED_FALSY_ZERO_HYGIENE_SURFACE,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE,
    REQUIRED_LIFECYCLE_STATES,
    REQUIRED_MECHANISM_ID,
    REQUIRED_OBSERVABILITY_SURFACE,
    REQUIRED_OWNER_SURFACE,
    REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
    REQUIRED_PROGRESS_METADATA_FIELDS,
    HypothesisPreregistrationError,
    load_and_validate_repo_contract,
    reject_holdout_dataset_or_path,
    validate_preregistration_contract,
)
from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.import_safety_v5 import (
    assert_no_runner_entrypoint_on_import,
    import_safety_attestation_v5,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
V5_CONTRACT_PATH = (
    REPO
    / "config/research/bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v5.json"
)
OWNER_MAP_PATH = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
GOVERNANCE = (
    REPO
    / "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V6.md"
)
EVIDENCE = REPO / "docs/evidence/preregister_bollinger_mr_midband_exit_efficiency_hypothesis_v6"
V5_EVAL_EVIDENCE = (
    REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v5"
)
V6_EVAL_EVIDENCE = (
    REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v6"
)
BACKLOG = REPO / "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
PREREG_SRC = (
    REPO / "src/research/bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v6.py"
)


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
    assert report["rerun_allowed"] is False
    assert report["mechanism_id"] == REQUIRED_MECHANISM_ID
    assert report["identical_exit_mechanism_to_development_v5"] is False
    assert report["identical_economic_hypothesis_to_development_v5"] is False
    assert report["economic_change_vs_development_v5"] is True
    assert report["lifecycle_checkpoint_surface"] == REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE
    assert (
        report["development_preregistration_digest"] == EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST
    )
    assert (
        report["development_preregistration_digest"]
        == "9ddcd32d78b3b3f60c168321404b2270a770409d46a3bff036f7dbc5eefd8fa5"
    )
    contract = _load(CONTRACT_PATH)
    assert contract["status"] == "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL"
    assert contract["pass"] is False
    assert contract["fail"] is True
    assert contract["acceptance_criteria_met"] is False
    assert (contract.get("terminal_closeout") or {}).get("decision_reason") == (
        "NET_PROFIT_FACTOR_NOT_IMPROVED"
    )


def test_v5_terminal_immutability() -> None:
    v5 = load_v5(REPO)
    assert v5["hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert v5["result_class"] == "INFRASTRUCTURE_FAILURE"
    assert v5["evaluation_run_count"] == 1
    assert v5["rerun_allowed"] is False
    assert v5["economic_verdict"] == "NOT_EVALUATED"
    contract = _load(V5_CONTRACT_PATH)
    assert contract["status"] == ("DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/INFRASTRUCTURE_FAILURE")
    closeout = contract.get("terminal_closeout") or {}
    assert closeout.get("diagnostic_class") == (
        "PROCESS_DIED_INCOMPLETE_PANEL_RUN_NO_LIFECYCLE_TERMINAL"
    )
    assert closeout.get("baseline_members_completed") == "3/46"


def test_economic_change_vs_v5_encoded() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["identical_exit_mechanism_to_development_v5"] is False
    assert contract["identical_economic_hypothesis_to_development_v5"] is False
    assert contract["economic_change_vs_development_v5"] is True
    assert contract["predecessor_partial_metrics_used"] is False
    mech = contract["exit_mechanism"]
    assert mech["mechanism_id"] == REQUIRED_MECHANISM_ID
    frozen = mech["frozen_parameters"]
    assert frozen["max_holding_horizon_hours"] == 48
    assert frozen["max_holding_bars"] == 48
    assert frozen["composite_trigger_policy"] == "first_of_midband_cross_or_max_holding"
    assert contract["treatment"]["includes_max_holding_horizon_exit"] is True
    assert contract["treatment"]["composite_exit_efficiency"] is True
    assert contract["treatment"]["bollinger_event_only"] is False


def test_no_runner_start_during_import_or_validation() -> None:
    assert_no_runner_entrypoint_on_import()
    attestation = import_safety_attestation_v5()
    assert attestation["runner_started_at_import"] is False
    assert attestation["run_slot_claimed_at_import"] is False
    assert attestation["evaluation_executed_at_import"] is False
    assert attestation["panel_data_accessed_at_import"] is False
    assert attestation["holdout_data_accessed_at_import"] is False
    tree = ast.parse(PREREG_SRC.read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    forbidden_names = {
        "run_development_evaluation",
        "claim_run_slot",
        "load_development_panel",
        "execute_evaluation",
    }
    for call in calls:
        func = call.func
        name = getattr(func, "id", None) or getattr(func, "attr", None)
        assert name not in forbidden_names
    report = load_and_validate_repo_contract(REPO)
    assert report["evaluation_executed"] is True
    assert report["result_class"] == "FAIL"


def test_holdout_access_forbidden() -> None:
    with pytest.raises(HypothesisPreregistrationError):
        reject_holdout_dataset_or_path("offline_economic_reevaluation_sealed_long_panel_v1")


def test_lifecycle_contract_monotonic_states_and_atomic_checkpoint() -> None:
    contract = _load(CONTRACT_PATH)
    life = contract["lifecycle_contract"]
    assert list(life["monotonic_lifecycle_states"]) == list(REQUIRED_LIFECYCLE_STATES)
    assert list(life["required_progress_metadata_fields"]) == list(
        REQUIRED_PROGRESS_METADATA_FIELDS
    )
    assert life["atomic_checkpoint_persistence"]["required"] is True
    assert life["checkpoint_never_authorizes_automatic_rerun"] is True
    assert life["checkpoint_cannot_reclaim_or_create_run_slot"] is True
    assert life["dead_process_before_lifecycle_terminal_is_infrastructure_failure"] is True
    assert life["partial_metrics_must_not_promote_to_baseline_treatment_or_delta"] is True
    assert life["import_or_validate_definition_must_not_start_runner"] is True


def test_partial_metrics_and_dead_process_classification_in_contract() -> None:
    contract = _load(CONTRACT_PATH)
    bind = contract["infrastructure_bindings"][
        "bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5"
    ]
    assert bind["partial_metrics_authoritative"] is False
    assert bind["dead_process_before_lifecycle_terminal_result_class"] == ("INFRASTRUCTURE_FAILURE")
    assert bind["checkpoint_cannot_reclaim_or_create_run_slot"] is True
    assert bind["does_not_authorize_v5_rerun"] is True
    assert bind["v5_terminal_unchanged"] is True
    assert "NO_CHECKPOINT_AUTHORIZED_RERUN" in contract["explicit_non_actions"]
    assert "NO_PARTIAL_METRICS_PROMOTION" in contract["explicit_non_actions"]
    assert "NO_V7_AUTO_CREATE" in contract["explicit_non_actions"]


def test_owner_map_and_backlog_consistency() -> None:
    owner_map = _load(OWNER_MAP_PATH)
    owners = owner_map["allowed_optimization_surfaces"]
    assert REQUIRED_OWNER_SURFACE in owners
    assert REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE in owners
    assert REQUIRED_OBSERVABILITY_SURFACE in owners
    assert "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V6" in owners
    backlog = _load(BACKLOG)
    assert backlog["governance_rules"]["preregistered_count_exact"] == 1
    assert len(backlog["preregistered_hypotheses"]) == 1
    assert (
        backlog["preregistered_hypotheses"][0]["hypothesis_id"]
        == "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7"
    )
    assert backlog["development_run_count"] == 6
    terminal_ids = {e["hypothesis_id"] for e in backlog["terminal_hypotheses"]}
    assert REQUIRED_HYPOTHESIS_ID in terminal_ids
    assert REQUIRED_PREDECESSOR_HYPOTHESIS_ID in terminal_ids
    v6 = next(
        e for e in backlog["terminal_hypotheses"] if e["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    )
    assert v6["result_class"] == "FAIL"
    assert v6["evaluation_run_count"] == 1
    assert v6["decision_reason"] == "NET_PROFIT_FACTOR_NOT_IMPROVED"
    assert v6["lifecycle_checkpoint_surface"] == REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE
    assert "NO_V6_EVALUATION_IN_THIS_SLICE" not in backlog["explicit_non_actions"]
    assert "NO_V6_RERUN" in backlog["explicit_non_actions"]
    assert "NO_V7_AUTO_CREATE" in backlog["explicit_non_actions"]
    assert "NO_V6_AUTO_CREATE" not in backlog["explicit_non_actions"]


def test_governance_and_evidence_present_docs_token_escaped() -> None:
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert "&#47;" in text
    assert EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST in text
    assert (EVIDENCE / "summary.json").is_file()
    assert (EVIDENCE / "safety_attestation.md").is_file()
    assert (EVIDENCE / "README.md").is_file()
    readme = (EVIDENCE / "README.md").read_text(encoding="utf-8")
    assert "&#47;" in readme
    summary = _load(EVIDENCE / "summary.json")
    assert summary["evaluation_run_count"] == 1
    assert summary["run_slot_claimed"] is True
    assert summary["runner_started"] is True
    assert summary["result_class"] == "FAIL"
    assert summary["holdout_accessed"] is False
    assert summary["economic_hypothesis_changed"] is True


def test_v6_evaluation_evidence_terminal_fail() -> None:
    assert V6_EVAL_EVIDENCE.is_dir()
    assert V5_EVAL_EVIDENCE.is_dir()
    summary = _load(V6_EVAL_EVIDENCE / "summary.json")
    assert summary["result_class"] == "FAIL"
    assert summary["evaluation_run_count"] == 1
    assert summary["evaluation_completed"] is True
    assert summary["holdout_data_accessed"] is False
    assert summary["acceptance_criteria_met"] is False
    claim = _load(V6_EVAL_EVIDENCE / "run_slot_claim.json")
    assert claim["slot_consumed"] is True


def test_mutated_run_count_fails_closed() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["evaluation_run_count"] = 0
    with pytest.raises(HypothesisPreregistrationError):
        validate_preregistration_contract(bad)


def test_surfaces_bound() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["observability_surface"] == REQUIRED_OBSERVABILITY_SURFACE
    assert report["falsy_zero_hygiene_bound"] is True
    assert report["binding_fix_bound"] is True
    assert report["binding_fix_surface"] == REQUIRED_BINDING_FIX_SURFACE
    assert REQUIRED_FALSY_ZERO_HYGIENE_SURFACE
