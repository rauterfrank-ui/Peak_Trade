"""Contract tests for ADX DI holdout preregistration v2.

Definition-only. No holdout data access. No backtest. No economic metrics.
V1 remains terminal and must not be mutated by this slice.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.adx_di_direction_confirmation_mr_eligibility_holdout_preregistration_v2 import (
    CONTRACT_REL_PATH,
    DECLARED_RUNNER_REL_PATH,
    EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST,
    HOLDOUT_OPAQUE_ID,
    OPERATOR_GO_ENV,
    REQUIRED_FROZEN_FILTER_PARAMETERS,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
    HoldoutPreregistrationError,
    assert_execution_go_present,
    assert_holdout_execution_blocked_by_definition_contract,
    compute_holdout_preregistration_digest,
    expected_holdout_split_digest,
    load_and_validate_repo_holdout_contract,
    materialize_holdout_split_definition,
    validate_holdout_preregistration_contract,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
V1_CONTRACT_PATH = (
    REPO
    / "config/research/adx_di_direction_confirmation_mr_eligibility_holdout_preregistered_measurement_contract_v1.json"
)
DEV_CONTRACT_PATH = (
    REPO / "config/research/"
    "adx_di_direction_confirmation_mr_eligibility_preregistered_economic_hypothesis_measurement_contract_v1.json"
)
EVIDENCE = (
    REPO / "docs/evidence/preregister_adx_di_direction_confirmation_mr_eligibility_holdout_v2"
)
GOVERNANCE = (
    REPO
    / "docs/governance/ADX_DI_DIRECTION_CONFIRMATION_MR_ELIGIBILITY_HOLDOUT_PREREGISTERED_MEASUREMENT_V2.md"
)
FORBIDDEN_RESULT_ARTIFACTS = (
    "baseline_metrics.json",
    "treatment_metrics.json",
    "probe_summary.json",
    "comparison_decision.json",
)
BASE_SHA = "55757341740de5be7413da5c9c4e76173ca4278a"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_holdout_v2_contract_validates_against_ssot() -> None:
    report = load_and_validate_repo_holdout_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is True
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["predecessor_hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert report["holdout_run_count"] == 0
    assert report["holdout_run_limit"] == 1
    assert report["execution_authorized"] is False
    assert report["new_evaluation_not_rerun"] is True
    assert report["holdout_split_digest"] == expected_holdout_split_digest()
    assert report["primary_decision_metric"] == "NET_PROFIT_FACTOR"
    assert report["holdout_preregistration_digest"] == EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST


def test_hypothesis_id_is_new_and_not_v1_rerun() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert contract["hypothesis_id"] != REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert contract["new_evaluation_not_rerun"] is True
    assert contract["v1_rerun_forbidden"] is True
    assert contract["holdout_run_count"] == 0
    assert contract["status"] == "DEFINITION_ONLY_HOLDOUT_PREREGISTERED"
    pred = contract["predecessor_holdout_v1"]
    assert pred["result_class"] == "ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN"
    assert pred["holdout_run_count"] == 1
    assert pred["terminal_preserved"] is True
    assert pred["rerun_forbidden"] is True


def test_v1_terminal_contract_unchanged_by_v2_slice() -> None:
    v1 = _load(V1_CONTRACT_PATH)
    assert v1["hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert v1["holdout_run_count"] == 1
    assert v1["holdout_run_limit"] == 1
    assert v1["status"] == "HOLDOUT_EVALUATION_EXECUTED_TERMINAL"
    assert v1["terminal_holdout_result_class"] == "ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN"
    assert v1["holdout_executed"] is True


def test_holdout_split_digest_matches_registered_definition() -> None:
    contract = _load(CONTRACT_PATH)
    expected = materialize_holdout_split_definition()
    assert contract["splits"]["holdout_split_definition"] == expected
    assert contract["splits"]["split_intervals_sha256"] == expected_holdout_split_digest()
    summary = _load(EVIDENCE / "summary.json")
    assert summary["holdout_split_digest"] == expected_holdout_split_digest()
    manifest = _load(EVIDENCE / "split_manifest.json")
    assert manifest["split_intervals_sha256"] == expected_holdout_split_digest()


def test_holdout_run_limit_exactly_one_and_count_zero() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["holdout_run_limit"] == 1
    assert contract["holdout_runs_allowed"] == 1
    assert contract["holdout_run_count"] == 0
    bad = copy.deepcopy(contract)
    bad["holdout_run_limit"] = 2
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_RUN_LIMIT"):
        validate_holdout_preregistration_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["holdout_run_count"] = 1
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_RUN_COUNT"):
        validate_holdout_preregistration_contract(bad2)


def test_execution_without_operator_go_is_blocked() -> None:
    contract = _load(CONTRACT_PATH)
    assert_holdout_execution_blocked_by_definition_contract(contract)
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_V2_EXECUTION_GO_REQUIRED"):
        assert_execution_go_present(environ={})
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_V2_EXECUTION_GO_REQUIRED"):
        assert_execution_go_present(environ={OPERATOR_GO_ENV: "false"})
    assert contract["holdout_execution_authorized"] is False
    assert contract["evaluation_authorized"] is False
    assert contract["execution_gate"]["requires_separate_explicit_operator_go"] is True
    assert OPERATOR_GO_ENV == "PEAK_TRADE_ADX_DI_HOLDOUT_V2_EXECUTION_GO"


def test_development_contract_remains_holdout_forbidden() -> None:
    dev = _load(DEV_CONTRACT_PATH)
    assert dev["holdout_forbidden"] is True
    assert dev["sealed_holdout_content_inspection_authorized"] is False
    assert dev["promotion_and_holdout_policy"]["holdout_forbidden_in_this_slice"] is True
    report = load_and_validate_repo_holdout_contract(REPO)
    assert report["valid"] is True


def test_acceptance_criteria_identical_to_v1_rules() -> None:
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
    assert contract["identical_measurement_rules_to_holdout_v1"] is True


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
    assert summary["holdout_executed"] is False
    assert summary["holdout_data_accessed"] is False
    assert summary["holdout_run_count"] == 0
    assert summary["evaluation_authorized"] is False
    assert summary["base_sha"] == BASE_SHA
    assert summary["declared_runner_rel_path"] == DECLARED_RUNNER_REL_PATH
    assert summary["new_evaluation_not_rerun"] is True
    assert summary["predecessor_holdout_v1_hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert not (REPO / DECLARED_RUNNER_REL_PATH).exists()


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


def test_no_holdout_runner_or_eval_package_in_this_slice() -> None:
    assert not (REPO / DECLARED_RUNNER_REL_PATH).exists()
    assert not (
        REPO / "src/research/adx_di_direction_confirmation_mr_eligibility_holdout_evaluation_v2"
    ).exists()
    assert not (
        REPO / "docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v2"
    ).exists()
