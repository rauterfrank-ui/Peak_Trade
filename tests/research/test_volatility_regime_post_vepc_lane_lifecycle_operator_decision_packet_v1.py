"""Contract tests for post-VEPC vol-regime lifecycle operator decision packet v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.volatility_regime_post_vepc_lane_lifecycle_operator_decision_packet_v1 import (
    GOVERNANCE_REL_PATH,
    PACKET_REL_PATH,
    DecisionPacketValidationError,
    load_and_validate_repo_decision_packet,
    validate_decision_packet_contract,
)

REPO = Path(__file__).resolve().parents[2]
PACKET_PATH = REPO / PACKET_REL_PATH
GOVERNANCE = REPO / GOVERNANCE_REL_PATH
OWNER_MAP = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_decision_packet_ready_no_application() -> None:
    report = load_and_validate_repo_decision_packet(REPO)
    assert report["valid"] is True
    assert report["packet_id"] == (
        "VOLATILITY_REGIME_POST_VEPC_LANE_LIFECYCLE_OPERATOR_DECISION_PACKET_V1"
    )
    assert report["status"] == "OPERATOR_DECISION_PACKET_READY"
    assert report["lane_status"] == "POST_TERMINAL_OPERATOR_DECISION_REQUIRED"
    assert report["decision_count"] == 3
    assert report["decision_application_authorized"] is False
    assert report["evaluation_authorized"] is False
    assert report["live_authorized"] is False
    assert report["orders_allowed"] is False


def test_enumerated_decisions_and_go_tokens() -> None:
    packet = _load(PACKET_PATH)
    decisions = packet["enumerated_operator_decisions"]
    assert [d["decision_id"] for d in decisions] == [
        "DECLARE_AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS",
        "CLOSE_LANE_NO_FURTHER_RESEARCH",
        "CREATE_SUCCESSOR_HYPOTHESIS",
    ]
    assert [d["go_token"] for d in decisions] == [
        "GO_VOLATILITY_REGIME_DECLARE_AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS_V1",
        "GO_VOLATILITY_REGIME_CLOSE_LANE_NO_FURTHER_RESEARCH_V1",
        "GO_VOLATILITY_REGIME_CREATE_SUCCESSOR_HYPOTHESIS_V1",
    ]
    assert decisions[2]["requires_hypothesis_id"] is True
    assert decisions[2]["requires_mechanism_definition"] is True
    assert packet["auto_create_successor_forbidden"] is True
    assert packet["closeout_applied"] is False
    assert packet["awaiting_declared"] is False
    assert packet["successor_created"] is False


def test_fail_closed_mutations() -> None:
    payload = _load(PACKET_PATH)
    bad = copy.deepcopy(payload)
    bad["evaluation_authorized"] = True
    with pytest.raises(DecisionPacketValidationError, match="EVALUATION_AUTHORIZED"):
        validate_decision_packet_contract(bad)
    bad2 = copy.deepcopy(payload)
    bad2["successor_created"] = True
    with pytest.raises(DecisionPacketValidationError, match="SUCCESSOR_CREATED"):
        validate_decision_packet_contract(bad2)
    bad3 = copy.deepcopy(payload)
    bad3["auto_create_successor_forbidden"] = False
    with pytest.raises(DecisionPacketValidationError, match="AUTO_CREATE_ALLOWED"):
        validate_decision_packet_contract(bad3)
    bad4 = copy.deepcopy(payload)
    bad4["enumerated_operator_decisions"] = bad4["enumerated_operator_decisions"][:2]
    with pytest.raises(DecisionPacketValidationError, match="DECISION_COUNT_NOT_3"):
        validate_decision_packet_contract(bad4)


def test_governance_and_owner_map() -> None:
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_VOLATILITY_REGIME_POST_VEPC_LANE_LIFECYCLE_OPERATOR_DECISION_PACKET_V1" in text
    )
    assert "POST_TERMINAL_OPERATOR_DECISION_REQUIRED" in text
    assert "CREATE_SUCCESSOR_HYPOTHESIS" in text
    owners = _load(OWNER_MAP)["allowed_optimization_surfaces"]
    assert "VOLATILITY_REGIME_POST_VEPC_LANE_LIFECYCLE_OPERATOR_DECISION_PACKET_V1" in owners
