"""Deterministic binding/digest resolution for VCEB v1 eval entry point."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.constants_v1 import (
    ALLOWED_DATASET_IDS,
    BASELINE_ID,
    BASELINE_IMPL_REL_PATH,
    CLI_REL_PATH,
    DATASET_CLASS,
    DATASET_ID,
    ENTRY_POINT_BINDING_REL_PATH,
    FEE_BPS_PER_SIDE,
    FORBIDDEN_HOLDOUT_IDS,
    FROZEN_MEASUREMENT_CONTRACT_DIGEST,
    GOVERNANCE_REL_PATH,
    HALF_SPREAD_BPS,
    IMPLEMENTATION_BINDING_REL_PATH,
    LIFECYCLE_AUTHORITY_REL_PATH,
    MEASUREMENT_CONTRACT_REL_PATH,
    OWNER_SURFACE,
    PRODUCTIVE_PNL_EVALUATOR_REL_PATH,
    PROGRAM_ID,
    SHARED_CHANNEL_CORE_OWNER,
    SHARED_CHANNEL_CORE_REL_PATH,
    SIGNAL_FAMILY,
    SLIPPAGE_BPS_PER_SIDE,
    STRATEGY_ID,
    STRATEGY_IDENTITY,
    STRATEGY_IMPL_REL_PATH,
    STRATEGY_VERSION,
    TIME_SEGMENT_DEFINITION_ID,
    VOL_STATE_REL_PATH,
)


class EntryPointBindingError(ValueError):
    """Fail-closed entry-point binding error."""


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise EntryPointBindingError(code)


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_dumps(payload).encode("utf-8")).hexdigest()


def load_json(repo_root: Path, rel_path: str) -> dict[str, Any]:
    path = repo_root / rel_path
    _require(path.is_file(), f"MISSING_FILE:{rel_path}")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_measurement_contract(repo_root: Path) -> dict[str, Any]:
    contract = load_json(repo_root, MEASUREMENT_CONTRACT_REL_PATH)
    _require(
        contract.get("contract_digest") == FROZEN_MEASUREMENT_CONTRACT_DIGEST,
        "MEASUREMENT_CONTRACT_DIGEST_DRIFT",
    )
    _require(contract.get("dataset_id") == DATASET_ID, "DATASET_ID_MISMATCH")
    _require(contract.get("dataset_class") == DATASET_CLASS, "DATASET_CLASS_MISMATCH")
    _require(
        contract.get("strategy_identity") == STRATEGY_IDENTITY,
        "STRATEGY_IDENTITY_MISMATCH",
    )
    _require(contract.get("signal_family") == SIGNAL_FAMILY, "SIGNAL_FAMILY_MISMATCH")
    _require(contract.get("program_id") == PROGRAM_ID, "PROGRAM_ID_MISMATCH")
    baseline = contract.get("baseline") or {}
    _require(baseline.get("baseline_id") == BASELINE_ID, "BASELINE_ID_MISMATCH")
    tsd = contract.get("time_segment_definition") or {}
    _require(
        tsd.get("time_segment_definition_id") == TIME_SEGMENT_DEFINITION_ID,
        "TIME_SEGMENT_DEFINITION_MISMATCH",
    )
    # Preregistration already reserves development_evaluation_authorized=true;
    # execution remains gated by the entry-point binding (kept false in this slice).
    _require(
        contract.get("development_evaluation_authorized") is True,
        "DEV_EVAL_AUTH_FALSE_ON_CONTRACT",
    )
    _require(contract.get("development_evaluation_executed") is False, "DEV_EVAL_EXECUTED_TRUE")
    _require(contract.get("development_run_count") == 0, "DEV_RUN_COUNT_NOT_ZERO")
    _require(contract.get("runner_start_count") == 0, "RUNNER_START_NOT_ZERO")
    exit_sem = contract.get("exit_semantics") or {}
    _require(
        exit_sem.get("productive_exit_pnl_evaluator_ref") == PRODUCTIVE_PNL_EVALUATOR_REL_PATH,
        "PRODUCTIVE_PNL_EVALUATOR_REF_DRIFT",
    )
    _require(exit_sem.get("second_pnl_truth_forbidden") is True, "SECOND_PNL_TRUTH_ALLOWED")
    _require(exit_sem.get("new_pnl_implementation_forbidden") is True, "NEW_PNL_IMPL_ALLOWED")
    return contract


def resolve_strategy_params(contract: Mapping[str, Any] | None = None) -> dict[str, Any]:
    frozen = dict((contract or {}).get("parameter_governance", {}).get("frozen_parameters") or {})
    if not frozen:
        frozen = {
            "channel_lookback_bars": 20,
            "contraction_min_consecutive_bars": 8,
            "contraction_percentile_inclusive_max": 0.3,
            "entry_window_end_offset": 1,
            "entry_window_start_offset": 1,
            "event_consumption": "SINGLE_USE",
            "ex_ante_exit_reachability_required": True,
            "expansion_absolute_percentile_inclusive_min": 0.65,
            "expansion_relative_percentile_rise_inclusive_min": 0.25,
            "initial_stop_atr_multiple": 1.5,
            "initial_stop_atr_period": 14,
            "joint_coincidence_required": True,
            "max_entries_per_transition_event": 1,
            "min_post_fill_bars_required_inclusive": 48,
            "percentile_lookback_bars": 120,
            "percentile_rank_min_valid_observations": 120,
            "percentile_rank_window_includes_current_value": True,
            "percentile_tie_method": "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF",
            "realized_volatility_period": 24,
            "regime_invalidation_percentile_lt": 0.4,
            "signal_lag_bars": 1,
            "time_exit_max_bars": 48,
            "trailing_stop_forbidden": True,
            "vol_estimator_family": "REALIZED_VOLATILITY",
        }
    return {
        "baseline_id": BASELINE_ID,
        "frozen_parameters": frozen,
        "shared_channel_core_owner": SHARED_CHANNEL_CORE_OWNER,
        "strategy_id": STRATEGY_ID,
        "strategy_identity": STRATEGY_IDENTITY,
        "strategy_version": STRATEGY_VERSION,
    }


def compute_strategy_params_digest(contract: Mapping[str, Any] | None = None) -> str:
    return stable_digest(resolve_strategy_params(contract))


def resolve_cost_execution_binding(contract: Mapping[str, Any]) -> dict[str, Any]:
    costs = contract.get("costs") or {}
    _require(float(costs.get("fee_bps_per_side")) == FEE_BPS_PER_SIDE, "FEE_BPS_DRIFT")
    _require(
        float(costs.get("slippage_bps_per_side")) == SLIPPAGE_BPS_PER_SIDE,
        "SLIPPAGE_BPS_DRIFT",
    )
    _require(float(costs.get("half_spread_bps")) == HALF_SPREAD_BPS, "HALF_SPREAD_DRIFT")
    return {
        "binding_version": "v1",
        "implicit_zero_cost_forbidden": True,
        "fee_model_binding": {
            "fee_bps_per_side": FEE_BPS_PER_SIDE,
            "fee_model_version": costs.get("fee_model_version"),
        },
        "slippage_model_binding": {
            "slippage_bps_per_side": SLIPPAGE_BPS_PER_SIDE,
            "slippage_model_version": costs.get("slippage_model_version"),
        },
        "spread_model_binding": {
            "conservative_half_spread_bps": HALF_SPREAD_BPS,
            "spread_model_version": costs.get("spread_model_version"),
        },
    }


def assert_dataset_allowed(dataset_id: str) -> None:
    _require(dataset_id in ALLOWED_DATASET_IDS, f"DATASET_NOT_ALLOWLISTED:{dataset_id}")
    _require(dataset_id not in FORBIDDEN_HOLDOUT_IDS, f"HOLDOUT_DATASET_REJECTED:{dataset_id}")


def reject_holdout_reference(value: str | None) -> None:
    if value is None:
        return
    lowered = value.lower()
    for forbidden in FORBIDDEN_HOLDOUT_IDS:
        if forbidden.lower() in lowered:
            raise EntryPointBindingError(f"HOLDOUT_REFERENCE_REJECTED:{value}")
    if "holdout" in lowered and "pre_holdout" not in lowered and "dev_pre_holdout" not in lowered:
        if "sealed" in lowered or "offline_economic_reevaluation_sealed" in lowered:
            raise EntryPointBindingError(f"HOLDOUT_REFERENCE_REJECTED:{value}")


def assert_shared_channel_core_bound() -> None:
    from src.research import price_channel_breakout_core_v1 as core
    from src.research import unconditional_20_bar_price_channel_breakout_v1 as baseline
    from src.research import volatility_contraction_expansion_breakout_v1_strategy_v1 as strategy

    _require(
        strategy.compute_prior_high_low_channel_bounds_v1
        is core.compute_prior_high_low_channel_bounds_v1,
        "STRATEGY_CHANNEL_CORE_DRIFT",
    )
    _require(
        baseline.compute_prior_high_low_channel_bounds_v1
        is core.compute_prior_high_low_channel_bounds_v1,
        "BASELINE_CHANNEL_CORE_DRIFT",
    )
    _require(
        strategy.classify_price_channel_break_v1 is core.classify_price_channel_break_v1,
        "STRATEGY_CHANNEL_CLASSIFY_DRIFT",
    )
    _require(
        baseline.classify_price_channel_break_v1 is core.classify_price_channel_break_v1,
        "BASELINE_CHANNEL_CLASSIFY_DRIFT",
    )


def compute_config_digest(repo_root: Path) -> str:
    contract = resolve_measurement_contract(repo_root)
    impl = load_json(repo_root, IMPLEMENTATION_BINDING_REL_PATH)
    payload = {
        "baseline_id": BASELINE_ID,
        "cost_execution_binding": resolve_cost_execution_binding(contract),
        "dataset_class": DATASET_CLASS,
        "dataset_id": DATASET_ID,
        "frozen_measurement_contract_digest": impl.get("frozen_measurement_contract_digest"),
        "implementation_binding_status": impl.get("status"),
        "measurement_contract_digest": contract["contract_digest"],
        "productive_exit_pnl_evaluator_ref": PRODUCTIVE_PNL_EVALUATOR_REL_PATH,
        "shared_channel_core_owner": SHARED_CHANNEL_CORE_OWNER,
        "signal_family": SIGNAL_FAMILY,
        "strategy_identity": STRATEGY_IDENTITY,
        "strategy_params_default": resolve_strategy_params(contract),
        "time_segment_definition_id": TIME_SEGMENT_DEFINITION_ID,
    }
    return stable_digest(payload)


def materialize_entry_point_binding_payload(repo_root: Path) -> dict[str, Any]:
    contract = resolve_measurement_contract(repo_root)
    impl = load_json(repo_root, IMPLEMENTATION_BINDING_REL_PATH)
    _require(impl.get("strategy_implementation_present") is True, "IMPL_NOT_PRESENT")
    _require(
        impl.get("frozen_measurement_contract_digest") == FROZEN_MEASUREMENT_CONTRACT_DIGEST,
        "IMPL_DIGEST_MISMATCH",
    )
    _require(
        impl.get("baseline_id") == BASELINE_ID
        or impl.get("strategy_identity") == STRATEGY_IDENTITY,
        "IMPL_IDENTITY_DRIFT",
    )
    _require(impl.get("development_evaluation_authorized") is False, "IMPL_BINDING_AUTH_TRUE")
    assert_dataset_allowed(DATASET_ID)
    assert_shared_channel_core_bound()
    pnl_path = repo_root / PRODUCTIVE_PNL_EVALUATOR_REL_PATH
    _require(pnl_path.is_file(), "PRODUCTIVE_PNL_EVALUATOR_MISSING")
    config_digest = compute_config_digest(repo_root)
    strategy_params_digest = compute_strategy_params_digest(contract)
    return {
        "artifact_kind": (
            "volatility_contraction_expansion_breakout_v1_development_evaluation_entry_point_binding"
        ),
        "artifact_version": "v1",
        "authority_effect": "NONE",
        "baseline_id": BASELINE_ID,
        "canonical_ssot": True,
        "cli_ref": CLI_REL_PATH,
        "config_digest": config_digest,
        "dataset_binding": {
            "dataset_class": DATASET_CLASS,
            "dataset_id": DATASET_ID,
            "holdout_forbidden": True,
            "holdout_ids_rejected": sorted(FORBIDDEN_HOLDOUT_IDS),
        },
        "development_evaluation_authorized": False,
        "development_evaluation_executed": False,
        "development_run_count": 0,
        "development_run_limit": 1,
        "economic_gate_open": False,
        "entry_point_status": "EXECUTABLE_EVALUATE_PATH_PRESENT_EVALUATION_UNAUTHORIZED",
        "evaluation_authorized": False,
        "evidence_ref": "docs/evidence/evaluate_volatility_contraction_expansion_breakout_development_v1/",
        "frozen_measurement_contract_digest": FROZEN_MEASUREMENT_CONTRACT_DIGEST,
        "frozen_measurement_contract_ref": MEASUREMENT_CONTRACT_REL_PATH,
        "governance_ref": GOVERNANCE_REL_PATH,
        "holdout_authorized": False,
        "holdout_forbidden": True,
        "hypothesis_id": contract["hypothesis_id"],
        "implementation_binding_ref": IMPLEMENTATION_BINDING_REL_PATH,
        "lifecycle_authority_ref": LIFECYCLE_AUTHORITY_REL_PATH,
        "owner_surface": OWNER_SURFACE,
        "productive_exit_pnl_evaluator_ref": PRODUCTIVE_PNL_EVALUATOR_REL_PATH,
        "productive_pnl_evaluator_duplicated": False,
        "program_id": PROGRAM_ID,
        "promotion_eligible": False,
        "retry_forbidden": True,
        "reused_canonical_owners": {
            "baseline": BASELINE_IMPL_REL_PATH.replace("/", ".").removesuffix(".py"),
            "productive_exit_pnl_evaluator": PRODUCTIVE_PNL_EVALUATOR_REL_PATH.replace(
                "/", "."
            ).removesuffix(".py"),
            "shared_channel_core": SHARED_CHANNEL_CORE_OWNER,
            "strategy": STRATEGY_IMPL_REL_PATH.replace("/", ".").removesuffix(".py"),
            "vol_state": VOL_STATE_REL_PATH.replace("/", ".").removesuffix(".py"),
        },
        "runner_present": True,
        "runner_start_count": 0,
        "runtime_effect": "NONE",
        "runtime_policy": {
            "capital_activated": False,
            "live_authorized": False,
            "orders_allowed": False,
            "paper_activated": False,
            "runtime_activated": False,
            "scheduler_authorized": False,
            "shadow_activated": False,
            "testnet_activated": False,
        },
        "schema_version": (
            "volatility_contraction_expansion_breakout_v1_development_evaluation_entry_point_binding.v1"
        ),
        "shared_channel_core_bound": True,
        "shared_channel_core_ref": SHARED_CHANNEL_CORE_REL_PATH,
        "signal_family": SIGNAL_FAMILY,
        "slice_class": "DEVELOPMENT_EVALUATION_EXECUTABLE_PATH_IMPLEMENTATION_ONLY",
        "status": "EXECUTABLE_EVALUATE_PATH_PRESENT_EVALUATION_UNAUTHORIZED",
        "strategy_id": STRATEGY_ID,
        "strategy_identity": STRATEGY_IDENTITY,
        "strategy_params_digest": strategy_params_digest,
        "strategy_version": STRATEGY_VERSION,
        "time_segment_definition_id": TIME_SEGMENT_DEFINITION_ID,
        "verdict": (
            "EXECUTABLE_EVALUATE_PATH_PRESENT_AWAITING_SEPARATE_OPERATOR_GO_"
            "FOR_DEVELOPMENT_EVALUATION_AUTHORIZATION"
        ),
    }


def load_and_validate_entry_point_binding(repo_root: Path) -> dict[str, Any]:
    expected = materialize_entry_point_binding_payload(repo_root)
    path = repo_root / ENTRY_POINT_BINDING_REL_PATH
    _require(path.is_file(), "ENTRY_POINT_BINDING_MISSING")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    for key in (
        "config_digest",
        "strategy_params_digest",
        "frozen_measurement_contract_digest",
        "dataset_binding",
        "development_run_count",
        "runner_start_count",
        "evaluation_authorized",
        "development_evaluation_authorized",
        "holdout_forbidden",
        "time_segment_definition_id",
        "status",
        "baseline_id",
        "shared_channel_core_bound",
        "productive_exit_pnl_evaluator_ref",
        "productive_pnl_evaluator_duplicated",
    ):
        _require(loaded.get(key) == expected.get(key), f"ENTRY_POINT_BINDING_DRIFT:{key}")
    return loaded
