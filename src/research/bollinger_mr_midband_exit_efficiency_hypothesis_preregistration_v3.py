"""Definition-only preregistration validator for Bollinger/MR midband exit-efficiency v3.

Research governance only. No backtest, no economic metrics, no runtime policy,
no holdout access, no productive trading-logic mutation.

V3 is a new independently versioned DEVELOPMENT_ONLY measurement ID with
identical economic/definition semantics to V2/V1. V2 remains terminal as
INCONCLUSIVE_INFRASTRUCTURE_FAILURE (run count 1; falsy-zero premeasurement
abort; no panel backtest; no economic metrics) and must not be rerun, reset,
or partially reused. V1 remains terminal and unchanged. Future evaluation
(separate Operator-GO) must bind EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1
and the already-merged panel_runner falsy-zero premeasurement hygiene.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_HYPOTHESIS_PREREGISTRATION_V3=true"
CONTRACT_REL_PATH = (
    "config/research/"
    "bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v3.json"
)
V2_CONTRACT_REL_PATH = (
    "config/research/"
    "bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v2.json"
)
V1_CONTRACT_REL_PATH = (
    "config/research/"
    "bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v1.json"
)
SEAL_REGISTRY_REL_PATH = (
    "config/research/regime_gated_standaside_mr_independent_dev_panel_seal_registry_v1.json"
)
ACQUISITION_CONTRACT_REL_PATH = (
    "config/research/regime_gated_standaside_mr_independent_dev_panel_acquisition_contract_v1.json"
)
OWNER_MAP_REL_PATH = (
    "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"
HOLDOUT_PATH_MARKER = "offline_economic_reevaluation_sealed_long_panel_v1"
REQUIRED_DATASET_CLASS = "DEVELOPMENT_ONLY"
REQUIRED_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V3"
)
REQUIRED_PREDECESSOR_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V2"
)
REQUIRED_V1_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V1"
)
REQUIRED_DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
REQUIRED_TREATMENT_TYPE = "POST_ENTRY_EXIT_EFFICIENCY_MECHANISM"
REQUIRED_MECHANISM_ID = "canonical_bollinger_side_aware_middle_band_exit_v1"
REQUIRED_PREREGISTRATION_STATE = "DEFINITION_ONLY_PREREGISTERED"
REQUIRED_OBSERVABILITY_SURFACE = "EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1"
REQUIRED_RESEARCH_QUESTION = (
    "Given COSTS_DESTROY_MARGINAL_EDGE on the sealed DEVELOPMENT_ONLY Bollinger/MR "
    "baseline (marginal gross PF~1.01, all-SHORT book), does a cost-structure or "
    "holding/exit-efficiency change class exist that preserves gross edge without "
    "retuning terminal entry-eligibility parameters or reopening exhausted filter families?"
)
REQUIRED_FROZEN_EXIT_PARAMETERS = {
    "bb_period": 20,
    "bb_std": 2.0,
    "exit_level": "middle_band",
    "exit_threshold_binding_value": 0.5,
    "long_exit_rule": "close_crosses_middle_from_below_to_at_or_above",
    "short_exit_rule": "close_crosses_middle_from_above_to_at_or_below",
    "stop_loss_remains_active_if_hit_first": True,
}
REQUIRED_PRIMARY_METRICS = (
    "net_profit_factor",
    "net_return",
    "net_pnl",
    "mean_realized_pnl_over_mfe_capture_ratio",
    "mean_mfe_to_exit_leakage",
    "trade_count",
    "turnover",
    "fees",
    "slippage",
)
REQUIRED_PASS_SUBSTRINGS = (
    "net_profit_factor_treatment > net_profit_factor_control",
    "net_pnl_treatment > net_pnl_control",
    "net_return_treatment > net_return_control",
    "mean_realized_pnl_over_mfe_capture_ratio_treatment > "
    "mean_realized_pnl_over_mfe_capture_ratio_control",
    "mean_mfe_to_exit_leakage_treatment < mean_mfe_to_exit_leakage_control",
    "improvement_not_solely_explained_by_reduced_trade_count_or_artificially_lower_turnover == true",
    "no_new_instrument_concentration == true",
    "cost_multiplier_treatment == 1.0",
    "cost_assumption_below_canonical_1x == false",
    "exit_divergence_observed == true",
)
REQUIRED_BASELINE_DIGESTS = {
    "binding_semantic_digest": "8a8fdbf2c24e6a4f40cf465b265f6487aa68a289ab204f008a8825a94752f7c8",
    "config_digest": "cb9873d09e762ae9d3155b64be444cd7d317865645a1c3c14028ba2e0cf44b5a",
    "data_digest": "0083e0502a05667f5b0ca31d374b3bef066f65aacfdb05ee020490cc1f15c638",
    "implementation_digest": "734a94cd4eaa753ff8ade60ebf41a60e116e2c97beade2bc5e8f56e2a6387f33",
}
REQUIRED_PANEL_SEAL = {
    "expected_manifest_sha256": "be953c559ac3dd797961bdda8cbc190076353c91d3299b9031ae1ee767d4b594",
    "expected_content_hash": "4a1978fe0e69a6cd7b19b32f5f95882cfdc3e36397aaec87bce2c4139ab1cfca",
}
REQUIRED_SPLIT_INTERVALS_SHA256 = "a35783bf0268c174dfe585c9839ba45cc6e3835021699786f4490a0d8c9b33db"
REQUIRED_ACQUISITION_SHA256 = "93e60f33eb8d9a62d6f9d98854ae9e934e3caaf3e508dcd87d60e9d80e28a246"
EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST = (
    "d90659b8b2580ef09de2efc5494701d8f8ecee15b5e49425d774f0d1a0e09501"
)
REQUIRED_FALSY_ZERO_HYGIENE_SURFACE = "PANEL_RUNNER_FALSY_ZERO_PREMEASUREMENT_HYGIENE"
V2_TERMINAL_ROOT_CAUSE = "PREMEASUREMENT_GATE_FALSE_POSITIVE_ZERO_OR_SENTINEL"
REQUIRED_DURABLE_DIAGNOSTICS = (
    "phase",
    "last_confirmed_member",
    "heartbeat_progress",
    "exit_code",
    "signal",
    "exception_class_and_truncated_traceback",
    "atomic_lifecycle_checkpoint",
)
DEFINITION_SEMANTICS_KEYS = (
    "research_question",
    "research_question_scope_selected",
    "research_question_scope_excluded",
    "parent_diagnostic_scope_id",
    "parent_diagnostic_class",
    "parent_diagnostic_flags",
    "hypothesis_statement",
    "scientific_hypothesis",
    "economic_hypothesis",
    "primary_decision_metric",
    "primary_decision_metric_contract",
    "dataset_id",
    "dataset_class",
    "holdout_forbidden",
    "sealed_holdout_id",
    "acquisition_contract_id",
    "acquisition_contract_ref",
    "acquisition_contract_sha256",
    "seal_registry_ref",
    "allowed_data_sources",
    "forbidden_data_sources",
    "baseline_config_id",
    "baseline_config_ref",
    "baseline_immutable",
    "baseline_evaluation_ref",
    "baseline_binding_digests",
    "panel_seal",
    "treatment",
    "control_arm",
    "shared_trading_semantics",
    "exit_mechanism",
    "exit_divergence_requirement",
    "pit_and_leakage_rules",
    "evaluation_unit",
    "common_panel_bounds",
    "splits",
    "seeds",
    "cost_model",
    "stop_and_ledger_semantics",
    "metrics",
    "decision_thresholds",
    "promotion_and_holdout_policy",
    "runtime_policy",
)
FORBIDDEN_RESULT_KEYS = frozenset(
    {
        "baseline_metrics",
        "treatment_metrics",
        "measured_net_return",
        "measured_profit_factor",
        "economic_metrics",
        "probe_summary",
    }
)
V2_TERMINAL_STATE = "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
V1_TERMINAL_STATE = "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
TERMINAL_RESULT_CLASSES = ("PASS", "FAIL", "INCONCLUSIVE_INFRASTRUCTURE_FAILURE")
TERMINAL_STATE_PREFIX = "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/"
TERMINAL_STATES_BY_RESULT_CLASS = {
    result_class: f"{TERMINAL_STATE_PREFIX}{result_class}"
    for result_class in TERMINAL_RESULT_CLASSES
}
TERMINAL_SLICE_CLASS = "DEVELOPMENT_EVALUATION_TERMINAL_CLOSEOUT"
FORBIDDEN_PARTIAL_TRANSFER_KEYS = frozenset(
    {
        "baseline_members_completed",
        "treatment_members_completed",
        "partial_baseline_metrics",
        "partial_treatment_metrics",
        "checkpoint_reuse",
        "v1_checkpoint_ref",
        "v1_partial_result_ref",
        "v2_checkpoint_ref",
        "v2_partial_result_ref",
    }
)


class HypothesisPreregistrationError(ValueError):
    """Fail-closed preregistration / split contract error."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _parse_utc(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def _fmt_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _floor_to_hour(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise HypothesisPreregistrationError("JSON_ROOT_MUST_BE_OBJECT")
    return raw


