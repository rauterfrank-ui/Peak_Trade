"""Definition-only holdout preregistration validator for ADX DI MR eligibility holdout v2.

Research governance only. No holdout data access, no backtest, no economic metrics,
no runtime policy mutation, no productive trading-logic mutation.

V2 is a new independently versioned evaluation ID. Holdout V1 remains terminal as
ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN and must not be rerun or mutated by this slice.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "ADX_DI_DIRECTION_CONFIRMATION_MR_ELIGIBILITY_HOLDOUT_PREREGISTRATION_V2=true"
CONTRACT_REL_PATH = (
    "config/research/"
    "adx_di_direction_confirmation_mr_eligibility_holdout_preregistered_measurement_contract_v2.json"
)
V1_CONTRACT_REL_PATH = (
    "config/research/"
    "adx_di_direction_confirmation_mr_eligibility_holdout_preregistered_measurement_contract_v1.json"
)
DEV_CONTRACT_REL_PATH = (
    "config/research/"
    "adx_di_direction_confirmation_mr_eligibility_preregistered_economic_hypothesis_measurement_contract_v1.json"
)
ACQUISITION_CONTRACT_REL_PATH = (
    "config/research/regime_gated_standaside_mr_independent_dev_panel_acquisition_contract_v1.json"
)
DATASET_SPLIT_POLICY_REL_PATH = (
    "docs/evidence/archive_failed_bollinger_v2_and_next_hypothesis_v1/dataset_split_policy.json"
)
BOLLINGER_ARCHIVE_REL_PATH = "config/research/bollinger_bands_v2_sealed_long_panel_terminal_economic_fail_archive_and_next_hypothesis_v1.json"

REQUIRED_HYPOTHESIS_ID = (
    "ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_HOLDOUT_V2"
)
REQUIRED_PREDECESSOR_HYPOTHESIS_ID = (
    "ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1"
)
REQUIRED_FILTER_ID = "canonical_adx_di_direction_confirmation_entry_eligibility_v1"
REQUIRED_DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1"
HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"
REQUIRED_PERIOD_START = "2023-08-16T05:55:00Z"
REQUIRED_PERIOD_END_EXCLUSIVE = "2024-09-01T00:00:00Z"
REQUIRED_INSTRUMENT_COUNT = 65
REQUIRED_CONTENT_HASH = "7bcda794ae2a355c6f36b2ea04703f39078063458f52034add44bec5644206bb"
REQUIRED_MANIFEST_SHA = "f4c616c556ff3f2500bb5deff2070c5ee9c4b6a5d5d6ca5da3dc7aca1e8a3e56"
REQUIRED_DEV_SPLIT = "a35783bf0268c174dfe585c9839ba45cc6e3835021699786f4490a0d8c9b33db"
REQUIRED_FEATURE_SHA = "05104afcc41e07d7b14ed8a0e3f2e7bcb97cfabc80cd6ef0c422004136eb36e4"
REQUIRED_FROZEN_FILTER_PARAMETERS = {
    "adx_period": 14,
    "uses_adx_level": False,
    "uses_di_order_only": True,
    "side_aware": True,
    "warmup_bars": 28,
    "tie_policy": "STAND_ASIDE_WHEN_PLUS_DI_EQUALS_MINUS_DI",
    "nan_policy": "STAND_ASIDE_WHEN_DI_NONFINITE",
}
REQUIRED_PRIMARY_METRICS = (
    "NET_RETURN_AFTER_FEES_AND_SLIPPAGE",
    "PROFIT_FACTOR",
    "MAX_DRAWDOWN",
    "SHARPE",
    "COST_DRAG",
    "TURNOVER",
    "TRADE_COUNT",
    "ENTRY_ELIGIBILITY_DIVERGENCE",
)
OPERATOR_GO_ENV = "PEAK_TRADE_ADX_DI_HOLDOUT_V2_EXECUTION_GO"
OPERATOR_GO_REQUIRED_VALUE = "true"
DECLARED_RUNNER_REL_PATH = (
    "scripts/research/run_evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v2.py"
)
EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST = (
    "4d1ec324977e33a808d40778548523b95df472b72f3d9133fcdf606a4796c332"
)
EXPECTED_HOLDOUT_SPLIT_DIGEST = "e29eeb4e9d264e1529a0c7419d707ce84df7919ee6ed95a833612fca46a7184d"
DEFINITION_ONLY_STATUS = "DEFINITION_ONLY_HOLDOUT_PREREGISTERED"
DEFINITION_ONLY_VERDICT = (
    "HOLDOUT_HYPOTHESIS_AND_MEASUREMENT_CONTRACT_PREREGISTERED_AWAITING_SEPARATE_EXECUTION_GO"
)
DEFINITION_ONLY_NEXT_CANONICAL_STEP = "REVIEW_AND_MERGE_DEFINITION_ONLY_HOLDOUT_V2_PREREGISTRATION_THEN_SEPARATE_OPERATOR_GO_FOR_EXACTLY_ONE_HOLDOUT_RUN"
TERMINAL_EXECUTED_STATUS = "HOLDOUT_EVALUATION_EXECUTED_TERMINAL"
ALLOWED_TERMINAL_RESULT_CLASSES = (
    "PASS",
    "FAIL",
    "INCONCLUSIVE",
    "ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN",
)
TERMINAL_OVERLAY_KEYS = frozenset(
    {
        "holdout_executed",
        "terminal_holdout_result_class",
        "terminal_holdout_reason",
        "evaluation_evidence_ref",
    }
)
EVALUATION_EVIDENCE_REL_PATH = (
    "docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v2/"
)
V1_TERMINAL_RESULT_CLASS = "ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN"
V1_EVALUATION_EVIDENCE_REL_PATH = (
    "docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v1/"
)


class HoldoutPreregistrationError(ValueError):
    """Fail-closed holdout v2 preregistration / execution-gate error."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def definition_body_for_preregistration_digest(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Reconstruct the frozen definition-only body used for the preregistration digest.

    Post-execution terminal overlays (run count / status / verdict / result class)
    are stripped or forced back to their definition-only values so the immutable
    preregistration identity remains ``EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST``.
    """
    body = {k: v for k, v in contract.items() if k != "holdout_preregistration_digest"}
    for key in TERMINAL_OVERLAY_KEYS:
        body.pop(key, None)
    body["status"] = DEFINITION_ONLY_STATUS
    body["verdict"] = DEFINITION_ONLY_VERDICT
    body["holdout_run_count"] = 0
    body["next_canonical_step"] = DEFINITION_ONLY_NEXT_CANONICAL_STEP
    return body


def compute_holdout_preregistration_digest(contract: Mapping[str, Any]) -> str:
    return canonical_json_sha256(definition_body_for_preregistration_digest(contract))


def load_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise HoldoutPreregistrationError("JSON_ROOT_MUST_BE_OBJECT")
    return raw


def materialize_holdout_split_definition() -> dict[str, Any]:
    intervals = {
        "holdout_final_audit": {
            "start": REQUIRED_PERIOD_START,
            "end_exclusive": REQUIRED_PERIOD_END_EXCLUSIVE,
        }
    }
    return {
        "method": "SEALED_HOLDOUT_SINGLE_FINAL_AUDIT_PANEL_V1",
        "evidence_id": HOLDOUT_OPAQUE_ID,
        "dataset_id": REQUIRED_DATASET_ID,
        "dataset_class": "SEALED_HOLDOUT_FINAL_AUDIT_ONLY",
        "role": "FINAL_AUDIT_ONLY",
        "period_start": REQUIRED_PERIOD_START,
        "period_end_exclusive": REQUIRED_PERIOD_END_EXCLUSIVE,
        "instrument_count": REQUIRED_INSTRUMENT_COUNT,
        "content_hash_from_registry": REQUIRED_CONTENT_HASH,
        "sealed_manifest_sha256_from_registry": REQUIRED_MANIFEST_SHA,
        "decision_segment": "full_sealed_holdout_panel",
        "intervals": intervals,
        "overlap_with_development_forbidden": True,
        "development_panel_end_exclusive": "2023-08-16T05:55:00Z",
        "bitcoin_excluded": True,
        "spot_excluded": True,
        "venue": "OKX",
        "instrument_class": "LINEAR_USDT_PERPETUAL",
        "frequency": "PT1H",
        "source_ssot_refs": [
            "config/research/regime_gated_standaside_mr_independent_dev_panel_acquisition_contract_v1.json#sealed_holdout_opaque_exclusion",
            "docs/evidence/archive_failed_bollinger_v2_and_next_hypothesis_v1/dataset_split_policy.json#sealed_holdout",
            "config/research/bollinger_bands_v2_sealed_long_panel_terminal_economic_fail_archive_and_next_hypothesis_v1.json",
        ],
    }


def expected_holdout_split_digest() -> str:
    return canonical_json_sha256(materialize_holdout_split_definition())


def assert_execution_go_present(*, environ: Mapping[str, str] | None = None) -> None:
    env = environ if environ is not None else os.environ
    if env.get(OPERATOR_GO_ENV) != OPERATOR_GO_REQUIRED_VALUE:
        raise HoldoutPreregistrationError(
            f"HOLDOUT_V2_EXECUTION_GO_REQUIRED:{OPERATOR_GO_ENV}={OPERATOR_GO_REQUIRED_VALUE}"
        )


def assert_holdout_run_not_yet_consumed(contract: Mapping[str, Any]) -> None:
    if int(contract.get("holdout_run_count") or 0) != 0:
        raise HoldoutPreregistrationError("HOLDOUT_V2_RUN_ALREADY_CONSUMED")


def assert_holdout_execution_blocked_by_definition_contract(
    contract: Mapping[str, Any],
) -> None:
    if contract.get("evaluation_authorized") is not False:
        raise HoldoutPreregistrationError("EVALUATION_MUST_REMAIN_UNAUTHORIZED")
    if contract.get("backtest_authorized") is not False:
        raise HoldoutPreregistrationError("BACKTEST_MUST_REMAIN_UNAUTHORIZED")
    if contract.get("holdout_execution_authorized") is not False:
        raise HoldoutPreregistrationError("HOLDOUT_EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    if contract.get("holdout_data_access_authorized") is not False:
        raise HoldoutPreregistrationError("HOLDOUT_DATA_ACCESS_MUST_REMAIN_UNAUTHORIZED")
    gate = contract.get("execution_gate") or {}
    if gate.get("requires_separate_explicit_operator_go") is not True:
        raise HoldoutPreregistrationError("EXECUTION_GO_REQUIRED_FLAG_MISSING")


def validate_holdout_preregistration_contract(
    contract: Mapping[str, Any],
    *,
    acquisition_contract: Mapping[str, Any] | None = None,
    dataset_split_policy: Mapping[str, Any] | None = None,
    bollinger_archive: Mapping[str, Any] | None = None,
    development_contract: Mapping[str, Any] | None = None,
    v1_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if contract.get("slice_class") != "DEFINITION_ONLY":
        raise HoldoutPreregistrationError("SLICE_MUST_BE_DEFINITION_ONLY")
    assert_holdout_execution_blocked_by_definition_contract(contract)
    status = contract.get("status")
    if status == TERMINAL_EXECUTED_STATUS:
        return _validate_terminal_executed_holdout_contract(
            contract,
            acquisition_contract=acquisition_contract,
            dataset_split_policy=dataset_split_policy,
            bollinger_archive=bollinger_archive,
            development_contract=development_contract,
            v1_contract=v1_contract,
        )
    if status != DEFINITION_ONLY_STATUS:
        raise HoldoutPreregistrationError("STATUS_MISMATCH")
    if contract.get("verdict") != DEFINITION_ONLY_VERDICT:
        raise HoldoutPreregistrationError("VERDICT_MISMATCH")
    if contract.get("hypothesis_id") != REQUIRED_HYPOTHESIS_ID:
        raise HoldoutPreregistrationError("HYPOTHESIS_ID_MISMATCH")
    if int(contract.get("hypothesis_count") or 0) != 1:
        raise HoldoutPreregistrationError("HYPOTHESIS_COUNT_MUST_BE_1")
    if int(contract.get("multiple_testing_budget") or 0) != 1:
        raise HoldoutPreregistrationError("MULTIPLE_TESTING_BUDGET_MUST_BE_1")
    if "holdout_run_count" not in contract or int(contract["holdout_run_count"]) != 0:
        raise HoldoutPreregistrationError("HOLDOUT_RUN_COUNT_MUST_BE_0")
    if int(contract.get("holdout_run_limit") or 0) != 1:
        raise HoldoutPreregistrationError("HOLDOUT_RUN_LIMIT_MUST_BE_1")
    if int(contract.get("holdout_runs_allowed") or 0) != 1:
        raise HoldoutPreregistrationError("HOLDOUT_RUNS_ALLOWED_MUST_BE_1")
    if contract.get("new_evaluation_not_rerun") is not True:
        raise HoldoutPreregistrationError("NEW_EVALUATION_NOT_RERUN_REQUIRED")
    if contract.get("v1_rerun_forbidden") is not True:
        raise HoldoutPreregistrationError("V1_RERUN_MUST_BE_FORBIDDEN")
    if contract.get("identical_measurement_rules_to_holdout_v1") is not True:
        raise HoldoutPreregistrationError("MEASUREMENT_RULES_MUST_MATCH_V1")
    for key in (
        "retry_forbidden",
        "restart_forbidden",
        "post_hoc_threshold_adjustment_forbidden",
        "post_result_tuning_forbidden",
        "optimization_forbidden",
        "variants_forbidden",
        "parameter_sweeps_forbidden",
        "repeat_after_result_inspection_forbidden",
        "reopen_after_terminal_result_forbidden_without_new_hypothesis_id",
    ):
        if contract.get(key) is not True:
            raise HoldoutPreregistrationError(f"LOCK_REQUIRED:{key}")

    if contract.get("dataset_id") != REQUIRED_DATASET_ID:
        raise HoldoutPreregistrationError("DATASET_ID_MISMATCH")
    if contract.get("sealed_holdout_id") != HOLDOUT_OPAQUE_ID:
        raise HoldoutPreregistrationError("SEALED_HOLDOUT_ID_MISMATCH")
    if contract.get("sealed_holdout_content_inspection_authorized") is not False:
        raise HoldoutPreregistrationError("HOLDOUT_INSPECTION_MUST_BE_FALSE")
    if contract.get("holdout_content_inspection_in_this_slice") is not False:
        raise HoldoutPreregistrationError("HOLDOUT_INSPECTION_IN_SLICE_MUST_BE_FALSE")

    universe = contract.get("universe_scope") or {}
    if universe.get("bitcoin_excluded") is not True:
        raise HoldoutPreregistrationError("BTC_MUST_BE_EXCLUDED")
    if universe.get("spot_excluded") is not True:
        raise HoldoutPreregistrationError("SPOT_MUST_BE_EXCLUDED")
    if universe.get("venue") != "OKX":
        raise HoldoutPreregistrationError("VENUE_MUST_BE_OKX")
    if universe.get("instrument_class") != "LINEAR_USDT_PERPETUAL":
        raise HoldoutPreregistrationError("INSTRUMENT_CLASS_MISMATCH")

    pred = contract.get("predecessor_holdout_v1") or {}
    if pred.get("hypothesis_id") != REQUIRED_PREDECESSOR_HYPOTHESIS_ID:
        raise HoldoutPreregistrationError("PREDECESSOR_HYPOTHESIS_ID_MISMATCH")
    if pred.get("result_class") != V1_TERMINAL_RESULT_CLASS:
        raise HoldoutPreregistrationError("PREDECESSOR_RESULT_CLASS_MISMATCH")
    if int(pred.get("holdout_run_count") or 0) != 1:
        raise HoldoutPreregistrationError("PREDECESSOR_RUN_COUNT_MUST_BE_1")
    if int(pred.get("holdout_run_limit") or 0) != 1:
        raise HoldoutPreregistrationError("PREDECESSOR_RUN_LIMIT_MUST_BE_1")
    if pred.get("terminal_preserved") is not True:
        raise HoldoutPreregistrationError("PREDECESSOR_MUST_REMAIN_TERMINAL")
    if pred.get("rerun_forbidden") is not True:
        raise HoldoutPreregistrationError("PREDECESSOR_RERUN_MUST_BE_FORBIDDEN")
    if pred.get("contract_ref") != V1_CONTRACT_REL_PATH:
        raise HoldoutPreregistrationError("PREDECESSOR_CONTRACT_REF_MISMATCH")
    if pred.get("evaluation_evidence_ref") != V1_EVALUATION_EVIDENCE_REL_PATH:
        raise HoldoutPreregistrationError("PREDECESSOR_EVIDENCE_REF_MISMATCH")
    if not str(pred.get("new_evaluation_rationale") or "").strip():
        raise HoldoutPreregistrationError("PREDECESSOR_RATIONALE_REQUIRED")

    dev = contract.get("development_binding") or {}
    if dev.get("development_result_class") != "PASS":
        raise HoldoutPreregistrationError("DEVELOPMENT_MUST_BE_PASS")
    if int(dev.get("development_run_count") or 0) != 1:
        raise HoldoutPreregistrationError("DEVELOPMENT_RUN_COUNT_MUST_BE_1")
    if int(dev.get("development_run_limit") or 0) != 1:
        raise HoldoutPreregistrationError("DEVELOPMENT_RUN_LIMIT_MUST_BE_1")
    if dev.get("development_split_intervals_sha256") != REQUIRED_DEV_SPLIT:
        raise HoldoutPreregistrationError("DEVELOPMENT_SPLIT_DIGEST_MISMATCH")
    if dev.get("development_feature_formula_sha256") != REQUIRED_FEATURE_SHA:
        raise HoldoutPreregistrationError("FEATURE_FORMULA_SHA_MISMATCH")
    if dev.get("second_development_run_forbidden") is not True:
        raise HoldoutPreregistrationError("SECOND_DEVELOPMENT_RUN_MUST_BE_FORBIDDEN")

    if contract.get("baseline_immutable") is not True:
        raise HoldoutPreregistrationError("BASELINE_MUST_BE_IMMUTABLE")
    if str(contract.get("baseline_config_id") or "") != (
        "bollinger_bands_v2_full_canonical_system_economic_binding_v1"
    ):
        raise HoldoutPreregistrationError("BASELINE_CONFIG_MISMATCH")

    treatment = contract.get("treatment") or {}
    if treatment.get("treatment_type") != "ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER":
        raise HoldoutPreregistrationError("TREATMENT_TYPE_INVALID")
    if treatment.get("identical_to_development_treatment") is not True:
        raise HoldoutPreregistrationError("TREATMENT_MUST_MATCH_DEVELOPMENT")
    for key in (
        "no_new_direction_authority",
        "no_new_switch_authority",
        "no_new_risk_authority",
        "no_new_sizing_authority",
        "no_new_execution_authority",
    ):
        if treatment.get(key) is not True:
            raise HoldoutPreregistrationError(f"AUTHORITY_LOCK:{key}")
    if treatment.get("runtime_implementation_in_this_slice") is not False:
        raise HoldoutPreregistrationError("RUNTIME_IMPLEMENTATION_FORBIDDEN")

    eligibility = contract.get("eligibility_filter") or {}
    if eligibility.get("filter_id") != REQUIRED_FILTER_ID:
        raise HoldoutPreregistrationError("FILTER_ID_MISMATCH")
    frozen = eligibility.get("frozen_parameters") or {}
    for key, expected in REQUIRED_FROZEN_FILTER_PARAMETERS.items():
        if frozen.get(key) != expected:
            raise HoldoutPreregistrationError(f"FILTER_PARAMETER_MISMATCH:{key}")
    feature_ids = {str(f.get("feature_id") or "") for f in (eligibility.get("features") or [])}
    if feature_ids != {"plus_di_14h", "minus_di_14h"}:
        raise HoldoutPreregistrationError("DI_FEATURE_IDS_MISMATCH")
    if eligibility.get("feature_formula_sha256") != REQUIRED_FEATURE_SHA:
        raise HoldoutPreregistrationError("FILTER_FEATURE_SHA_MISMATCH")

    cost = contract.get("cost_model") or {}
    for key, expected in (
        ("fee_bps", 10.0),
        ("slippage_bps", 5.0),
        ("half_spread_bps", 5.0),
        ("roundtrip_reference_bps", 30.0),
    ):
        if float(cost.get(key)) != expected:
            raise HoldoutPreregistrationError(f"COST_MISMATCH:{key}")
    if cost.get("fixed") is not True:
        raise HoldoutPreregistrationError("COST_MUST_BE_FIXED")
    if cost.get("cost_drag_fully_included_in_net_metrics") is not True:
        raise HoldoutPreregistrationError("COST_DRAG_MUST_BE_INCLUDED")

    stop = contract.get("stop_and_ledger_semantics") or {}
    if float(stop.get("stop_pct")) != 0.025:
        raise HoldoutPreregistrationError("STOP_PCT_MISMATCH")
    if stop.get("mutation_forbidden") is not True:
        raise HoldoutPreregistrationError("STOP_MUTATION_FORBIDDEN")

    if str(contract.get("primary_decision_metric") or "") != "NET_PROFIT_FACTOR":
        raise HoldoutPreregistrationError("PRIMARY_DECISION_METRIC_MISMATCH")
    metrics = (contract.get("metrics") or {}).get("primary") or []
    if tuple(metrics) != REQUIRED_PRIMARY_METRICS:
        raise HoldoutPreregistrationError("PRIMARY_METRICS_MISMATCH")

    thresholds = contract.get("decision_thresholds") or {}
    if int(thresholds.get("minimum_trade_count") or 0) != 50:
        raise HoldoutPreregistrationError("MINIMUM_TRADE_COUNT_MISMATCH")
    if float(thresholds.get("max_trade_count_reduction_fraction_vs_control")) != 0.5:
        raise HoldoutPreregistrationError("TRADE_REDUCTION_FRACTION_MISMATCH")
    for key in ("pass_requires_all", "fail_if_any", "inconclusive_if_any"):
        if not thresholds.get(key):
            raise HoldoutPreregistrationError(f"THRESHOLD_MISSING:{key}")
    pass_all = " ".join(str(x) for x in (thresholds.get("pass_requires_all") or []))
    if "entry_eligibility_divergence_observed" not in pass_all:
        raise HoldoutPreregistrationError("PASS_MUST_REQUIRE_ENTRY_DIVERGENCE")
    if "net_profit_factor_treatment > net_profit_factor_control" not in pass_all:
        raise HoldoutPreregistrationError("PASS_MUST_REQUIRE_PF_IMPROVEMENT")
    if thresholds.get("inconclusive_never_for_poor_economic_results") is not True:
        raise HoldoutPreregistrationError("INCONCLUSIVE_MUST_EXCLUDE_POOR_ECONOMICS")
    if thresholds.get("on_any_terminal_result_retry_forbidden") is not True:
        raise HoldoutPreregistrationError("TERMINAL_RETRY_MUST_BE_FORBIDDEN")
    if thresholds.get("decision_segment") != "full_sealed_holdout_panel":
        raise HoldoutPreregistrationError("DECISION_SEGMENT_MISMATCH")

    divergence = contract.get("entry_eligibility_divergence_requirement") or {}
    if divergence.get("required") is not True:
        raise HoldoutPreregistrationError("ENTRY_ELIGIBILITY_DIVERGENCE_REQUIRED")
    if divergence.get("if_absent_result_class") != "FAIL":
        raise HoldoutPreregistrationError("DIVERGENCE_ABSENCE_MUST_FAIL")

    expected_split = materialize_holdout_split_definition()
    expected_digest = canonical_json_sha256(expected_split)
    splits = contract.get("splits") or {}
    if splits.get("method") != "SEALED_HOLDOUT_SINGLE_FINAL_AUDIT_PANEL_V1":
        raise HoldoutPreregistrationError("SPLIT_METHOD_MISMATCH")
    if splits.get("split_intervals_sha256") != expected_digest:
        raise HoldoutPreregistrationError("HOLDOUT_SPLIT_DIGEST_MISMATCH")
    if splits.get("holdout_split_definition") != expected_split:
        raise HoldoutPreregistrationError("HOLDOUT_SPLIT_DEFINITION_MISMATCH")
    panel = contract.get("common_panel_bounds") or {}
    if panel.get("start") != REQUIRED_PERIOD_START:
        raise HoldoutPreregistrationError("PANEL_START_MISMATCH")
    if panel.get("end_exclusive") != REQUIRED_PERIOD_END_EXCLUSIVE:
        raise HoldoutPreregistrationError("PANEL_END_MISMATCH")
    if panel.get("content_hash_from_registry") != REQUIRED_CONTENT_HASH:
        raise HoldoutPreregistrationError("CONTENT_HASH_MISMATCH")
    if panel.get("sealed_manifest_sha256_from_registry") != REQUIRED_MANIFEST_SHA:
        raise HoldoutPreregistrationError("MANIFEST_SHA_MISMATCH")
    if int(panel.get("instrument_count_from_registry") or 0) != REQUIRED_INSTRUMENT_COUNT:
        raise HoldoutPreregistrationError("INSTRUMENT_COUNT_MISMATCH")

    terminals = contract.get("terminal_state_transitions") or {}
    for cls in ("PASS", "FAIL", "INCONCLUSIVE", "ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN"):
        entry = terminals.get(cls) or {}
        if entry.get("terminal") is not True:
            raise HoldoutPreregistrationError(f"TERMINAL_FLAG_MISSING:{cls}")
        if int(entry.get("holdout_run_count_after") or 0) != 1:
            raise HoldoutPreregistrationError(f"TERMINAL_RUN_COUNT_AFTER:{cls}")
        if cls != "ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN":
            if entry.get("reopen_forbidden_without_new_hypothesis_id") is not True:
                raise HoldoutPreregistrationError(f"REOPEN_FORBIDDEN_MISSING:{cls}")
            if entry.get("economic_validity_offline_gate_opened") is not False:
                raise HoldoutPreregistrationError(f"ECONOMIC_GATE_MUST_STAY_CLOSED:{cls}")
            if entry.get("promotion_eligible") is not False:
                raise HoldoutPreregistrationError(f"PROMOTION_MUST_STAY_CLOSED:{cls}")

    promo = contract.get("promotion_and_economic_gate_policy") or {}
    if promo.get("promotion_eligible") is not False:
        raise HoldoutPreregistrationError("PROMOTION_MUST_BE_FALSE")
    if promo.get("economic_validity_offline_gate_pass") is not False:
        raise HoldoutPreregistrationError("ECONOMIC_GATE_MUST_REMAIN_CLOSED")
    if promo.get("economic_gate_remains_closed_regardless_of_holdout_result") is not True:
        raise HoldoutPreregistrationError("ECONOMIC_GATE_INVARIANT_MISSING")

    gate = contract.get("execution_gate") or {}
    if gate.get("operator_go_env") != OPERATOR_GO_ENV:
        raise HoldoutPreregistrationError("OPERATOR_GO_ENV_MISMATCH")
    if gate.get("operator_go_required_value") != OPERATOR_GO_REQUIRED_VALUE:
        raise HoldoutPreregistrationError("OPERATOR_GO_VALUE_MISMATCH")

    runtime = contract.get("runtime_policy") or {}
    for key in (
        "runtime_activated",
        "shadow_activated",
        "paper_activated",
        "testnet_activated",
        "live_authorized",
        "orders_allowed",
        "scheduler_authorized",
    ):
        if runtime.get(key) is not False:
            raise HoldoutPreregistrationError(f"RUNTIME_FLAG_MUST_BE_FALSE:{key}")

    declared = contract.get("declared_future_evaluation_targets") or {}
    if declared.get("authorized_in_this_slice") is not False:
        raise HoldoutPreregistrationError("DECLARED_TARGETS_MUST_BE_UNAUTHORIZED")
    if declared.get("runner_rel_path") != DECLARED_RUNNER_REL_PATH:
        raise HoldoutPreregistrationError("DECLARED_RUNNER_MISMATCH")

    evidence = contract.get("expected_evidence_schema") or {}
    if not evidence.get("required_artifacts_after_execution"):
        raise HoldoutPreregistrationError("EVIDENCE_SCHEMA_REQUIRED")
    if not evidence.get("must_record_fields"):
        raise HoldoutPreregistrationError("EVIDENCE_FIELDS_REQUIRED")
    if contract.get("next_canonical_step") != DEFINITION_ONLY_NEXT_CANONICAL_STEP:
        raise HoldoutPreregistrationError("NEXT_CANONICAL_STEP_MISMATCH")

    stored = str(contract.get("holdout_preregistration_digest") or "")
    recomputed = compute_holdout_preregistration_digest(contract)
    if stored != recomputed:
        raise HoldoutPreregistrationError("HOLDOUT_PREREGISTRATION_DIGEST_MISMATCH")
    if stored != EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST:
        raise HoldoutPreregistrationError("HOLDOUT_PREREGISTRATION_DIGEST_DRIFT")

    if acquisition_contract is not None:
        excl = acquisition_contract.get("sealed_holdout_opaque_exclusion") or {}
        if excl.get("evidence_id") != HOLDOUT_OPAQUE_ID:
            raise HoldoutPreregistrationError("ACQ_HOLDOUT_ID_MISMATCH")
        if excl.get("dataset_id_from_registry") != REQUIRED_DATASET_ID:
            raise HoldoutPreregistrationError("ACQ_DATASET_MISMATCH")
        if excl.get("period_start_from_registry") != REQUIRED_PERIOD_START:
            raise HoldoutPreregistrationError("ACQ_START_MISMATCH")
        if excl.get("period_end_from_registry") != REQUIRED_PERIOD_END_EXCLUSIVE:
            raise HoldoutPreregistrationError("ACQ_END_MISMATCH")
        if int(excl.get("instrument_count_from_registry") or 0) != REQUIRED_INSTRUMENT_COUNT:
            raise HoldoutPreregistrationError("ACQ_INSTRUMENT_COUNT_MISMATCH")
        if excl.get("content_inspection_authorized") is not False:
            raise HoldoutPreregistrationError("ACQ_INSPECTION_MUST_BE_FALSE")

    if dataset_split_policy is not None:
        sealed = dataset_split_policy.get("sealed_holdout") or {}
        if sealed.get("dataset_id") != REQUIRED_DATASET_ID:
            raise HoldoutPreregistrationError("POLICY_DATASET_MISMATCH")
        if sealed.get("period_start") != REQUIRED_PERIOD_START:
            raise HoldoutPreregistrationError("POLICY_START_MISMATCH")
        if sealed.get("period_end") != REQUIRED_PERIOD_END_EXCLUSIVE:
            raise HoldoutPreregistrationError("POLICY_END_MISMATCH")
        if sealed.get("content_hash") != REQUIRED_CONTENT_HASH:
            raise HoldoutPreregistrationError("POLICY_CONTENT_HASH_MISMATCH")
        if sealed.get("sealed_manifest_sha256") != REQUIRED_MANIFEST_SHA:
            raise HoldoutPreregistrationError("POLICY_MANIFEST_SHA_MISMATCH")
        if int(sealed.get("instrument_count") or 0) != REQUIRED_INSTRUMENT_COUNT:
            raise HoldoutPreregistrationError("POLICY_INSTRUMENT_COUNT_MISMATCH")
        if sealed.get("role") != "FINAL_AUDIT_ONLY":
            raise HoldoutPreregistrationError("POLICY_ROLE_MISMATCH")

    if bollinger_archive is not None:
        if bollinger_archive.get("dataset_content_hash") != REQUIRED_CONTENT_HASH:
            raise HoldoutPreregistrationError("ARCHIVE_CONTENT_HASH_MISMATCH")
        if bollinger_archive.get("sealed_manifest_sha256") != REQUIRED_MANIFEST_SHA:
            raise HoldoutPreregistrationError("ARCHIVE_MANIFEST_SHA_MISMATCH")
        if bollinger_archive.get("evaluation_period") != (
            f"{REQUIRED_PERIOD_START}..{REQUIRED_PERIOD_END_EXCLUSIVE}"
        ):
            raise HoldoutPreregistrationError("ARCHIVE_PERIOD_MISMATCH")

    if development_contract is not None:
        if development_contract.get("holdout_forbidden") is not True:
            raise HoldoutPreregistrationError("DEV_CONTRACT_HOLDOUT_MUST_REMAIN_FORBIDDEN")
        if development_contract.get("sealed_holdout_content_inspection_authorized") is not False:
            raise HoldoutPreregistrationError("DEV_CONTRACT_INSPECTION_MUST_REMAIN_FALSE")
        promo_dev = development_contract.get("promotion_and_holdout_policy") or {}
        if promo_dev.get("holdout_forbidden_in_this_slice") is not True:
            raise HoldoutPreregistrationError("DEV_CONTRACT_HOLDOUT_IN_SLICE_MUST_REMAIN_TRUE")
        if development_contract.get("hypothesis_id") != REQUIRED_PREDECESSOR_HYPOTHESIS_ID:
            raise HoldoutPreregistrationError("DEV_CONTRACT_HYPOTHESIS_MISMATCH")

    if v1_contract is not None:
        if v1_contract.get("hypothesis_id") != REQUIRED_PREDECESSOR_HYPOTHESIS_ID:
            raise HoldoutPreregistrationError("V1_CONTRACT_HYPOTHESIS_MISMATCH")
        if v1_contract.get("status") != "HOLDOUT_EVALUATION_EXECUTED_TERMINAL":
            raise HoldoutPreregistrationError("V1_MUST_REMAIN_TERMINAL_EXECUTED")
        if int(v1_contract.get("holdout_run_count") or 0) != 1:
            raise HoldoutPreregistrationError("V1_RUN_COUNT_MUST_REMAIN_1")
        if int(v1_contract.get("holdout_run_limit") or 0) != 1:
            raise HoldoutPreregistrationError("V1_RUN_LIMIT_MUST_REMAIN_1")
        if v1_contract.get("terminal_holdout_result_class") != V1_TERMINAL_RESULT_CLASS:
            raise HoldoutPreregistrationError("V1_TERMINAL_RESULT_MUST_BE_PRESERVED")
        if v1_contract.get("holdout_executed") is not True:
            raise HoldoutPreregistrationError("V1_HOLDOUT_EXECUTED_MUST_REMAIN_TRUE")

    return {
        "valid": True,
        "definition_only": True,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "predecessor_hypothesis_id": REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
        "holdout_run_count": 0,
        "holdout_run_limit": 1,
        "holdout_split_digest": expected_digest,
        "holdout_preregistration_digest": stored,
        "execution_authorized": False,
        "new_evaluation_not_rerun": True,
        "primary_decision_metric": "NET_PROFIT_FACTOR",
        "filter_id": REQUIRED_FILTER_ID,
    }


def _validate_terminal_executed_holdout_contract(
    contract: Mapping[str, Any],
    *,
    acquisition_contract: Mapping[str, Any] | None = None,
    dataset_split_policy: Mapping[str, Any] | None = None,
    bollinger_archive: Mapping[str, Any] | None = None,
    development_contract: Mapping[str, Any] | None = None,
    v1_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate post-execution terminal overlays without mutating definition identity."""
    if int(contract.get("holdout_run_count") or 0) != 1:
        raise HoldoutPreregistrationError("HOLDOUT_RUN_COUNT_MUST_BE_1_AFTER_EXECUTION")
    if int(contract.get("holdout_run_limit") or 0) != 1:
        raise HoldoutPreregistrationError("HOLDOUT_RUN_LIMIT_MUST_BE_1")
    if int(contract.get("holdout_runs_allowed") or 0) != 1:
        raise HoldoutPreregistrationError("HOLDOUT_RUNS_ALLOWED_MUST_BE_1")
    if contract.get("holdout_executed") is not True:
        raise HoldoutPreregistrationError("HOLDOUT_EXECUTED_MUST_BE_TRUE")
    result_class = str(contract.get("terminal_holdout_result_class") or "")
    if result_class not in ALLOWED_TERMINAL_RESULT_CLASSES:
        raise HoldoutPreregistrationError("TERMINAL_RESULT_CLASS_INVALID")
    if not str(contract.get("terminal_holdout_reason") or "").strip():
        raise HoldoutPreregistrationError("TERMINAL_REASON_REQUIRED")
    if contract.get("evaluation_evidence_ref") != EVALUATION_EVIDENCE_REL_PATH:
        raise HoldoutPreregistrationError("EVALUATION_EVIDENCE_REF_MISMATCH")
    if contract.get("retry_forbidden") is not True:
        raise HoldoutPreregistrationError("LOCK_REQUIRED:retry_forbidden")
    if contract.get("post_result_tuning_forbidden") is not True:
        raise HoldoutPreregistrationError("LOCK_REQUIRED:post_result_tuning_forbidden")
    if contract.get("reopen_after_terminal_result_forbidden_without_new_hypothesis_id") is not True:
        raise HoldoutPreregistrationError(
            "LOCK_REQUIRED:reopen_after_terminal_result_forbidden_without_new_hypothesis_id"
        )
    if contract.get("hypothesis_id") != REQUIRED_HYPOTHESIS_ID:
        raise HoldoutPreregistrationError("HYPOTHESIS_ID_MISMATCH")
    if contract.get("new_evaluation_not_rerun") is not True:
        raise HoldoutPreregistrationError("NEW_EVALUATION_NOT_RERUN_REQUIRED")
    if contract.get("v1_rerun_forbidden") is not True:
        raise HoldoutPreregistrationError("V1_RERUN_MUST_BE_FORBIDDEN")

    definition_view = definition_body_for_preregistration_digest(contract)
    definition_view["holdout_preregistration_digest"] = contract.get(
        "holdout_preregistration_digest"
    )
    report = validate_holdout_preregistration_contract(
        definition_view,
        acquisition_contract=acquisition_contract,
        dataset_split_policy=dataset_split_policy,
        bollinger_archive=bollinger_archive,
        development_contract=development_contract,
        v1_contract=v1_contract,
    )
    report.update(
        {
            "definition_only": False,
            "holdout_executed": True,
            "holdout_run_count": 1,
            "terminal_holdout_result_class": result_class,
            "terminal_holdout_reason": str(contract.get("terminal_holdout_reason")),
            "evaluation_evidence_ref": EVALUATION_EVIDENCE_REL_PATH,
            "execution_authorized": False,
            "new_evaluation_not_rerun": True,
        }
    )
    return report


