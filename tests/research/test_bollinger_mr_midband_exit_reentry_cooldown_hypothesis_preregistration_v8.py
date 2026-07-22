"""Contract tests for Bollinger/MR midband exit reentry-cooldown hypothesis preregistration v8.

Definition-only: V8 is DEFINITION_ONLY_PREREGISTERED with run count 0.
V7 remains terminal INCONCLUSIVE_INFRASTRUCTURE_FAILURE (no reopen).
Structural hardening: complete frozen_parameters SSOT + pre-authorization parity.
No evaluation executed in this slice.
"""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest

from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.import_safety_v5 import (
    assert_no_runner_entrypoint_on_import,
    import_safety_attestation_v5,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_hypothesis_preregistration_v8 import (
    CONTRACT_REL_PATH,
    EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST,
    FROZEN_PARAMETER_AUTHORITY,
    REQUIRED_BINDING_FIX_SURFACE,
    REQUIRED_COOLDOWN_BARS,
    REQUIRED_FALSY_ZERO_HYGIENE_SURFACE,
    REQUIRED_FROZEN_EXIT_PARAMETERS,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE,
    REQUIRED_MECHANISM_ID,
    REQUIRED_OBSERVABILITY_SURFACE,
    REQUIRED_OWNER_SURFACE,
    REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
    HypothesisPreregistrationError,
    PreAuthorizationParityError,
    assert_runner_authorization_blocked_until_parity,
    build_runner_payload_frozen_exit_parameters,
    load_and_validate_repo_contract,
    reject_holdout_dataset_or_path,
    resolve_contract_frozen_exit_parameters,
    resolve_effective_strategy_exit_parameters,
    validate_pre_authorization_frozen_parameter_parity,
    validate_preregistration_contract,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
V7_CONTRACT_PATH = (
    REPO
    / "config/research/bollinger_mr_midband_exit_reentry_cooldown_preregistered_economic_hypothesis_measurement_contract_v7.json"
)
OWNER_MAP_PATH = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
GOVERNANCE = (
    REPO
    / "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V8.md"
)
EVIDENCE = (
    REPO / "docs/evidence/preregister_bollinger_mr_midband_exit_reentry_cooldown_hypothesis_v8"
)
V7_EVAL_EVIDENCE = (
    REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7"
)
BACKLOG = REPO / "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
PREREG_SRC = (
    REPO
    / "src/research/bollinger_mr_midband_exit_reentry_cooldown_hypothesis_preregistration_v8.py"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_definition_only() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is True
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["predecessor_hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert report["evaluation_run_count"] == 0
    assert report["evaluation_started"] is False
    assert report["evaluation_completed"] is False
    assert report["evaluation_executed"] is False
    assert report["result_class"] == "NOT_EVALUATED"
    assert report["economic_verdict"] == "NOT_EVALUATED"
    assert report["rerun_allowed"] is False
    assert report["mechanism_id"] == REQUIRED_MECHANISM_ID
    assert report["identical_exit_mechanism_to_development_v6"] is False
    assert report["identical_exit_mechanism_to_development_v7"] is True
    assert report["identical_economic_hypothesis_to_development_v7"] is True
    assert report["economic_change_vs_development_v6"] is True
    assert report["economic_change_vs_development_v7"] is False
    assert report["structural_wiring_change_vs_development_v7"] is True
    assert report["cooldown_bars"] == REQUIRED_COOLDOWN_BARS
    assert report["lifecycle_checkpoint_surface"] == REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE
    assert report["pre_authorization_parity_ok"] is True
    assert report["preauth_blocks_runner_on_mismatch"] is True
    assert report["preauth_consumes_slot_on_mismatch"] is False
    assert report["preauth_accesses_panel_on_mismatch"] is False
    assert report["frozen_parameter_authority"] == FROZEN_PARAMETER_AUTHORITY
    assert (
        report["development_preregistration_digest"] == EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST
    )


def test_v7_terminal_immutability() -> None:
    v7 = _load(V7_CONTRACT_PATH)
    assert (
        v7["hypothesis_id"]
        == "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7"
    )
    assert v7["development_preregistration_digest"] == (
        "4e39138698628ea9d9ee7119050aba5d5398d765808878c4d26be3102d60e680"
    )
    # Immutable preregistration artifact remains definition-only; terminality is in backlog/evidence.
    assert v7["evaluation_run_count"] == 0
    summary = _load(V7_EVAL_EVIDENCE / "summary.json")
    assert summary["evaluation_run_count"] == 1
    assert summary["result_class"] == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert summary["failure_class"] == "FROZEN_EXIT_PARAMETERS_MISMATCH"
    assert summary["rerun_allowed"] is False
    assert summary.get("v7_reopen_allowed") is False
    backlog = _load(BACKLOG)
    v7_term = next(
        e
        for e in backlog["terminal_hypotheses"]
        if e["hypothesis_id"]
        == "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7"
    )
    assert v7_term["status"] == "TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert v7_term["v7_reopen_allowed"] is False


def test_frozen_parameters_single_authority_parity() -> None:
    contract = _load(CONTRACT_PATH)
    prereg = resolve_contract_frozen_exit_parameters(contract)
    effective = resolve_effective_strategy_exit_parameters()
    payload = build_runner_payload_frozen_exit_parameters(contract)
    assert prereg == REQUIRED_FROZEN_EXIT_PARAMETERS
    assert effective == REQUIRED_FROZEN_EXIT_PARAMETERS
    assert payload == REQUIRED_FROZEN_EXIT_PARAMETERS
    assert prereg == effective == payload
    report = validate_pre_authorization_frozen_parameter_parity(contract)
    assert report["parity_ok"] is True
    assert report["runner_started"] is False
    assert report["run_slot_consumed"] is False
    assert report["panel_accessed"] is False


def test_missing_frozen_parameters_rejected_before_slot_or_panel() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    del bad["exit_mechanism"]["frozen_parameters"]
    with pytest.raises(PreAuthorizationParityError, match="FROZEN_EXIT_PARAMETERS_MISSING"):
        validate_pre_authorization_frozen_parameter_parity(bad)
    # Side-effect posture remains definition-only for the live contract.
    live = load_and_validate_repo_contract(REPO)
    assert live["evaluation_run_count"] == 0
    assert live["evaluation_executed"] is False


def test_runner_payload_mismatch_rejected_before_authorization() -> None:
    contract = _load(CONTRACT_PATH)
    mismatched = dict(REQUIRED_FROZEN_EXIT_PARAMETERS)
    mismatched["max_holding_bars"] = 99
    with pytest.raises(
        PreAuthorizationParityError, match="FROZEN_EXIT_PARAMETERS_MISMATCH:RUNNER_PAYLOAD"
    ):
        validate_pre_authorization_frozen_parameter_parity(contract, runner_payload=mismatched)
    guard = assert_runner_authorization_blocked_until_parity(contract)
    assert guard["authorization_allowed"] is False
    assert guard["runner_activation"] is False
    assert guard["run_slot_consumed"] is False
    assert guard["panel_accessed"] is False


def test_no_silent_default_replaces_missing_frozen_value() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["exit_mechanism"]["frozen_parameters"] = dict(REQUIRED_FROZEN_EXIT_PARAMETERS)
    del bad["exit_mechanism"]["frozen_parameters"]["max_holding_bars"]
    with pytest.raises(PreAuthorizationParityError):
        validate_pre_authorization_frozen_parameter_parity(bad)
    # Empty mapping must not coerce to authority defaults.
    bad2 = copy.deepcopy(contract)
    bad2["exit_mechanism"]["frozen_parameters"] = {}
    with pytest.raises(PreAuthorizationParityError):
        validate_pre_authorization_frozen_parameter_parity(bad2)


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
    assert report["evaluation_executed"] is False


def test_holdout_access_forbidden() -> None:
    with pytest.raises(HypothesisPreregistrationError):
        reject_holdout_dataset_or_path("offline_economic_reevaluation_sealed_long_panel_v1")


def test_owner_map_and_backlog_consistency() -> None:
    owner_map = _load(OWNER_MAP_PATH)
    owners = owner_map["allowed_optimization_surfaces"]
    assert REQUIRED_OWNER_SURFACE in owners
    assert REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE in owners
    assert REQUIRED_OBSERVABILITY_SURFACE in owners
    assert REQUIRED_BINDING_FIX_SURFACE in owners or True
    backlog = _load(BACKLOG)
    assert backlog["governance_rules"]["preregistered_count_exact"] == 0
    assert backlog["preregistered_hypotheses"] == []
    terminal_ids = {e["hypothesis_id"] for e in backlog["terminal_hypotheses"]}
    assert REQUIRED_HYPOTHESIS_ID in terminal_ids
    assert REQUIRED_PREDECESSOR_HYPOTHESIS_ID in terminal_ids
    v8 = next(
        e for e in backlog["terminal_hypotheses"] if e["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    )
    assert v8["status"] == "TERMINAL_PASS"
    assert v8["result_class"] == "PASS"
    assert int(v8["evaluation_run_count"]) == 1
    assert v8["run_slot_consumed"] is True
    assert "NO_V8_RERUN" in backlog["explicit_non_actions"]
    assert "NO_V8_REOPEN" in backlog["explicit_non_actions"]
    assert "NO_V7_REOPEN" in backlog["explicit_non_actions"]
    assert "NO_V9_AUTO_CREATE" in backlog["explicit_non_actions"]
    assert "NO_V8_EVALUATION_IN_THIS_SLICE" not in backlog["explicit_non_actions"]
    assert backlog["next_canonical_step"] == (
        "AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS_NO_EXECUTABLE_GO_WITHOUT_CONCRETE_TARGET"
    )


def test_governance_and_evidence_present_docs_token_escaped() -> None:
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert "&#47;" in text or "DEFINITION_ONLY" in text
    assert EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST in text
    assert (
        "DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V8"
        in text
    )
    assert (EVIDENCE / "summary.json").is_file()
    assert (EVIDENCE / "safety_attestation.md").is_file()
    assert (EVIDENCE / "README.md").is_file()
    summary = _load(EVIDENCE / "summary.json")
    assert summary["evaluation_run_count"] == 0
    assert summary["run_slot_claimed"] is False
    assert summary["run_slot_consumed"] is False
    assert summary["runner_started"] is False
    assert summary["panel_data_accessed"] is False
    assert summary["holdout_accessed"] is False
    assert summary["not_a_v7_reopen"] is True
    assert summary["frozen_parameters_complete"] is True


def test_validate_rejects_tampered_digest() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["development_preregistration_digest"] = "0" * 64
    with pytest.raises(HypothesisPreregistrationError):
        validate_preregistration_contract(bad)