def reject_holdout_dataset_or_path(value: str) -> None:
    text = str(value or "")
    lowered = text.lower()
    if HOLDOUT_PATH_MARKER in lowered:
        raise HypothesisPreregistrationError(f"HOLDOUT_PATH_OR_ID_REJECTED:{text}")
    if "docs/evidence/offline_economic_reevaluation_sealed_long_panel_v1" in lowered:
        raise HypothesisPreregistrationError(f"HOLDOUT_PATH_OR_ID_REJECTED:{text}")


def materialize_chronological_splits(
    *,
    panel_start: str,
    panel_end_exclusive: str,
    train_share: float = 0.6,
    validation_share: float = 0.2,
    final_share: float = 0.2,
    max_feature_lookback_hours: int = 20,
    max_holding_horizon_hours: int = 48,
) -> dict[str, Any]:
    if abs((train_share + validation_share + final_share) - 1.0) > 1e-12:
        raise HypothesisPreregistrationError("SPLIT_SHARES_MUST_SUM_TO_ONE")
    start = _parse_utc(panel_start)
    end = _parse_utc(panel_end_exclusive)
    if end <= start:
        raise HypothesisPreregistrationError("PANEL_BOUNDS_INVALID")
    total = end - start
    train_end = _floor_to_hour(start + total * train_share)
    val_end = _floor_to_hour(start + total * (train_share + validation_share))
    if not (start < train_end < val_end < end):
        raise HypothesisPreregistrationError("SPLIT_BOUNDS_NOT_STRICTLY_ORDERED")

    intervals = {
        "train_definition": {
            "start": _fmt_utc(start),
            "end_exclusive": _fmt_utc(train_end),
        },
        "validation": {
            "start": _fmt_utc(train_end),
            "end_exclusive": _fmt_utc(val_end),
        },
        "final_development_confirmation": {
            "start": _fmt_utc(val_end),
            "end_exclusive": _fmt_utc(end),
        },
    }
    if intervals["validation"]["start"] != intervals["train_definition"]["end_exclusive"]:
        raise HypothesisPreregistrationError("TRAIN_VALIDATION_GAP_OR_OVERLAP")
    if (
        intervals["final_development_confirmation"]["start"]
        != intervals["validation"]["end_exclusive"]
    ):
        raise HypothesisPreregistrationError("VALIDATION_FINAL_GAP_OR_OVERLAP")

    embargo = timedelta(hours=int(max_feature_lookback_hours))
    purge = timedelta(hours=int(max_feature_lookback_hours + max_holding_horizon_hours))
    return {
        **intervals,
        "method": "CHRONOLOGICAL_60_20_20_FLOOR_HOUR",
        "split_intervals_sha256": canonical_json_sha256(intervals),
        "max_feature_lookback_hours": int(max_feature_lookback_hours),
        "max_holding_horizon_hours": int(max_holding_horizon_hours),
        "embargo_hours": int(max_feature_lookback_hours),
        "purge_hours": int(max_feature_lookback_hours + max_holding_horizon_hours),
        "embargo_duration": f"PT{int(max_feature_lookback_hours)}H",
        "purge_duration": f"PT{int(max_feature_lookback_hours + max_holding_horizon_hours)}H",
        "validation_feature_eligible_from": _fmt_utc(train_end + embargo),
        "validation_label_eligible_from": _fmt_utc(train_end + purge),
        "final_feature_eligible_from": _fmt_utc(val_end + embargo),
        "final_label_eligible_from": _fmt_utc(val_end + purge),
    }


