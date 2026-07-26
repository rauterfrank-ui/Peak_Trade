"""Prepared Development-evaluation entry-point binding validator (no execution)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_"
    "DEVELOPMENT_EVALUATION_ENTRY_POINT=true"
)
BINDING_REL_PATH = (
    "config/research/"
    "momentum_v2_volatility_scaled_own_instrument_continuation_v1_"
    "development_evaluation_entry_point_binding_v1.json"
)
REQUIRED_DIGEST = "0820d94b306cf7b3240bccc2eee06484debdcd7ae1eb77d4a683425247a4c4ce"
REQUIRED_HYPOTHESIS_ID = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
)
REQUIRED_EXEC_GO = (
    "GO_MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_"
    "BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION_V1"
)


class DevelopmentEntryPointValidationError(ValueError):
    """Fail-closed development entry-point validation error."""


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise DevelopmentEntryPointValidationError(code)


def validate_entry_point_binding(
    payload: Mapping[str, Any], *, repo_root: Path | None = None
) -> dict[str, Any]:
    _require(
        payload.get("status") == "PREPARED_SLOT_AVAILABLE_EXECUTION_UNAUTHORIZED",
        "STATUS",
    )
    _require(payload.get("development_evaluation_authorized") is False, "DEV_EVAL_AUTH")
    _require(payload.get("development_evaluation_executed") is False, "DEV_EVAL_EXECUTED")
    _require(payload.get("evaluation_authorized") is False, "EVAL_AUTH")
    _require(payload.get("run_slot_consumed") is False, "SLOT_CONSUMED")
    _require(payload.get("development_run_slot_available") is True, "SLOT_UNAVAILABLE")
    _require(payload.get("development_run_count") == 0, "RUN_COUNT")
    _require(payload.get("runner_start_count") == 0, "RUNNER_START")
    _require(payload.get("holdout_authorized") is False, "HOLDOUT")
    _require(payload.get("sealed_allowed") is False, "SEALED")
    _require(payload.get("promotion_eligible") is False, "PROMOTION")
    _require(payload.get("activation_eligible") is False, "ACTIVATION")
    _require(payload.get("one_shot_consumption_guard") is True, "ONE_SHOT")
    _require(payload.get("retry_forbidden") is True, "RETRY")
    _require(
        payload.get("operator_go_token_required_for_execution") == REQUIRED_EXEC_GO,
        "EXEC_GO",
    )
    _require(
        payload.get("frozen_measurement_contract_digest") == REQUIRED_DIGEST,
        "DIGEST",
    )
    _require(payload.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYP")
    if repo_root is not None:
        runner = repo_root / str(payload.get("runner_script_ref"))
        _require(runner.is_file(), "RUNNER_MISSING")
    return {
        "valid": True,
        "development_evaluation_authorized": False,
        "development_run_slot_available": True,
        "development_run_slot_consumed": False,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
    }


def load_and_validate_repo_entry_point(repo_root: Path) -> dict[str, Any]:
    payload = json.loads((repo_root / BINDING_REL_PATH).read_text(encoding="utf-8"))
    return validate_entry_point_binding(payload, repo_root=repo_root)
