"""Lane backlog validator for Momentum V2 vol-scaled after terminal closeout."""

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
DECISION_PACKET_REL_PATH = (
    "config/research/momentum_v2_volatility_scaled_own_instrument_continuation_"
    "program_definition_operator_decision_packet_v1.json"
)
REQUIRED_STATUS = "LANE_CLOSED_NO_FURTHER_RESEARCH"
REQUIRED_PROGRAM_ID = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_RESEARCH_PROGRAM_V1"
)
REQUIRED_WORKSTREAM_ID = "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_WORKSTREAM_V1"
REQUIRED_HYPOTHESIS_ID = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
)
REQUIRED_STRATEGY_IDENTITY = "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1"
REQUIRED_NEXT_STEP = "LANE_CLOSED_NO_FURTHER_RESEARCH_NO_EXECUTABLE_GO"
REQUIRED_EVIDENCE = "docs/evidence/evaluate_momentum_v2_volatility_scaled_own_instrument_continuation_development_v1/"


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
    _require(payload.get("run_budget_consumed") is True, "RUN_BUDGET_NOT_CONSUMED")
    _require(payload.get("retry_allowed") is False, "RETRY_ALLOWED")
    _require(payload.get("reopen_allowed") is False, "REOPEN_ALLOWED")
    _require(payload.get("next_canonical_step") == REQUIRED_NEXT_STEP, "NEXT_STEP_STALE")
    _require(payload.get("next_eligible") == "NONE", "NEXT_ELIGIBLE_NOT_NONE")
    _require(
        payload.get("operator_decision_packet_ref") == DECISION_PACKET_REL_PATH,
        "DECISION_PACKET_REF_MISSING",
    )
    rules = payload.get("governance_rules") or {}
    _require(rules.get("preregistered_count_exact") == 0, "PREREGISTERED_COUNT_NOT_0")
    _require(rules.get("open_unpreregistered_count_exact") == 0, "OPEN_UNPREREGISTERED_NOT_0")
    _require(rules.get("economic_gate_closed") is True, "ECONOMIC_GATE_NOT_CLOSED")
    _require(rules.get("promotion_closed") is True, "PROMOTION_NOT_CLOSED")
    _require(rules.get("retuning_after_fail_forbidden") is True, "RETUNING_NOT_FORBIDDEN")
    _require(payload.get("open_unpreregistered_candidates") == [], "OPEN_CANDIDATES_NONEMPTY")
    prereg = payload.get("preregistered_hypotheses") or []
    _require(len(prereg) == 0, "PREREGISTERED_LEN_NOT_0")
    terminals = payload.get("terminal_hypotheses") or []
    _require(len(terminals) == 1, "TERMINAL_LEN_NOT_1")
    hyp = terminals[0]
    _require(hyp.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID_MISMATCH")
    _require(hyp.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY")
    _require(hyp.get("status") == "TERMINAL_FAIL", "HYPOTHESIS_STATUS")
    _require(hyp.get("terminal_result") == "FAIL_CLOSED_NO_RETRY", "TERMINAL_RESULT")
    _require(hyp.get("economic_validity") == "FAIL", "HYP_ECONOMIC_VALIDITY")
    _require(hyp.get("evaluation_authorized") is False, "HYP_EVALUATION_AUTHORIZED")
    _require(hyp.get("development_run_count") == 1, "HYP_DEVELOPMENT_RUN_COUNT")
    _require(hyp.get("run_slot_consumed") is True, "HYP_RUN_SLOT_CONSUMED")
    _require(hyp.get("retry_allowed") is False, "HYP_RETRY_ALLOWED")
    _require(hyp.get("rerun_allowed") is False, "HYP_RERUN_ALLOWED")
    _require(hyp.get("reopen_allowed") is False, "HYP_REOPEN_ALLOWED")
    _require(hyp.get("holdout_allowed") is False, "HYP_HOLDOUT_ALLOWED")
    _require(hyp.get("evaluation_evidence_ref") == REQUIRED_EVIDENCE, "HYP_EVIDENCE_REF")
    promo = payload.get("promotion_and_economic_gate_policy") or {}
    _require(promo.get("promotion_eligible") is False, "PROMOTION_ELIGIBLE")
    _require(promo.get("economic_gate_open") is False, "ECONOMIC_GATE_OPEN")
    siblings = payload.get("closed_sibling_lanes") or {}
    _require(siblings.get("reopen_forbidden") is True, "SIBLING_REOPEN_ALLOWED")
    _require(
        siblings.get("cross_sectional_momentum_lane_status") == "LANE_CLOSED_NO_FURTHER_RESEARCH",
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
        "runtime_activated",
        "capital_activated",
    ):
        _require(rt.get(key) is False, f"RUNTIME_POLICY_{key.upper()}")

    if repo_root is not None:
        gov = repo_root / GOVERNANCE_REL_PATH
        _require(gov.is_file(), "GOVERNANCE_DOC_MISSING")
        evidence = repo_root / REQUIRED_EVIDENCE
        _require(evidence.is_dir(), "EVALUATION_EVIDENCE_MISSING")
        summary = evidence / "summary.json"
        _require(summary.is_file(), "EVALUATION_SUMMARY_MISSING")
        summary_payload = load_json(summary)
        _require(summary_payload.get("status") == "DEVELOPMENT_FAIL", "EVALUATION_RESULT_NOT_FAIL")
        _require(summary_payload.get("economic_validity") == "FAIL", "ECONOMIC_VALIDITY_NOT_FAIL")
        _require(summary_payload.get("holdout_accessed") is False, "HOLDOUT_ACCESSED")
        _require(summary_payload.get("sealed_accessed") is False, "SEALED_ACCESSED")
        _require(summary_payload.get("run_slot_consumed") is True, "SUMMARY_RUN_SLOT_NOT_CONSUMED")
        _require(summary_payload.get("development_run_count") == 1, "SUMMARY_DEV_RUN_COUNT")
        pending = payload.get("pending_separate_scopes_untouched") or {}
        _require(
            pending.get("momentum_1h_v2_raw_binding_hypothesis_id")
            == "MOMENTUM_HORIZON_V2_NON_BITCOIN_FUTURES_V2",
            "PENDING_MOMENTUM_1H_V2",
        )

    return {
        "valid": True,
        "status": REQUIRED_STATUS,
        "program_id": REQUIRED_PROGRAM_ID,
        "next_eligible": "NONE",
        "preregistered_count": 0,
        "terminal_count": 1,
        "evaluation_authorized": False,
        "development_reevaluation_eligible": False,
        "holdout_eligible": False,
        "sealed_eligible": False,
        "promotion_eligible": False,
        "activation_eligible": False,
        "automatic_selection_enabled": False,
        "historical_evidence_preserved": True,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
    }


def load_and_validate_repo_backlog(repo_root: Path) -> dict[str, Any]:
    payload = load_json(repo_root / BACKLOG_REL_PATH)
    return validate_backlog_contract(payload, repo_root=repo_root)