def preflight_holdout_execution_gates(contract: Mapping[str, Any]) -> dict[str, Any]:
    stored_digest = str(contract.get("holdout_preregistration_digest") or "")
    if stored_digest != EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST:
        raise HoldoutPreregistrationError("HOLDOUT_PREREGISTRATION_DIGEST_DRIFT")
    split_digest = str((contract.get("splits") or {}).get("split_intervals_sha256") or "")
    if split_digest != EXPECTED_HOLDOUT_SPLIT_DIGEST:
        raise HoldoutPreregistrationError("HOLDOUT_SPLIT_DIGEST_DRIFT")
    assert_holdout_run_not_yet_consumed(contract)
    if int(contract.get("holdout_run_limit") or 0) != 1:
        raise HoldoutPreregistrationError("HOLDOUT_RUN_LIMIT_MUST_BE_1")
    if contract.get("new_evaluation_not_rerun") is not True:
        raise HoldoutPreregistrationError("NEW_EVALUATION_NOT_RERUN_REQUIRED")
    return {
        "holdout_preregistration_digest": stored_digest,
        "holdout_split_digest": split_digest,
        "holdout_run_count_before": int(contract.get("holdout_run_count") or 0),
        "holdout_run_limit": int(contract.get("holdout_run_limit") or 0),
        "gates_passed": True,
    }


