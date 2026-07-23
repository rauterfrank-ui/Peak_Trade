"""Definition-only SSOT validator for CS path-efficiency continuation program v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_RESEARCH_PROGRAM_V1=true"
PROGRAM_REL_PATH = (
    "config/research/cross_sectional_path_efficiency_continuation_research_program_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_RESEARCH_PROGRAM_V1.md"
)
REQUIRED_PROGRAM_ID = "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_RESEARCH_PROGRAM_V1"
REQUIRED_WORKSTREAM_ID = "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_WORKSTREAM_V1"
REQUIRED_STATUS = "DEFINITION_ONLY"
REQUIRED_SIGNAL_FAMILY = "CROSS_SECTIONAL_PATH_EFFICIENCY"
REQUIRED_TARGET = "CROSS_SECTIONAL_PATH_EFFICIENCY_DIRECTIONAL_CONTINUATION"
REQUIRED_HYPOTHESIS_ID = "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_STRATEGY_IDENTITY = "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1"
REQUIRED_TREATMENT = "OWN_INSTRUMENT_CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_ADMISSION"
CLOSED_VOL = "config/research/volatility_regime_research_program_v1.json"
CLOSED_CS_MOM = "config/research/material_different_cross_sectional_momentum_program_v1.json"
OPEN_CSRHR = (
    "config/research/cross_sectional_short_horizon_return_reversal_research_program_v1.json"
)
OPEN_CSRHR_BACKLOG = (
    "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
)
REQUIRED_CLOSED_PROGRAM = "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"
REQUIRED_CSRHR_STATUS = "DEFINITION_ONLY"
REQUIRED_CSRHR_BACKLOG_STATUS = "OPEN_BACKLOG"


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
    _require(payload.get("workstream_id") == REQUIRED_WORKSTREAM_ID, "WORKSTREAM_ID_MISMATCH")
    _require(payload.get("status") == REQUIRED_STATUS, "STATUS_NOT_DEFINITION_ONLY")
    _require(payload.get("program_family") == "CROSS_SECTIONAL_PATH_EFFICIENCY", "FAMILY")
    _require(
        payload.get("slice_class") == "DEFINITION_ONLY_GOVERNANCE",
        "SLICE_NOT_DEFINITION_ONLY_GOVERNANCE",
    )
    _require(payload.get("authority_effect") == "NONE", "AUTHORITY_EFFECT_NOT_NONE")
    _require(payload.get("runtime_effect") == "NONE", "RUNTIME_EFFECT_NOT_NONE")
    _require(payload.get("signal_family") == REQUIRED_SIGNAL_FAMILY, "SIGNAL_FAMILY")
    _require(payload.get("target_phenomenon") == REQUIRED_TARGET, "TARGET_PHENOMENON")
    _require(payload.get("treatment_type") == REQUIRED_TREATMENT, "TREATMENT_TYPE")
    _require(payload.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID")
    _require(payload.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY")
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED_TRUE")
    _require(
        payload.get("development_evaluation_authorized") is True,
        "DEVELOPMENT_EVALUATION_AUTHORIZED_TRUE",
    )
    _require(
        payload.get("development_evaluation_executed") is True,
        "DEVELOPMENT_EVALUATION_EXECUTED_TRUE",
    )
    _require(payload.get("development_run_count") == 1, "DEVELOPMENT_RUN_COUNT_NOT_ZERO")
    _require(payload.get("development_run_limit") == 1, "DEVELOPMENT_RUN_LIMIT_NOT_1")
    _require(payload.get("runner_start_count") == 1, "RUNNER_START_COUNT_NOT_ZERO")
    _require(payload.get("run_slot_consumed") is True, "RUN_SLOT_CONSUMED")
    _require(payload.get("run_budget_consumed") is True, "RUN_BUDGET_CONSUMED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(payload.get("implementation_authorized") is True, "IMPLEMENTATION_AUTHORIZED")
    _require(
        payload.get("strategy_implementation_present") is True,
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
        independence.get("independent_from_open_csrhr_program") is True,
        "NOT_INDEPENDENT_OF_CSRHR",
    )
    _require(
        independence.get("not_a_csrhr_continuation_or_semantic_reuse") is True,
        "CSRHR_REUSE_NOT_FORBIDDEN",
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
    retry = payload.get("retry_policy") or {}
    _require(retry.get("after_development_fail") == "FAIL_CLOSED_NO_RETRY", "RETRY_POLICY")
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
    _require(
        payload.get("sealed_holdout_binding_status") == "UNBOUND_UNTOUCHED_ACCESS_FORBIDDEN",
        "HOLDOUT_STATUS",
    )

    if repo_root is not None:
        vol = load_json(repo_root / CLOSED_VOL)
        mom = load_json(repo_root / CLOSED_CS_MOM)
        csrhr = load_json(repo_root / OPEN_CSRHR)
        csrhr_bl = load_json(repo_root / OPEN_CSRHR_BACKLOG)
        _require(vol.get("status") == REQUIRED_CLOSED_PROGRAM, "VOL_REGIME_NOT_CLOSED")
        _require(mom.get("status") == REQUIRED_CLOSED_PROGRAM, "CS_MOMENTUM_NOT_CLOSED")
        _require(csrhr.get("status") == REQUIRED_CSRHR_STATUS, "CSRHR_NOT_DEFINITION_ONLY")
        _require(
            csrhr_bl.get("status") == REQUIRED_CSRHR_BACKLOG_STATUS,
            "CSRHR_BACKLOG_NOT_OPEN",
        )
        _require(csrhr_bl.get("development_run_count") == 0, "CSRHR_DEV_RUN_MUTATED")
        gov = repo_root / GOVERNANCE_REL_PATH
        _require(gov.is_file(), "GOVERNANCE_DOC_MISSING")

    return {
        "valid": True,
        "definition_only": True,
        "program_id": REQUIRED_PROGRAM_ID,
        "workstream_id": REQUIRED_WORKSTREAM_ID,
        "status": REQUIRED_STATUS,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "evaluation_authorized": False,
        "implementation_authorized": True,
        "development_run_count": 1,
        "holdout_forbidden": True,
    }


def load_and_validate_repo_program(repo_root: Path) -> dict[str, Any]:
    payload = load_json(repo_root / PROGRAM_REL_PATH)
    return validate_program_contract(payload, repo_root=repo_root)