def _contains_banned_result_keys(obj: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            key_path = f"{path}.{key}"
            if key in FORBIDDEN_RESULT_KEYS:
                found.append(key_path)
            found.extend(_contains_banned_result_keys(value, key_path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            found.extend(_contains_banned_result_keys(item, f"{path}[{idx}]"))
    return found


def definition_body_for_preregistration_digest(contract: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in contract.items() if k != "development_preregistration_digest"}


def compute_development_preregistration_digest(contract: Mapping[str, Any]) -> str:
    return canonical_json_sha256(definition_body_for_preregistration_digest(contract))


def assert_definition_semantics_identical_to_predecessor(
    v3_contract: Mapping[str, Any],
    predecessor_contract: Mapping[str, Any],
) -> None:
    for key in DEFINITION_SEMANTICS_KEYS:
        if v3_contract.get(key) != predecessor_contract.get(key):
            raise HypothesisPreregistrationError(f"DEFINITION_SEMANTICS_DRIFT:{key}")


def assert_v2_terminal_preserved(v2_contract: Mapping[str, Any]) -> None:
    if v2_contract.get("hypothesis_id") != REQUIRED_PREDECESSOR_HYPOTHESIS_ID:
        raise HypothesisPreregistrationError("V2_HYPOTHESIS_ID_MISMATCH")
    if v2_contract.get("status") != V2_TERMINAL_STATE:
        raise HypothesisPreregistrationError("V2_STATUS_MUST_REMAIN_TERMINAL")
    if v2_contract.get("preregistration_state") != V2_TERMINAL_STATE:
        raise HypothesisPreregistrationError("V2_PREREGISTRATION_STATE_MUST_REMAIN_TERMINAL")
    if int(v2_contract.get("evaluation_run_count", -1)) != 1:
        raise HypothesisPreregistrationError("V2_EVALUATION_RUN_COUNT_MUST_REMAIN_1")
    if v2_contract.get("result_class") != "INCONCLUSIVE_INFRASTRUCTURE_FAILURE":
        raise HypothesisPreregistrationError("V2_RESULT_CLASS_MUST_REMAIN_INCONCLUSIVE")
    if v2_contract.get("economic_verdict") != "NOT_EVALUATED":
        raise HypothesisPreregistrationError("V2_ECONOMIC_VERDICT_MUST_REMAIN_NOT_EVALUATED")
    if v2_contract.get("rerun_allowed") is not False:
        raise HypothesisPreregistrationError("V2_RERUN_MUST_REMAIN_FORBIDDEN")
    if v2_contract.get("evaluation_started") is not True:
        raise HypothesisPreregistrationError("V2_EVALUATION_STARTED_MUST_REMAIN_TRUE")
    if v2_contract.get("evaluation_completed") is not False:
        raise HypothesisPreregistrationError("V2_EVALUATION_COMPLETED_MUST_REMAIN_FALSE")


def assert_v1_terminal_preserved(v1_contract: Mapping[str, Any]) -> None:
    if v1_contract.get("hypothesis_id") != REQUIRED_V1_HYPOTHESIS_ID:
        raise HypothesisPreregistrationError("V1_HYPOTHESIS_ID_MISMATCH")
    if v1_contract.get("status") != V1_TERMINAL_STATE:
        raise HypothesisPreregistrationError("V1_STATUS_MUST_REMAIN_TERMINAL")
    if int(v1_contract.get("evaluation_run_count", -1)) != 1:
        raise HypothesisPreregistrationError("V1_EVALUATION_RUN_COUNT_MUST_REMAIN_1")
    if v1_contract.get("result_class") != "INCONCLUSIVE_INFRASTRUCTURE_FAILURE":
        raise HypothesisPreregistrationError("V1_RESULT_CLASS_MUST_REMAIN_INCONCLUSIVE")
    if v1_contract.get("rerun_allowed") is not False:
        raise HypothesisPreregistrationError("V1_RERUN_MUST_REMAIN_FORBIDDEN")


def _terminal_result_class_for_status(status: Any) -> str | None:
    """Return the terminal result class if ``status`` names an authorized terminal state."""
    for result_class, state in TERMINAL_STATES_BY_RESULT_CLASS.items():
        if status == state:
            return result_class
    return None


def validate_preregistration_contract(
    contract: Mapping[str, Any],
    *,
    v2_contract: Mapping[str, Any] | None = None,
    v1_contract: Mapping[str, Any] | None = None,
    seal_registry: Mapping[str, Any] | None = None,
    acquisition_sha256: str | None = None,
    owner_map: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    # Dual-mode: DEFINITION_ONLY_PREREGISTERED (current, pre-run) or a terminal
    # closeout after exactly one development evaluation run (PASS / FAIL /
    # INCONCLUSIVE_INFRASTRUCTURE_FAILURE), mirroring the v1 terminal branch.
    terminal_result_class = _terminal_result_class_for_status(contract.get("status"))
    if terminal_result_class is not None:
        if contract.get("slice_class") != TERMINAL_SLICE_CLASS:
            raise HypothesisPreregistrationError("SLICE_MUST_BE_TERMINAL_CLOSEOUT")
        if contract.get("preregistration_state") != contract.get("status"):
            raise HypothesisPreregistrationError("PREREGISTRATION_STATE_MISMATCH")
        if contract.get("evaluation_authorized") is not False:
            raise HypothesisPreregistrationError("EVALUATION_MUST_BE_UNAUTHORIZED")
        if contract.get("backtest_authorized") is not False:
            raise HypothesisPreregistrationError("BACKTEST_MUST_BE_UNAUTHORIZED")
        if contract.get("implementation_authorized") is not False:
            raise HypothesisPreregistrationError("IMPLEMENTATION_MUST_BE_UNAUTHORIZED")
        if contract.get("evaluation_executed") is not True:
            raise HypothesisPreregistrationError("EVALUATION_EXECUTED_MUST_BE_TRUE")
        if contract.get("evaluation_started") is not True:
            raise HypothesisPreregistrationError("EVALUATION_STARTED_MUST_BE_TRUE")
        evaluation_completed_expected = (
            terminal_result_class != "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
        )
        if contract.get("evaluation_completed") is not evaluation_completed_expected:
            raise HypothesisPreregistrationError("EVALUATION_COMPLETED_MISMATCH")
        if int(contract.get("evaluation_run_count", -1)) != 1:
            raise HypothesisPreregistrationError("EVALUATION_RUN_COUNT_MUST_BE_1")
        if contract.get("result_class") != terminal_result_class:
            raise HypothesisPreregistrationError("RESULT_CLASS_MISMATCH")
        economic_verdict_expected = (
            "NOT_EVALUATED"
            if terminal_result_class == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
            else terminal_result_class
        )
        if contract.get("economic_verdict") != economic_verdict_expected:
            raise HypothesisPreregistrationError("ECONOMIC_VERDICT_MISMATCH")
        pass_expected = terminal_result_class == "PASS"
        fail_expected = terminal_result_class == "FAIL"
        if contract.get("pass") is not pass_expected:
            raise HypothesisPreregistrationError("PASS_FLAG_MISMATCH")
        if contract.get("fail") is not fail_expected:
            raise HypothesisPreregistrationError("FAIL_FLAG_MISMATCH")
        # One-shot: terminal closeout consumes the sole run slot; no rerun ever.
        if contract.get("rerun_allowed") is not False:
            raise HypothesisPreregistrationError("RERUN_MUST_REMAIN_FORBIDDEN")
        if contract.get("holdout_data_accessed") is not False:
            raise HypothesisPreregistrationError("HOLDOUT_DATA_ACCESSED_MUST_BE_FALSE")
    else:
        if contract.get("slice_class") != "DEFINITION_ONLY":
            raise HypothesisPreregistrationError("SLICE_MUST_BE_DEFINITION_ONLY")
        if contract.get("preregistration_state") != REQUIRED_PREREGISTRATION_STATE:
            raise HypothesisPreregistrationError("PREREGISTRATION_STATE_MISMATCH")
        if contract.get("status") != REQUIRED_PREREGISTRATION_STATE:
            raise HypothesisPreregistrationError("STATUS_MUST_BE_DEFINITION_ONLY_PREREGISTERED")
        if contract.get("evaluation_authorized") is not False:
            raise HypothesisPreregistrationError("EVALUATION_MUST_BE_UNAUTHORIZED")
        if contract.get("backtest_authorized") is not False:
            raise HypothesisPreregistrationError("BACKTEST_MUST_BE_UNAUTHORIZED")
        if contract.get("implementation_authorized") is not False:
            raise HypothesisPreregistrationError("IMPLEMENTATION_MUST_BE_UNAUTHORIZED")
        if contract.get("evaluation_executed") is not False:
            raise HypothesisPreregistrationError("EVALUATION_EXECUTED_MUST_BE_FALSE")
        if contract.get("evaluation_started") is not False:
            raise HypothesisPreregistrationError("EVALUATION_STARTED_MUST_BE_FALSE")
        if contract.get("evaluation_completed") is not False:
            raise HypothesisPreregistrationError("EVALUATION_COMPLETED_MUST_BE_FALSE")
        if int(contract.get("evaluation_run_count", -1)) != 0:
            raise HypothesisPreregistrationError("EVALUATION_RUN_COUNT_MUST_BE_0")
        if contract.get("result_class") != "NOT_EVALUATED":
            raise HypothesisPreregistrationError("RESULT_CLASS_MUST_BE_NOT_EVALUATED")
        if contract.get("economic_verdict") != "NOT_EVALUATED":
            raise HypothesisPreregistrationError("ECONOMIC_VERDICT_MUST_BE_NOT_EVALUATED")
        if contract.get("pass") is not False or contract.get("fail") is not False:
            raise HypothesisPreregistrationError("PASS_FAIL_MUST_BE_FALSE")
        # One-shot: first evaluation still available via separate GO; no second/rerun slot.
        if contract.get("rerun_allowed") is not False:
            raise HypothesisPreregistrationError("RERUN_MUST_BE_FORBIDDEN_UNDER_ONE_SHOT")
        if contract.get("holdout_data_accessed") is not False:
            raise HypothesisPreregistrationError("HOLDOUT_DATA_ACCESSED_MUST_BE_FALSE")
    if int(contract.get("hypothesis_count") or 0) != 1:
        raise HypothesisPreregistrationError("HYPOTHESIS_COUNT_MUST_BE_1")
    if int(contract.get("multiple_testing_budget") or 0) != 1:
        raise HypothesisPreregistrationError("MULTIPLE_TESTING_BUDGET_MUST_BE_1")
    if int(contract.get("evaluation_run_count_authorized") or 0) != 1:
        raise HypothesisPreregistrationError("EVALUATION_RUN_COUNT_AUTHORIZED_MUST_BE_1")
    if int(contract.get("development_evaluation_runs_allowed") or 0) != 1:
        raise HypothesisPreregistrationError("DEVELOPMENT_RUNS_ALLOWED_MUST_BE_1")
    if contract.get("development_only") is not True:
        raise HypothesisPreregistrationError("DEVELOPMENT_ONLY_REQUIRED")
    if contract.get("holdout_allowed") is not False:
        raise HypothesisPreregistrationError("HOLDOUT_ALLOWED_MUST_BE_FALSE")
    for flag in (
        "optimization_forbidden",
        "variants_forbidden",
        "parameter_sweeps_forbidden",
        "parameter_grid_forbidden",
        "best_of_forbidden",
        "post_hoc_threshold_adjustment_forbidden",
        "post_hoc_result_based_selection_forbidden",
        "repeat_after_result_inspection_forbidden",
        "new_evaluation_not_rerun",
        "v1_rerun_forbidden",
        "v2_rerun_forbidden",
        "identical_measurement_rules_to_development_v1",
        "identical_measurement_rules_to_development_v2",
    ):
        if contract.get(flag) is not True:
            raise HypothesisPreregistrationError(f"{flag.upper()}_REQUIRED")
    if contract.get("hypothesis_id") != REQUIRED_HYPOTHESIS_ID:
        raise HypothesisPreregistrationError("HYPOTHESIS_ID_MISMATCH")
    if contract.get("hypothesis_id") == REQUIRED_PREDECESSOR_HYPOTHESIS_ID:
        raise HypothesisPreregistrationError("HYPOTHESIS_ID_MUST_NOT_EQUAL_V2")
    if contract.get("hypothesis_id") == REQUIRED_V1_HYPOTHESIS_ID:
        raise HypothesisPreregistrationError("HYPOTHESIS_ID_MUST_NOT_EQUAL_V1")
    if contract.get("research_question") != REQUIRED_RESEARCH_QUESTION:
        raise HypothesisPreregistrationError("RESEARCH_QUESTION_MISMATCH")
    if contract.get("research_question_scope_selected") != "EXIT_EFFICIENCY_ONLY":
        raise HypothesisPreregistrationError("SCOPE_MUST_BE_EXIT_EFFICIENCY_ONLY")
    if contract.get("dataset_id") != REQUIRED_DATASET_ID:
        raise HypothesisPreregistrationError("DATASET_ID_MISMATCH")
    if contract.get("dataset_class") != REQUIRED_DATASET_CLASS:
        raise HypothesisPreregistrationError("DATASET_CLASS_MUST_BE_DEVELOPMENT_ONLY")
    if contract.get("holdout_forbidden") is not True:
        raise HypothesisPreregistrationError("HOLDOUT_FORBIDDEN_REQUIRED")
    if contract.get("sealed_holdout_id") != HOLDOUT_OPAQUE_ID:
        raise HypothesisPreregistrationError("SEALED_HOLDOUT_ID_MISMATCH")
    if contract.get("sealed_holdout_content_inspection_authorized") is not False:
        raise HypothesisPreregistrationError("HOLDOUT_INSPECTION_MUST_BE_FALSE")
    if contract.get("short_side_hypothesis_preregistered") is not False:
        raise HypothesisPreregistrationError("SHORT_SIDE_HYPOTHESIS_FORBIDDEN")
    if contract.get("holdout_candidate_preregistered") is not False:
        raise HypothesisPreregistrationError("HOLDOUT_CANDIDATE_FORBIDDEN")
    if contract.get("competing_open_hypotheses_forbidden") is not True:
        raise HypothesisPreregistrationError("COMPETING_OPEN_HYPOTHESES_MUST_BE_FORBIDDEN")
    if int(contract.get("competing_open_hypothesis_count_allowed", -1)) != 0:
        raise HypothesisPreregistrationError("COMPETING_OPEN_COUNT_MUST_BE_0")

    for banned_key in FORBIDDEN_PARTIAL_TRANSFER_KEYS:
        if banned_key in contract:
            raise HypothesisPreregistrationError(f"PARTIAL_TRANSFER_FORBIDDEN:{banned_key}")

    reject_holdout_dataset_or_path(str(contract.get("dataset_id")))
    for src in contract.get("allowed_data_sources") or []:
        reject_holdout_dataset_or_path(str(src))

    banned = _contains_banned_result_keys(contract)
    if banned:
        raise HypothesisPreregistrationError(f"EMBEDDED_RESULT_METRICS:{','.join(banned[:8])}")

    if contract.get("baseline_config_id") != (
        "bollinger_bands_v2_full_canonical_system_economic_binding_v1"
    ):
        raise HypothesisPreregistrationError("BASELINE_CONFIG_ID_MISMATCH")
    if contract.get("baseline_immutable") is not True:
        raise HypothesisPreregistrationError("BASELINE_MUST_BE_IMMUTABLE")

    digests = contract.get("baseline_binding_digests") or {}
    if not isinstance(digests, Mapping):
        raise HypothesisPreregistrationError("BASELINE_DIGESTS_REQUIRED")
    for key, expected in REQUIRED_BASELINE_DIGESTS.items():
        if digests.get(key) != expected:
            raise HypothesisPreregistrationError(f"BASELINE_DIGEST_MISMATCH:{key}")

    panel_seal = contract.get("panel_seal") or {}
    if not isinstance(panel_seal, Mapping):
        raise HypothesisPreregistrationError("PANEL_SEAL_REQUIRED")
    for key, expected in REQUIRED_PANEL_SEAL.items():
        if panel_seal.get(key) != expected:
            raise HypothesisPreregistrationError(f"PANEL_SEAL_MISMATCH:{key}")

    if acquisition_sha256 is not None:
        if contract.get("acquisition_contract_sha256") != acquisition_sha256:
            raise HypothesisPreregistrationError("ACQUISITION_SHA256_MISMATCH")
    elif contract.get("acquisition_contract_sha256") != REQUIRED_ACQUISITION_SHA256:
        raise HypothesisPreregistrationError("ACQUISITION_SHA256_MISMATCH")

    treatment = contract.get("treatment") or {}
    if not isinstance(treatment, dict):
        raise HypothesisPreregistrationError("TREATMENT_REQUIRED")
    if treatment.get("treatment_type") != REQUIRED_TREATMENT_TYPE:
        raise HypothesisPreregistrationError("TREATMENT_TYPE_INVALID")
    if int(treatment.get("treatment_count") or 0) != 1:
        raise HypothesisPreregistrationError("TREATMENT_COUNT_MUST_BE_1")
    if treatment.get("acts_after_entry_fill_only") is not True:
        raise HypothesisPreregistrationError("MUST_ACT_AFTER_ENTRY_FILL_ONLY")
    if treatment.get("acts_before_entry_decision") is not False:
        raise HypothesisPreregistrationError("MUST_NOT_ACT_BEFORE_ENTRY")
    if treatment.get("reporting_or_attribution_only") is not False:
        raise HypothesisPreregistrationError("REPORTING_ONLY_GATE_FORBIDDEN")
    for key in (
        "no_new_direction_authority",
        "no_new_entry_authority",
        "no_new_side_selection_authority",
        "no_new_switch_authority",
        "no_new_risk_authority",
        "no_new_sizing_authority",
        "no_new_execution_authority",
    ):
        if treatment.get(key) is not True:
            raise HypothesisPreregistrationError(f"{key.upper()}_REQUIRED")
    if treatment.get("runtime_implementation_in_this_slice") is not False:
        raise HypothesisPreregistrationError("RUNTIME_IMPLEMENTATION_FORBIDDEN_IN_SLICE")

    shared = contract.get("shared_trading_semantics") or {}
    if shared.get("identical_except_exit_mechanism") is not True:
        raise HypothesisPreregistrationError("SHARED_SEMANTICS_MUST_MATCH_EXCEPT_EXIT")
    if shared.get("entry_eligibility_unchanged") is not True:
        raise HypothesisPreregistrationError("ENTRY_ELIGIBILITY_MUST_BE_UNCHANGED")
    if shared.get("master_v2_and_double_play_sole_direction_authority") is not True:
        raise HypothesisPreregistrationError("MASTER_V2_DOUBLE_PLAY_SOLE_AUTHORITY_REQUIRED")
    if shared.get("production_strategy_semantics_unchanged") is not True:
        raise HypothesisPreregistrationError("PRODUCTION_STRATEGY_SEMANTICS_CHANGED")
    if shared.get("double_play_authority_unchanged") is not True:
        raise HypothesisPreregistrationError("DOUBLE_PLAY_AUTHORITY_CHANGED")
    if shared.get("risk_sizing_execution_semantics_unchanged") is not True:
        raise HypothesisPreregistrationError("RISK_SIZING_EXECUTION_SEMANTICS_CHANGED")

    mechanism = contract.get("exit_mechanism") or {}
    if not isinstance(mechanism, dict):
        raise HypothesisPreregistrationError("EXIT_MECHANISM_REQUIRED")
    if mechanism.get("mechanism_id") != REQUIRED_MECHANISM_ID:
        raise HypothesisPreregistrationError("MECHANISM_ID_MISMATCH")
    if mechanism.get("mechanism_class") != "EXIT_EFFICIENCY":
        raise HypothesisPreregistrationError("MECHANISM_CLASS_MUST_BE_EXIT_EFFICIENCY")
    if mechanism.get("lookahead_forbidden") is not True:
        raise HypothesisPreregistrationError("LOOKAHEAD_MUST_BE_FORBIDDEN")
    if mechanism.get("future_mfe_forbidden") is not True:
        raise HypothesisPreregistrationError("FUTURE_MFE_MUST_BE_FORBIDDEN")
    if mechanism.get("fail_closed_if_missing_state_or_index_or_digest_binding") is not True:
        raise HypothesisPreregistrationError("FAIL_CLOSED_STATE_BINDING_REQUIRED")
    frozen = mechanism.get("frozen_parameters") or {}
    for key, expected in REQUIRED_FROZEN_EXIT_PARAMETERS.items():
        if frozen.get(key) != expected:
            raise HypothesisPreregistrationError(f"EXIT_PARAMETER_MISMATCH:{key}")
    if mechanism.get("direction_or_side_effect") != "NONE":
        raise HypothesisPreregistrationError("DIRECTION_OR_SIDE_EFFECT_FORBIDDEN")
    if mechanism.get("entry_effect") != "NONE":
        raise HypothesisPreregistrationError("ENTRY_EFFECT_FORBIDDEN")
    if mechanism.get("instrument_selection_effect") != "NONE":
        raise HypothesisPreregistrationError("INSTRUMENT_SELECTION_EFFECT_FORBIDDEN")
    if mechanism.get("cost_model_effect") != "NONE":
        raise HypothesisPreregistrationError("COST_MODEL_EFFECT_FORBIDDEN")

    divergence = contract.get("exit_divergence_requirement") or {}
    if divergence.get("required") is not True:
        raise HypothesisPreregistrationError("EXIT_DIVERGENCE_REQUIRED")
    if divergence.get("if_absent_result_class") != "FAIL":
        raise HypothesisPreregistrationError("DIVERGENCE_ABSENCE_MUST_FAIL")

    cost = contract.get("cost_model") or {}
    for key in ("fee_bps", "slippage_bps", "half_spread_bps", "roundtrip_reference_bps"):
        if key not in cost or cost[key] is None:
            raise HypothesisPreregistrationError(f"COST_MODEL_MISSING:{key}")
    if float(cost.get("fee_bps")) != 10.0:
        raise HypothesisPreregistrationError("FEE_BPS_MUST_MATCH_CANONICAL")
    if float(cost.get("slippage_bps")) != 5.0:
        raise HypothesisPreregistrationError("SLIPPAGE_BPS_MUST_MATCH_CANONICAL")
    if float(cost.get("half_spread_bps")) != 5.0:
        raise HypothesisPreregistrationError("HALF_SPREAD_BPS_MUST_MATCH_CANONICAL")
    if float(cost.get("cost_multiplier")) != 1.0:
        raise HypothesisPreregistrationError("COST_MULTIPLIER_MUST_BE_1X")
    if float(cost.get("canonical_cost_multiplier_minimum")) != 1.0:
        raise HypothesisPreregistrationError("CANONICAL_COST_MINIMUM_MUST_BE_1X")
    if cost.get("cost_assumption_below_canonical_1x_forbidden") is not True:
        raise HypothesisPreregistrationError("COST_BELOW_1X_MUST_BE_FORBIDDEN")
    if cost.get("fixed") is not True:
        raise HypothesisPreregistrationError("COST_MODEL_MUST_BE_FIXED")
    if cost.get("cost_drag_fully_included_in_net_metrics") is not True:
        raise HypothesisPreregistrationError("COST_DRAG_MUST_BE_INCLUDED")

    metrics = contract.get("metrics") or {}
    primary = metrics.get("primary") or []
    if list(primary) != list(REQUIRED_PRIMARY_METRICS):
        raise HypothesisPreregistrationError("PRIMARY_METRICS_MISMATCH")
    guardrails = set(metrics.get("guardrails") or [])
    for required_guard in (
        "long_short_attribution",
        "instrument_attribution",
        "instrument_concentration",
        "cost_multiplier",
    ):
        if required_guard not in guardrails:
            raise HypothesisPreregistrationError(f"GUARDRAIL_MISSING:{required_guard}")

    thresholds = contract.get("decision_thresholds") or {}
    if thresholds.get("pass_criteria_frozen") is not True:
        raise HypothesisPreregistrationError("PASS_CRITERIA_MUST_BE_FROZEN")
    pass_requires = [str(x) for x in (thresholds.get("pass_requires_all") or [])]
    for required in REQUIRED_PASS_SUBSTRINGS:
        if not any(required in item for item in pass_requires):
            raise HypothesisPreregistrationError(f"PASS_MUST_REQUIRE:{required}")

    promo = contract.get("promotion_and_holdout_policy") or {}
    if promo.get("economic_validity_offline_gate_pass") is not False:
        raise HypothesisPreregistrationError("ECONOMIC_GATE_MUST_BE_CLOSED")
    if promo.get("economic_gate_open") is not False:
        raise HypothesisPreregistrationError("ECONOMIC_GATE_OPEN_FORBIDDEN")
    if promo.get("promotion_eligible") is not False:
        raise HypothesisPreregistrationError("PROMOTION_MUST_BE_CLOSED")
    if promo.get("promotion_gate_open") is not False:
        raise HypothesisPreregistrationError("PROMOTION_GATE_OPEN_FORBIDDEN")
    if promo.get("holdout_preregistered") is not False:
        raise HypothesisPreregistrationError("HOLDOUT_PREREGISTERED_FORBIDDEN")

    runtime = contract.get("runtime_policy") or {}
    for key in (
        "runtime_activated",
        "shadow_activated",
        "testnet_activated",
        "live_authorized",
        "orders_allowed",
        "scheduler_authorized",
        "capital_activated",
    ):
        if runtime.get(key) is not False:
            raise HypothesisPreregistrationError(f"RUNTIME_UNLOCKED:{key}")

    splits = contract.get("splits") or {}
    if not isinstance(splits, Mapping):
        raise HypothesisPreregistrationError("SPLITS_REQUIRED")
    panel = contract.get("common_panel_bounds") or {}
    expected_splits = materialize_chronological_splits(
        panel_start=str(panel.get("start")),
        panel_end_exclusive=str(panel.get("end_exclusive")),
        max_feature_lookback_hours=int(splits.get("max_feature_lookback_hours") or 20),
        max_holding_horizon_hours=int(splits.get("max_holding_horizon_hours") or 48),
    )
    if splits.get("split_intervals_sha256") != REQUIRED_SPLIT_INTERVALS_SHA256:
        raise HypothesisPreregistrationError("SPLIT_DIGEST_MISMATCH")
    if expected_splits["split_intervals_sha256"] != splits.get("split_intervals_sha256"):
        raise HypothesisPreregistrationError("SPLIT_DIGEST_RECOMPUTE_MISMATCH")
    for key in (
        "train_definition",
        "validation",
        "final_development_confirmation",
        "validation_feature_eligible_from",
        "validation_label_eligible_from",
        "final_feature_eligible_from",
        "final_label_eligible_from",
    ):
        if splits.get(key) != expected_splits.get(key):
            raise HypothesisPreregistrationError(f"SPLIT_FIELD_MISMATCH:{key}")

    if seal_registry is not None:
        seal_panel = seal_registry.get("panel") or {}
        if seal_panel.get("common_panel_start") != panel.get("start"):
            raise HypothesisPreregistrationError("SEAL_PANEL_START_MISMATCH")
        if seal_panel.get("common_panel_end") != panel.get("end_exclusive"):
            raise HypothesisPreregistrationError("SEAL_PANEL_END_MISMATCH")
        hashes = seal_registry.get("hashes") or {}
        if hashes.get("sealed_lifecycle_manifest_sha256") != panel_seal.get(
            "expected_manifest_sha256"
        ):
            raise HypothesisPreregistrationError("SEAL_MANIFEST_MISMATCH")
        if hashes.get("sealed_lifecycle_content_hash") != panel_seal.get("expected_content_hash"):
            raise HypothesisPreregistrationError("SEAL_CONTENT_HASH_MISMATCH")
        if seal_registry.get("dataset_id") != REQUIRED_DATASET_ID:
            raise HypothesisPreregistrationError("SEAL_DATASET_MISMATCH")

    terminal_states = set(contract.get("terminal_states_authorized") or [])
    for required_state in (
        "DEFINITION_ONLY_PREREGISTERED",
        "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/PASS",
        "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL",
        "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/INCONCLUSIVE_INFRASTRUCTURE_FAILURE",
    ):
        if required_state not in terminal_states:
            raise HypothesisPreregistrationError(f"TERMINAL_STATE_MISSING:{required_state}")

    pred = contract.get("predecessor_development_v2")
    if not isinstance(pred, Mapping):
        raise HypothesisPreregistrationError("PREDECESSOR_V2_REQUIRED")
    if pred.get("hypothesis_id") != REQUIRED_PREDECESSOR_HYPOTHESIS_ID:
        raise HypothesisPreregistrationError("PREDECESSOR_ID_MISMATCH")
    if pred.get("terminal_preserved") is not True:
        raise HypothesisPreregistrationError("PREDECESSOR_TERMINAL_PRESERVED_REQUIRED")
    if pred.get("rerun_forbidden") is not True:
        raise HypothesisPreregistrationError("PREDECESSOR_RERUN_FORBIDDEN_REQUIRED")
    if pred.get("result_class") != "INCONCLUSIVE_INFRASTRUCTURE_FAILURE":
        raise HypothesisPreregistrationError("PREDECESSOR_RESULT_CLASS_MISMATCH")
    if int(pred.get("evaluation_run_count", -1)) != 1:
        raise HypothesisPreregistrationError("PREDECESSOR_RUN_COUNT_MUST_BE_1")
    if pred.get("partial_results_reused") is not False:
        raise HypothesisPreregistrationError("PREDECESSOR_PARTIAL_REUSE_MUST_BE_FALSE")
    if pred.get("process_death_root_cause") != V2_TERMINAL_ROOT_CAUSE:
        raise HypothesisPreregistrationError("PREDECESSOR_ROOT_CAUSE_MISMATCH")
    if pred.get("panel_backtest_executed") is not False:
        raise HypothesisPreregistrationError("PREDECESSOR_PANEL_BACKTEST_MUST_BE_FALSE")
    if pred.get("economic_metrics_produced") is not False:
        raise HypothesisPreregistrationError("PREDECESSOR_ECONOMIC_METRICS_MUST_BE_FALSE")

    life = contract.get("lifecycle_contract")
    if not isinstance(life, Mapping):
        raise HypothesisPreregistrationError("LIFECYCLE_CONTRACT_REQUIRED")
    for key in (
        "one_run_only",
        "runner_start_persistence_required",
        "terminal_state_persistence_required",
        "no_rerun_after_runner_start",
        "infrastructure_failure_distinct_from_economic_failure",
        "auto_resume_forbidden",
        "auto_rerun_on_infrastructure_failure_forbidden",
    ):
        if life.get(key) is not True:
            raise HypothesisPreregistrationError(f"LIFECYCLE_{key.upper()}_REQUIRED")
    if int(life.get("evaluation_run_count_authorized", -1)) != 1:
        raise HypothesisPreregistrationError("LIFECYCLE_RUN_COUNT_AUTHORIZED_MUST_BE_1")
    if life.get("infrastructure_failure_result_class") != ("INCONCLUSIVE_INFRASTRUCTURE_FAILURE"):
        raise HypothesisPreregistrationError("LIFECYCLE_INFRA_RESULT_CLASS_MISMATCH")
    if life.get("infrastructure_failure_economic_verdict") != "NOT_EVALUATED":
        raise HypothesisPreregistrationError("LIFECYCLE_INFRA_ECONOMIC_VERDICT_MISMATCH")
    if life.get("economic_failure_result_class") != "FAIL":
        raise HypothesisPreregistrationError("LIFECYCLE_ECONOMIC_FAIL_CLASS_MISMATCH")

    infra = contract.get("infrastructure_bindings") or {}
    obs = infra.get("evaluation_runner_lifecycle_observability_v1")
    if not isinstance(obs, Mapping):
        raise HypothesisPreregistrationError("OBSERVABILITY_BINDING_REQUIRED")
    if obs.get("surface_id") != REQUIRED_OBSERVABILITY_SURFACE:
        raise HypothesisPreregistrationError("OBSERVABILITY_SURFACE_MISMATCH")
    if obs.get("binding_required_for_future_evaluation") is not True:
        raise HypothesisPreregistrationError("OBSERVABILITY_BINDING_MUST_BE_REQUIRED")
    if obs.get("auto_resume_forbidden") is not True:
        raise HypothesisPreregistrationError("AUTO_RESUME_MUST_BE_FORBIDDEN")
    if obs.get("auto_rerun_on_infrastructure_failure_forbidden") is not True:
        raise HypothesisPreregistrationError("AUTO_RERUN_MUST_BE_FORBIDDEN")
    if obs.get("required_result_class_on_incomplete_run") != (
        "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    ):
        raise HypothesisPreregistrationError("INCOMPLETE_RUN_RESULT_CLASS_MISMATCH")
    diagnostics = list(obs.get("required_durable_diagnostics") or [])
    for required_diag in REQUIRED_DURABLE_DIAGNOSTICS:
        if required_diag not in diagnostics:
            raise HypothesisPreregistrationError(f"DURABLE_DIAGNOSTIC_MISSING:{required_diag}")
    if owner_map is not None:
        owners = owner_map.get("allowed_optimization_surfaces") or {}
        if REQUIRED_OBSERVABILITY_SURFACE not in owners:
            raise HypothesisPreregistrationError("OBSERVABILITY_OWNER_MAP_ENTRY_MISSING")

    hygiene = infra.get("panel_runner_falsy_zero_premeasurement_hygiene")
    if not isinstance(hygiene, Mapping):
        raise HypothesisPreregistrationError("FALSY_ZERO_HYGIENE_BINDING_REQUIRED")
    if hygiene.get("surface_id") != REQUIRED_FALSY_ZERO_HYGIENE_SURFACE:
        raise HypothesisPreregistrationError("FALSY_ZERO_HYGIENE_SURFACE_MISMATCH")
    if hygiene.get("binding_required_for_future_evaluation") is not True:
        raise HypothesisPreregistrationError("FALSY_ZERO_HYGIENE_BINDING_MUST_BE_REQUIRED")
    if hygiene.get("root_cause_addressed") != V2_TERMINAL_ROOT_CAUSE:
        raise HypothesisPreregistrationError("FALSY_ZERO_HYGIENE_ROOT_CAUSE_MISMATCH")
    if hygiene.get("does_not_authorize_v2_rerun") is not True:
        raise HypothesisPreregistrationError("FALSY_ZERO_MUST_NOT_AUTHORIZE_V2_RERUN")
    if hygiene.get("v2_terminal_unchanged") is not True:
        raise HypothesisPreregistrationError("FALSY_ZERO_V2_TERMINAL_UNCHANGED_REQUIRED")

    if terminal_result_class is None:
        # Definition-only: the contract must be byte-identical to what was frozen
        # at preregistration time, so the digest is recomputed over the full
        # contract and pinned against the hardcoded EXPECTED constant.
        digest = compute_development_preregistration_digest(contract)
        if contract.get("development_preregistration_digest") != digest:
            raise HypothesisPreregistrationError("DEVELOPMENT_PREREGISTRATION_DIGEST_MISMATCH")
        if digest != EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST:
            raise HypothesisPreregistrationError("DEVELOPMENT_PREREGISTRATION_DIGEST_UNEXPECTED")
    else:
        # Terminal closeout legitimately mutates execution-outcome fields, so the
        # full-contract digest can no longer match the pre-run snapshot. The
        # provenance marker itself (set once, at preregistration time) must be
        # carried forward unchanged; definition-semantics drift is separately
        # fail-closed by assert_definition_semantics_identical_to_predecessor below.
        if contract.get("development_preregistration_digest") != (
            EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST
        ):
            raise HypothesisPreregistrationError(
                "DEVELOPMENT_PREREGISTRATION_DIGEST_PROVENANCE_MISMATCH"
            )
        digest = EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST

    if v2_contract is not None:
        assert_v2_terminal_preserved(v2_contract)
        assert_definition_semantics_identical_to_predecessor(contract, v2_contract)
    if v1_contract is not None:
        assert_v1_terminal_preserved(v1_contract)

    if terminal_result_class is None:
        return {
            "valid": True,
            "definition_only": True,
            "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
            "predecessor_hypothesis_id": REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
            "dataset_id": REQUIRED_DATASET_ID,
            "treatment_type": REQUIRED_TREATMENT_TYPE,
            "mechanism_id": REQUIRED_MECHANISM_ID,
            "preregistration_state": REQUIRED_PREREGISTRATION_STATE,
            "development_only": True,
            "holdout_allowed": False,
            "evaluation_run_count": 0,
            "evaluation_run_count_authorized": 1,
            "evaluation_started": False,
            "evaluation_completed": False,
            "evaluation_executed": False,
            "result_class": "NOT_EVALUATED",
            "economic_verdict": "NOT_EVALUATED",
            "multiple_testing_budget": 1,
            "pass_criteria_frozen": True,
            "exit_divergence_required": True,
            "cost_model_canonical": True,
            "new_evaluation_not_rerun": True,
            "v2_partial_results_reused": False,
            "definition_semantics_identical": True,
            "observability_surface_bound": True,
            "observability_surface": REQUIRED_OBSERVABILITY_SURFACE,
            "falsy_zero_hygiene_bound": True,
            "development_preregistration_digest": digest,
            "rerun_allowed": False,
        }

    return {
        "valid": True,
        "definition_only": False,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "predecessor_hypothesis_id": REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
        "dataset_id": REQUIRED_DATASET_ID,
        "treatment_type": REQUIRED_TREATMENT_TYPE,
        "mechanism_id": REQUIRED_MECHANISM_ID,
        "preregistration_state": str(contract.get("preregistration_state")),
        "development_only": True,
        "holdout_allowed": False,
        "evaluation_run_count": 1,
        "evaluation_run_count_authorized": 1,
        "evaluation_started": True,
        "evaluation_completed": bool(contract.get("evaluation_completed")),
        "evaluation_executed": True,
        "result_class": terminal_result_class,
        "economic_verdict": contract.get("economic_verdict"),
        "multiple_testing_budget": 1,
        "pass_criteria_frozen": True,
        "exit_divergence_required": True,
        "cost_model_canonical": True,
        "new_evaluation_not_rerun": True,
        "v2_partial_results_reused": False,
        "definition_semantics_identical": True,
        "observability_surface_bound": True,
        "observability_surface": REQUIRED_OBSERVABILITY_SURFACE,
        "falsy_zero_hygiene_bound": True,
        "development_preregistration_digest": digest,
        "rerun_allowed": False,
    }


def load_and_validate_repo_contract(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    contract_path = root / CONTRACT_REL_PATH
    if not contract_path.is_file():
        raise HypothesisPreregistrationError(f"CONTRACT_MISSING:{contract_path}")
    v2_path = root / V2_CONTRACT_REL_PATH
    if not v2_path.is_file():
        raise HypothesisPreregistrationError(f"V2_CONTRACT_MISSING:{v2_path}")
    v1_path = root / V1_CONTRACT_REL_PATH
    if not v1_path.is_file():
        raise HypothesisPreregistrationError(f"V1_CONTRACT_MISSING:{v1_path}")
    seal_path = root / SEAL_REGISTRY_REL_PATH
    if not seal_path.is_file():
        raise HypothesisPreregistrationError(f"SEAL_REGISTRY_MISSING:{seal_path}")
    acq_path = root / ACQUISITION_CONTRACT_REL_PATH
    if not acq_path.is_file():
        raise HypothesisPreregistrationError(f"ACQUISITION_CONTRACT_MISSING:{acq_path}")
    owner_path = root / OWNER_MAP_REL_PATH
    if not owner_path.is_file():
        raise HypothesisPreregistrationError(f"OWNER_MAP_MISSING:{owner_path}")
    contract = load_json(contract_path)
    v2_contract = load_json(v2_path)
    v1_contract = load_json(v1_path)
    seal = load_json(seal_path)
    owner_map = load_json(owner_path)
    acq_sha = file_sha256(acq_path)
    report = validate_preregistration_contract(
        contract,
        v2_contract=v2_contract,
        v1_contract=v1_contract,
        seal_registry=seal,
        acquisition_sha256=acq_sha,
        owner_map=owner_map,
    )
    report["contract_path"] = CONTRACT_REL_PATH
    report["v2_contract_path"] = V2_CONTRACT_REL_PATH
    report["v1_contract_path"] = V1_CONTRACT_REL_PATH
    report["seal_registry_path"] = SEAL_REGISTRY_REL_PATH
    return report
