"""Validator for post-VEPC vol-regime lifecycle operator decision packet v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.canonical_research_lane_post_terminal_lifecycle_contract_v1 import (
    CONTRACT_ID as LIFECYCLE_CONTRACT_ID,
)

PACKAGE_MARKER = "VOLATILITY_REGIME_POST_VEPC_LANE_LIFECYCLE_OPERATOR_DECISION_PACKET_V1=true"
PACKET_REL_PATH = (
    "config/research/volatility_regime_post_vepc_lane_lifecycle_operator_decision_packet_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/VOLATILITY_REGIME_POST_VEPC_LANE_LIFECYCLE_OPERATOR_DECISION_PACKET_V1.md"
)
BACKLOG_REL_PATH = "config/research/volatility_regime_hypothesis_backlog_v1.json"
PROGRAM_REL_PATH = "config/research/volatility_regime_research_program_v1.json"
REQUIRED_PACKET_ID = "VOLATILITY_REGIME_POST_VEPC_LANE_LIFECYCLE_OPERATOR_DECISION_PACKET_V1"
REQUIRED_STATUS = "OPERATOR_DECISION_PACKET_READY"
REQUIRED_LANE_STATUS = "POST_TERMINAL_OPERATOR_DECISION_REQUIRED"
REQUIRED_DECISIONS = (
    "DECLARE_AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS",
    "CLOSE_LANE_NO_FURTHER_RESEARCH",
    "CREATE_SUCCESSOR_HYPOTHESIS",
)
REQUIRED_GO_TOKENS = (
    "GO_VOLATILITY_REGIME_DECLARE_AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS_V1",
    "GO_VOLATILITY_REGIME_CLOSE_LANE_NO_FURTHER_RESEARCH_V1",
    "GO_VOLATILITY_REGIME_CREATE_SUCCESSOR_HYPOTHESIS_V1",
)


class DecisionPacketValidationError(ValueError):
    """Fail-closed decision-packet validation error."""


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise DecisionPacketValidationError(code)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_decision_packet_contract(
    payload: Mapping[str, Any], *, repo_root: Path | None = None
) -> dict[str, Any]:
    _require(payload.get("packet_id") == REQUIRED_PACKET_ID, "PACKET_ID_MISMATCH")
    _require(payload.get("status") == REQUIRED_STATUS, "STATUS_NOT_READY")
    _require(payload.get("lane_status") == REQUIRED_LANE_STATUS, "LANE_STATUS_MISMATCH")
    _require(
        payload.get("lifecycle_contract_id") == LIFECYCLE_CONTRACT_ID,
        "LIFECYCLE_CONTRACT_MISMATCH",
    )
    _require(payload.get("authority_effect") == "NONE", "AUTHORITY_EFFECT_NOT_NONE")
    _require(payload.get("runtime_effect") == "NONE", "RUNTIME_EFFECT_NOT_NONE")
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _require(payload.get("evaluation_executed") is False, "EVALUATION_EXECUTED")
    _require(payload.get("holdout_accessed") is False, "HOLDOUT_ACCESSED")
    _require(payload.get("live_authorized") is False, "LIVE_AUTHORIZED")
    _require(payload.get("orders_allowed") is False, "ORDERS_ALLOWED")
    _require(payload.get("decision_application_authorized") is False, "DECISION_APPLIED")
    _require(payload.get("closeout_applied") is False, "CLOSEOUT_APPLIED")
    _require(payload.get("awaiting_declared") is False, "AWAITING_DECLARED")
    _require(payload.get("successor_created") is False, "SUCCESSOR_CREATED")
    _require(payload.get("auto_create_successor_forbidden") is True, "AUTO_CREATE_ALLOWED")
    _require(payload.get("auto_await_forbidden") is True, "AUTO_AWAIT_ALLOWED")
    _require(payload.get("auto_close_forbidden") is True, "AUTO_CLOSE_ALLOWED")

    decisions = payload.get("enumerated_operator_decisions") or []
    _require(len(decisions) == 3, "DECISION_COUNT_NOT_3")
    decision_ids = tuple(d.get("decision_id") for d in decisions)
    _require(decision_ids == REQUIRED_DECISIONS, "DECISION_IDS_MISMATCH")
    go_tokens = tuple(d.get("go_token") for d in decisions)
    _require(go_tokens == REQUIRED_GO_TOKENS, "GO_TOKENS_MISMATCH")

    create = decisions[2]
    _require(create.get("requires_hypothesis_id") is True, "CREATE_HYPOTHESIS_ID_OPTIONAL")
    _require(
        create.get("requires_mechanism_definition") is True,
        "CREATE_MECHANISM_OPTIONAL",
    )

    forbidden = set(payload.get("forbidden_actions") or [])
    for required in (
        "AUTO_CREATE_SUCCESSOR",
        "EXECUTABLE_GO_WITHOUT_TARGET",
        "VEPC_RETRY",
        "HOLDOUT_ACCESS",
        "LIVE_ORDERS",
        "EVALUATION_EXECUTION",
    ):
        _require(required in forbidden, f"MISSING_FORBIDDEN:{required}")

    _require(
        payload.get("next_admissible_scope")
        == "VOLATILITY_REGIME_POST_TERMINAL_ENUMERATED_DECISION_APPLICATION_V1",
        "NEXT_SCOPE_MISMATCH",
    )
    next_tokens = list(payload.get("next_admissible_scope_go_tokens") or [])
    _require(next_tokens == list(REQUIRED_GO_TOKENS), "NEXT_GO_TOKENS_MISMATCH")

    if repo_root is not None:
        backlog = load_json(repo_root / BACKLOG_REL_PATH)
        program = load_json(repo_root / PROGRAM_REL_PATH)
        _require(
            backlog.get("status") == REQUIRED_LANE_STATUS,
            "BACKLOG_NOT_POST_TERMINAL",
        )
        _require(backlog.get("preregistered_hypotheses") == [], "BACKLOG_PREREG_NONEMPTY")
        _require(
            backlog.get("open_unpreregistered_candidates") == [],
            "BACKLOG_OPEN_NONEMPTY",
        )
        _require(backlog.get("explicit_closeout_decision") is False, "BACKLOG_CLOSEOUT_TRUE")
        _require(backlog.get("explicit_waiting_decision") is False, "BACKLOG_WAITING_TRUE")
        terminals = {t.get("strategy_identity") for t in (backlog.get("terminal_hypotheses") or [])}
        _require(
            "VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1" in terminals,
            "VEPC_NOT_TERMINAL",
        )
        _require(
            program.get("lane_backlog_status") == REQUIRED_LANE_STATUS,
            "PROGRAM_LANE_STATUS_MISMATCH",
        )
        _require(
            program.get("development_evaluation_authorized") is False,
            "PROGRAM_DEV_EVAL_AUTHORIZED",
        )
        _require(
            program.get("strategy_id") == "volatility_expansion_pullback_continuation",
            "PROGRAM_STRATEGY_ID_DRIFT",
        )
        gov = repo_root / GOVERNANCE_REL_PATH
        _require(gov.is_file(), "GOVERNANCE_DOC_MISSING")

    return {
        "valid": True,
        "packet_id": REQUIRED_PACKET_ID,
        "status": REQUIRED_STATUS,
        "lane_status": REQUIRED_LANE_STATUS,
        "decision_count": 3,
        "decision_application_authorized": False,
        "evaluation_authorized": False,
        "live_authorized": False,
        "orders_allowed": False,
    }


def load_and_validate_repo_decision_packet(repo_root: Path) -> dict[str, Any]:
    path = repo_root / PACKET_REL_PATH
    _require(path.is_file(), "PACKET_SSOT_MISSING")
    return validate_decision_packet_contract(load_json(path), repo_root=repo_root)
