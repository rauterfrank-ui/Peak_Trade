"""Definition-only preregistration validator for Bollinger/MR midband exit-efficiency v1.

Research governance only. No backtest, no economic metrics, no runtime policy,
no holdout access, no productive trading-logic mutation.

Derived from the sealed DEVELOPMENT_ONLY failure-decomposition
NEXT_RESEARCH_QUESTION (EXIT_EFFICIENCY_ONLY). Single falsifiable
post-entry exit mechanism; no entry/side/instrument filter; no cost weakening.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_HYPOTHESIS_PREREGISTRATION_V1=true"
CONTRACT_REL_PATH = (
    "config/research/"
    "bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v1.json"
)
SEAL_REGISTRY_REL_PATH = (
    "config/research/regime_gated_standaside_mr_independent_dev_panel_seal_registry_v1.json"
)
ACQUISITION_CONTRACT_REL_PATH = (
    "config/research/regime_gated_standaside_mr_independent_dev_panel_acquisition_contract_v1.json"
)
HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"
HOLDOUT_PATH_MARKER = "offline_economic_reevaluation_sealed_long_panel_v1"
REQUIRED_DATASET_CLASS = "DEVELOPMENT_ONLY"
REQUIRED_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V1"
)
REQUIRED_DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
REQUIRED_TREATMENT_TYPE = "POST_ENTRY_EXIT_EFFICIENCY_MECHANISM"
REQUIRED_MECHANISM_ID = "canonical_bollinger_side_aware_middle_band_exit_v1"
REQUIRED_PREREGISTRATION_STATE = "DEFINITION_ONLY_PREREGISTERED"
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
    "mean_realized_pnl_over_mfe_capture_ratio_treatment > mean_realized_pnl_over_mfe_capture_ratio_control",
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
FORBIDDEN_RESULT_KEYS = frozenset(
    {
        "baseline_metrics",
        "treatment_metrics",
        "measured_net_return",
        "measured_profit_factor",
        "economic_metrics",
        "RESULT_CLASS",
        "result_class",
        "comparison_decision",
        "probe_summary",
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
                # Allow documented if_absent_result_class under divergence requirement.
                if key in {"RESULT_CLASS", "result_class"} and "if_absent_result_class" not in path:
                    if key_path.endswith(".if_absent_result_class"):
                        pass
                    elif "decision_thresholds" not in path:
                        found.append(key_path)
                elif key not in {"RESULT_CLASS", "result_class"}:
                    found.append(key_path)
            found.extend(_contains_banned_result_keys(value, key_path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            found.extend(_contains_banned_result_keys(item, f"{path}[{idx}]"))
    return found


def validate_preregistration_contract(
    contract: Mapping[str, Any],
    *,
    seal_registry: Mapping[str, Any] | None = None,
    acquisition_sha256: str | None = None,
) -> dict[str, Any]:
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
    if int(contract.get("evaluation_run_count", -1)) != 0:
        raise HypothesisPreregistrationError("EVALUATION_RUN_COUNT_MUST_BE_0")
    if int(contract.get("hypothesis_count") or 0) != 1:
        raise HypothesisPreregistrationError("HYPOTHESIS_COUNT_MUST_BE_1")
    if int(contract.get("multiple_testing_budget") or 0) != 1:
        raise HypothesisPreregistrationError("MULTIPLE_TESTING_BUDGET_MUST_BE_1")
    if int(contract.get("evaluation_run_count_authorized") or 0) != 1:
        raise HypothesisPreregistrationError("EVALUATION_RUN_COUNT_MUST_BE_1")
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
    ):
        if contract.get(flag) is not True:
            raise HypothesisPreregistrationError(f"{flag.upper()}_REQUIRED")
    if contract.get("hypothesis_id") != REQUIRED_HYPOTHESIS_ID:
        raise HypothesisPreregistrationError("HYPOTHESIS_ID_MISMATCH")
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
    ):
        if required_state not in terminal_states:
            raise HypothesisPreregistrationError(f"TERMINAL_STATE_MISSING:{required_state}")

    return {
        "valid": True,
        "definition_only": True,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "dataset_id": REQUIRED_DATASET_ID,
        "treatment_type": REQUIRED_TREATMENT_TYPE,
        "mechanism_id": REQUIRED_MECHANISM_ID,
        "preregistration_state": REQUIRED_PREREGISTRATION_STATE,
        "development_only": True,
        "holdout_allowed": False,
        "evaluation_run_count": 0,
        "evaluation_run_count_authorized": 1,
        "multiple_testing_budget": 1,
        "pass_criteria_frozen": True,
        "exit_divergence_required": True,
        "cost_model_canonical": True,
    }


def load_and_validate_repo_contract(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    contract_path = root / CONTRACT_REL_PATH
    if not contract_path.is_file():
        raise HypothesisPreregistrationError(f"CONTRACT_MISSING:{contract_path}")
    seal_path = root / SEAL_REGISTRY_REL_PATH
    if not seal_path.is_file():
        raise HypothesisPreregistrationError(f"SEAL_REGISTRY_MISSING:{seal_path}")
    acq_path = root / ACQUISITION_CONTRACT_REL_PATH
    if not acq_path.is_file():
        raise HypothesisPreregistrationError(f"ACQUISITION_CONTRACT_MISSING:{acq_path}")
    contract = load_json(contract_path)
    seal = load_json(seal_path)
    acq_sha = file_sha256(acq_path)
    report = validate_preregistration_contract(
        contract,
        seal_registry=seal,
        acquisition_sha256=acq_sha,
    )
    report["contract_path"] = CONTRACT_REL_PATH
    report["seal_registry_path"] = SEAL_REGISTRY_REL_PATH
    return report
