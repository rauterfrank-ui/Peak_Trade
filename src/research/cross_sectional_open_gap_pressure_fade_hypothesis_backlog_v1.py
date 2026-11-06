"""Closed-lane backlog validator for CS open-gap pressure fade after DEVELOPMENT_FAIL."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.canonical_research_lane_post_terminal_lifecycle_contract_v1 import (
    CONTRACT_ID as LIFECYCLE_CONTRACT_ID,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_HYPOTHESIS_BACKLOG_V1=true"
BACKLOG_REL_PATH = (
    "config/research/cross_sectional_open_gap_pressure_fade_hypothesis_backlog_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_HYPOTHESIS_BACKLOG_V1.md"
)
REQUIRED_STATUS = "LANE_CLOSED_NO_FURTHER_RESEARCH"
REQUIRED_PROGRAM_ID = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_RESEARCH_PROGRAM_V1"
REQUIRED_WORKSTREAM_ID = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_WORKSTREAM_V1"
REQUIRED_HYPOTHESIS_ID = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_STRATEGY_IDENTITY = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1"
REQUIRED_NEXT_STEP = (
    "NEW_DISTINCT_RESEARCH_PROGRAM_OR_FULL_CANONICAL_SYSTEM_BINDING_OR_OTHER_EVIDENCE_CLASS"
    "_REQUIRES_OPERATOR_RATIFICATION"
)
REQUIRED_EVIDENCE = "docs/evidence/evaluate_cross_sectional_open_gap_pressure_fade_development_v1/"
CLOSED_CSRHR_BACKLOG = (
    "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
)


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
    _require(payload.get("workstream_id") == REQUIRED_WORKSTREAM_ID, "WORKSTREAM_ID_MISMATCH")
    _require(payload.get("status") == REQUIRED_STATUS, "STATUS_NOT_LANE_CLOSED")
    _require(
        payload.get("lifecycle_contract_id") == LIFECYCLE_CONTRACT_ID,
        "LIFECYCLE_CONTRACT_MISMATCH",
    )
    _require(payload.get("explicit_closeout_decision") is True, "CLOSEOUT_DECISION_REQUIRED")
    _require(payload.get("explicit_waiting_decision") is False, "WAITING_DECISION_TRUE")
    _require(payload.get("lane_auto_closed") is False, "LANE_AUTO_CLOSED")
    _require(payload.get("create_successor_hypothesis") is False, "CREATE_SUCCESSOR_TRUE")
    _require(payload.get("successor_found") is False, "SUCCESSOR_FOUND_TRUE")
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _require(
        payload.get("development_evaluation_authorized") is False,
        "DEVELOPMENT_EVALUATION_AUTHORIZED",
    )
    _require(payload.get("implementation_authorized") is False, "IMPLEMENTATION_AUTHORIZED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(payload.get("development_run_count") == 1, "DEVELOPMENT_RUN_COUNT_NOT_ONE")
    _require(payload.get("runner_start_count") == 1, "RUNNER_START_COUNT_NOT_ONE")
    _require(payload.get("retry_allowed") is False, "RETRY_ALLOWED")
    _require(payload.get("reopen_allowed") is False, "REOPEN_ALLOWED")
    _require(payload.get("next_canonical_step") == REQUIRED_NEXT_STEP, "NEXT_STEP_STALE")
    _require(payload.get("next_eligible") == "NONE", "NEXT_ELIGIBLE_NOT_NONE")
    _require(payload.get("open_unpreregistered_candidates") == [], "OPEN_CANDIDATES_NONEMPTY")
    rules = payload.get("governance_rules") or {}
    _require(rules.get("preregistered_count_exact") == 0, "PREREGISTERED_COUNT_NOT_0")
    _require(rules.get("open_unpreregistered_count_exact") == 0, "OPEN_UNPREREGISTERED_NOT_0")
    _require(rules.get("economic_gate_closed") is True, "ECONOMIC_GATE_NOT_CLOSED")
    _require(rules.get("promotion_closed") is True, "PROMOTION_NOT_CLOSED")
    _require(rules.get("retuning_after_fail_forbidden") is True, "RETUNE_ALLOWED")
    _require(rules.get("development_runs_per_hypothesis") == 1, "DEV_RUNS_PER_HYP_NOT_1")
    prereg = payload.get("preregistered_hypotheses") or []
    _require(len(prereg) == 0, "PREREGISTERED_LEN_NOT_0")
    terminals = payload.get("terminal_hypotheses") or []
    _require(len(terminals) == 1, "TERMINAL_LEN_NOT_1")
    hyp = terminals[0]
    _require(hyp.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID_MISMATCH")
    _require(hyp.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY")
    _require(hyp.get("status") == "TERMINAL_FAIL", "HYPOTHESIS_STATUS")
    _require(hyp.get("terminal_result") == "FAIL_CLOSED_NO_RETRY", "TERMINAL_RESULT")
    _require(hyp.get("implementation_present") is True, "HYP_IMPLEMENTATION_PRESENT")
    _require(hyp.get("implementation_pr") == 5495, "HYP_IMPLEMENTATION_PR")
    _require(hyp.get("development_pr") == 5496, "HYP_DEVELOPMENT_PR")
    _require(hyp.get("evaluation_authorized") is False, "HYP_EVALUATION_AUTHORIZED")
    _require(hyp.get("development_run_count") == 1, "HYP_DEVELOPMENT_RUN_COUNT")
    _require(hyp.get("development_run_limit") == 1, "HYP_DEVELOPMENT_RUN_LIMIT")
    _require(hyp.get("run_slot_consumed") is True, "HYP_RUN_SLOT_CONSUMED")
    _require(hyp.get("retry_allowed") is False, "HYP_RETRY_ALLOWED")
    _require(hyp.get("evaluation_evidence_ref") == REQUIRED_EVIDENCE, "HYP_EVIDENCE_REF")
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
    _require(
        siblings.get("path_efficiency_continuation_status")
        == "DEVELOPMENT_FAIL_SLOT_CONSUMED_NO_RETRY",
        "PATH_EFFICIENCY_NOT_TERMINAL",
    )
    _require(
        siblings.get("clv_pressure_continuation_status")
        == "DEVELOPMENT_FAIL_SLOT_CONSUMED_NO_RETRY",
        "CLV_PRESSURE_NOT_TERMINAL",
    )
    _require(
        siblings.get("cross_sectional_short_horizon_return_reversal_lane_status")
        == "LANE_CLOSED_NO_FURTHER_RESEARCH",
        "CSRHR_SIBLING_NOT_CLOSED",
    )
    open_sib = payload.get("open_sibling_lanes") or {}
    _require(open_sib.get("none") is True, "OPEN_SIBLING_NONE_REQUIRED")
    _require(
        payload.get("sealed_holdout_binding_status") == "UNBOUND_UNTOUCHED_ACCESS_FORBIDDEN",
        "HOLDOUT_STATUS",
    )
    promo = payload.get("promotion_and_economic_gate_policy") or {}
    _require(promo.get("promotion_eligible") is False, "PROMOTION_ELIGIBLE")
    _require(promo.get("economic_gate_open") is False, "ECONOMIC_GATE_OPEN")
    _require(promo.get("economic_validity_offline_gate_pass") is False, "ECONOMIC_VALIDITY_PASS")
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
        csrhr_bl = load_json(repo_root / CLOSED_CSRHR_BACKLOG)
        _require(
            csrhr_bl.get("status") == "LANE_CLOSED_NO_FURTHER_RESEARCH",
            "CSRHR_BACKLOG_NOT_CLOSED",
        )
        gov = repo_root / GOVERNANCE_REL_PATH
        _require(gov.is_file(), "GOVERNANCE_DOC_MISSING")
        evidence = repo_root / REQUIRED_EVIDENCE
        _require(evidence.is_dir(), "EVALUATION_EVIDENCE_MISSING")
        summary = load_json(evidence / "summary.json")
        _require(summary.get("development_result") == "DEVELOPMENT_FAIL", "SUMMARY_NOT_FAIL")
        _require(summary.get("holdout_accessed") is False, "HOLDOUT_ACCESSED")
        _require(summary.get("promotion_eligible") is False, "SUMMARY_PROMOTION")
        _require(summary.get("retry_forbidden") is True, "RETRY_NOT_FORBIDDEN")

    return {
        "valid": True,
        "status": REQUIRED_STATUS,
        "program_id": REQUIRED_PROGRAM_ID,
        "next_eligible": "NONE",
        "preregistered_count": 0,
        "terminal_count": 1,
        "evaluation_authorized": False,
        "development_run_count": 1,
        "next_canonical_step": REQUIRED_NEXT_STEP,
    }


def load_and_validate_repo_backlog(repo_root: Path) -> dict[str, Any]:
    payload = load_json(repo_root / BACKLOG_REL_PATH)
    return validate_backlog_contract(payload, repo_root=repo_root)
