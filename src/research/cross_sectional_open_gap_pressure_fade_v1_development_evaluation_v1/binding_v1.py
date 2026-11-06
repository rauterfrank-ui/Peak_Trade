"""Deterministic binding/digest resolution for CS open-gap pressure fade v1 eval entry point."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_open_gap_pressure_fade_v1_development_evaluation_v1.constants_v1 import (
    ALLOWED_DATASET_IDS,
    DATASET_CLASS,
    DATASET_ID,
    DEFAULT_LOOKBACK_N,
    DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK,
    DEFAULT_REBALANCE_INTERVAL_BARS,
    DEFAULT_SIGNAL_LAG_BARS,
    EFFECTIVE_ENTRY_COST_BPS,
    EFFECTIVE_EXIT_COST_BPS,
    ENTRY_POINT_BINDING_REL_PATH,
    FEE_BPS_PER_SIDE,
    FORBIDDEN_HOLDOUT_IDS,
    FROZEN_MEASUREMENT_CONTRACT_DIGEST,
    HALF_SPREAD_BPS,
    IMPLEMENTATION_BINDING_REL_PATH,
    MEASUREMENT_CONTRACT_REL_PATH,
    ROUNDTRIP_COST_BPS,
    SCORE_FORMULA_VERSION,
    SIGNAL_FAMILY,
    SLIPPAGE_BPS_PER_SIDE,
    STRATEGY_ID,
    STRATEGY_IDENTITY,
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
    _require(
        contract.get("time_segment_definition_id") == TIME_SEGMENT_DEFINITION_ID,
        "TIME_SEGMENT_DEFINITION_MISMATCH",
    )
    return contract


def resolve_strategy_params(
    *, lookback_n: int | None = None, rebalance_interval_bars: int | None = None
) -> dict[str, Any]:
    params = {
        "lookback_n": int(lookback_n if lookback_n is not None else DEFAULT_LOOKBACK_N),
        "rebalance_interval_bars": int(
            rebalance_interval_bars
            if rebalance_interval_bars is not None
            else DEFAULT_REBALANCE_INTERVAL_BARS
        ),
        "signal_lag_bars": DEFAULT_SIGNAL_LAG_BARS,
        "min_eligible_members_for_rank": DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK,
        "selection_count_fixed_n": 1,
        "vol_normalization": False,
        "score_formula_version": SCORE_FORMULA_VERSION,
        "strategy_id": STRATEGY_ID,
        "strategy_identity": STRATEGY_IDENTITY,
        "strategy_version": STRATEGY_VERSION,
    }
    return params


def compute_strategy_params_digest(
    *, lookback_n: int | None = None, rebalance_interval_bars: int | None = None
) -> str:
    return stable_digest(
        resolve_strategy_params(
            lookback_n=lookback_n, rebalance_interval_bars=rebalance_interval_bars
        )
    )


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
        "execution_model_binding": {
            "effective_entry_cost_bps": EFFECTIVE_ENTRY_COST_BPS,
            "effective_exit_cost_bps": EFFECTIVE_EXIT_COST_BPS,
            "roundtrip_cost_bps": ROUNDTRIP_COST_BPS,
            "execution_model_version": "backtest_execution_v0",
            "execution_price_observation_source": "MODELLED_NOT_OBSERVED",
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


def compute_config_digest(repo_root: Path) -> str:
    contract = resolve_measurement_contract(repo_root)
    impl = load_json(repo_root, IMPLEMENTATION_BINDING_REL_PATH)
    payload = {
        "measurement_contract_digest": contract["contract_digest"],
        "dataset_id": DATASET_ID,
        "dataset_class": DATASET_CLASS,
        "strategy_identity": STRATEGY_IDENTITY,
        "signal_family": SIGNAL_FAMILY,
        "time_segment_definition_id": TIME_SEGMENT_DEFINITION_ID,
        "implementation_binding_status": impl.get("status"),
        "frozen_measurement_contract_digest": impl.get("frozen_measurement_contract_digest"),
        "cost_execution_binding": resolve_cost_execution_binding(contract),
        "strategy_params_default": resolve_strategy_params(),
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
    assert_dataset_allowed(DATASET_ID)
    config_digest = compute_config_digest(repo_root)
    strategy_params_digest = compute_strategy_params_digest()
    return {
        "artifact_kind": "cross_sectional_open_gap_pressure_fade_v1_development_evaluation_entry_point_binding",
        "artifact_version": "v1",
        "authority_effect": "NONE",
        "canonical_ssot": True,
        "cli_ref": (
            "scripts/research/run_evaluate_cross_sectional_open_gap_pressure_fade_development_v1.py"
        ),
        "config_digest": config_digest,
        "dataset_binding": {
            "dataset_class": DATASET_CLASS,
            "dataset_id": DATASET_ID,
            "holdout_forbidden": True,
            "holdout_ids_rejected": sorted(FORBIDDEN_HOLDOUT_IDS),
        },
        "development_evaluation_authorized": bool(
            contract.get("development_evaluation_authorized") is True
        ),
        "development_evaluation_executed": bool(
            contract.get("development_evaluation_executed") is True
        ),
        "development_run_count": int(contract.get("development_run_count") or 0),
        "development_run_limit": 1,
        "economic_gate_open": False,
        "entry_point_status": (
            "EXECUTABLE_EVALUATE_PATH_PRESENT_EVALUATION_EXECUTED"
            if contract.get("development_evaluation_executed") is True
            else "EXECUTABLE_EVALUATE_PATH_PRESENT_AWAITING_OR_AUTHORIZED"
        ),
        "evaluation_authorized": False,
        "evidence_ref": (
            "docs/evidence/evaluate_cross_sectional_open_gap_pressure_fade_development_v1/"
        ),
        "frozen_measurement_contract_digest": FROZEN_MEASUREMENT_CONTRACT_DIGEST,
        "frozen_measurement_contract_ref": MEASUREMENT_CONTRACT_REL_PATH,
        "governance_ref": (
            "docs/governance/"
            "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1.md"
        ),
        "holdout_authorized": False,
        "holdout_forbidden": True,
        "hypothesis_id": contract["hypothesis_id"],
        "implementation_binding_ref": IMPLEMENTATION_BINDING_REL_PATH,
        "lifecycle_authority_ref": (
            "config/research/cross_sectional_open_gap_pressure_fade_hypothesis_backlog_v1.json"
        ),
        "owner_surface": (
            "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1"
        ),
        "program_id": contract["program_id"],
        "promotion_eligible": False,
        "retry_forbidden": True,
        "reused_canonical_owners": {
            "backtest_wiring": "src.research.cross_sectional_single_slot_backtest_wiring_v0",
            "economic_validity_policy": "src.backtest.economic_validity_policy_v1",
            "score": "src.research.cross_sectional_open_gap_pressure_fade_v1_score_v1",
            "selection": "src.research.cross_sectional_open_gap_pressure_fade_v1_selection_v1",
            "stats": "src.backtest.stats",
        },
        "runner_start_count": int(contract.get("runner_start_count") or 0),
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
            "cross_sectional_open_gap_pressure_fade_v1_development_evaluation_"
            "entry_point_binding.v1"
        ),
        "score_formula_version": SCORE_FORMULA_VERSION,
        "signal_family": SIGNAL_FAMILY,
        "slice_class": "DEVELOPMENT_EVALUATION_EXECUTABLE_PATH_IMPLEMENTATION_ONLY",
        "status": (
            "EXECUTABLE_EVALUATE_PATH_PRESENT_EVALUATION_EXECUTED"
            if contract.get("development_evaluation_executed") is True
            else "EXECUTABLE_EVALUATE_PATH_PRESENT_AUTHORIZED_AWAITING_OR_COMPLETE"
        ),
        "strategy_id": STRATEGY_ID,
        "strategy_identity": STRATEGY_IDENTITY,
        "strategy_params_digest": strategy_params_digest,
        "strategy_version": STRATEGY_VERSION,
        "time_segment_definition_id": TIME_SEGMENT_DEFINITION_ID,
        "verdict": (
            "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL"
            if contract.get("development_evaluation_executed") is True
            else "DEVELOPMENT_EVALUATION_AUTHORIZED_SINGLE_RUN_SLOT"
        ),
        "operator_go_token": (
            "GO_CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_"
            "BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION_V1"
        ),
        "scope_id": (
            "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION_V1"
        ),
    }


def write_entry_point_binding(repo_root: Path) -> dict[str, Any]:
    payload = materialize_entry_point_binding_payload(repo_root)
    path = repo_root / ENTRY_POINT_BINDING_REL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return payload


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
    ):
        _require(loaded.get(key) == expected.get(key), f"ENTRY_POINT_BINDING_DRIFT:{key}")
    return loaded