def load_and_validate_repo_holdout_contract(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    contract = load_json(root / CONTRACT_REL_PATH)
    acquisition = load_json(root / ACQUISITION_CONTRACT_REL_PATH)
    policy = load_json(root / DATASET_SPLIT_POLICY_REL_PATH)
    archive = load_json(root / BOLLINGER_ARCHIVE_REL_PATH)
    development = load_json(root / DEV_CONTRACT_REL_PATH)
    v1_contract = load_json(root / V1_CONTRACT_REL_PATH)
    return validate_holdout_preregistration_contract(
        contract,
        acquisition_contract=acquisition,
        dataset_split_policy=policy,
        bollinger_archive=archive,
        development_contract=development,
        v1_contract=v1_contract,
    )


__all__ = [
    "CONTRACT_REL_PATH",
    "DECLARED_RUNNER_REL_PATH",
    "EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST",
    "EXPECTED_HOLDOUT_SPLIT_DIGEST",
    "HOLDOUT_OPAQUE_ID",
    "HoldoutPreregistrationError",
    "OPERATOR_GO_ENV",
    "PACKAGE_MARKER",
    "REQUIRED_FROZEN_FILTER_PARAMETERS",
    "REQUIRED_HYPOTHESIS_ID",
    "REQUIRED_PREDECESSOR_HYPOTHESIS_ID",
    "TERMINAL_EXECUTED_STATUS",
    "EVALUATION_EVIDENCE_REL_PATH",
    "assert_execution_go_present",
    "assert_holdout_execution_blocked_by_definition_contract",
    "assert_holdout_run_not_yet_consumed",
    "canonical_json_sha256",
    "compute_holdout_preregistration_digest",
    "definition_body_for_preregistration_digest",
    "expected_holdout_split_digest",
    "load_and_validate_repo_holdout_contract",
    "materialize_holdout_split_definition",
    "preflight_holdout_execution_gates",
    "validate_holdout_preregistration_contract",
]
