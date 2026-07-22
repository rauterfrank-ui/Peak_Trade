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
REQUIRED_STATUS = "OPEN_BACKLOG"
REQUIRED_PROGRAM_ID = "MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_PROGRAM_V1"
REQUIRED_HYPOTHESIS_ID = "CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_NON_BITCOIN_PERPETUALS_V1"
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
    _require(payload.get("status") == REQUIRED_STATUS, "STATUS_NOT_OPEN_BACKLOG")
    _require(
        payload.get("lifecycle_contract_id") == LIFECYCLE_CONTRACT_ID,
        "LIFECYCLE_CONTRACT_MISMATCH",
    )
    _require(payload.get("explicit_closeout_decision") is False, "UNEXPECTED_CLOSEOUT")
    _require(payload.get("lane_auto_closed") is False, "LANE_AUTO_CLOSED")
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _require(
        payload.get("development_evaluation_authorized") is False,
        "DEVELOPMENT_EVALUATION_AUTHORIZED",
    )
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(payload.get("development_run_count") == 0, "DEVELOPMENT_RUN_COUNT_NONZERO")
    rules = payload.get("governance_rules") or {}
    _require(rules.get("preregistered_count_exact") == 1, "PREREGISTERED_COUNT_NOT_1")
    _require(
        rules.get("open_unpreregistered_count_exact") == 0,
        "OPEN_UNPREREGISTERED_NOT_0",
    )
    _require(payload.get("open_unpreregistered_candidates") == [], "OPEN_CANDIDATES_NONEMPTY")
    _require(payload.get("terminal_hypotheses") == [], "TERMINAL_NONEMPTY")
    prereg = payload.get("preregistered_hypotheses") or []
    _require(len(prereg) == 1, "PREREGISTERED_LEN_NOT_1")
    hyp = prereg[0]
    _require(hyp.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID_MISMATCH")
    _require(hyp.get("status") == "DEFINITION_ONLY_PREREGISTERED", "HYPOTHESIS_STATUS")
    _require(hyp.get("evaluation_authorized") is False, "HYP_EVAL_AUTHORIZED")
    _require(hyp.get("development_run_count") == 0, "HYP_RUN_COUNT_NONZERO")
    _require(hyp.get("holdout_allowed") is False, "HYP_HOLDOUT_ALLOWED")
    _require(hyp.get("implementation_present") is True, "HYP_IMPLEMENTATION_PRESENT_FALSE")
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
        "preregistered_count": 1,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "development_run_count": 0,
        "evaluation_authorized": False,
        "holdout_forbidden": True,
        "promotion_eligible": False,
    }


def load_and_validate_repo_backlog(repo_root: Path) -> dict[str, Any]:
    path = repo_root / BACKLOG_REL_PATH
    _require(path.is_file(), "BACKLOG_SSOT_MISSING")
    return validate_backlog_contract(load_json(path), repo_root=repo_root)
