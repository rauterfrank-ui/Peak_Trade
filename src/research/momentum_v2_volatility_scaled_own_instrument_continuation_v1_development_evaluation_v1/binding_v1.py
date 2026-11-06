"""Deterministic binding/digest resolution for Momentum V2 vol-scaled eval entry point."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_v1_development_evaluation_v1.constants_v1 import (
    ALLOWED_DATASET_IDS,
    BASELINE_ID,
    CLI_REL_PATH,
    DATASET_CLASS,
    DATASET_ID,
    ENTRY_POINT_BINDING_REL_PATH,
    FEE_BPS_PER_SIDE,
    FORBIDDEN_HOLDOUT_IDS,
    FROZEN_MEASUREMENT_CONTRACT_DIGEST,
    GOVERNANCE_REL_PATH,
    HALF_SPREAD_BPS,
    HYPOTHESIS_ID,
    IMPLEMENTATION_BINDING_REL_PATH,
    LIFECYCLE_AUTHORITY_REL_PATH,
    MEASUREMENT_CONTRACT_REL_PATH,
    OWNER_SURFACE,
    PRODUCTIVE_PNL_EVALUATOR_REL_PATH,
    PROGRAM_ID,
    SIGNAL_FAMILY,
    SLIPPAGE_BPS_PER_SIDE,
    STRATEGY_ID,
    STRATEGY_IDENTITY,
    STRATEGY_SIGNAL_REL_PATH,
    STRATEGY_VERSION,
    TIME_SEGMENT_DEFINITION_ID,
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
    _require(contract.get("hypothesis_id") == HYPOTHESIS_ID, "HYPOTHESIS_ID_MISMATCH")
    baseline = contract.get("baseline") or {}
    _require(baseline.get("baseline_id") == BASELINE_ID, "BASELINE_ID_MISMATCH")
    _require(
        contract.get("time_segment_definition_id") == TIME_SEGMENT_DEFINITION_ID,
        "TIME_SEGMENT_DEFINITION_MISMATCH",
    )
    _require(
        contract.get("development_evaluation_authorized") is True,
        "DEV_EVAL_AUTH_FALSE_ON_CONTRACT",
    )
    return contract


def resolve_strategy_params(contract: Mapping[str, Any] | None = None) -> dict[str, Any]:
    frozen = dict(
        (contract or {}).get("parameter_governance", {}).get("frozen_non_grid_parameters") or {}
    )
    if not frozen:
        frozen = {
            "entry_side": "NONE",
            "lookback_period": 20,
            "output_contract": "ENTRY_EXIT_EVENT_V1",
            "pit_safe": True,
            "realized_vol_estimator": "std_of_one_bar_simple_returns_over_lookback_period",
            "realized_vol_zero_or_non_finite_policy": "NO_SIGNAL_FAIL_CLOSED",
            "registry_mutation_forbidden": True,
            "short_entry_forbidden": True,
            "signal_lag_bars": 1,
            "vol_scaled_entry_z": 1.0,
            "vol_scaled_exit_z": 0.0,
            "vol_scaling_required": True,
        }
    return {
        "baseline_id": BASELINE_ID,
        "frozen_non_grid_parameters": frozen,
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


def assert_signal_implementation_bound(repo_root: Path) -> None:
    signal_path = repo_root / STRATEGY_SIGNAL_REL_PATH
    _require(signal_path.is_file(), "STRATEGY_SIGNAL_MISSING")
    from src.research import (
        momentum_v2_volatility_scaled_own_instrument_continuation_v1_signal_v1 as signal,
    )

    _require(
        signal.STRATEGY_IDENTITY == STRATEGY_IDENTITY,
        "SIGNAL_STRATEGY_IDENTITY_DRIFT",
    )
    _require(signal.HYPOTHESIS_ID == HYPOTHESIS_ID, "SIGNAL_HYPOTHESIS_DRIFT")
    _require(signal.BASELINE_ID == BASELINE_ID, "SIGNAL_BASELINE_DRIFT")
    _require(signal.SHORT_ENTRY_FORBIDDEN is True, "SHORT_ENTRY_ALLOWED")
    _require(
        signal.validate_frozen_parameters_v1(
            lookback_period=20,
            signal_lag_bars=1,
            entry_z=1.0,
            exit_z=0.0,
        ),
        "FROZEN_PARAMS_DRIFT",
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
        "signal_family": SIGNAL_FAMILY,
        "strategy_identity": STRATEGY_IDENTITY,
        "strategy_params_default": resolve_strategy_params(contract),
        "strategy_signal_ref": STRATEGY_SIGNAL_REL_PATH,
        "time_segment_definition_id": TIME_SEGMENT_DEFINITION_ID,
    }
    return stable_digest(payload)


def materialize_entry_point_binding_payload(repo_root: Path) -> dict[str, Any]:
    contract = resolve_measurement_contract(repo_root)
    impl = load_json(repo_root, IMPLEMENTATION_BINDING_REL_PATH)
    binding = load_json(repo_root, ENTRY_POINT_BINDING_REL_PATH)
    _require(impl.get("strategy_implementation_present") is True, "IMPL_NOT_PRESENT")
    _require(
        impl.get("frozen_measurement_contract_digest") == FROZEN_MEASUREMENT_CONTRACT_DIGEST,
        "IMPL_DIGEST_MISMATCH",
    )
    _require(impl.get("strategy_identity") == STRATEGY_IDENTITY, "IMPL_IDENTITY_DRIFT")
    assert_dataset_allowed(DATASET_ID)
    assert_signal_implementation_bound(repo_root)
    pnl_path = repo_root / PRODUCTIVE_PNL_EVALUATOR_REL_PATH
    _require(pnl_path.is_file(), "PRODUCTIVE_PNL_EVALUATOR_MISSING")
    config_digest = compute_config_digest(repo_root)
    strategy_params_digest = compute_strategy_params_digest(contract)
    return {
        "artifact_kind": (
            "momentum_v2_volatility_scaled_own_instrument_continuation_v1_"
            "development_evaluation_entry_point_binding"
        ),
        "artifact_version": "v1",
        "authority_effect": "NONE",
        "baseline_id": BASELINE_ID,
        "canonical_ssot": True,
        "cli_ref": CLI_REL_PATH,
        "config_digest": config_digest,
        "costs_binding": binding.get("costs_binding"),
        "dataset_binding": {
            "dataset_class": DATASET_CLASS,
            "dataset_id": DATASET_ID,
            "holdout_forbidden": True,
            "holdout_ids_rejected": sorted(FORBIDDEN_HOLDOUT_IDS),
        },
        "dataset_id": DATASET_ID,
        "development_evaluation_authorized": bool(binding.get("development_evaluation_authorized")),
        "development_evaluation_executed": bool(binding.get("development_evaluation_executed")),
        "development_run_count": int(binding.get("development_run_count") or 0),
        "development_run_limit": 1,
        "development_run_slot_available": bool(binding.get("development_run_slot_available")),
        "economic_gate_open": False,
        "evaluation_authorized": False,
        "evidence_ref": (
            "docs/evidence/"
            "evaluate_momentum_v2_volatility_scaled_own_instrument_continuation_development_v1/"
        ),
        "frozen_measurement_contract_digest": FROZEN_MEASUREMENT_CONTRACT_DIGEST,
        "frozen_measurement_contract_ref": MEASUREMENT_CONTRACT_REL_PATH,
        "governance_ref": GOVERNANCE_REL_PATH,
        "holdout_authorized": False,
        "holdout_forbidden": True,
        "hypothesis_id": HYPOTHESIS_ID,
        "implementation_binding_ref": IMPLEMENTATION_BINDING_REL_PATH,
        "lifecycle_authority_ref": LIFECYCLE_AUTHORITY_REL_PATH,
        "owner_surface": OWNER_SURFACE,
        "productive_exit_pnl_evaluator_ref": PRODUCTIVE_PNL_EVALUATOR_REL_PATH,
        "productive_pnl_evaluator_duplicated": False,
        "program_id": PROGRAM_ID,
        "promotion_eligible": False,
        "retry_forbidden": True,
        "run_slot_consumed": bool(binding.get("run_slot_consumed")),
        "runner_present": True,
        "runner_script_ref": CLI_REL_PATH,
        "runner_start_count": int(binding.get("runner_start_count") or 0),
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
        "schema_version": ("momentum_v2_vol_scaled_development_evaluation_entry_point_binding.v1"),
        "sealed_allowed": False,
        "signal_family": SIGNAL_FAMILY,
        "status": binding.get("status"),
        "strategy_id": STRATEGY_ID,
        "strategy_identity": STRATEGY_IDENTITY,
        "strategy_params_digest": strategy_params_digest,
        "strategy_signal_ref": STRATEGY_SIGNAL_REL_PATH,
        "strategy_version": STRATEGY_VERSION,
        "time_segment_definition_id": TIME_SEGMENT_DEFINITION_ID,
        "verdict": binding.get("verdict"),
    }


def load_and_validate_entry_point_binding(repo_root: Path) -> dict[str, Any]:
    expected = materialize_entry_point_binding_payload(repo_root)
    path = repo_root / ENTRY_POINT_BINDING_REL_PATH
    _require(path.is_file(), "ENTRY_POINT_BINDING_MISSING")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    for key in (
        "frozen_measurement_contract_digest",
        "development_evaluation_authorized",
        "evaluation_authorized",
        "holdout_forbidden",
        "time_segment_definition_id",
        "baseline_id" if "baseline_id" in loaded else "strategy_identity",
        "productive_exit_pnl_evaluator_ref"
        if "productive_exit_pnl_evaluator_ref" in loaded
        else "runner_script_ref",
    ):
        if key == "baseline_id" and "baseline_id" not in loaded:
            _require(loaded.get("strategy_identity") == STRATEGY_IDENTITY, "IDENTITY_DRIFT")
            continue
        if key == "productive_exit_pnl_evaluator_ref" and key not in loaded:
            _require(loaded.get("runner_script_ref") == CLI_REL_PATH, "RUNNER_REF_DRIFT")
            continue
        _require(loaded.get(key) == expected.get(key), f"ENTRY_POINT_BINDING_DRIFT:{key}")
    _require(loaded.get("hypothesis_id") == HYPOTHESIS_ID, "ENTRY_POINT_HYP_DRIFT")
    _require(loaded.get("strategy_identity") == STRATEGY_IDENTITY, "ENTRY_POINT_STRAT_DRIFT")
    _require(loaded.get("dataset_id") == DATASET_ID, "ENTRY_POINT_DATASET_DRIFT")
    return loaded
