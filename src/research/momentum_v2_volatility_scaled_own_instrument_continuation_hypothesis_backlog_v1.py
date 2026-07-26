"""Definition-only backlog validator for Momentum V2 vol-scaled continuation lane v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.canonical_research_lane_post_terminal_lifecycle_contract_v1 import (
    CONTRACT_ID as LIFECYCLE_CONTRACT_ID,
)

PACKAGE_MARKER = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_HYPOTHESIS_BACKLOG_V1=true"
)
BACKLOG_REL_PATH = (
    "config/research/momentum_v2_volatility_scaled_own_instrument_continuation_"
    "hypothesis_backlog_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_"
    "HYPOTHESIS_BACKLOG_V1.md"
)
REQUIRED_STATUS = "DEVELOPMENT_FAIL_SLOT_CONSUMED"
REQUIRED_PROGRAM_ID = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_RESEARCH_PROGRAM_V1"
)
REQUIRED_WORKSTREAM_ID = "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_WORKSTREAM_V1"
REQUIRED_HYPOTHESIS_ID = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
)
REQUIRED_STRATEGY_IDENTITY = "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1"
REQUIRED_HYP_STATUS = "DEVELOPMENT_FAIL"


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
    _require(payload.get("status") == REQUIRED_STATUS, "STATUS_NOT_DEVELOPMENT_FAIL_SLOT_CONSUMED")
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
    _require(payload.get("development_run_count") == 1, "DEVELOPMENT_RUN_COUNT")
    _require(payload.get("runner_start_count") == 1, "RUNNER_START_COUNT")
    _require(payload.get("run_budget_consumed") is True, "RUN_BUDGET_NOT_CONSUMED")
    _require(payload.get("next_eligible") == "NONE", "NEXT_ELIGIBLE_MISMATCH")
    _require(payload.get("open_unpreregistered_candidates") == [], "OPEN_CANDIDATES_NONEMPTY")
    _require(payload.get("terminal_hypotheses") == [REQUIRED_HYPOTHESIS_ID], "TERMINAL_MISMATCH")
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
    _require(hyp.get("status") == REQUIRED_HYP_STATUS, "HYP_STATUS")
    _require(hyp.get("development_run_count") == 1, "HYP_DEV_RUN_COUNT")
    _require(hyp.get("runner_start_count") == 1, "HYP_RUNNER_START_COUNT")
    _require(hyp.get("run_slot_consumed") is True, "HYP_RUN_SLOT_CONSUMED")
    _require(hyp.get("implementation_present") is True, "IMPLEMENTATION_PRESENT")
    _require(hyp.get("economic_validity") == "FAIL", "HYP_ECONOMIC_VALIDITY")
    pending = payload.get("pending_separate_scopes_untouched") or {}
    _require(
        pending.get("momentum_1h_v2_raw_binding_hypothesis_id")
        == "MOMENTUM_HORIZON_V2_NON_BITCOIN_FUTURES_V2",
        "PENDING_MOMENTUM_1H_V2",
    )
    if repo_root is not None:
        _require((repo_root / GOVERNANCE_REL_PATH).is_file(), "GOVERNANCE_DOC_MISSING")
    return {
        "valid": True,
        "status": REQUIRED_STATUS,
        "preregistered_count": 1,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "evaluation_authorized": False,
    }


def load_and_validate_repo_backlog(repo_root: Path) -> dict[str, Any]:
    payload = load_json(repo_root / BACKLOG_REL_PATH)
    return validate_backlog_contract(payload, repo_root=repo_root)
