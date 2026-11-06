"""Contract tests for Bollinger/MR midband exit-efficiency hypothesis preregistration v4.

Terminal closeout: V4 is DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/INFRASTRUCTURE_FAILURE
with run count 1. V3 remains terminal FAIL (run count 1; no rerun).
V2/V1 remain terminal. No second evaluation under this preregistration.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v3 import (
    load_and_validate_repo_contract as load_v3,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v4 import (
    CONTRACT_REL_PATH,
    EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST,
    REQUIRED_BINDING_FIX_ROOT_CAUSE,
    REQUIRED_BINDING_FIX_SHA,
    REQUIRED_BINDING_FIX_SURFACE,
    REQUIRED_FALSY_ZERO_HYGIENE_SURFACE,
    REQUIRED_FROZEN_EXIT_PARAMETERS,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_OBSERVABILITY_SURFACE,
    REQUIRED_OWNER_SURFACE,
    REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
    REQUIRED_V1_HYPOTHESIS_ID,
    REQUIRED_V2_HYPOTHESIS_ID,
    V3_TERMINAL_ROOT_CAUSE,
    HypothesisPreregistrationError,
    load_and_validate_repo_contract,
    reject_holdout_dataset_or_path,
    validate_preregistration_contract,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
V3_CONTRACT_PATH = (
    REPO
    / "config/research/bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v3.json"
)
OWNER_MAP_PATH = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
GOVERNANCE = (
    REPO
    / "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V4.md"
)
EVIDENCE = REPO / "docs/evidence/preregister_bollinger_mr_midband_exit_efficiency_hypothesis_v4"
V3_EVAL_EVIDENCE = (
    REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v3"
)
V4_EVAL_EVIDENCE = (
    REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v4"
)
BACKLOG = REPO / "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"


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
    assert report["new_evaluation_not_rerun"] is True
    assert report["v3_partial_results_reused"] is False
    assert report["identical_exit_mechanism_to_development_v3"] is True
    assert report["enhanced_measurement_validity_relative_to_development_v3"] is True
    assert report["observability_surface_bound"] is True
    assert report["observability_surface"] == REQUIRED_OBSERVABILITY_SURFACE
    assert report["falsy_zero_hygiene_bound"] is True
    assert report["binding_fix_bound"] is True
    assert report["binding_fix_surface"] == REQUIRED_BINDING_FIX_SURFACE
    assert report["development_preregistration_digest"] == (
        EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST
    )
    assert report["rerun_allowed"] is False


def test_hypothesis_id_unique_and_not_v3_rerun() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert contract["hypothesis_id"] != REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert contract["hypothesis_id"] != REQUIRED_V2_HYPOTHESIS_ID
    assert contract["hypothesis_id"] != REQUIRED_V1_HYPOTHESIS_ID
    assert contract["new_evaluation_not_rerun"] is True
    assert contract["v3_rerun_forbidden"] is True
    assert contract["identical_exit_mechanism_to_development_v3"] is True
    assert contract["identical_measurement_rules_to_development_v3"] is False


def test_v3_remains_terminal_fail() -> None:
    v3_report = load_v3(REPO)
    assert v3_report["evaluation_run_count"] == 1
    assert v3_report["result_class"] == "FAIL"
    assert v3_report["rerun_allowed"] is False
    v3 = _load(V3_CONTRACT_PATH)
    assert v3["status"] == "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL"
    assert v3["evaluation_run_count"] == 1


def test_holdout_rejected() -> None:
    with pytest.raises(HypothesisPreregistrationError):
        reject_holdout_dataset_or_path("offline_economic_reevaluation_sealed_long_panel_v1")


def test_effective_config_digest_inequality_prerequisite() -> None:
    contract = _load(CONTRACT_PATH)
    mvp = contract["measurement_validity_prerequisites"]
    eff = mvp["effective_config_digest_inequality"]
    assert eff["required"] is True
    assert eff["baseline_and_treatment_effective_digests_must_differ"] is True
    assert eff["if_identical_result_class"] == "INVALID_MEASUREMENT_IDENTICAL_EFFECTIVE_CONFIGS"
    assert eff["if_identical_block_real_panel_run"] is True


def test_open_side_binding_prerequisite() -> None:
    contract = _load(CONTRACT_PATH)
    open_side = contract["measurement_validity_prerequisites"]["open_side_binding"]
    assert open_side["required"] is True
    assert open_side["open_side_must_be_bound_in_per_bar_exit_decision_input"] is True
    assert open_side["if_absent_result_class"] == "INVALID_MEASUREMENT_BINDING_MISSING"
    assert open_side["if_absent_block_real_panel_run"] is True


def test_exit_observability_prerequisite() -> None:
    contract = _load(CONTRACT_PATH)
    exit_obs = contract["measurement_validity_prerequisites"]["exit_observability"]
    assert exit_obs["required"] is True
    assert (
        exit_obs[
            "exit_bars_observed_must_be_gt_0_for_at_least_one_admissible_synthetic_contract_case"
        ]
        is True
    )
    assert exit_obs["if_absent_result_class"] == "INVALID_MEASUREMENT_NO_EXIT_OBSERVABILITY"
    assert exit_obs["if_absent_block_real_panel_run"] is True


def test_synthetic_divergence_prerequisite() -> None:
    contract = _load(CONTRACT_PATH)
    synth = contract["measurement_validity_prerequisites"]["synthetic_divergence"]
    assert synth["required"] is True
    assert synth["synthetic_divergence_expected"] is True
    assert synth["if_absent_result_class"] == "INVALID_MEASUREMENT_BINDING_MISSING"
    assert synth["if_absent_block_real_panel_run"] is True


def test_mutated_run_count_away_from_one_fails_closed() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["evaluation_run_count"] = 0
    with pytest.raises(HypothesisPreregistrationError, match="EVALUATION_RUN_COUNT_MUST_BE_1"):
        validate_preregistration_contract(bad)


def test_dropped_prerequisite_fails_closed() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    del bad["measurement_validity_prerequisites"]["open_side_binding"]
    with pytest.raises(HypothesisPreregistrationError, match="MVP_OPEN_SIDE_BINDING_REQUIRED"):
        validate_preregistration_contract(bad)


def test_registry_backlog_consistency() -> None:
    backlog = _load(BACKLOG)
    assert backlog["governance_rules"]["preregistered_count_exact"] == 0
    assert backlog["preregistered_hypotheses"] == []
    assert any(
        e["hypothesis_id"]
        == "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V8"
        for e in backlog["terminal_hypotheses"]
    )
    assert any(e["hypothesis_id"].endswith("_V6") for e in backlog["terminal_hypotheses"])
    assert len(backlog["terminal_hypotheses"]) == 8
    ids = {e["hypothesis_id"] for e in backlog["terminal_hypotheses"]}
    assert REQUIRED_HYPOTHESIS_ID in ids
    assert REQUIRED_PREDECESSOR_HYPOTHESIS_ID in ids
    assert REQUIRED_V2_HYPOTHESIS_ID in ids
    assert REQUIRED_V1_HYPOTHESIS_ID in ids
    assert any(i.endswith("_V5") for i in ids)
    v4 = next(
        e for e in backlog["terminal_hypotheses"] if e["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    )
    assert v4["status"] == "TERMINAL_INFRASTRUCTURE_FAILURE"
    assert v4["evaluation_run_count"] == 1
    assert v4["result_class"] == "INFRASTRUCTURE_FAILURE"
    assert "NO_V3_RERUN" in backlog["explicit_non_actions"]
    assert "NO_HOLDOUT_AFTER_FAIL" in backlog["explicit_non_actions"]
    assert "NO_RETUNING_AFTER_FAIL" in backlog["explicit_non_actions"]
    assert "NO_V4_RERUN" in backlog["explicit_non_actions"]
    assert "NO_V5_RERUN" in backlog["explicit_non_actions"]
    assert "NO_V6_RERUN" in backlog["explicit_non_actions"]
    assert "NO_V7_AUTO_CREATE" in backlog["explicit_non_actions"]
    assert "NO_V6_AUTO_CREATE" not in backlog["explicit_non_actions"]
    assert "NO_V5_AUTO_CREATE" not in backlog["explicit_non_actions"]
    assert "NO_V3_ECONOMIC_RESULT_IMPORT" in backlog["explicit_non_actions"]
    assert "NO_V4_AUTO_CREATE" not in backlog["explicit_non_actions"]


def test_governance_and_evidence_present() -> None:
    assert GOVERNANCE.is_file()
    assert (
        "DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V4"
        in (GOVERNANCE.read_text(encoding="utf-8"))
    )
    assert (EVIDENCE / "README.md").is_file()
    assert (EVIDENCE / "summary.json").is_file()
    assert (EVIDENCE / "safety_attestation.md").is_file()
    assert (EVIDENCE / "split_manifest.json").is_file()
    assert (EVIDENCE / "timing_proof.txt").is_file()
    assert (EVIDENCE / "timing_proof_meta.txt").is_file()
    assert (V3_EVAL_EVIDENCE / "summary.json").is_file()


def test_v4_evaluation_evidence_terminal() -> None:
    assert V4_EVAL_EVIDENCE.is_dir()
    summary = _load(V4_EVAL_EVIDENCE / "summary.json")
    assert summary["evaluation_run_count"] == 1
    assert summary["evaluation_executed"] is True
    assert summary["result_class"] == "INFRASTRUCTURE_FAILURE"
    assert summary["holdout_data_accessed"] is False
    assert summary["runner_start_count"] == 1
    assert (V4_EVAL_EVIDENCE / "run_slot_claim.json").is_file()


def test_binding_fix_surface_registered() -> None:
    contract = _load(CONTRACT_PATH)
    binding = contract["infrastructure_bindings"][
        "mv2_wiring_mod_capture_alias_open_side_binding_fix"
    ]
    assert binding["surface_id"] == REQUIRED_BINDING_FIX_SURFACE
    assert binding["merged_on_main_sha"] == REQUIRED_BINDING_FIX_SHA
    assert binding["root_cause_addressed"] == REQUIRED_BINDING_FIX_ROOT_CAUSE
    assert binding["root_cause_addressed"] == V3_TERMINAL_ROOT_CAUSE
    assert binding["does_not_authorize_v3_rerun"] is True
    assert binding["v3_terminal_unchanged"] is True
    owner_map = _load(OWNER_MAP_PATH)
    owners = owner_map["allowed_optimization_surfaces"]
    assert REQUIRED_OWNER_SURFACE in owners
    assert contract["exit_mechanism"]["frozen_parameters"] == REQUIRED_FROZEN_EXIT_PARAMETERS
    assert (
        REQUIRED_FALSY_ZERO_HYGIENE_SURFACE
        == (
            contract["infrastructure_bindings"]["panel_runner_falsy_zero_premeasurement_hygiene"][
                "surface_id"
            ]
        )
    )
