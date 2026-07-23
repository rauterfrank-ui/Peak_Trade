"""Definition-only SSOT validator for CS short-horizon return-reversal program v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1=true"
PROGRAM_REL_PATH = (
    "config/research/cross_sectional_short_horizon_return_reversal_research_program_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1.md"
)
REQUIRED_PROGRAM_ID = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1"
REQUIRED_STATUS = "DEFINITION_ONLY"
REQUIRED_SIGNAL_FAMILY = "CROSS_SECTIONAL_RETURN_REVERSAL"
REQUIRED_TARGET = "SHORT_HORIZON_CROSS_SECTIONAL_RELATIVE_RETURN_REVERSAL"
REQUIRED_HYPOTHESIS_ID = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_STRATEGY_IDENTITY = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1"
CLOSED_VOL = "config/research/volatility_regime_research_program_v1.json"
CLOSED_CS_MOM = "config/research/material_different_cross_sectional_momentum_program_v1.json"
REQUIRED_CLOSED_PROGRAM = "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"


class ProgramValidationError(ValueError):
    """Fail-closed program SSOT validation error."""


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise ProgramValidationError(code)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_program_contract(
    payload: Mapping[str, Any], *, repo_root: Path | None = None
) -> dict[str, Any]:
    _require(payload.get("program_id") == REQUIRED_PROGRAM_ID, "PROGRAM_ID_MISMATCH")
    _require(payload.get("status") == REQUIRED_STATUS, "STATUS_NOT_DEFINITION_ONLY")
    _require(payload.get("program_family") == "CROSS_SECTIONAL_RETURN_REVERSAL", "FAMILY")
    _require(
        payload.get("slice_class") == "DEFINITION_ONLY_GOVERNANCE",
        "SLICE_NOT_DEFINITION_ONLY_GOVERNANCE",
    )
    _require(payload.get("authority_effect") == "NONE", "AUTHORITY_EFFECT_NOT_NONE")
    _require(payload.get("runtime_effect") == "NONE", "RUNTIME_EFFECT_NOT_NONE")
    _require(payload.get("signal_family") == REQUIRED_SIGNAL_FAMILY, "SIGNAL_FAMILY")
    _require(payload.get("target_phenomenon") == REQUIRED_TARGET, "TARGET_PHENOMENON")
    _require(payload.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID")
    _require(payload.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY")
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED_TRUE")
    _require(
        payload.get("development_evaluation_authorized") is False,
        "DEVELOPMENT_EVALUATION_AUTHORIZED_TRUE",
    )
    _require(
        payload.get("development_evaluation_executed") is False,
        "DEVELOPMENT_EVALUATION_EXECUTED_TRUE",
    )
    _require(payload.get("development_run_count") == 0, "DEVELOPMENT_RUN_COUNT_NOT_ZERO")
    _require(payload.get("runner_start_count") == 0, "RUNNER_START_COUNT_NOT_ZERO")
    _require(payload.get("run_slot_consumed") is False, "RUN_SLOT_CONSUMED")
    _require(payload.get("run_budget_consumed") is False, "RUN_BUDGET_CONSUMED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(payload.get("implementation_authorized") is False, "IMPLEMENTATION_AUTHORIZED")
    _require(
        payload.get("strategy_implementation_present") is False,
        "STRATEGY_IMPLEMENTATION_PRESENT",
    )
    _require(payload.get("runtime_authorized") is False, "RUNTIME_AUTHORIZED")
    _require(
        payload.get("requires_new_separate_operator_authorization_for_evaluation") is True,
        "EVAL_GO_NOT_REQUIRED",
    )
    independence = payload.get("causal_independence") or {}
    _require(
        independence.get("independent_from_closed_volatility_regime_program") is True,
        "NOT_INDEPENDENT_OF_VOL_REGIME",
    )
    _require(
        independence.get("independent_from_closed_cross_sectional_momentum_lane") is True,
        "NOT_INDEPENDENT_OF_CS_MOMENTUM",
    )
    _require(
        independence.get("not_a_retry_of_terminal_cross_sectional_relative_strength_momentum_v1")
        is True,
        "CS_MOMENTUM_RETRY_NOT_FORBIDDEN",
    )
    _require(
        independence.get("not_a_volatility_regime_reopen") is True,
        "VOL_REGIME_REOPEN_NOT_FORBIDDEN",
    )
    rt = payload.get("runtime_policy") or {}
    for key in (
        "live_authorized",
        "orders_allowed",
        "shadow_activated",
        "paper_activated",
        "testnet_activated",
        "scheduler_authorized",
        "runtime_activated",
    ):
        _require(rt.get(key) is False, f"RUNTIME_POLICY_{key.upper()}")
    econ = payload.get("promotion_and_economic_gate_policy") or {}
    _require(econ.get("economic_gate_open") is False, "ECONOMIC_GATE_OPEN")
    _require(econ.get("promotion_eligible") is False, "PROMOTION_ELIGIBLE")
    universe = payload.get("universe_scope") or {}
    _require(universe.get("bitcoin_excluded") is True, "BTC_NOT_EXCLUDED")
    _require(universe.get("spot_excluded") is True, "SPOT_NOT_EXCLUDED")
    _require(universe.get("venue") == "OKX", "VENUE_NOT_OKX")
    _require(universe.get("frequency") == "PT1H", "TIMEFRAME_NOT_PT1H")

    if repo_root is not None:
        vol = load_json(repo_root / CLOSED_VOL)
        mom = load_json(repo_root / CLOSED_CS_MOM)
        _require(vol.get("status") == REQUIRED_CLOSED_PROGRAM, "VOL_REGIME_NOT_CLOSED")
        _require(mom.get("status") == REQUIRED_CLOSED_PROGRAM, "CS_MOMENTUM_NOT_CLOSED")
        gov = repo_root / GOVERNANCE_REL_PATH
        _require(gov.is_file(), "GOVERNANCE_DOC_MISSING")

    return {
        "valid": True,
        "definition_only": True,
        "program_id": REQUIRED_PROGRAM_ID,
        "status": REQUIRED_STATUS,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "evaluation_authorized": False,
        "development_run_count": 0,
        "holdout_forbidden": True,
    }


def load_and_validate_repo_program(repo_root: Path) -> dict[str, Any]:
    payload = load_json(repo_root / PROGRAM_REL_PATH)
    return validate_program_contract(payload, repo_root=repo_root)
