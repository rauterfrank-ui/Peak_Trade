"""Validator for CS open-gap pressure fade v1 strategy-implementation binding."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_open_gap_pressure_fade_v1_hypothesis_preregistration_v1 import (
    compute_contract_digest,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_STRATEGY_IMPLEMENTATION_BINDING=true"
BINDING_REL_PATH = (
    "config/research/"
    "cross_sectional_open_gap_pressure_fade_v1_strategy_implementation_binding_v1.json"
)
MEASUREMENT_REL_PATH = (
    "config/research/"
    "cross_sectional_open_gap_pressure_fade_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
CSRHR_BACKLOG_REL_PATH = (
    "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
)
REQUIRED_IMPL_FILES = (
    "src/research/cross_sectional_open_gap_pressure_fade_v1_score_v1.py",
    "src/research/cross_sectional_open_gap_pressure_fade_v1_selection_v1.py",
)
REQUIRED_STRATEGY_IDENTITY = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1"
REQUIRED_PROGRAM_ID = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_RESEARCH_PROGRAM_V1"
REQUIRED_WORKSTREAM_ID = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_WORKSTREAM_V1"
REQUIRED_HYPOTHESIS_ID = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_GO_TOKEN = "GO_CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_STRATEGY_IMPLEMENTATION_ONLY_V1"
REQUIRED_SCORE_FORMULA_VERSION = "negated_mean_open_gap_fixed_lookback_v1"


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
    _require(payload.get("implementation_authorized") is True, "IMPL_NOT_AUTHORIZED")
    _require(
        payload.get("implementation_matches_preregistration") is True,
        "IMPL_DOES_NOT_MATCH_PREREG",
    )
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _require(
        payload.get("development_evaluation_authorized") is False,
        "DEVELOPMENT_EVALUATION_AUTHORIZED",
    )
    _require(
        payload.get("development_evaluation_executed") is False,
        "DEVELOPMENT_EVALUATION_EXECUTED",
    )
    _require(payload.get("development_run_count") == 0, "DEVELOPMENT_RUN_COUNT")
    _require(payload.get("runner_start_count") == 0, "RUNNER_START_COUNT")
    _require(payload.get("run_slot_consumed") is False, "RUN_SLOT_CONSUMED")
    _require(payload.get("runner_present") is False, "RUNNER_PRESENT")
    _require(payload.get("holdout_authorized") is False, "HOLDOUT_AUTHORIZED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(payload.get("promotion_eligible") is False, "PROMOTION_ELIGIBLE")
    _require(payload.get("backtest_authorized") is False, "BACKTEST_AUTHORIZED")
    _require(payload.get("master_v2_mutation") is False, "MASTER_V2_MUTATION")
    _require(
        payload.get("double_play_remains_sole_authority") is True,
        "DOUBLE_PLAY_NOT_SOLE",
    )
    _require(payload.get("strategy_parameters_changed") is False, "STRATEGY_PARAMETERS_CHANGED")
    _require(
        payload.get("frozen_measurement_contract_mutated") is False,
        "MEASUREMENT_CONTRACT_MUTATED",
    )
    _require(
        payload.get("directional_form") == "D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION",
        "DIRECTIONAL_FORM",
    )
    _require(payload.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY")
    _require(payload.get("program_id") == REQUIRED_PROGRAM_ID, "PROGRAM_ID")
    _require(payload.get("workstream_id") == REQUIRED_WORKSTREAM_ID, "WORKSTREAM_ID")
    _require(payload.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID")
    _require(payload.get("operator_go_token") == REQUIRED_GO_TOKEN, "GO_TOKEN")
    _require(
        payload.get("score_formula_version") == REQUIRED_SCORE_FORMULA_VERSION,
        "SCORE_FORMULA",
    )
    _require(payload.get("selection_mode") == "single_top1_by_score_desc", "SELECTION_MODE")
    params = payload.get("parameter_defaults") or {}
    _require(params.get("lookback_n") == 30, "LOOKBACK_N")
    _require(params.get("rebalance_interval_bars") == 5, "REBALANCE_INTERVAL")
    _require(params.get("signal_lag_bars") == 1, "SIGNAL_LAG")
    _require(params.get("min_eligible_members_for_rank") == 5, "MIN_ELIGIBLE")
    _require(params.get("selection_count_fixed_n") == 1, "SELECTION_N")
    _require(params.get("vol_normalization") is False, "VOL_NORM")
    # Fail-closed against CLV residue parameters.
    _require(params.get("lookback_n") != 36, "CLV_LOOKBACK_RESIDUE")
    _require(params.get("rebalance_interval_bars") != 6, "CLV_REBALANCE_RESIDUE")
    non_actions = set(payload.get("explicit_non_actions") or [])
    for required in (
        "NO_EVALUATION",
        "NO_RUNNER",
        "NO_HOLDOUT_ACCESS",
        "NO_CSRHR_MUTATION",
        "NO_CSRHR_CONTINUE",
        "NO_CSRHR_SEMANTIC_REUSE",
        "NO_PATH_EFFICIENCY_RETRY",
        "NO_CLV_PRESSURE_RETRY",
        "NO_DEVELOPMENT_EVALUATION_EXECUTION_IN_THIS_SLICE",
        "NO_RUN_SLOT_CONSUMPTION",
    ):
        _require(required in non_actions, f"MISSING_NON_ACTION_{required}")
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

    frozen_digest = str(payload.get("frozen_measurement_contract_digest") or "")
    _require(bool(frozen_digest), "FROZEN_DIGEST_MISSING")

    if repo_root is not None:
        for rel in REQUIRED_IMPL_FILES:
            _require((repo_root / rel).is_file(), f"MISSING_IMPL_FILE:{rel}")
        meas_path = repo_root / MEASUREMENT_REL_PATH
        _require(meas_path.is_file(), "MEASUREMENT_CONTRACT_MISSING")
        measurement = json.loads(meas_path.read_text(encoding="utf-8"))
        live_digest = compute_contract_digest(measurement)
        _require(
            measurement.get("contract_digest") == live_digest,
            "LIVE_MEASUREMENT_DIGEST_FIELD_MISMATCH",
        )
        _require(frozen_digest == live_digest, "BINDING_DIGEST_NOT_PREREGISTRATION")
        _require(
            measurement.get("strategy_implementation_present") is False,
            "MEASUREMENT_CONTRACT_IMPL_FLAG_MUTATED",
        )
        _require(measurement.get("evaluation_authorized") is False, "MEASUREMENT_EVAL_FLIPPED")
        _require(
            measurement.get("development_evaluation_executed") is False,
            "MEASUREMENT_DEV_EVAL_EXECUTED",
        )
        _require(measurement.get("development_run_count") == 0, "MEASUREMENT_DEV_RUN_MUTATED")
        _require(measurement.get("run_slot_consumed") is False, "MEASUREMENT_RUN_SLOT_MUTATED")
        csrhr = json.loads((repo_root / CSRHR_BACKLOG_REL_PATH).read_text(encoding="utf-8"))
        _require(csrhr.get("status") == "OPEN_BACKLOG", "CSRHR_MUTATED")
        _require(csrhr.get("development_run_count") == 0, "CSRHR_DEV_RUN_MUTATED")

    return {
        "valid": True,
        "strategy_implementation_present": True,
        "implementation_matches_preregistration": True,
        "evaluation_authorized": False,
        "development_evaluation_executed": False,
        "development_run_count": 0,
        "run_slot_consumed": False,
        "holdout_authorized": False,
        "frozen_digest": frozen_digest,
        "directional_form": "D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION",
        "double_play_remains_sole_authority": True,
        "csrhr_unchanged": True,
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
    "REQUIRED_SCORE_FORMULA_VERSION",
    "load_and_validate_repo_binding",
    "validate_implementation_binding",
]
