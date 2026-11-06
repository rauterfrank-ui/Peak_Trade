"""Definition/synthetic-only tests for the ADX DI HOLDOUT evaluation package.

No holdout data access: this test module never calls
``resolve_holdout_archive_root`` / ``load_member_bars`` / ``run_holdout_evaluation``
/ ``run_arm``, and never sets ``PEAK_TRADE_ADX_DI_HOLDOUT_V2_EXECUTION_GO``. It only
exercises pure definitions, contract-digest checks, and the decision helper
against synthetic metrics.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import src.research.adx_di_direction_confirmation_mr_eligibility_holdout_evaluation_v2 as holdout_pkg
from src.research.adx_di_direction_confirmation_mr_eligibility_holdout_evaluation_v2.decision_v1 import (
    REASON_ALL_PASS_REQUIRES_MET,
    REASON_INSUFFICIENT_CONTROL_TRADE_COUNT,
    REASON_NO_DIVERGENCE,
    REASON_PROFIT_FACTOR_NOT_IMPROVED,
    RESULT_FAIL,
    RESULT_INCONCLUSIVE,
    RESULT_PASS,
    decide_development_evaluation,
)
from src.research.adx_di_direction_confirmation_mr_eligibility_holdout_evaluation_v2.holdout_panel_bars_v1 import (
    EXPECTED_CONTENT_HASH,
    EXPECTED_MANIFEST_SHA256,
    INSTRUMENT_COUNT,
    PERIOD_END_EXCLUSIVE,
    PERIOD_START,
    REQUIRED_DATASET_ID,
    SEALED_ARCHIVE_SUBDIR,
    _canonical_id_to_dir_name,
)
from src.research.adx_di_direction_confirmation_mr_eligibility_holdout_evaluation_v2.panel_runner_v1 import (
    CONFIG_ID,
    EVALUATION_RUN_ID,
)
from src.research.adx_di_direction_confirmation_mr_eligibility_holdout_preregistration_v2 import (
    CONTRACT_REL_PATH,
    DECLARED_RUNNER_REL_PATH,
    EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST,
    EXPECTED_HOLDOUT_SPLIT_DIGEST,
    OPERATOR_GO_ENV,
    REQUIRED_HYPOTHESIS_ID,
    HoldoutPreregistrationError,
    assert_execution_go_present,
    assert_holdout_run_not_yet_consumed,
    expected_holdout_split_digest,
    load_and_validate_repo_holdout_contract,
    materialize_holdout_split_definition,
    preflight_holdout_execution_gates,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
DEV_CONTRACT_PATH = (
    REPO / "config/research/"
    "adx_di_direction_confirmation_mr_eligibility_preregistered_economic_hypothesis_measurement_contract_v1.json"
)
RUNNER_PATH = REPO / DECLARED_RUNNER_REL_PATH


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# --- package marker ---------------------------------------------------------


def test_package_markers_present() -> None:
    assert holdout_pkg.ADX_DI_DIRECTION_CONFIRMATION_MR_ELIGIBILITY_HOLDOUT_EVALUATION_V2 is True
    assert holdout_pkg.HOLDOUT_EXECUTION_IMPLEMENTED is True


# --- GO env gate -------------------------------------------------------------


def test_go_absent_blocks_execution_go_assertion() -> None:
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_V2_EXECUTION_GO_REQUIRED"):
        assert_execution_go_present(environ={})
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_V2_EXECUTION_GO_REQUIRED"):
        assert_execution_go_present(environ={OPERATOR_GO_ENV: "false"})


def test_go_present_satisfies_execution_go_assertion() -> None:
    # Presence of GO alone does not access any data; it is a pure env check.
    assert_execution_go_present(environ={OPERATOR_GO_ENV: "true"})


# --- frozen digest constants -------------------------------------------------


def test_expected_holdout_digest_constants_match_contract_on_disk() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["holdout_preregistration_digest"] == EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST
    assert contract["splits"]["split_intervals_sha256"] == EXPECTED_HOLDOUT_SPLIT_DIGEST
    assert EXPECTED_HOLDOUT_SPLIT_DIGEST == expected_holdout_split_digest()


def test_terminal_contract_validates_with_count_one() -> None:
    report = load_and_validate_repo_holdout_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is False
    assert report["holdout_executed"] is True
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["holdout_run_count"] == 1
    assert report["holdout_run_limit"] == 1
    assert report["execution_authorized"] is False
    assert report["holdout_split_digest"] == expected_holdout_split_digest()
    assert report["holdout_split_digest"] == EXPECTED_HOLDOUT_SPLIT_DIGEST
    assert report["terminal_holdout_result_class"] == "FAIL"
    assert isinstance(materialize_holdout_split_definition(), dict)


def test_holdout_run_limit_one_and_count_consumed() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["holdout_run_limit"] == 1
    assert contract["holdout_run_count"] == 1


# --- preflight gate function (unit-tested, not invoked against real data) --


def test_preflight_execution_gates_block_on_consumed_contract() -> None:
    contract = _load(CONTRACT_PATH)
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_V2_RUN_ALREADY_CONSUMED"):
        preflight_holdout_execution_gates(contract)
    assert contract["holdout_preregistration_digest"] == EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST
    assert contract["splits"]["split_intervals_sha256"] == EXPECTED_HOLDOUT_SPLIT_DIGEST


def test_preflight_blocks_when_holdout_run_already_consumed() -> None:
    contract = _load(CONTRACT_PATH)
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_V2_RUN_ALREADY_CONSUMED"):
        preflight_holdout_execution_gates(contract)
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_V2_RUN_ALREADY_CONSUMED"):
        assert_holdout_run_not_yet_consumed(contract)
    # Definition-view with count 0 still passes the not-yet-consumed assertion.
    from src.research.adx_di_direction_confirmation_mr_eligibility_holdout_preregistration_v2 import (
        definition_body_for_preregistration_digest,
    )

    definition_view = definition_body_for_preregistration_digest(contract)
    assert_holdout_run_not_yet_consumed(definition_view)


def _definition_preflight_view() -> dict:
    contract = _load(CONTRACT_PATH)
    from src.research.adx_di_direction_confirmation_mr_eligibility_holdout_preregistration_v2 import (
        definition_body_for_preregistration_digest,
    )

    view = definition_body_for_preregistration_digest(contract)
    view["holdout_preregistration_digest"] = contract["holdout_preregistration_digest"]
    view["splits"] = copy.deepcopy(contract["splits"])
    view["development_binding"] = copy.deepcopy(contract["development_binding"])
    view["holdout_run_limit"] = 1
    return view


def test_preflight_blocks_on_preregistration_digest_drift() -> None:
    tampered = _definition_preflight_view()
    tampered["holdout_preregistration_digest"] = "0" * 64
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_PREREGISTRATION_DIGEST_DRIFT"):
        preflight_holdout_execution_gates(tampered)


def test_preflight_blocks_on_split_digest_drift() -> None:
    tampered = _definition_preflight_view()
    tampered["splits"] = dict(tampered["splits"])
    tampered["splits"]["split_intervals_sha256"] = "0" * 64
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_SPLIT_DIGEST_DRIFT"):
        preflight_holdout_execution_gates(tampered)


def test_preflight_blocks_when_run_limit_not_one() -> None:
    tampered = _definition_preflight_view()
    tampered["holdout_run_limit"] = 2
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_RUN_LIMIT_MUST_BE_1"):
        preflight_holdout_execution_gates(tampered)


def test_preflight_blocks_when_preregistration_digest_drifts() -> None:
    contract = _load(CONTRACT_PATH)
    from src.research.adx_di_direction_confirmation_mr_eligibility_holdout_preregistration_v2 import (
        definition_body_for_preregistration_digest,
    )

    body = definition_body_for_preregistration_digest(contract)
    body["holdout_preregistration_digest"] = "0" * 64
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_PREREGISTRATION_DIGEST_DRIFT"):
        preflight_holdout_execution_gates(body)


def test_preflight_blocks_when_new_evaluation_flag_missing() -> None:
    contract = _load(CONTRACT_PATH)
    from src.research.adx_di_direction_confirmation_mr_eligibility_holdout_preregistration_v2 import (
        definition_body_for_preregistration_digest,
    )

    body = definition_body_for_preregistration_digest(contract)
    body["holdout_preregistration_digest"] = EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST
    body["new_evaluation_not_rerun"] = False
    with pytest.raises(HoldoutPreregistrationError, match="NEW_EVALUATION_NOT_RERUN_REQUIRED"):
        preflight_holdout_execution_gates(body)


def test_development_contract_still_holdout_forbidden() -> None:
    dev = _load(DEV_CONTRACT_PATH)
    assert dev["holdout_forbidden"] is True
    assert dev["sealed_holdout_content_inspection_authorized"] is False
    assert dev["promotion_and_holdout_policy"]["holdout_forbidden_in_this_slice"] is True
    report = load_and_validate_repo_holdout_contract(REPO)
    assert report["valid"] is True


# --- decision helper (reused unchanged; synthetic metrics only) ------------


def _baseline_metrics(**overrides) -> dict:
    base = {
        "trade_count": 100,
        "net_return": 0.01,
        "max_drawdown": -0.05,
        "profit_factor": 0.9,
    }
    base.update(overrides)
    return base


def _treatment_metrics(**overrides) -> dict:
    base = {
        "trade_count": 80,
        "net_return": 0.02,
        "max_drawdown": -0.04,
        "profit_factor": 1.1,
    }
    base.update(overrides)
    return base


def test_decision_pass_when_all_requires_met() -> None:
    out = decide_development_evaluation(
        baseline=_baseline_metrics(),
        treatment=_treatment_metrics(),
        entry_eligibility_divergence_observed=True,
        minimum_trade_count=50,
        max_trade_count_reduction_fraction=0.5,
    )
    assert out["result_class"] == RESULT_PASS
    assert out["reason"] == REASON_ALL_PASS_REQUIRES_MET
    assert all(out["checks"].values())


def test_decision_fail_on_no_divergence_even_with_good_economics() -> None:
    out = decide_development_evaluation(
        baseline=_baseline_metrics(),
        treatment=_treatment_metrics(),
        entry_eligibility_divergence_observed=False,
        minimum_trade_count=50,
    )
    assert out["result_class"] == RESULT_FAIL
    assert out["reason"] == REASON_NO_DIVERGENCE


def test_decision_fail_when_profit_factor_not_improved() -> None:
    out = decide_development_evaluation(
        baseline=_baseline_metrics(profit_factor=1.2),
        treatment=_treatment_metrics(profit_factor=1.0),
        entry_eligibility_divergence_observed=True,
        minimum_trade_count=50,
    )
    assert out["result_class"] == RESULT_FAIL
    assert out["reason"] == REASON_PROFIT_FACTOR_NOT_IMPROVED


def test_decision_inconclusive_low_control_trade_count() -> None:
    out = decide_development_evaluation(
        baseline=_baseline_metrics(trade_count=10),
        treatment=_treatment_metrics(trade_count=8),
        entry_eligibility_divergence_observed=True,
        minimum_trade_count=50,
    )
    assert out["result_class"] == RESULT_INCONCLUSIVE
    assert out["reason"] == REASON_INSUFFICIENT_CONTROL_TRADE_COUNT


def test_decision_never_sets_promotion_or_runtime_flags() -> None:
    out = decide_development_evaluation(
        baseline=_baseline_metrics(),
        treatment=_treatment_metrics(),
        entry_eligibility_divergence_observed=True,
        minimum_trade_count=50,
    )
    forbidden_keys = {
        "promotion_eligible",
        "runtime_activated",
        "shadow_activated",
        "testnet_activated",
        "orders_sent",
        "live_authorized",
    }
    assert forbidden_keys.isdisjoint(out.keys())


# --- holdout_panel_bars_v1 constants (no data access) ------------------------


def test_holdout_panel_bars_constants_match_contract() -> None:
    contract = _load(CONTRACT_PATH)
    panel = contract["common_panel_bounds"]
    assert REQUIRED_DATASET_ID == contract["dataset_id"]
    assert EXPECTED_CONTENT_HASH == panel["content_hash_from_registry"]
    assert EXPECTED_MANIFEST_SHA256 == panel["sealed_manifest_sha256_from_registry"]
    assert PERIOD_START == panel["start"] == contract["splits"]["holdout_final_audit"]["start"]
    assert (
        PERIOD_END_EXCLUSIVE
        == panel["end_exclusive"]
        == contract["splits"]["holdout_final_audit"]["end_exclusive"]
    )
    assert INSTRUMENT_COUNT == panel["instrument_count_from_registry"] == 65
    assert SEALED_ARCHIVE_SUBDIR == "sealed_lifecycle_long_panel_v1_d884a000_20260720T1832Z"


def test_canonical_id_to_dir_name_mapping_is_pure_string_transform() -> None:
    # Pure string transform, exercised on synthetic ids only (no filesystem
    # access, no sealed holdout data touched).
    assert (
        _canonical_id_to_dir_name("okx:linear_perpetual:1INCH:USDT:USDT:perp")
        == "okx_linear_perpetual_1INCH_USDT_USDT_perp"
    )
    assert _canonical_id_to_dir_name("a:b:c") == "a_b_c"


# --- runner script / declared path -------------------------------------------


def test_declared_runner_path_matches_preregistration() -> None:
    assert DECLARED_RUNNER_REL_PATH == (
        "scripts/research/run_evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v2.py"
    )
    contract = _load(CONTRACT_PATH)
    assert contract["declared_future_evaluation_targets"]["runner_rel_path"] == (
        DECLARED_RUNNER_REL_PATH
    )
    assert RUNNER_PATH.is_file()


def test_runner_script_uses_lock_and_marker_and_go_gate() -> None:
    text = RUNNER_PATH.read_text(encoding="utf-8")
    assert ".holdout_run.lock" in text
    assert ".holdout_run_consumed" in text
    assert "fcntl" in text
    assert "assert_execution_go_present" in text
    assert "HOLDOUT_DUPLICATE_RUN_BLOCKED" in text
    assert "run_holdout_evaluation" in text
    assert "resolve_holdout_archive_root" not in text
    assert "load_member_bars" not in text


def test_runner_script_default_output_dir_matches_declared_evidence_dir() -> None:
    contract = _load(CONTRACT_PATH)
    text = RUNNER_PATH.read_text(encoding="utf-8")
    evidence_dir = contract["declared_future_evaluation_targets"]["evidence_dir_rel_path"].rstrip(
        "/"
    )
    assert evidence_dir in text


def test_evaluation_run_id_and_config_id_constants() -> None:
    assert EVALUATION_RUN_ID == "evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v2"
    assert CONFIG_ID == "bollinger_bands_v2_full_canonical_system_economic_binding_v1"


def test_terminal_evaluation_evidence_complete() -> None:
    evidence = (
        REPO / "docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v2"
    )
    required = [
        "summary.json",
        "run_manifest.json",
        "comparison_decision.json",
        "baseline_metrics.json",
        "treatment_metrics.json",
        "config_snapshot.json",
        "code_config_hashes.json",
        "safety_attestation.md",
        "README.md",
        ".holdout_run_consumed",
    ]
    for name in required:
        assert (evidence / name).is_file(), name
    summary = _load(evidence / "summary.json")
    assert summary["result_class"] == "FAIL"
    assert summary["holdout_run_count"] == 1
    assert summary["holdout_run_count_before"] == 0
    assert summary["no_retry"] is True
    assert summary["no_post_result_tuning"] is True
    assert summary["holdout_preregistration_digest"] == EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST
    assert summary["holdout_split_digest"] == EXPECTED_HOLDOUT_SPLIT_DIGEST
