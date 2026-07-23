"""Validator for VTDC v1 strategy-implementation binding."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.volatility_term_structure_depressed_continuation_v1_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    compute_contract_digest,
)

PACKAGE_MARKER = (
    "VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1_STRATEGY_IMPLEMENTATION_BINDING=true"
)
BINDING_REL_PATH = (
    "config/research/volatility_term_structure_depressed_continuation_v1_"
    "strategy_implementation_binding_v1.json"
)
REQUIRED_DIGEST = "280eaec6dca1cb8e6cf1c62ec2ff5913abcf659a03811cadf6d0e01188d45ec8"
REQUIRED_STRATEGY_IDENTITY = "VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1"
REQUIRED_PREDECESSOR = "VOLATILITY_TERM_STRUCTURE_REVERSION_V1"
REQUIRED_BASELINE_ID = "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
REQUIRED_PROGRAM_ID = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
REQUIRED_PRODUCTIVE_PNL_REF = (
    "src/research/volatility_compression_breakout_v1_development_evaluation_v1/"
    "productive_exit_pnl_evaluator_v1.py"
)
REQUIRED_IMPL_FILES = (
    "src/research/volatility_term_structure_depressed_continuation_v1_vol_state_v1.py",
    "src/research/volatility_term_structure_depressed_continuation_v1_exit_state_machine_v1.py",
    "src/research/volatility_term_structure_depressed_continuation_v1_strategy_v1.py",
    "src/research/unconditional_20_bar_price_channel_breakout_v1.py",
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
    _require(payload.get("exit_state_machine_implemented") is True, "EXIT_SM_FALSE")
    _require(payload.get("entry_only_implementation") is False, "ENTRY_ONLY_TRUE")
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
    _require(payload.get("predecessor_strategy_id") == REQUIRED_PREDECESSOR, "PREDECESSOR")
    _require(payload.get("baseline_id") == REQUIRED_BASELINE_ID, "BASELINE_ID")
    _require(payload.get("program_id") == REQUIRED_PROGRAM_ID, "PROGRAM_ID")
    _require(payload.get("strategy_parameters_changed") is False, "STRATEGY_PARAMETERS_CHANGED")
    notes = payload.get("implementation_notes") or {}
    _require(notes.get("rv_short_horizon_completed_bars") == 8, "RV_SHORT_NOT_8")
    _require(notes.get("rv_long_horizon_completed_bars") == 48, "RV_LONG_NOT_48")
    _require(notes.get("trailing_stop_forbidden") is True, "TRAILING_ALLOWED")
    _require(
        notes.get("vol_estimator_family") == "REALIZED_VOLATILITY_TERM_STRUCTURE",
        "VOL_FAMILY",
    )
    _require(
        notes.get("productive_pnl_evaluator_ref") == REQUIRED_PRODUCTIVE_PNL_REF,
        "PRODUCTIVE_PNL_REF",
    )
    non_actions = set(payload.get("explicit_non_actions") or [])
    _require("NO_SECOND_PNL_TRUTH" in non_actions, "SECOND_PNL_NOT_FORBIDDEN")
    _require("NO_VTSR_V1_RETRY" in non_actions, "VTSR_RETRY_NOT_FORBIDDEN")
    _require("NO_TRAILING_STOP" in non_actions, "TRAILING_NOT_FORBIDDEN")
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
        meas_path = repo_root / CONTRACT_REL_PATH
        _require(meas_path.is_file(), "MEASUREMENT_CONTRACT_MISSING")
        contract = json.loads(meas_path.read_text(encoding="utf-8"))
        digest = compute_contract_digest(contract)
        _require(digest == REQUIRED_DIGEST, "LIVE_DIGEST_MISMATCH")
        _require(contract.get("contract_digest") == REQUIRED_DIGEST, "CONTRACT_DIGEST_FIELD")
        _require(contract.get("strategy_implementation_present") is False, "CONTRACT_IMPL_FLIPPED")

    return {
        "valid": True,
        "strategy_identity": REQUIRED_STRATEGY_IDENTITY,
        "strategy_implementation_present": True,
        "exit_state_machine_implemented": True,
        "evaluation_authorized": False,
        "development_evaluation_authorized": False,
        "frozen_measurement_contract_digest": REQUIRED_DIGEST,
    }


def load_and_validate_repo_binding(repo_root: Path) -> dict[str, Any]:
    path = repo_root / BINDING_REL_PATH
    _require(path.is_file(), "BINDING_MISSING")
    return validate_implementation_binding(
        json.loads(path.read_text(encoding="utf-8")), repo_root=repo_root
    )


__all__ = [
    "BINDING_REL_PATH",
    "ImplementationBindingValidationError",
    "PACKAGE_MARKER",
    "REQUIRED_DIGEST",
    "load_and_validate_repo_binding",
    "validate_implementation_binding",
]
