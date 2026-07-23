"""Definition-only backlog validator for CS intrabar close-location pressure continuation lane v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.canonical_research_lane_post_terminal_lifecycle_contract_v1 import (
    CONTRACT_ID as LIFECYCLE_CONTRACT_ID,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_HYPOTHESIS_BACKLOG_V1=true"
)
BACKLOG_REL_PATH = "config/research/cross_sectional_intrabar_close_location_pressure_continuation_hypothesis_backlog_v1.json"
GOVERNANCE_REL_PATH = "docs/governance/CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_HYPOTHESIS_BACKLOG_V1.md"
REQUIRED_STATUS = "OPEN_BACKLOG"
REQUIRED_PROGRAM_ID = (
    "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_RESEARCH_PROGRAM_V1"
)
REQUIRED_WORKSTREAM_ID = (
    "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_WORKSTREAM_V1"
)
REQUIRED_HYPOTHESIS_ID = (
    "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
)
REQUIRED_STRATEGY_IDENTITY = "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1"
REQUIRED_HYP_STATUS = "PREREGISTERED_DEFINITION_ONLY"
OPEN_CSRHR_BACKLOG = (
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
    _require(payload.get("development_run_count") == 0, "DEVELOPMENT_RUN_COUNT_NOT_ZERO")
    _require(payload.get("runner_start_count") == 0, "RUNNER_START_COUNT_NOT_ZERO")
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
    _require(rules.get("development_runs_per_hypothesis") == 1, "DEV_RUNS_PER_HYP_NOT_1")
    _require(rules.get("retuning_after_fail_forbidden") is True, "RETUNE_ALLOWED")
    prereg = payload.get("preregistered_hypotheses") or []
    _require(len(prereg) == 1, "PREREGISTERED_LEN_NOT_1")
    hyp = prereg[0]
    _require(hyp.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID_MISMATCH")
    _require(hyp.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY")
    _require(hyp.get("status") == REQUIRED_HYP_STATUS, "HYPOTHESIS_STATUS")
    _require(hyp.get("implementation_present") is True, "HYP_IMPLEMENTATION_PRESENT")
    _require(hyp.get("evaluation_authorized") is False, "HYP_EVALUATION_AUTHORIZED")
    _require(hyp.get("development_run_count") == 0, "HYP_DEVELOPMENT_RUN_COUNT")
    _require(hyp.get("development_run_limit") == 1, "HYP_DEVELOPMENT_RUN_LIMIT")
    _require(hyp.get("run_slot_consumed") is False, "HYP_RUN_SLOT_CONSUMED")
    _require(hyp.get("retry_allowed") is False, "HYP_RETRY_ALLOWED")
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
    open_sib = payload.get("open_sibling_lanes") or {}
    _require(
        open_sib.get("cross_sectional_short_horizon_return_reversal_lane_status") == "OPEN_BACKLOG",
        "CSRHR_SIBLING_NOT_OPEN",
    )
    _require(open_sib.get("mutation_forbidden") is True, "CSRHR_MUTATION_ALLOWED")
    _require(open_sib.get("semantic_reuse_forbidden") is True, "CSRHR_REUSE_ALLOWED")
    _require(open_sib.get("continuation_forbidden") is True, "CSRHR_CONTINUE_ALLOWED")
    _require(
        payload.get("sealed_holdout_binding_status") == "UNBOUND_UNTOUCHED_ACCESS_FORBIDDEN",
        "HOLDOUT_STATUS",
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
        csrhr_bl = load_json(repo_root / OPEN_CSRHR_BACKLOG)
        _require(csrhr_bl.get("status") == "OPEN_BACKLOG", "CSRHR_BACKLOG_NOT_OPEN")
        _require(csrhr_bl.get("development_run_count") == 0, "CSRHR_DEV_RUN_MUTATED")
        _require(csrhr_bl.get("evaluation_authorized") is False, "CSRHR_EVAL_AUTHORIZED")

    return {
        "valid": True,
        "status": REQUIRED_STATUS,
        "program_id": REQUIRED_PROGRAM_ID,
        "workstream_id": REQUIRED_WORKSTREAM_ID,
        "next_eligible": REQUIRED_HYPOTHESIS_ID,
        "preregistered_count": 1,
        "evaluation_authorized": False,
        "development_run_count": 0,
    }


def load_and_validate_repo_backlog(repo_root: Path) -> dict[str, Any]:
    payload = load_json(repo_root / BACKLOG_REL_PATH)
    return validate_backlog_contract(payload, repo_root=repo_root)
