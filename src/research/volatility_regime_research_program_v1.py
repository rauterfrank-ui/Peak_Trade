"""Definition-only SSOT validator for VOLATILITY_REGIME_RESEARCH_PROGRAM_V1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1=true"
PROGRAM_REL_PATH = "config/research/volatility_regime_research_program_v1.json"
GOVERNANCE_REL_PATH = "docs/governance/VOLATILITY_REGIME_RESEARCH_PROGRAM_V1.md"
REQUIRED_PROGRAM_ID = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
REQUIRED_STATUS = "DEFINITION_ONLY_PROGRAM_OPEN"
REQUIRED_STRATEGY_IDENTITY = "VOLATILITY_COMPRESSION_BREAKOUT_V1"
REQUIRED_SIGNAL_FAMILY = "VOLATILITY_REGIME"
REQUIRED_TARGET_PHENOMENON = "VOLATILITY_COMPRESSION_TO_EXPANSION_TRANSITION"
REQUIRED_PRIOR_HYPOTHESIS = "VOL_BREAKOUT_COILED_SPRING_NON_BITCOIN_FUTURES_V1"
CLOSED_ENTRY_BACKLOG = (
    "config/research/canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.json"
)
CLOSED_EXIT_BACKLOG = "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
CLOSED_CS_MOMENTUM_PROGRAM = (
    "config/research/material_different_cross_sectional_momentum_program_v1.json"
)
REQUIRED_CLOSED = "LANE_CLOSED_NO_FURTHER_RESEARCH"
REQUIRED_CS_CLOSED = "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"


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
        payload.get("slice_class") == "DEFINITION_ONLY_GOVERNANCE",
        "SLICE_NOT_DEFINITION_ONLY_GOVERNANCE",
    )
    _require(payload.get("authority_effect") == "NONE", "AUTHORITY_EFFECT_NOT_NONE")
    _require(payload.get("runtime_effect") == "NONE", "RUNTIME_EFFECT_NOT_NONE")
    _require(
        payload.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY,
        "STRATEGY_IDENTITY_MISMATCH",
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
    _require(
        payload.get("sealed_holdout_binding_status") == "UNBOUND_UNTOUCHED",
        "HOLDOUT_NOT_UNBOUND",
    )
    _require(payload.get("promotion_authorized") is False, "PROMOTION_AUTHORIZED_TRUE")
    _require(payload.get("runtime_authorized") is False, "RUNTIME_AUTHORIZED_TRUE")
    _require(payload.get("implementation_authorized") is False, "IMPLEMENTATION_AUTHORIZED_TRUE")
    _require(
        payload.get("strategy_implementation_present") is False,
        "STRATEGY_IMPLEMENTATION_PRESENT_TRUE",
    )
    _require(
        payload.get("strategy_implementation_authorized_in_this_slice") is False,
        "STRATEGY_IMPLEMENTATION_AUTHORIZED",
    )
    _require(payload.get("development_run_count") == 0, "DEVELOPMENT_RUN_COUNT_NOT_ZERO")
    _require(payload.get("development_run_limit") == 1, "DEVELOPMENT_RUN_LIMIT_NOT_ONE")
    _require(payload.get("runner_start_count") == 0, "RUNNER_START_COUNT_NOT_ZERO")
    _require(payload.get("run_slot_consumed") is False, "RUN_SLOT_CONSUMED")
    _require(payload.get("retry_allowed") is False, "RETRY_ALLOWED")
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
        independence.get("independent_from_closed_cross_sectional_momentum_lane") is True,
        "NOT_INDEPENDENT_FROM_CS_MOMENTUM",
    )
    _require(
        independence.get("cross_sectional_momentum_dependency") is False,
        "CS_MOMENTUM_DEPENDENCY",
    )
    _require(
        independence.get("not_a_retry_of_terminal_vol_breakout_coiled_spring") is True,
        "COILED_SPRING_RETRY_NOT_FORBIDDEN",
    )
    forbidden = set(independence.get("forbidden_lineage_refs") or [])
    for required in (
        "vol_breakout/v1_unchanged_binding_retry",
        "VOL_BREAKOUT_COILED_SPRING_NON_BITCOIN_FUTURES_V1",
        "cross_sectional_relative_strength_momentum/v1",
        "bollinger_bands_mean_reversion",
    ):
        _require(required in forbidden, f"MISSING_FORBIDDEN_LINEAGE:{required}")
    md = payload.get("material_difference_vs_terminal_coiled_spring") or {}
    _require(
        md.get("prior_terminal_hypothesis_id") == REQUIRED_PRIOR_HYPOTHESIS,
        "PRIOR_HYPOTHESIS_MISMATCH",
    )
    _require(md.get("unchanged_binding_retry_forbidden") is True, "UNCHANGED_RETRY_ALLOWED")
    _require(
        md.get("reopen_of_terminal_vol_breakout_v1_forbidden") is True,
        "VOL_BREAKOUT_REOPEN_ALLOWED",
    )
    diffs = md.get("differences") or {}
    for key in (
        "vol_estimator",
        "compression_gate",
        "expansion_gate",
        "entry",
        "baseline",
        "dataset_universe",
        "program_identity",
    ):
        _require(bool(diffs.get(key)), f"MISSING_MATERIAL_DIFFERENCE:{key}")

    if repo_root is not None:
        entry = load_json(repo_root / CLOSED_ENTRY_BACKLOG)
        exitb = load_json(repo_root / CLOSED_EXIT_BACKLOG)
        cs = load_json(repo_root / CLOSED_CS_MOMENTUM_PROGRAM)
        _require(entry.get("status") == REQUIRED_CLOSED, "ENTRY_LANE_NOT_CLOSED")
        _require(exitb.get("status") == REQUIRED_CLOSED, "EXIT_LANE_NOT_CLOSED")
        _require(cs.get("status") == REQUIRED_CS_CLOSED, "CS_MOMENTUM_LANE_NOT_CLOSED")
        backlog = load_json(repo_root / str(payload.get("lane_backlog_ref")))
        _require(backlog.get("status") == "OPEN_BACKLOG", "LANE_BACKLOG_NOT_OPEN")
        _require(backlog.get("program_id") == REQUIRED_PROGRAM_ID, "BACKLOG_PROGRAM_MISMATCH")

    return {
        "valid": True,
        "program_id": REQUIRED_PROGRAM_ID,
        "status": REQUIRED_STATUS,
        "strategy_identity": REQUIRED_STRATEGY_IDENTITY,
        "signal_family": REQUIRED_SIGNAL_FAMILY,
        "definition_only": True,
        "strategy_implementation_present": False,
        "holdout_authorized": False,
        "evaluation_authorized": False,
        "promotion_eligible": False,
        "development_run_count": 0,
        "runner_start_count": 0,
        "run_slot_consumed": False,
        "retry_allowed": False,
        "material_difference_explicit": True,
        "causally_independent_from_cs_momentum": True,
    }


def load_and_validate_repo_program(repo_root: Path) -> dict[str, Any]:
    path = repo_root / PROGRAM_REL_PATH
    _require(path.is_file(), "PROGRAM_SSOT_MISSING")
    return validate_program_contract(load_json(path), repo_root=repo_root)
