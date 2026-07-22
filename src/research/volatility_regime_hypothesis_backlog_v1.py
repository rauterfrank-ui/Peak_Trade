"""Definition-only backlog validator for volatility regime lane v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.canonical_research_lane_post_terminal_lifecycle_contract_v1 import (
    CONTRACT_ID as LIFECYCLE_CONTRACT_ID,
)

PACKAGE_MARKER = "VOLATILITY_REGIME_HYPOTHESIS_BACKLOG_V1=true"
BACKLOG_REL_PATH = "config/research/volatility_regime_hypothesis_backlog_v1.json"
GOVERNANCE_REL_PATH = "docs/governance/VOLATILITY_REGIME_HYPOTHESIS_BACKLOG_V1.md"
REQUIRED_STATUS = "OPEN_BACKLOG"
REQUIRED_PROGRAM_ID = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
REQUIRED_HYPOTHESIS_ID = "VOLATILITY_EXPANSION_PERSISTENCE_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_STRATEGY_IDENTITY = "VOLATILITY_EXPANSION_PERSISTENCE_V1"
REQUIRED_TERMINAL_STRATEGY_IDENTITY = "VOLATILITY_COMPRESSION_BREAKOUT_V1"
REQUIRED_TERMINAL_HYPOTHESIS_ID = "VOLATILITY_COMPRESSION_BREAKOUT_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_CLOSED = "LANE_CLOSED_NO_FURTHER_RESEARCH"
REQUIRED_CS_CLOSED = "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"
REQUIRED_DATASET = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"


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
    _require(payload.get("explicit_closeout_decision") is False, "CLOSEOUT_DECISION_TRUE")
    _require(payload.get("explicit_waiting_decision") is False, "WAITING_DECISION_FORBIDDEN")
    _require(payload.get("lane_auto_closed") is False, "LANE_AUTO_CLOSED")
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _require(
        payload.get("development_evaluation_authorized") is False,
        "DEVELOPMENT_EVALUATION_AUTHORIZED",
    )
    _require(payload.get("implementation_authorized") is False, "IMPLEMENTATION_AUTHORIZED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(
        payload.get("sealed_holdout_binding_status") == "UNBOUND_UNTOUCHED",
        "HOLDOUT_NOT_UNBOUND",
    )
    _require(payload.get("dataset_id") == REQUIRED_DATASET, "DATASET_ID_MISMATCH")
    _require(payload.get("dataset_class") == "DEVELOPMENT_ONLY", "DATASET_CLASS")
    _require(payload.get("development_run_count") == 0, "DEVELOPMENT_RUN_COUNT_NOT_ZERO")
    _require(payload.get("retry_allowed") is False, "RETRY_ALLOWED")
    rules = payload.get("governance_rules") or {}
    _require(rules.get("preregistered_count_exact") == 1, "PREREGISTERED_COUNT_NOT_1")
    _require(
        rules.get("open_unpreregistered_count_exact") == 0,
        "OPEN_UNPREREGISTERED_NOT_0",
    )
    _require(rules.get("retuning_after_fail_forbidden") is True, "RETUNING_NOT_FORBIDDEN")
    _require(rules.get("development_runs_per_hypothesis") == 1, "DEV_RUNS_PER_HYP_NOT_1")
    _require(payload.get("open_unpreregistered_candidates") == [], "OPEN_CANDIDATES_NONEMPTY")
    prereg = payload.get("preregistered_hypotheses") or []
    _require(len(prereg) == 1, "PREREGISTERED_LEN_NOT_1")
    hyp = prereg[0]
    _require(hyp.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID_MISMATCH")
    _require(hyp.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY")
    _require(hyp.get("status") == "DEFINITION_ONLY_PREREGISTERED", "HYPOTHESIS_STATUS")
    _require(hyp.get("evaluation_authorized") is False, "HYP_EVAL_AUTHORIZED")
    _require(hyp.get("development_run_count") == 0, "HYP_RUN_COUNT_NOT_ZERO")
    _require(hyp.get("development_run_limit") == 1, "HYP_RUN_LIMIT_NOT_ONE")
    _require(hyp.get("implementation_present") is False, "HYP_IMPLEMENTATION_PRESENT")
    _require(hyp.get("run_slot_consumed") is False, "HYP_RUN_SLOT_CONSUMED")
    _require(hyp.get("runner_start_count") == 0, "HYP_RUNNER_START_NOT_ZERO")
    _require(hyp.get("holdout_allowed") is False, "HYP_HOLDOUT_ALLOWED")
    _require(hyp.get("retry_allowed") is False, "HYP_RETRY_ALLOWED")
    terminals = payload.get("terminal_hypotheses") or []
    _require(len(terminals) == 1, "TERMINAL_LEN_NOT_1")
    term = terminals[0]
    _require(
        term.get("hypothesis_id") == REQUIRED_TERMINAL_HYPOTHESIS_ID,
        "TERMINAL_HYPOTHESIS_ID",
    )
    _require(
        term.get("strategy_identity") == REQUIRED_TERMINAL_STRATEGY_IDENTITY,
        "TERMINAL_STRATEGY_IDENTITY",
    )
    _require(term.get("status") == "TERMINAL_FAIL", "TERMINAL_STATUS")
    _require(term.get("terminal_result") == "FAIL_CLOSED_NO_RETRY", "TERMINAL_RESULT")
    _require(term.get("retry_allowed") is False, "TERMINAL_RETRY_ALLOWED")
    _require(term.get("run_slot_consumed") is True, "TERMINAL_RUN_SLOT_NOT_CONSUMED")
    siblings = payload.get("closed_sibling_lanes") or {}
    _require(
        siblings.get("entry_eligibility_lane_status") == REQUIRED_CLOSED,
        "ENTRY_SIBLING_NOT_CLOSED",
    )
    _require(
        siblings.get("exit_efficiency_lane_status") == REQUIRED_CLOSED,
        "EXIT_SIBLING_NOT_CLOSED",
    )
    _require(
        siblings.get("cross_sectional_momentum_lane_status") == REQUIRED_CS_CLOSED,
        "CS_MOMENTUM_SIBLING_NOT_CLOSED",
    )
    _require(siblings.get("reopen_forbidden") is True, "SIBLING_REOPEN_NOT_FORBIDDEN")
    gates = payload.get("promotion_and_economic_gate_policy") or {}
    _require(gates.get("promotion_eligible") is False, "PROMOTION_ELIGIBLE")
    _require(gates.get("economic_gate_open") is False, "ECONOMIC_GATE_OPEN")

    if repo_root is not None:
        entry = load_json(repo_root / siblings["entry_eligibility_backlog_ref"])
        exitb = load_json(repo_root / siblings["exit_efficiency_backlog_ref"])
        cs = load_json(repo_root / siblings["cross_sectional_momentum_program_ref"])
        _require(entry.get("status") == REQUIRED_CLOSED, "LIVE_ENTRY_NOT_CLOSED")
        _require(exitb.get("status") == REQUIRED_CLOSED, "LIVE_EXIT_NOT_CLOSED")
        _require(cs.get("status") == REQUIRED_CS_CLOSED, "LIVE_CS_MOMENTUM_NOT_CLOSED")

    return {
        "valid": True,
        "status": REQUIRED_STATUS,
        "program_id": REQUIRED_PROGRAM_ID,
        "preregistered_count": 1,
        "terminal_count": 1,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "strategy_identity": REQUIRED_STRATEGY_IDENTITY,
        "development_run_count": 0,
        "dataset_id": REQUIRED_DATASET,
        "evaluation_authorized": False,
        "holdout_forbidden": True,
        "promotion_eligible": False,
        "retry_allowed": False,
    }


def load_and_validate_repo_backlog(repo_root: Path) -> dict[str, Any]:
    path = repo_root / BACKLOG_REL_PATH
    _require(path.is_file(), "BACKLOG_SSOT_MISSING")
    return validate_backlog_contract(load_json(path), repo_root=repo_root)
