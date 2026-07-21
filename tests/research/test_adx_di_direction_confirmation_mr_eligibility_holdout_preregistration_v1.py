"""Contract tests for ADX DI holdout preregistration v1.

Definition-only. No holdout data access. No backtest. No economic metrics.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.adx_di_direction_confirmation_mr_eligibility_holdout_preregistration_v1 import (
    CONTRACT_REL_PATH,
    DECLARED_RUNNER_REL_PATH,
    EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST,
    HOLDOUT_OPAQUE_ID,
    OPERATOR_GO_ENV,
    REQUIRED_FROZEN_FILTER_PARAMETERS,
    REQUIRED_HYPOTHESIS_ID,
    HoldoutPreregistrationError,
    assert_execution_go_present,
    assert_holdout_execution_blocked_by_definition_contract,
    compute_holdout_preregistration_digest,
    definition_body_for_preregistration_digest,
    expected_holdout_split_digest,
    load_and_validate_repo_holdout_contract,
    materialize_holdout_split_definition,
    validate_holdout_preregistration_contract,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
DEV_CONTRACT_PATH = (
    REPO / "config/research/"
    "adx_di_direction_confirmation_mr_eligibility_preregistered_economic_hypothesis_measurement_contract_v1.json"
)
EVIDENCE = (
    REPO / "docs/evidence/preregister_adx_di_direction_confirmation_mr_eligibility_holdout_v1"
)
GOVERNANCE = (
    REPO
    / "docs/governance/ADX_DI_DIRECTION_CONFIRMATION_MR_ELIGIBILITY_HOLDOUT_PREREGISTERED_MEASUREMENT_V1.md"
)
FORBIDDEN_RESULT_ARTIFACTS = (
    "baseline_metrics.json",
    "treatment_metrics.json",
    "probe_summary.json",
    "comparison_decision.json",
)
BASE_SHA = "3078b06a18c3ad9a3f99518fe8035381a23b33b4"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_holdout_contract_validates_against_ssot() -> None:
    report = load_and_validate_repo_holdout_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is False
    assert report["holdout_executed"] is True
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["holdout_run_count"] == 1
    assert report["holdout_run_limit"] == 1
    assert report["execution_authorized"] is False
    assert report["holdout_split_digest"] == expected_holdout_split_digest()
    assert report["primary_decision_metric"] == "NET_PROFIT_FACTOR"
    assert report["terminal_holdout_result_class"] == "ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN"
    assert report["holdout_preregistration_digest"] == EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST


def test_hypothesis_id_and_development_pass_binding() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    dev = contract["development_binding"]
    assert dev["development_result_class"] == "PASS"
    assert dev["development_run_count"] == 1
    assert dev["development_run_limit"] == 1
    assert contract["holdout_run_count"] == 1
    assert contract["holdout_executed"] is True
    assert contract["status"] == "HOLDOUT_EVALUATION_EXECUTED_TERMINAL"


def test_holdout_split_digest_matches_registered_definition() -> None:
    contract = _load(CONTRACT_PATH)
    expected = materialize_holdout_split_definition()
    assert contract["splits"]["holdout_split_definition"] == expected
    assert contract["splits"]["split_intervals_sha256"] == expected_holdout_split_digest()
    summary = _load(EVIDENCE / "summary.json")
    assert summary["holdout_split_digest"] == expected_holdout_split_digest()
    manifest = _load(EVIDENCE / "split_manifest.json")
    assert manifest["split_intervals_sha256"] == expected_holdout_split_digest()


def test_holdout_run_limit_exactly_one_and_count_consumed() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["holdout_run_limit"] == 1
    assert contract["holdout_runs_allowed"] == 1
    assert contract["holdout_run_count"] == 1
    bad = copy.deepcopy(contract)
    bad["holdout_run_limit"] = 2
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_RUN_LIMIT"):
        validate_holdout_preregistration_contract(bad)
    # Definition-view still rejects non-zero count.
    definition_view = definition_body_for_preregistration_digest(contract)
    definition_view["holdout_preregistration_digest"] = contract["holdout_preregistration_digest"]
    bad2 = copy.deepcopy(definition_view)
    bad2["holdout_run_count"] = 1
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_RUN_COUNT"):
        validate_holdout_preregistration_contract(bad2)


def test_execution_without_operator_go_is_blocked() -> None:
    contract = _load(CONTRACT_PATH)
    assert_holdout_execution_blocked_by_definition_contract(contract)
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_EXECUTION_GO_REQUIRED"):
        assert_execution_go_present(environ={})
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_EXECUTION_GO_REQUIRED"):
        assert_execution_go_present(environ={OPERATOR_GO_ENV: "false"})
    # GO alone is insufficient while definition contract forbids execution
    assert contract["holdout_execution_authorized"] is False
    assert contract["evaluation_authorized"] is False
    assert contract["execution_gate"]["requires_separate_explicit_operator_go"] is True


def test_development_contract_remains_holdout_forbidden() -> None:
    dev = _load(DEV_CONTRACT_PATH)
    assert dev["holdout_forbidden"] is True
    assert dev["sealed_holdout_content_inspection_authorized"] is False
    assert dev["promotion_and_holdout_policy"]["holdout_forbidden_in_this_slice"] is True
    report = load_and_validate_repo_holdout_contract(REPO)
    assert report["valid"] is True


def test_acceptance_criteria_complete_numeric_deterministic() -> None:
    contract = _load(CONTRACT_PATH)
    th = contract["decision_thresholds"]
    assert th["minimum_trade_count"] == 50
    assert th["max_trade_count_reduction_fraction_vs_control"] == 0.5
    assert isinstance(th["pass_requires_all"], list) and len(th["pass_requires_all"]) >= 7
    assert isinstance(th["fail_if_any"], list) and len(th["fail_if_any"]) >= 7
    assert isinstance(th["inconclusive_if_any"], list) and len(th["inconclusive_if_any"]) >= 4
    assert th["inconclusive_never_for_poor_economic_results"] is True
    assert contract["primary_decision_metric"] == "NET_PROFIT_FACTOR"
    assert contract["eligibility_filter"]["frozen_parameters"] == REQUIRED_FROZEN_FILTER_PARAMETERS
    assert contract["cost_model"]["fee_bps"] == 10.0
    assert contract["cost_model"]["slippage_bps"] == 5.0
    assert contract["stop_and_ledger_semantics"]["stop_pct"] == 0.025


def test_retry_and_post_result_tuning_forbidden() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["retry_forbidden"] is True
    assert contract["restart_forbidden"] is True
    assert contract["post_result_tuning_forbidden"] is True
    assert contract["post_hoc_threshold_adjustment_forbidden"] is True
    assert contract["repeat_after_result_inspection_forbidden"] is True
    assert contract["decision_thresholds"]["on_any_terminal_result_retry_forbidden"] is True
    bad = copy.deepcopy(contract)
    bad["retry_forbidden"] = False
    with pytest.raises(HoldoutPreregistrationError, match="LOCK_REQUIRED:retry_forbidden"):
        validate_holdout_preregistration_contract(bad)


def test_terminal_states_consistent() -> None:
    contract = _load(CONTRACT_PATH)
    terminals = contract["terminal_state_transitions"]
    for cls in ("PASS", "FAIL", "INCONCLUSIVE", "ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN"):
        entry = terminals[cls]
        assert entry["terminal"] is True
        assert entry["holdout_run_count_after"] == 1
    for cls in ("PASS", "FAIL", "INCONCLUSIVE"):
        assert terminals[cls]["reopen_forbidden_without_new_hypothesis_id"] is True
        assert terminals[cls]["economic_validity_offline_gate_opened"] is False
        assert terminals[cls]["promotion_eligible"] is False


def test_universe_non_bitcoin_perpetuals_only() -> None:
    contract = _load(CONTRACT_PATH)
    u = contract["universe_scope"]
    assert u["bitcoin_excluded"] is True
    assert u["spot_excluded"] is True
    assert u["instrument_class"] == "LINEAR_USDT_PERPETUAL"
    assert u["venue"] == "OKX"


def test_definition_only_prereg_evidence_pack_has_no_result_metrics() -> None:
    assert EVIDENCE.is_dir()
    assert GOVERNANCE.is_file()
    for name in FORBIDDEN_RESULT_ARTIFACTS:
        assert not (EVIDENCE / name).exists()
    summary = _load(EVIDENCE / "summary.json")
    # Historical preregistration evidence remains definition-only.
    assert summary["holdout_executed"] is False
    assert summary["holdout_data_accessed"] is False
    assert summary["holdout_run_count"] == 0
    assert summary["evaluation_authorized"] is False
    assert summary["base_sha"] == BASE_SHA
    assert summary["declared_runner_rel_path"] == DECLARED_RUNNER_REL_PATH
    eval_summary = (
        REPO
        / "docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v1"
        / "summary.json"
    )
    assert eval_summary.is_file()
    eval_payload = _load(eval_summary)
    assert eval_payload["holdout_run_count"] == 1
    assert eval_payload["result_class"] == "ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN"
    contract_now = _load(CONTRACT_PATH)
    assert contract_now["holdout_run_count"] == 1
    assert contract_now["holdout_executed"] is True


def test_preregistration_digest_stable() -> None:
    contract = _load(CONTRACT_PATH)
    stored = contract["holdout_preregistration_digest"]
    assert stored == compute_holdout_preregistration_digest(contract)
    assert stored == EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST
    assert len(stored) == 64


def test_sealed_holdout_opaque_id_bound() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["sealed_holdout_id"] == HOLDOUT_OPAQUE_ID
    assert contract["sealed_holdout_content_inspection_authorized"] is False
