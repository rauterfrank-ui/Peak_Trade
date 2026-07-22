"""Validator for VOLATILITY_COMPRESSION_BREAKOUT_V1 strategy-implementation binding."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "VOLATILITY_COMPRESSION_BREAKOUT_V1_STRATEGY_IMPLEMENTATION_BINDING=true"
BINDING_REL_PATH = (
    "config/research/volatility_compression_breakout_v1_strategy_implementation_binding_v1.json"
)
MEASUREMENT_REL_PATH = (
    "config/research/"
    "volatility_compression_breakout_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
REQUIRED_DIGEST = "e8edbb7d2cbc55fa7ca979b3f1fc882fa56c03bd91cc2e708f0100342fae3785"
REQUIRED_IMPL_FILES = (
    "src/research/price_channel_breakout_core_v1.py",
    "src/research/volatility_compression_breakout_v1_vol_state_v1.py",
    "src/research/volatility_compression_breakout_v1_strategy_v1.py",
    "src/research/unconditional_20_bar_price_channel_breakout_v1.py",
)
REQUIRED_STRATEGY_IDENTITY = "VOLATILITY_COMPRESSION_BREAKOUT_V1"
REQUIRED_BASELINE_ID = "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
REQUIRED_PROGRAM_ID = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"


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
    _require(
        payload.get("strategy_and_baseline_share_identical_channel_core") is True,
        "SHARED_CORE_NOT_IDENTICAL",
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

    return {
        "valid": True,
        "strategy_implementation_present": True,
        "baseline_implementation_present": True,
        "shared_channel_core_present": True,
        "evaluation_authorized": False,
        "holdout_authorized": False,
        "frozen_digest": REQUIRED_DIGEST,
        "baseline_id": REQUIRED_BASELINE_ID,
    }


def load_and_validate_repo_binding(repo_root: Path) -> dict[str, Any]:
    path = repo_root / BINDING_REL_PATH
    _require(path.is_file(), "BINDING_MISSING")
    return validate_implementation_binding(
        json.loads(path.read_text(encoding="utf-8")), repo_root=repo_root
    )
