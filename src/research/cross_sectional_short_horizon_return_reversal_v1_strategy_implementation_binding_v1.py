"""Validator for CSRHR v1 strategy-implementation binding."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1_STRATEGY_IMPLEMENTATION_BINDING=true"
)
BINDING_REL_PATH = (
    "config/research/"
    "cross_sectional_short_horizon_return_reversal_v1_strategy_implementation_binding_v1.json"
)
MEASUREMENT_REL_PATH = (
    "config/research/"
    "cross_sectional_short_horizon_return_reversal_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
BACKLOG_REL_PATH = (
    "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
)
REQUIRED_DIGEST = "3d983bbfa1db6c319f6c4399549679a5b7fd2d635d8e72d4452330da9059729a"
REQUIRED_IMPL_FILES = (
    "src/research/cross_sectional_short_horizon_return_reversal_v1_score_v1.py",
    "src/research/cross_sectional_short_horizon_return_reversal_v1_selection_v1.py",
)
REQUIRED_STRATEGY_IDENTITY = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1"
REQUIRED_PROGRAM_ID = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1"
REQUIRED_HYPOTHESIS_ID = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1_STRATEGY_IMPLEMENTATION_ONLY_V1"
)
FORBIDDEN_IMPORT_TOKENS = (
    "src.runtime",
    "src.execution",
    "src.scheduler",
    "src.trading.master_v2",
    "src.risk",
    "requests",
    "urllib",
    "httpx",
    "aiohttp",
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
    _require(payload.get("implementation_authorized") is True, "IMPL_NOT_AUTHORIZED")
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _require(
        payload.get("development_evaluation_authorized") is False,
        "DEVELOPMENT_EVALUATION_AUTHORIZED",
    )
    _require(payload.get("development_run_count") == 0, "DEVELOPMENT_RUN_COUNT")
    _require(payload.get("runner_start_count") == 0, "RUNNER_START_COUNT")
    _require(payload.get("run_slot_consumed") is False, "RUN_SLOT_CONSUMED")
    _require(payload.get("holdout_authorized") is False, "HOLDOUT_AUTHORIZED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(payload.get("promotion_eligible") is False, "PROMOTION_ELIGIBLE")
    _require(payload.get("backtest_authorized") is False, "BACKTEST_AUTHORIZED")
    _require(payload.get("master_v2_mutation") is False, "MASTER_V2_MUTATION")
    _require(
        payload.get("double_play_remains_sole_authority") is True,
        "DOUBLE_PLAY_NOT_SOLE",
    )
    _require(payload.get("automatic_backlog_selection") is False, "AUTOMATIC_SELECTION")
    _require(payload.get("production_strategy_selection") is False, "PRODUCTION_SELECTION")
    _require(
        payload.get("frozen_measurement_contract_digest") == REQUIRED_DIGEST,
        "DIGEST_MISMATCH",
    )
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
    _require(payload.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID")
    _require(payload.get("operator_go_token") == REQUIRED_GO_TOKEN, "GO_TOKEN")
    _require(
        payload.get("score_formula_version") == "negated_raw_trailing_log_return_fixed_lookback_v1",
        "SCORE_FORMULA",
    )
    _require(payload.get("selection_mode") == "single_top1_by_score_desc", "SELECTION_MODE")
    _require(payload.get("polarity") == "REVERSAL_NEGATED_TRAILING_LOG_RETURN", "POLARITY")
    params = payload.get("parameter_defaults") or {}
    _require(params.get("lookback_n") == 24, "LOOKBACK_N")
    _require(params.get("rebalance_interval_bars") == 4, "REBALANCE_INTERVAL")
    _require(params.get("signal_lag_bars") == 1, "SIGNAL_LAG")
    _require(params.get("min_eligible_members_for_rank") == 5, "MIN_ELIGIBLE")
    _require(params.get("vol_normalization") is False, "VOL_NORM")
    non_actions = set(payload.get("explicit_non_actions") or [])
    for required in (
        "NO_EVALUATION",
        "NO_RUNNER",
        "NO_HOLDOUT_ACCESS",
        "NO_SEALED_ACCESS",
        "NO_PROMOTION",
        "NO_RUNTIME",
        "NO_MASTER_V2_MUTATION",
        "NO_DOUBLE_PLAY_AUTHORITY_CHANGE",
        "NO_RUN_SLOT_CONSUMPTION",
        "NO_AUTOMATIC_BACKLOG_SELECTION",
        "NO_PRODUCTION_STRATEGY_SELECTION",
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

    if repo_root is not None:
        for rel in REQUIRED_IMPL_FILES:
            path = repo_root / rel
            _require(path.is_file(), f"MISSING_IMPL_FILE:{rel}")
            text = path.read_text(encoding="utf-8")
            for token in FORBIDDEN_IMPORT_TOKENS:
                _require(token not in text, f"FORBIDDEN_IMPORT:{token}")
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
        _require(measurement.get("run_slot_consumed") is False, "MEASUREMENT_RUN_SLOT")
        _require(
            measurement.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID,
            "MEASUREMENT_HYPOTHESIS_ID",
        )
        backlog_path = repo_root / BACKLOG_REL_PATH
        _require(backlog_path.is_file(), "BACKLOG_MISSING")
        backlog = json.loads(backlog_path.read_text(encoding="utf-8"))
        _require(backlog.get("status") == "OPEN_BACKLOG", "BACKLOG_NOT_OPEN")
        prereg = backlog.get("preregistered_hypotheses") or []
        _require(len(prereg) == 1, "BACKLOG_PREREG_LEN")
        hyp = prereg[0]
        _require(hyp.get("status") == "PREREGISTERED_DEFINITION_ONLY", "BACKLOG_HYP_STATUS")
        _require(hyp.get("run_slot_consumed") is False, "BACKLOG_RUN_SLOT")
        _require(hyp.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "BACKLOG_HYP_ID")

    return {
        "valid": True,
        "strategy_implementation_present": True,
        "evaluation_authorized": False,
        "holdout_authorized": False,
        "run_slot_consumed": False,
        "frozen_digest": REQUIRED_DIGEST,
        "directional_form": "D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION",
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
    }


def load_and_validate_repo_binding(repo_root: Path) -> dict[str, Any]:
    path = repo_root / BINDING_REL_PATH
    _require(path.is_file(), "BINDING_MISSING")
    return validate_implementation_binding(
        json.loads(path.read_text(encoding="utf-8")), repo_root=repo_root
    )
