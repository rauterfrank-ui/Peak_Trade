"""Definition-only backlog validator for cross-sectional momentum lane v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.canonical_research_lane_post_terminal_lifecycle_contract_v1 import (
    CONTRACT_ID as LIFECYCLE_CONTRACT_ID,
)

PACKAGE_MARKER = "MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_HYPOTHESIS_BACKLOG_V1=true"
BACKLOG_REL_PATH = (
    "config/research/material_different_cross_sectional_momentum_hypothesis_backlog_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_HYPOTHESIS_BACKLOG_V1.md"
)
REQUIRED_STATUS = "LANE_CLOSED_NO_FURTHER_RESEARCH"
REQUIRED_NEXT_CANONICAL_STEP = "LANE_CLOSED_NO_FURTHER_RESEARCH_NO_EXECUTABLE_GO"
REQUIRED_PROGRAM_ID = "MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_PROGRAM_V1"
REQUIRED_HYPOTHESIS_ID = "CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_STRATEGY_IDENTITY = "CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1"
REQUIRED_TERMINAL_RESULT = "FAIL_CLOSED_NO_RETRY"
REQUIRED_CLOSED = "LANE_CLOSED_NO_FURTHER_RESEARCH"


class BacklogValidationError(ValueError):
    """Fail-closed backlog validation error."""


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise BacklogValidationError(code)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_backlog_contract(
    payload: Mapping[str, Any], *, repo_root: Path | None = None
) -> dict[str, Any]:
    _require(payload.get("program_id") == REQUIRED_PROGRAM_ID, "PROGRAM_ID_MISMATCH")
    _require(payload.get("status") == REQUIRED_STATUS, "STATUS_NOT_LANE_CLOSED")
    _require(
        payload.get("next_canonical_step") == REQUIRED_NEXT_CANONICAL_STEP,
        "NEXT_CANONICAL_STEP_MISMATCH",
    )
    _require(
        payload.get("lifecycle_contract_id") == LIFECYCLE_CONTRACT_ID,
        "LIFECYCLE_CONTRACT_MISMATCH",
    )
    _require(payload.get("explicit_closeout_decision") is True, "CLOSEOUT_DECISION_REQUIRED")
    _require(payload.get("explicit_waiting_decision") is False, "WAITING_DECISION_FORBIDDEN")
    _require(payload.get("lane_auto_closed") is False, "LANE_AUTO_CLOSED")
    _require(payload.get("create_successor_hypothesis") is False, "CREATE_SUCCESSOR_TRUE")
    _require(payload.get("automatic_successor_creation") is False, "AUTO_SUCCESSOR_TRUE")
    _require(payload.get("successor_found") is False, "SUCCESSOR_FOUND_TRUE")
    _require(payload.get("next_eligible") == "NONE", "NEXT_ELIGIBLE_NOT_NONE")
    _require(payload.get("retry_allowed") is False, "RETRY_ALLOWED")
    _require(payload.get("reopen_allowed") is False, "REOPEN_ALLOWED")
    _require(
        payload.get("requires_new_separate_operator_authorization") is True,
        "NEW_PROGRAM_AUTH_NOT_REQUIRED",
    )
    _require(
        payload.get("terminal_strategy_id") == REQUIRED_STRATEGY_IDENTITY,
        "TERMINAL_STRATEGY_ID_MISMATCH",
    )
    _require(payload.get("terminal_result") == REQUIRED_TERMINAL_RESULT, "TERMINAL_RESULT_MISMATCH")
    _require(payload.get("run_budget_consumed") is True, "RUN_BUDGET_NOT_CONSUMED")
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _require(
        payload.get("development_evaluation_authorized") is False,
        "DEVELOPMENT_EVALUATION_AUTHORIZED",
    )
    _require(payload.get("implementation_authorized") is False, "IMPLEMENTATION_AUTHORIZED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(payload.get("development_run_count") == 1, "DEVELOPMENT_RUN_COUNT_NOT_ONE")
    _require(payload.get("runner_start_count") == 1, "RUNNER_START_COUNT_NOT_ONE")
    rules = payload.get("governance_rules") or {}
    _require(rules.get("preregistered_count_exact") == 0, "PREREGISTERED_COUNT_NOT_0")
    _require(
        rules.get("open_unpreregistered_count_exact") == 0,
        "OPEN_UNPREREGISTERED_NOT_0",
    )
    _require(
        rules.get("exactly_one_next_eligible_for_preregistration") is False,
        "NEXT_ELIGIBLE_STILL_TRUE",
    )
    _require(rules.get("retuning_after_fail_forbidden") is True, "RETUNING_NOT_FORBIDDEN")
    _require(payload.get("open_unpreregistered_candidates") == [], "OPEN_CANDIDATES_NONEMPTY")
    _require(payload.get("preregistered_hypotheses") == [], "PREREGISTERED_NONEMPTY")
    terminal = payload.get("terminal_hypotheses") or []
    _require(len(terminal) == 1, "TERMINAL_LEN_NOT_1")
    hyp = terminal[0]
    _require(hyp.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID_MISMATCH")
    _require(hyp.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY")
    _require(hyp.get("status") == "TERMINAL_FAIL", "HYPOTHESIS_STATUS")
    _require(hyp.get("terminal_result") == REQUIRED_TERMINAL_RESULT, "HYP_TERMINAL_RESULT")
    _require(hyp.get("evaluation_authorized") is False, "HYP_EVAL_AUTHORIZED")
    _require(hyp.get("development_run_count") == 1, "HYP_RUN_COUNT_NOT_ONE")
    _require(hyp.get("runner_start_count") == 1, "HYP_RUNNER_START_NOT_ONE")
    _require(hyp.get("run_slot_consumed") is True, "HYP_RUN_SLOT_NOT_CONSUMED")
    _require(hyp.get("rerun_allowed") is False, "HYP_RERUN_ALLOWED")
    _require(hyp.get("retry_allowed") is False, "HYP_RETRY_ALLOWED")
    _require(hyp.get("reopen_allowed") is False, "HYP_REOPEN_ALLOWED")
    _require(hyp.get("holdout_allowed") is False, "HYP_HOLDOUT_ALLOWED")
    siblings = payload.get("closed_sibling_lanes") or {}
    _require(
        siblings.get("entry_eligibility_lane_status") == REQUIRED_CLOSED,
        "ENTRY_SIBLING_NOT_CLOSED",
    )
    _require(
        siblings.get("exit_efficiency_lane_status") == REQUIRED_CLOSED,
        "EXIT_SIBLING_NOT_CLOSED",
    )
    _require(siblings.get("reopen_forbidden") is True, "SIBLING_REOPEN_NOT_FORBIDDEN")
    gates = payload.get("promotion_and_economic_gate_policy") or {}
    _require(gates.get("promotion_eligible") is False, "PROMOTION_ELIGIBLE")
    _require(gates.get("economic_gate_open") is False, "ECONOMIC_GATE_OPEN")

    if repo_root is not None:
        entry = load_json(repo_root / siblings["entry_eligibility_backlog_ref"])
        exitb = load_json(repo_root / siblings["exit_efficiency_backlog_ref"])
        _require(entry.get("status") == REQUIRED_CLOSED, "LIVE_ENTRY_NOT_CLOSED")
        _require(exitb.get("status") == REQUIRED_CLOSED, "LIVE_EXIT_NOT_CLOSED")

    return {
        "valid": True,
        "status": REQUIRED_STATUS,
        "program_id": REQUIRED_PROGRAM_ID,
        "preregistered_count": 0,
        "terminal_count": 1,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "terminal_strategy_id": REQUIRED_STRATEGY_IDENTITY,
        "terminal_result": REQUIRED_TERMINAL_RESULT,
        "development_run_count": 1,
        "runner_start_count": 1,
        "run_budget_consumed": True,
        "successor_found": False,
        "next_eligible": "NONE",
        "retry_allowed": False,
        "reopen_allowed": False,
        "evaluation_authorized": False,
        "holdout_forbidden": True,
        "promotion_eligible": False,
    }


def load_and_validate_repo_backlog(repo_root: Path) -> dict[str, Any]:
    path = repo_root / BACKLOG_REL_PATH
    _require(path.is_file(), "BACKLOG_SSOT_MISSING")
    return validate_backlog_contract(load_json(path), repo_root=repo_root)
