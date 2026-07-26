"""Validator for Momentum V2 vol-scaled strategy-implementation binding v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_"
    "STRATEGY_IMPLEMENTATION_BINDING=true"
)
BINDING_REL_PATH = (
    "config/research/"
    "momentum_v2_volatility_scaled_own_instrument_continuation_v1_"
    "strategy_implementation_binding_v1.json"
)
MEASUREMENT_REL_PATH = (
    "config/research/"
    "momentum_v2_volatility_scaled_own_instrument_continuation_v1_preregistered_"
    "economic_hypothesis_measurement_contract_v1.json"
)
BACKLOG_REL_PATH = (
    "config/research/momentum_v2_volatility_scaled_own_instrument_continuation_"
    "hypothesis_backlog_v1.json"
)
NEAR_DUP_REL_PATH = (
    "config/research/momentum_v2_volatility_scaled_own_instrument_continuation_v1_"
    "near_duplicate_gate_v1.json"
)
SELECTION_REL_PATH = (
    "config/research/momentum_v2_volatility_scaled_own_instrument_continuation_v1_"
    "operator_selection_record_v1.json"
)
REQUIRED_DIGEST = "0820d94b306cf7b3240bccc2eee06484debdcd7ae1eb77d4a683425247a4c4ce"
REQUIRED_IMPL_FILES = (
    "src/research/momentum_v2_volatility_scaled_own_instrument_continuation_v1_signal_v1.py",
)
REQUIRED_STRATEGY_IDENTITY = "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1"
REQUIRED_PROGRAM_ID = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_RESEARCH_PROGRAM_V1"
)
REQUIRED_HYPOTHESIS_ID = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
)
REQUIRED_GO_TOKEN = (
    "GO_MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_"
    "SELECTION_AND_OFFLINE_STRATEGY_IMPLEMENTATION_V1"
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
        payload.get("status")
        == "STRATEGY_IMPLEMENTATION_PRESENT_DEVELOPMENT_EVALUATION_EXECUTED_FAIL",
        "STATUS_NOT_IMPLEMENTATION_PRESENT",
    )
    _require(payload.get("strategy_implementation_present") is True, "IMPL_PRESENT_FALSE")
    _require(payload.get("implementation_authorized") is True, "IMPL_NOT_AUTHORIZED")
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _require(
        payload.get("development_evaluation_authorized") is False,
        "DEVELOPMENT_EVALUATION_AUTHORIZED",
    )
    _require(
        payload.get("development_evaluation_executed") is True,
        "DEVELOPMENT_EVALUATION_EXECUTED",
    )
    _require(payload.get("development_run_count") == 1, "DEVELOPMENT_RUN_COUNT")
    _require(payload.get("runner_start_count") == 1, "RUNNER_START_COUNT")
    _require(payload.get("run_slot_consumed") is True, "RUN_SLOT_CONSUMED")
    _require(
        payload.get("development_run_slot_available") is False,
        "RUN_SLOT_STILL_AVAILABLE",
    )
    _require(payload.get("holdout_authorized") is False, "HOLDOUT_AUTHORIZED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(payload.get("promotion_eligible") is False, "PROMOTION_ELIGIBLE")
    _require(payload.get("backtest_authorized") is False, "BACKTEST_AUTHORIZED")
    _require(payload.get("master_v2_mutation") is False, "MASTER_V2_MUTATION")
    _require(
        payload.get("double_play_remains_sole_authority") is True,
        "DOUBLE_PLAY_NOT_SOLE",
    )
    _require(payload.get("short_entry_forbidden") is True, "SHORT_ENTRY_ALLOWED")
    _require(payload.get("entry_side") == "NONE", "ENTRY_SIDE")
    _require(
        payload.get("near_duplicate_verdict") == "MATERIALLY_DISTINCT",
        "NEAR_DUPLICATE_NOT_DISTINCT",
    )
    _require(
        payload.get("frozen_measurement_contract_digest") == REQUIRED_DIGEST,
        "DIGEST_MISMATCH",
    )
    _require(
        payload.get("frozen_measurement_contract_mutated") is False,
        "MEASUREMENT_CONTRACT_MUTATED",
    )
    _require(
        payload.get("directional_form") == "OWN_INSTRUMENT_LONG_ENTRY_EXIT_EVENT_TIMING_ONLY",
        "DIRECTIONAL_FORM",
    )
    _require(payload.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY")
    _require(payload.get("program_id") == REQUIRED_PROGRAM_ID, "PROGRAM_ID")
    _require(payload.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID")
    _require(payload.get("operator_go_token") == REQUIRED_GO_TOKEN, "GO_TOKEN")
    _require(
        payload.get("signal_formula_version")
        == "vol_scaled_raw_return_over_trailing_realized_vol_v1",
        "SIGNAL_FORMULA",
    )
    params = payload.get("parameter_defaults") or {}
    _require(params.get("lookback_period") == 20, "LOOKBACK")
    _require(params.get("signal_lag_bars") == 1, "SIGNAL_LAG")
    _require(params.get("vol_scaled_entry_z") == 1.0, "ENTRY_Z")
    _require(params.get("vol_scaled_exit_z") == 0.0, "EXIT_Z")
    _require(params.get("vol_scaling_required") is True, "VOL_SCALING")
    _require(params.get("short_entry_forbidden") is True, "SHORT_ENTRY_PARAM")
    non_actions = set(payload.get("explicit_non_actions") or [])
    for required in (
        "NO_HOLDOUT_ACCESS",
        "NO_SEALED_ACCESS",
        "NO_PROMOTION",
        "NO_RUNTIME",
        "NO_MASTER_V2_MUTATION",
        "NO_DOUBLE_PLAY_AUTHORITY_CHANGE",
        "NO_AUTOMATIC_BACKLOG_SELECTION",
        "NO_SECOND_DEVELOPMENT_RUN",
        "NO_REGISTRY_MUTATION",
        "NO_SHORT_ENTRY",
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
            measurement.get("development_run_count") == 0,
            "MEASUREMENT_DEV_RUN_MUTATED",
        )
        _require(
            measurement.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID,
            "MEASUREMENT_HYPOTHESIS_ID",
        )
        near = json.loads((repo_root / NEAR_DUP_REL_PATH).read_text(encoding="utf-8"))
        _require(near.get("verdict") == "MATERIALLY_DISTINCT", "NEAR_DUP_VERDICT")
        sel = json.loads((repo_root / SELECTION_REL_PATH).read_text(encoding="utf-8"))
        _require(sel.get("selection_authorized") is True, "SELECTION_NOT_AUTHORIZED")
        _require(
            sel.get("development_run_slot_consumed") is True,
            "SELECTION_SLOT_NOT_CONSUMED",
        )
        _require(sel.get("development_run_slot_available") is False, "SELECTION_SLOT_AVAILABLE")
        backlog = json.loads((repo_root / BACKLOG_REL_PATH).read_text(encoding="utf-8"))
        _require(
            backlog.get("status") == "LANE_CLOSED_NO_FURTHER_RESEARCH",
            "BACKLOG_NOT_CLOSED",
        )
        _require(backlog.get("preregistered_hypotheses") == [], "BACKLOG_PREREG_NONEMPTY")
        terminals = backlog.get("terminal_hypotheses") or []
        _require(len(terminals) == 1, "BACKLOG_TERMINAL_LEN")
        hyp = terminals[0]
        _require(hyp.get("implementation_present") is True, "BACKLOG_IMPL_PRESENT")
        _require(hyp.get("run_slot_consumed") is True, "BACKLOG_RUN_SLOT")
        _require(hyp.get("development_run_count") == 1, "BACKLOG_DEV_RUNS")
        _require(hyp.get("status") == "TERMINAL_FAIL", "BACKLOG_HYP_STATUS")
        _require(hyp.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "BACKLOG_HYP_ID")
        _require(hyp.get("retry_allowed") is False, "BACKLOG_RETRY_ALLOWED")
        _require(hyp.get("holdout_allowed") is False, "BACKLOG_HOLDOUT_ALLOWED")
        _require(backlog.get("development_evaluation_authorized") is False, "BACKLOG_DEV_EVAL")

    return {
        "valid": True,
        "strategy_implementation_present": True,
        "evaluation_authorized": False,
        "holdout_authorized": False,
        "run_slot_consumed": True,
        "development_run_slot_available": False,
        "frozen_digest": REQUIRED_DIGEST,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "near_duplicate_verdict": "MATERIALLY_DISTINCT",
        "development_evaluation_executed": True,
    }


def load_and_validate_repo_binding(repo_root: Path) -> dict[str, Any]:
    payload = json.loads((repo_root / BINDING_REL_PATH).read_text(encoding="utf-8"))
    return validate_implementation_binding(payload, repo_root=repo_root)
