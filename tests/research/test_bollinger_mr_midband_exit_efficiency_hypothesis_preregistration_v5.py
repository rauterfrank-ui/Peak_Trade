"""Contract tests for Bollinger/MR midband exit-efficiency hypothesis preregistration v5.

Definition-only: V5 is DEFINITION_ONLY_PREREGISTERED with run count 0.
V4 remains terminal INFRASTRUCTURE_FAILURE (run count 1; no rerun).
V3/V2/V1 remain terminal. No evaluation executed in this slice.
"""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest

from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v4 import (
    load_and_validate_repo_contract as load_v4,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v5 import (
    CONTRACT_REL_PATH,
    EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST,
    REQUIRED_BINDING_FIX_SURFACE,
    REQUIRED_FALSY_ZERO_HYGIENE_SURFACE,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE,
    REQUIRED_LIFECYCLE_STATES,
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
V4_CONTRACT_PATH = (
    REPO
    / "config/research/bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v4.json"
)
OWNER_MAP_PATH = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
GOVERNANCE = (
    REPO
    / "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V5.md"
)
EVIDENCE = REPO / "docs/evidence/preregister_bollinger_mr_midband_exit_efficiency_hypothesis_v5"
V4_EVAL_EVIDENCE = (
    REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v4"
)
V5_EVAL_EVIDENCE = (
    REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v5"
)
BACKLOG = REPO / "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
PREREG_SRC = (
    REPO / "src/research/bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v5.py"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_terminal_infrastructure_failure() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is False
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["predecessor_hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert report["evaluation_run_count"] == 1
    assert report["evaluation_started"] is True
    assert report["evaluation_completed"] is False
    assert report["evaluation_executed"] is True
    assert report["result_class"] == "INFRASTRUCTURE_FAILURE"
    assert report["economic_verdict"] == "NOT_EVALUATED"
    assert report["rerun_allowed"] is False
    assert report["lifecycle_checkpoint_surface"] == REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE
    assert (
        report["development_preregistration_digest"] == EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST
    )
    assert (
        report["development_preregistration_digest"]
        == "b85903ebc76d1fefdb576075e88a1b72d9abb852ad4da5f1f8c5bc9c0bd21b2e"
    )


def test_v4_terminal_immutability() -> None:
    v4 = load_v4(REPO)
    assert v4["hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert v4["result_class"] == "INFRASTRUCTURE_FAILURE"
    assert v4["evaluation_run_count"] == 1
    assert v4["rerun_allowed"] is False
    assert v4["economic_verdict"] == "NOT_EVALUATED"
    contract = _load(V4_CONTRACT_PATH)
    assert contract["status"] == ("DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/INFRASTRUCTURE_FAILURE")
    closeout = contract.get("terminal_closeout") or {}
    assert closeout.get("diagnostic_class") == (
        "PROCESS_DIED_INCOMPLETE_PANEL_RUN_NO_LIFECYCLE_TERMINAL"
    )


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
    # Module must not invoke an evaluation runner at import/collection time.
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
    assert "NO_CHECKPOINT_AUTHORIZED_RERUN" in contract["explicit_non_actions"]
    assert "NO_PARTIAL_METRICS_PROMOTION" in contract["explicit_non_actions"]


def test_owner_map_and_backlog_consistency() -> None:
    owner_map = _load(OWNER_MAP_PATH)
    owners = owner_map["allowed_optimization_surfaces"]
    assert REQUIRED_OWNER_SURFACE in owners
    assert REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE in owners
    assert REQUIRED_OBSERVABILITY_SURFACE in owners
    backlog = _load(BACKLOG)
    assert backlog["governance_rules"]["preregistered_count_exact"] == 1
    assert len(backlog["preregistered_hypotheses"]) == 1
    assert (
        backlog["preregistered_hypotheses"][0]["hypothesis_id"]
        == "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V8"
    )
    assert any(e["hypothesis_id"].endswith("_V6") for e in backlog["terminal_hypotheses"])
    terminal_ids = {e["hypothesis_id"] for e in backlog["terminal_hypotheses"]}
    assert REQUIRED_PREDECESSOR_HYPOTHESIS_ID in terminal_ids
    assert REQUIRED_HYPOTHESIS_ID in terminal_ids
    assert "NO_V5_RERUN" in backlog["explicit_non_actions"]
    assert "NO_V6_RERUN" in backlog["explicit_non_actions"]
    assert "NO_V7_AUTO_CREATE" in backlog["explicit_non_actions"]
    assert "NO_V6_AUTO_CREATE" not in backlog["explicit_non_actions"]
    assert "NO_V5_AUTO_CREATE" not in backlog["explicit_non_actions"]


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
    assert summary["evaluation_run_count"] == 0
    assert summary["run_slot_claimed"] is False
    assert summary["runner_started"] is False
    assert summary["panel_data_accessed"] is False
    assert summary["holdout_accessed"] is False


def test_v5_evaluation_evidence_dir_present() -> None:
    assert V5_EVAL_EVIDENCE.exists()
    assert V4_EVAL_EVIDENCE.is_dir()


def test_mutated_run_count_fails_closed() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["evaluation_run_count"] = 2
    with pytest.raises(HypothesisPreregistrationError):
        validate_preregistration_contract(bad)


def test_surfaces_bound() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["observability_surface"] == REQUIRED_OBSERVABILITY_SURFACE
    assert report["falsy_zero_hygiene_bound"] is True
    assert report["binding_fix_bound"] is True
    assert report["binding_fix_surface"] == REQUIRED_BINDING_FIX_SURFACE
    assert REQUIRED_FALSY_ZERO_HYGIENE_SURFACE
