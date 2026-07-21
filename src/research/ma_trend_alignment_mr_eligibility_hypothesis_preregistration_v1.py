"""Definition-only preregistration validator for MA trend-alignment MR eligibility v1.

Research governance only. No backtest, no economic metrics, no runtime policy,
no holdout access, no productive trading-logic mutation.

Orthogonal to four prior FAILs on the same DEVELOPMENT panel:
regime-gated absolute-threshold classifier, ATR-percentile mid-band eligibility,
RSI(14) exhaustion eligibility, and ADX(14) range-admission eligibility.
This filter uses single-feature SMA(50) side-aware with-trend admission
(long iff close > SMA50; short iff close < SMA50) from rsi_reversion.py.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "MA_TREND_ALIGNMENT_MR_ELIGIBILITY_HYPOTHESIS_PREREGISTRATION_V1=true"
CONTRACT_REL_PATH = (
    "config/research/"
    "ma_trend_alignment_mr_eligibility_preregistered_economic_hypothesis_measurement_contract_v1.json"
)
SEAL_REGISTRY_REL_PATH = (
    "config/research/regime_gated_standaside_mr_independent_dev_panel_seal_registry_v1.json"
)
HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"
HOLDOUT_PATH_MARKER = "offline_economic_reevaluation_sealed_long_panel_v1"
REQUIRED_DATASET_CLASS = "DEVELOPMENT_ONLY"
REQUIRED_HYPOTHESIS_ID = "MA_TREND_ALIGNMENT_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
REQUIRED_TREATMENT_TYPE = "ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER"
REQUIRED_FILTER_ID = "canonical_ma_trend_alignment_entry_eligibility_v1"
REQUIRED_FROZEN_FILTER_PARAMETERS = {
    "ma_period": 50,
    "ma_type": "SMA",
    "side_aware": True,
    "warmup_bars": 50,
}
FORBIDDEN_PRIOR_FEATURE_IDS = frozenset(
    {
        "atr_14h",
        "atr_14h_rolling_percentile_rank_100h",
        "realized_vol_168h",
        "range_compression_72h",
        "trend_strength_168h",
        "rsi_14h",
        "adx_14h",
    }
)
REQUIRED_PRIOR_FAILED_HYPOTHESIS_IDS = frozenset(
    {
        "REGIME_GATED_STANDASIDE_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1",
        "ENTRY_EFFECTIVE_MR_ELIGIBILITY_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1",
        "RSI_EXHAUSTION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1",
        "ADX_RANGE_ADMISSION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1",
    }
)
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
    max_feature_lookback_hours: int = 168,
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


def validate_preregistration_contract(
    contract: Mapping[str, Any],
    *,
    seal_registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if contract.get("slice_class") != "DEFINITION_ONLY":
        raise HypothesisPreregistrationError("SLICE_MUST_BE_DEFINITION_ONLY")
    if contract.get("evaluation_authorized") is not False:
        raise HypothesisPreregistrationError("EVALUATION_MUST_BE_UNAUTHORIZED")
    if contract.get("backtest_authorized") is not False:
        raise HypothesisPreregistrationError("BACKTEST_MUST_BE_UNAUTHORIZED")
    if contract.get("implementation_authorized") is not False:
        raise HypothesisPreregistrationError("IMPLEMENTATION_MUST_BE_UNAUTHORIZED")
    if int(contract.get("hypothesis_count") or 0) != 1:
        raise HypothesisPreregistrationError("HYPOTHESIS_COUNT_MUST_BE_1")
    if int(contract.get("multiple_testing_budget") or 0) != 1:
        raise HypothesisPreregistrationError("MULTIPLE_TESTING_BUDGET_MUST_BE_1")
    if int(contract.get("evaluation_run_count_authorized") or 0) != 1:
        raise HypothesisPreregistrationError("EVALUATION_RUN_COUNT_MUST_BE_1")
    if int(contract.get("development_evaluation_runs_allowed") or 0) != 1:
        raise HypothesisPreregistrationError("DEVELOPMENT_RUNS_ALLOWED_MUST_BE_1")
    if contract.get("optimization_forbidden") is not True:
        raise HypothesisPreregistrationError("OPTIMIZATION_MUST_BE_FORBIDDEN")
    if contract.get("variants_forbidden") is not True:
        raise HypothesisPreregistrationError("VARIANTS_MUST_BE_FORBIDDEN")
    if contract.get("parameter_sweeps_forbidden") is not True:
        raise HypothesisPreregistrationError("PARAMETER_SWEEPS_MUST_BE_FORBIDDEN")
    if contract.get("post_hoc_threshold_adjustment_forbidden") is not True:
        raise HypothesisPreregistrationError("POST_HOC_THRESHOLD_ADJUSTMENT_FORBIDDEN")
    if contract.get("repeat_after_result_inspection_forbidden") is not True:
        raise HypothesisPreregistrationError("REPEAT_AFTER_RESULT_INSPECTION_FORBIDDEN")
    if contract.get("hypothesis_id") != REQUIRED_HYPOTHESIS_ID:
        raise HypothesisPreregistrationError("HYPOTHESIS_ID_MISMATCH")
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
    reject_holdout_dataset_or_path(str(contract.get("dataset_id")))
    for src in contract.get("allowed_data_sources") or []:
        reject_holdout_dataset_or_path(str(src))

    baseline = str(contract.get("baseline_config_id") or "").strip()
    if not baseline:
        raise HypothesisPreregistrationError("BASELINE_CONFIG_ID_REQUIRED")
    if contract.get("baseline_immutable") is not True:
        raise HypothesisPreregistrationError("BASELINE_MUST_BE_IMMUTABLE")

    treatment = contract.get("treatment") or {}
    if not isinstance(treatment, dict):
        raise HypothesisPreregistrationError("TREATMENT_REQUIRED")
    if treatment.get("treatment_type") != REQUIRED_TREATMENT_TYPE:
        raise HypothesisPreregistrationError("TREATMENT_TYPE_INVALID")
    if int(treatment.get("treatment_count") or 0) != 1:
        raise HypothesisPreregistrationError("TREATMENT_COUNT_MUST_BE_1")
    if treatment.get("acts_before_entry_decision") is not True:
        raise HypothesisPreregistrationError("FILTER_MUST_ACT_BEFORE_ENTRY")
    if treatment.get("reporting_or_attribution_only") is not False:
        raise HypothesisPreregistrationError("REPORTING_ONLY_GATE_FORBIDDEN")
    if treatment.get("no_new_direction_authority") is not True:
        raise HypothesisPreregistrationError("DIRECTION_AUTHORITY_CHANGE_FORBIDDEN")
    if treatment.get("no_new_switch_authority") is not True:
        raise HypothesisPreregistrationError("SWITCH_AUTHORITY_CHANGE_FORBIDDEN")
    if treatment.get("no_new_risk_authority") is not True:
        raise HypothesisPreregistrationError("RISK_AUTHORITY_CHANGE_FORBIDDEN")
    if treatment.get("no_new_sizing_authority") is not True:
        raise HypothesisPreregistrationError("SIZING_AUTHORITY_CHANGE_FORBIDDEN")
    if treatment.get("no_new_execution_authority") is not True:
        raise HypothesisPreregistrationError("EXECUTION_AUTHORITY_CHANGE_FORBIDDEN")
    if treatment.get("runtime_implementation_in_this_slice") is not False:
        raise HypothesisPreregistrationError("RUNTIME_IMPLEMENTATION_FORBIDDEN_IN_SLICE")

    shared = contract.get("shared_trading_semantics") or {}
    if shared.get("identical_for_treatment_and_control") is not True:
        raise HypothesisPreregistrationError("SHARED_SEMANTICS_MUST_BE_IDENTICAL")
    if shared.get("master_v2_and_double_play_sole_authority") is not True:
        raise HypothesisPreregistrationError("MASTER_V2_DOUBLE_PLAY_SOLE_AUTHORITY_REQUIRED")

    eligibility = contract.get("eligibility_filter") or {}
    if not isinstance(eligibility, dict):
        raise HypothesisPreregistrationError("ELIGIBILITY_FILTER_REQUIRED")
    if eligibility.get("filter_id") != REQUIRED_FILTER_ID:
        raise HypothesisPreregistrationError("FILTER_ID_MISMATCH")
    if eligibility.get("lookahead_forbidden") is not True:
        raise HypothesisPreregistrationError("LOOKAHEAD_MUST_BE_FORBIDDEN")
    if eligibility.get("threshold_adjustment_forbidden_after_preregistration") is not True:
        raise HypothesisPreregistrationError("FILTER_THRESHOLD_LOCK_REQUIRED")
    frozen = eligibility.get("frozen_parameters") or {}
    for key, expected in REQUIRED_FROZEN_FILTER_PARAMETERS.items():
        if frozen.get(key) != expected:
            raise HypothesisPreregistrationError(f"FILTER_PARAMETER_MISMATCH:{key}")
    declared_forbidden = set(eligibility.get("forbidden_prior_feature_ids") or [])
    if not FORBIDDEN_PRIOR_FEATURE_IDS.issubset(declared_forbidden):
        raise HypothesisPreregistrationError("FORBIDDEN_PRIOR_FEATURE_IDS_DECLARATION_INCOMPLETE")
    features = eligibility.get("features") or []
    if not features:
        raise HypothesisPreregistrationError("ELIGIBILITY_FEATURES_REQUIRED")
    for feat in features:
        fid = str(feat.get("feature_id") or "")
        if fid in FORBIDDEN_PRIOR_FEATURE_IDS:
            raise HypothesisPreregistrationError(f"PRIOR_FAILED_FEATURE_REUSE_FORBIDDEN:{fid}")
        if fid.startswith("atr_"):
            raise HypothesisPreregistrationError(f"ATR_FEATURE_REUSE_FORBIDDEN:{fid}")
        if fid.startswith("rsi_"):
            raise HypothesisPreregistrationError(f"RSI_FEATURE_REUSE_FORBIDDEN:{fid}")
        if fid.startswith("adx_"):
            raise HypothesisPreregistrationError(f"ADX_FEATURE_REUSE_FORBIDDEN:{fid}")
        if not feat.get("causal"):
            raise HypothesisPreregistrationError("FEATURE_MUST_BE_CAUSAL")
        if int(feat.get("lookback_hours") or 0) <= 0:
            raise HypothesisPreregistrationError("FEATURE_LOOKBACK_REQUIRED")

    divergence = contract.get("entry_eligibility_divergence_requirement") or {}
    if divergence.get("required") is not True:
        raise HypothesisPreregistrationError("ENTRY_ELIGIBILITY_DIVERGENCE_REQUIRED")
    if divergence.get("if_absent_result_class") != "FAIL":
        raise HypothesisPreregistrationError("DIVERGENCE_ABSENCE_MUST_FAIL")

    prior_failed = contract.get("prior_failed_hypotheses") or []
    if not isinstance(prior_failed, list) or len(prior_failed) < 4:
        raise HypothesisPreregistrationError("PRIOR_FAILED_HYPOTHESES_MUST_LIST_ALL_PRIORS")
    prior_ids = {str(entry.get("hypothesis_id") or "") for entry in prior_failed}
    if not REQUIRED_PRIOR_FAILED_HYPOTHESIS_IDS.issubset(prior_ids):
        raise HypothesisPreregistrationError("PRIOR_FAILED_HYPOTHESES_MISSING_REQUIRED_REFERENCE")
    for entry in prior_failed:
        if entry.get("result_class") != "FAIL":
            raise HypothesisPreregistrationError("PRIOR_FAILED_HYPOTHESES_MUST_BE_FAIL")

    cost = contract.get("cost_model") or {}
    for key in ("fee_bps", "slippage_bps", "half_spread_bps", "roundtrip_reference_bps"):
        if key not in cost or cost[key] is None:
            raise HypothesisPreregistrationError(f"COST_MODEL_MISSING:{key}")
    if cost.get("fixed") is not True:
        raise HypothesisPreregistrationError("COST_MODEL_MUST_BE_FIXED")
    if cost.get("cost_drag_fully_included_in_net_metrics") is not True:
        raise HypothesisPreregistrationError("COST_DRAG_MUST_BE_INCLUDED")

    stop = contract.get("stop_and_ledger_semantics") or {}
    if stop.get("unchanged_from_baseline_binding") is not True:
        raise HypothesisPreregistrationError("STOP_LEDGER_MUST_BE_UNCHANGED")
    if stop.get("mutation_forbidden") is not True:
        raise HypothesisPreregistrationError("STOP_LEDGER_MUTATION_FORBIDDEN")

    metrics = (contract.get("metrics") or {}).get("primary") or []
    if tuple(metrics) != REQUIRED_PRIMARY_METRICS:
        raise HypothesisPreregistrationError("PRIMARY_METRICS_MISMATCH")

    thresholds = contract.get("decision_thresholds") or {}
    for key in (
        "minimum_trade_count",
        "max_trade_count_reduction_fraction_vs_control",
        "pass_requires_all",
        "fail_if_any",
        "inconclusive_if_any",
    ):
        if key not in thresholds or thresholds[key] in (None, [], ""):
            raise HypothesisPreregistrationError(f"THRESHOLD_MISSING:{key}")
    if float(thresholds.get("max_trade_count_reduction_fraction_vs_control")) < 0:
        raise HypothesisPreregistrationError("TRADE_REDUCTION_FRACTION_INVALID")
    if thresholds.get("inconclusive_never_for_poor_economic_results") is not True:
        raise HypothesisPreregistrationError("INCONCLUSIVE_MUST_EXCLUDE_POOR_ECONOMICS")
    if thresholds.get("threshold_adjustment_forbidden_after_preregistration") is not True:
        raise HypothesisPreregistrationError("THRESHOLDS_MUST_BE_LOCKED")
    if thresholds.get("on_fail_retuning_forbidden") is not True:
        raise HypothesisPreregistrationError("ON_FAIL_RETUNING_MUST_BE_FORBIDDEN")
    if thresholds.get("on_fail_holdout_forbidden") is not True:
        raise HypothesisPreregistrationError("ON_FAIL_HOLDOUT_MUST_BE_FORBIDDEN")
    if str(contract.get("primary_decision_metric") or "") != "NET_PROFIT_FACTOR":
        raise HypothesisPreregistrationError("PRIMARY_DECISION_METRIC_MISMATCH")
    pass_all = " ".join(str(x) for x in (thresholds.get("pass_requires_all") or []))
    if "entry_eligibility_divergence_observed" not in pass_all:
        raise HypothesisPreregistrationError("PASS_MUST_REQUIRE_ENTRY_DIVERGENCE")

    promo = contract.get("promotion_and_holdout_policy") or {}
    if promo.get("promotion_eligible") is not False:
        raise HypothesisPreregistrationError("PROMOTION_MUST_BE_FALSE")
    if promo.get("economic_validity_offline_gate_pass") is not False:
        raise HypothesisPreregistrationError("ECONOMIC_GATE_MUST_REMAIN_CLOSED")
    if promo.get("economic_validity_offline_gate_changed") is not False:
        raise HypothesisPreregistrationError("ECONOMIC_GATE_MUST_BE_UNCHANGED")
    if promo.get("holdout_forbidden_in_this_slice") is not True:
        raise HypothesisPreregistrationError("HOLDOUT_FORBIDDEN_IN_SLICE_REQUIRED")

    runtime = contract.get("runtime_policy") or {}
    for key in (
        "runtime_activated",
        "shadow_activated",
        "testnet_activated",
        "live_authorized",
        "orders_allowed",
        "scheduler_authorized",
    ):
        if runtime.get(key) is not False:
            raise HypothesisPreregistrationError(f"RUNTIME_FLAG_MUST_BE_FALSE:{key}")

    splits = contract.get("splits") or {}
    panel = contract.get("common_panel_bounds") or {}
    expected = materialize_chronological_splits(
        panel_start=str(panel["start"]),
        panel_end_exclusive=str(panel["end_exclusive"]),
        train_share=float(splits.get("train_definition_share", 0.6)),
        validation_share=float(splits.get("validation_share", 0.2)),
        final_share=float(splits.get("final_development_confirmation_share", 0.2)),
        max_feature_lookback_hours=int(splits.get("max_feature_lookback_hours", 168)),
        max_holding_horizon_hours=int(splits.get("max_holding_horizon_hours", 48)),
    )
    for name in (
        "train_definition",
        "validation",
        "final_development_confirmation",
    ):
        if splits.get(name) != expected[name]:
            raise HypothesisPreregistrationError(f"SPLIT_MISMATCH:{name}")
    if splits.get("split_intervals_sha256") != expected["split_intervals_sha256"]:
        raise HypothesisPreregistrationError("SPLIT_HASH_MISMATCH")
    if int(splits.get("purge_hours") or 0) != int(expected["purge_hours"]):
        raise HypothesisPreregistrationError("PURGE_MISMATCH")
    if int(splits.get("embargo_hours") or 0) != int(expected["embargo_hours"]):
        raise HypothesisPreregistrationError("EMBARGO_MISMATCH")
    for key in (
        "validation_feature_eligible_from",
        "validation_label_eligible_from",
        "final_feature_eligible_from",
        "final_label_eligible_from",
    ):
        if splits.get(key) != expected[key]:
            raise HypothesisPreregistrationError(f"PURGE_EMBARGO_BOUND_MISMATCH:{key}")

    if seal_registry is not None:
        if seal_registry.get("dataset_id") != REQUIRED_DATASET_ID:
            raise HypothesisPreregistrationError("SEAL_REGISTRY_DATASET_MISMATCH")
        if seal_registry.get("classification", {}).get("role") != REQUIRED_DATASET_CLASS:
            raise HypothesisPreregistrationError("SEAL_REGISTRY_NOT_DEVELOPMENT_ONLY")
        panel_meta = seal_registry.get("panel") or {}
        if panel_meta.get("common_panel_start") != panel.get("start"):
            raise HypothesisPreregistrationError("COMMON_PANEL_START_MISMATCH")
        if panel_meta.get("common_panel_end") != panel.get("end_exclusive"):
            raise HypothesisPreregistrationError("COMMON_PANEL_END_MISMATCH")

    return {
        "valid": True,
        "hypothesis_id": contract["hypothesis_id"],
        "dataset_id": contract["dataset_id"],
        "multiple_testing_budget": 1,
        "evaluation_run_count_authorized": 1,
        "split_intervals_sha256": expected["split_intervals_sha256"],
        "treatment_type": treatment["treatment_type"],
        "filter_id": eligibility["filter_id"],
        "entry_eligibility_divergence_required": True,
        "definition_only": True,
    }


def load_and_validate_repo_contract(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    contract = load_json(root / CONTRACT_REL_PATH)
    seal = load_json(root / SEAL_REGISTRY_REL_PATH)
    return validate_preregistration_contract(contract, seal_registry=seal)


__all__ = [
    "CONTRACT_REL_PATH",
    "FORBIDDEN_PRIOR_FEATURE_IDS",
    "HOLDOUT_OPAQUE_ID",
    "HypothesisPreregistrationError",
    "PACKAGE_MARKER",
    "REQUIRED_FROZEN_FILTER_PARAMETERS",
    "REQUIRED_PRIOR_FAILED_HYPOTHESIS_IDS",
    "canonical_json_sha256",
    "load_and_validate_repo_contract",
    "materialize_chronological_splits",
    "reject_holdout_dataset_or_path",
    "validate_preregistration_contract",
]
