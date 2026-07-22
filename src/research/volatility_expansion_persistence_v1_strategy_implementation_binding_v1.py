"""Validator for VOLATILITY_EXPANSION_PERSISTENCE_V1 strategy-implementation binding."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "VOLATILITY_EXPANSION_PERSISTENCE_V1_STRATEGY_IMPLEMENTATION_BINDING=true"
BINDING_REL_PATH = (
    "config/research/volatility_expansion_persistence_v1_strategy_implementation_binding_v1.json"
)
MEASUREMENT_REL_PATH = (
    "config/research/"
    "volatility_expansion_persistence_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
REQUIRED_DIGEST = "92e2117ce7e60fe771c4d6e1d6d1aeb8645af80512e21cb9ff21fc4477c7c70e"
REQUIRED_IMPL_FILES = (
    "src/research/price_channel_breakout_core_v1.py",
    "src/research/volatility_expansion_persistence_v1_vol_state_v1.py",
    "src/research/volatility_expansion_persistence_v1_strategy_v1.py",
    "src/research/unconditional_20_bar_price_channel_breakout_v1.py",
)
REQUIRED_STRATEGY_IDENTITY = "VOLATILITY_EXPANSION_PERSISTENCE_V1"
REQUIRED_BASELINE_ID = "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
REQUIRED_PROGRAM_ID = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
REQUIRED_PRODUCTIVE_PNL_REF = (
    "src/research/volatility_compression_breakout_v1_development_evaluation_v1/"
    "productive_exit_pnl_evaluator_v1.py"
)


class ImplementationBindingValidationError(ValueError):
    """Fail-closed implementation-binding validation error."""


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise ImplementationBindingValidationError(code)


def validate_implementation_binding(
    payload: Mapping[str, Any], *, repo_root: Path | None = None
) -> dict[str, Any]:
    _require(
        payload.get("status") == "STRATEGY_IMPLEMENTATION_PRESENT",
        "STATUS_NOT_IMPLEMENTATION_PRESENT",
    )
    _require(payload.get("strategy_implementation_present") is True, "IMPL_PRESENT_FALSE")
    _require(payload.get("baseline_implementation_present") is True, "BASELINE_IMPL_FALSE")
    _require(payload.get("shared_channel_core_present") is True, "SHARED_CORE_FALSE")
    _require(payload.get("implementation_authorized") is True, "IMPL_NOT_AUTHORIZED")
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _require(
        payload.get("development_evaluation_authorized") is False,
        "DEVELOPMENT_EVALUATION_AUTHORIZED",
    )
    _require(payload.get("holdout_authorized") is False, "HOLDOUT_AUTHORIZED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(payload.get("promotion_eligible") is False, "PROMOTION_ELIGIBLE")
    _require(payload.get("backtest_authorized") is False, "BACKTEST_AUTHORIZED")
    _require(payload.get("runner_present") is False, "RUNNER_PRESENT")
    _require(payload.get("master_v2_mutation") is False, "MASTER_V2_MUTATION")
    _require(
        payload.get("double_play_remains_sole_authority") is True,
        "DOUBLE_PLAY_NOT_SOLE",
    )
    _require(
        payload.get("frozen_measurement_contract_digest") == REQUIRED_DIGEST,
        "DIGEST_MISMATCH",
    )
    _require(
        payload.get("frozen_measurement_contract_mutated") is False,
        "MEASUREMENT_CONTRACT_MUTATED",
    )
    _require(payload.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY")
    _require(payload.get("baseline_id") == REQUIRED_BASELINE_ID, "BASELINE_ID")
    _require(payload.get("program_id") == REQUIRED_PROGRAM_ID, "PROGRAM_ID")
    _require(payload.get("strategy_parameters_changed") is False, "STRATEGY_PARAMETERS_CHANGED")
    _require(
        payload.get("strategy_and_baseline_share_identical_channel_core") is True,
        "SHARED_CORE_NOT_IDENTICAL",
    )
    notes = payload.get("implementation_notes") or {}
    _require(notes.get("atr_period") == 14, "ATR_PERIOD_NOT_14")
    _require(
        notes.get("productive_pnl_evaluator_ref") == REQUIRED_PRODUCTIVE_PNL_REF,
        "PRODUCTIVE_PNL_REF",
    )
    non_actions = set(payload.get("explicit_non_actions") or [])
    _require("NO_SECOND_PNL_TRUTH" in non_actions, "SECOND_PNL_NOT_FORBIDDEN")
    _require(
        "NO_VOLATILITY_COMPRESSION_BREAKOUT_V1_RETRY" in non_actions,
        "VCB_RETRY_NOT_FORBIDDEN",
    )
    impl_files = tuple(payload.get("implementation_files") or ())
    _require(impl_files == REQUIRED_IMPL_FILES, "IMPL_FILES_MISMATCH")
    runtime = payload.get("runtime_policy") or {}
    for key in (
        "runtime_activated",
        "shadow_activated",
        "testnet_activated",
        "live_authorized",
        "orders_allowed",
        "scheduler_authorized",
        "capital_activated",
        "paper_activated",
    ):
        _require(runtime.get(key) is False, f"RUNTIME_{key.upper()}")

    if repo_root is not None:
        for rel in REQUIRED_IMPL_FILES:
            _require((repo_root / rel).is_file(), f"MISSING_IMPL_FILE:{rel}")
        _require((repo_root / REQUIRED_PRODUCTIVE_PNL_REF).is_file(), "PRODUCTIVE_PNL_MISSING")
        meas_path = repo_root / MEASUREMENT_REL_PATH
        _require(meas_path.is_file(), "MEASUREMENT_CONTRACT_MISSING")
        measurement = json.loads(meas_path.read_text(encoding="utf-8"))
        _require(
            measurement.get("contract_digest") == REQUIRED_DIGEST,
            "LIVE_MEASUREMENT_DIGEST_MISMATCH",
        )
        _require(
            measurement.get("strategy_implementation_present") is False,
            "MEASUREMENT_CONTRACT_IMPL_FLAG_MUTATED",
        )
        _require(measurement.get("evaluation_authorized") is False, "MEASUREMENT_EVAL_AUTH")
        _require(measurement.get("development_run_count") == 0, "MEASUREMENT_RUN_COUNT")
        _require(measurement.get("runner_start_count") == 0, "MEASUREMENT_RUNNER_START")
        _require(measurement.get("run_slot_consumed") is False, "MEASUREMENT_RUN_SLOT")
        frozen = (measurement.get("parameter_governance") or {}).get("frozen_parameters") or {}
        _require(frozen.get("atr_period") == 14, "MEASUREMENT_ATR_PERIOD")
        _require(frozen.get("expansion_confirmation_threshold") == 0.80, "MEASUREMENT_EXP_THR")
        _require(
            (measurement.get("parameter_governance") or {}).get("open_parameters_remaining")
            is False,
            "OPEN_PARAMETERS_REMAINING",
        )

    return {
        "valid": True,
        "strategy_implementation_present": True,
        "baseline_implementation_present": True,
        "shared_channel_core_present": True,
        "evaluation_authorized": False,
        "holdout_authorized": False,
        "frozen_digest": REQUIRED_DIGEST,
        "baseline_id": REQUIRED_BASELINE_ID,
        "productive_pnl_evaluator_reused": True,
        "second_pnl_truth_created": False,
        "development_run_count": 0,
    }


def load_and_validate_repo_binding(repo_root: Path) -> dict[str, Any]:
    path = repo_root / BINDING_REL_PATH
    _require(path.is_file(), "BINDING_MISSING")
    return validate_implementation_binding(
        json.loads(path.read_text(encoding="utf-8")), repo_root=repo_root
    )
