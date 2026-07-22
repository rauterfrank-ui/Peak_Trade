"""Definition-only SSOT validator for MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_PROGRAM_V1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_PROGRAM_V1=true"
PROGRAM_REL_PATH = "config/research/material_different_cross_sectional_momentum_program_v1.json"
GOVERNANCE_REL_PATH = "docs/governance/MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_PROGRAM_V1.md"
REQUIRED_PROGRAM_ID = "MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_PROGRAM_V1"
REQUIRED_STATUS = "STRATEGY_IMPLEMENTATION_PRESENT_PROGRAM_OPEN"
REQUIRED_STRATEGY_IDENTITY = "CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1"
REQUIRED_SIGNAL_FAMILY = "CROSS_SECTIONAL_MOMENTUM"
REQUIRED_TARGET_PHENOMENON = "PERSISTENCE_OF_RELATIVE_RETURNS_ACROSS_NON_BTC_LINEAR_USDT_FUTURES"
CLOSED_ENTRY_BACKLOG = (
    "config/research/canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.json"
)
CLOSED_EXIT_BACKLOG = "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
REQUIRED_CLOSED_STATUS = "LANE_CLOSED_NO_FURTHER_RESEARCH"


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
    _require(payload.get("status") == REQUIRED_STATUS, "STATUS_NOT_DEFINITION_ONLY_OPEN")
    _require(
        payload.get("slice_class") == "STRATEGY_IMPLEMENTATION_ONLY",
        "SLICE_NOT_STRATEGY_IMPLEMENTATION_ONLY",
    )
    _require(payload.get("authority_effect") == "NONE", "AUTHORITY_EFFECT_NOT_NONE")
    _require(payload.get("runtime_effect") == "NONE", "RUNTIME_EFFECT_NOT_NONE")
    _require(
        payload.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY_MISMATCH"
    )
    _require(payload.get("signal_family") == REQUIRED_SIGNAL_FAMILY, "SIGNAL_FAMILY_MISMATCH")
    _require(
        payload.get("target_phenomenon") == REQUIRED_TARGET_PHENOMENON,
        "TARGET_PHENOMENON_MISMATCH",
    )
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED_TRUE")
    _require(
        payload.get("development_evaluation_authorized") is True,
        "DEVELOPMENT_EVALUATION_AUTHORIZED_FALSE",
    )
    _require(payload.get("holdout_authorized") is False, "HOLDOUT_AUTHORIZED_TRUE")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(payload.get("promotion_authorized") is False, "PROMOTION_AUTHORIZED_TRUE")
    _require(payload.get("runtime_authorized") is False, "RUNTIME_AUTHORIZED_TRUE")
    _require(payload.get("development_run_count") == 0, "DEVELOPMENT_RUN_COUNT_NONZERO")
    _require(payload.get("runner_start_count") == 0, "RUNNER_START_COUNT_NONZERO")
    _require(payload.get("run_slot_consumed") is False, "RUN_SLOT_CONSUMED")
    _require(
        payload.get("strategy_implementation_present") is True,
        "STRATEGY_IMPLEMENTATION_PRESENT_FALSE",
    )
    _require(
        payload.get("strategy_implementation_authorized_in_this_slice") is True,
        "STRATEGY_IMPLEMENTATION_NOT_AUTHORIZED",
    )
    _require(payload.get("implementation_authorized") is True, "IMPLEMENTATION_AUTHORIZED_FALSE")
    gates = payload.get("promotion_and_economic_gate_policy") or {}
    _require(gates.get("promotion_eligible") is False, "PROMOTION_ELIGIBLE_TRUE")
    _require(gates.get("economic_gate_open") is False, "ECONOMIC_GATE_OPEN")
    runtime = payload.get("runtime_policy") or {}
    for key in (
        "runtime_activated",
        "shadow_activated",
        "paper_activated",
        "testnet_activated",
        "live_authorized",
        "orders_allowed",
        "scheduler_authorized",
        "capital_activated",
    ):
        _require(runtime.get(key) is False, f"RUNTIME_POLICY_{key.upper()}_TRUE")
    independence = payload.get("causal_independence") or {}
    _require(
        independence.get("independent_from_closed_entry_eligibility_lane") is True,
        "NOT_INDEPENDENT_FROM_ENTRY_LANE",
    )
    _require(
        independence.get("independent_from_closed_exit_efficiency_lane") is True,
        "NOT_INDEPENDENT_FROM_EXIT_LANE",
    )
    _require(
        independence.get("prior_terminal_relative_strength_v0_retry_forbidden") is True,
        "RS_V0_RETRY_NOT_FORBIDDEN",
    )
    forbidden = set(independence.get("forbidden_lineage_refs") or [])
    for required in (
        "bollinger_bands_mean_reversion",
        "midband_exit_logic",
        "reentry_cooldown",
        "adx_di_direction_confirmation",
        "regime_gated_standaside",
    ):
        _require(required in forbidden, f"MISSING_FORBIDDEN_LINEAGE:{required}")

    if repo_root is not None:
        entry = load_json(repo_root / CLOSED_ENTRY_BACKLOG)
        exitb = load_json(repo_root / CLOSED_EXIT_BACKLOG)
        _require(entry.get("status") == REQUIRED_CLOSED_STATUS, "ENTRY_LANE_NOT_CLOSED")
        _require(exitb.get("status") == REQUIRED_CLOSED_STATUS, "EXIT_LANE_NOT_CLOSED")
        _require(entry.get("explicit_closeout_decision") is True, "ENTRY_CLOSEOUT_FALSE")
        _require(exitb.get("explicit_closeout_decision") is True, "EXIT_CLOSEOUT_FALSE")

    return {
        "valid": True,
        "program_id": REQUIRED_PROGRAM_ID,
        "status": REQUIRED_STATUS,
        "strategy_identity": REQUIRED_STRATEGY_IDENTITY,
        "definition_only": False,
        "strategy_implementation_present": True,
        "holdout_authorized": False,
        "evaluation_authorized": False,
        "promotion_eligible": False,
        "development_run_count": 0,
        "runner_start_count": 0,
    }


def load_and_validate_repo_program(repo_root: Path) -> dict[str, Any]:
    path = repo_root / PROGRAM_REL_PATH
    _require(path.is_file(), "PROGRAM_SSOT_MISSING")
    return validate_program_contract(load_json(path), repo_root=repo_root)
