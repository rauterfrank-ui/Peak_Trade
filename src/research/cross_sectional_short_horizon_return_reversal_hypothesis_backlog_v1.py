"""Definition-only backlog validator for CS short-horizon return-reversal lane v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.canonical_research_lane_post_terminal_lifecycle_contract_v1 import (
    CONTRACT_ID as LIFECYCLE_CONTRACT_ID,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_HYPOTHESIS_BACKLOG_V1=true"
BACKLOG_REL_PATH = (
    "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_HYPOTHESIS_BACKLOG_V1.md"
)
REQUIRED_STATUS = "OPEN_BACKLOG"
REQUIRED_PROGRAM_ID = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1"
REQUIRED_HYPOTHESIS_ID = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_STRATEGY_IDENTITY = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1"
REQUIRED_HYP_STATUS = "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL"


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
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _require(
        payload.get("development_evaluation_authorized") is False,
        "DEVELOPMENT_EVALUATION_AUTHORIZED",
    )
    _require(payload.get("implementation_authorized") is True, "IMPLEMENTATION_AUTHORIZED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(payload.get("development_run_count") == 1, "DEVELOPMENT_RUN_COUNT_NOT_ZERO")
    _require(payload.get("runner_start_count") == 1, "RUNNER_START_COUNT_NOT_ZERO")
    _require(payload.get("next_eligible") == REQUIRED_HYPOTHESIS_ID, "NEXT_ELIGIBLE_MISMATCH")
    _require(payload.get("open_unpreregistered_candidates") == [], "OPEN_CANDIDATES_NONEMPTY")
    _require(payload.get("terminal_hypotheses") == [], "TERMINAL_NONEMPTY")
    rules = payload.get("governance_rules") or {}
    _require(rules.get("preregistered_count_exact") == 1, "PREREGISTERED_COUNT_NOT_1")
    _require(rules.get("open_unpreregistered_count_exact") == 0, "OPEN_UNPREREGISTERED_NOT_0")
    _require(rules.get("economic_gate_closed") is True, "ECONOMIC_GATE_NOT_CLOSED")
    _require(
        rules.get("evaluation_requires_separate_operator_go") is True,
        "EVAL_GO_NOT_REQUIRED",
    )
    prereg = payload.get("preregistered_hypotheses") or []
    _require(len(prereg) == 1, "PREREGISTERED_LEN_NOT_1")
    hyp = prereg[0]
    _require(hyp.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID_MISMATCH")
    _require(hyp.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY")
    _require(hyp.get("status") == REQUIRED_HYP_STATUS, "HYPOTHESIS_STATUS")
    _require(hyp.get("evaluation_authorized") is False, "HYP_EVALUATION_AUTHORIZED")
    _require(hyp.get("development_run_count") == 1, "HYP_DEVELOPMENT_RUN_COUNT")
    _require(hyp.get("run_slot_consumed") is True, "HYP_RUN_SLOT_CONSUMED")
    siblings = payload.get("closed_sibling_lanes") or {}
    _require(siblings.get("reopen_forbidden") is True, "SIBLING_REOPEN_ALLOWED")
    _require(
        siblings.get("volatility_regime_lane_status") == "LANE_CLOSED_NO_FURTHER_RESEARCH",
        "VOL_REGIME_SIBLING_NOT_CLOSED",
    )
    _require(
        siblings.get("cross_sectional_momentum_lane_status")
        == "PROGRAM_CLOSED_NO_FURTHER_RESEARCH",
        "CS_MOMENTUM_SIBLING_NOT_CLOSED",
    )
    rt = payload.get("runtime_policy") or {}
    for key in (
        "live_authorized",
        "orders_allowed",
        "shadow_activated",
        "paper_activated",
        "testnet_activated",
        "scheduler_authorized",
    ):
        _require(rt.get(key) is False, f"RUNTIME_POLICY_{key.upper()}")

    if repo_root is not None:
        gov = repo_root / GOVERNANCE_REL_PATH
        _require(gov.is_file(), "GOVERNANCE_DOC_MISSING")

    return {
        "valid": True,
        "status": REQUIRED_STATUS,
        "program_id": REQUIRED_PROGRAM_ID,
        "next_eligible": REQUIRED_HYPOTHESIS_ID,
        "preregistered_count": 1,
        "evaluation_authorized": False,
    }


def load_and_validate_repo_backlog(repo_root: Path) -> dict[str, Any]:
    payload = load_json(repo_root / BACKLOG_REL_PATH)
    return validate_backlog_contract(payload, repo_root=repo_root)
