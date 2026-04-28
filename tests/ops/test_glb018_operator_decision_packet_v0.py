"""Synthetic GLB-018 operator decision packet contract tests.

These tests characterize a future non-authorizing decision-packet contract.
They do not import production report code, read real registries, read generated
artifacts, close sessions, or authorize live trading.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any


CONTRACT = "operator_glb018_decision_packet_v0"

ALLOWED_DECISIONS = {
    "review_with_events",
    "evidence_missing_review",
    "defer_by_authority",
    "closeout_path_required",
    "stop",
}

AUTHORITY_FLAGS = {
    "live_authorization": False,
    "bounded_pilot_approval": False,
    "closeout_approval": False,
    "gate_passage": False,
    "strategy_readiness": False,
    "autonomy_readiness": False,
    "external_authority_completion": False,
}


def canonical_session_rows() -> list[dict[str, Any]]:
    return [
        {
            "session_id": "session_20260319_152033_bounded_pilot_8e5f2c",
            "triage_state": "CLOSEOUT_REVIEW_NEEDED",
            "execution_events_present": True,
            "operator_decision": "closeout_path_required",
        },
        {
            "session_id": "session_20260319_151416_bounded_pilot_579507",
            "triage_state": "CLOSEOUT_REVIEW_NEEDED",
            "execution_events_present": True,
            "operator_decision": "closeout_path_required",
        },
        {
            "session_id": "session_20260318_154852_bounded_pilot_979b86",
            "triage_state": "CLOSEOUT_REVIEW_NEEDED",
            "execution_events_present": False,
            "operator_decision": "evidence_missing_review",
        },
        {
            "session_id": "session_20260318_122341_bounded_pilot_02c8eb",
            "triage_state": "CLOSEOUT_REVIEW_NEEDED",
            "execution_events_present": False,
            "operator_decision": "evidence_missing_review",
        },
        {
            "session_id": "session_20260318_122123_bounded_pilot_8c7be9",
            "triage_state": "CLOSEOUT_REVIEW_NEEDED",
            "execution_events_present": False,
            "operator_decision": "evidence_missing_review",
        },
    ]


def build_operator_decision_packet(rows: list[dict[str, Any]]) -> dict[str, Any]:
    validate_operator_decision_rows(rows)

    decision_counts = Counter(row["operator_decision"] for row in rows)
    return {
        "contract": CONTRACT,
        "non_authorizing": True,
        "session_decisions": rows,
        "decision_counts": dict(sorted(decision_counts.items())),
        "operator_decision_required": True,
        "authority_boundary": dict(AUTHORITY_FLAGS),
        "hard_boundaries": [
            "do_not_mutate_registry_json",
            "do_not_mutate_out_ops",
            "do_not_close_sessions_from_this_packet",
            "do_not_infer_live_readiness",
            "do_not_authorize_live_trading",
        ],
    }


def validate_operator_decision_rows(rows: list[dict[str, Any]]) -> None:
    if len(rows) != 5:
        msg = f"expected exactly 5 session decisions, got {len(rows)}"
        raise ValueError(msg)

    seen: set[str] = set()
    for row in rows:
        session_id = row.get("session_id")
        decision = row.get("operator_decision")
        if not session_id:
            raise ValueError("missing session_id")
        if session_id in seen:
            raise ValueError(f"duplicate session_id: {session_id}")
        seen.add(session_id)
        if decision not in ALLOWED_DECISIONS:
            raise ValueError(f"invalid operator_decision: {decision!r}")


def assert_authority_false(packet: dict[str, Any]) -> None:
    assert packet["non_authorizing"] is True
    assert packet["authority_boundary"] == AUTHORITY_FLAGS


def test_builds_canonical_operator_decision_packet() -> None:
    packet = build_operator_decision_packet(canonical_session_rows())

    assert packet["contract"] == CONTRACT
    assert len(packet["session_decisions"]) == 5
    assert packet["operator_decision_required"] is True
    assert_authority_false(packet)


def test_decision_counts_match_current_glb018_packet_shape() -> None:
    packet = build_operator_decision_packet(canonical_session_rows())

    assert packet["decision_counts"] == {
        "closeout_path_required": 2,
        "evidence_missing_review": 3,
    }


def test_allowed_decisions_are_explicit() -> None:
    assert ALLOWED_DECISIONS == {
        "review_with_events",
        "evidence_missing_review",
        "defer_by_authority",
        "closeout_path_required",
        "stop",
    }


def test_invalid_decision_is_rejected() -> None:
    rows = canonical_session_rows()
    rows[0] = {**rows[0], "operator_decision": "approve_live"}

    try:
        build_operator_decision_packet(rows)
    except ValueError as exc:
        assert "invalid operator_decision" in str(exc)
    else:
        raise AssertionError("invalid decision was not rejected")


def test_missing_session_decision_is_rejected() -> None:
    rows = canonical_session_rows()[:4]

    try:
        build_operator_decision_packet(rows)
    except ValueError as exc:
        assert "expected exactly 5 session decisions" in str(exc)
    else:
        raise AssertionError("missing session decision was not rejected")


def test_duplicate_session_id_is_rejected() -> None:
    rows = canonical_session_rows()
    rows[1] = {**rows[1], "session_id": rows[0]["session_id"]}

    try:
        build_operator_decision_packet(rows)
    except ValueError as exc:
        assert "duplicate session_id" in str(exc)
    else:
        raise AssertionError("duplicate session id was not rejected")


def test_hard_boundaries_forbid_mutation_and_authorization() -> None:
    packet = build_operator_decision_packet(canonical_session_rows())

    assert packet["hard_boundaries"] == [
        "do_not_mutate_registry_json",
        "do_not_mutate_out_ops",
        "do_not_close_sessions_from_this_packet",
        "do_not_infer_live_readiness",
        "do_not_authorize_live_trading",
    ]


def test_serialized_packet_contains_no_unqualified_authority_claims() -> None:
    packet = build_operator_decision_packet(canonical_session_rows())
    serialized = json.dumps(packet, sort_keys=True).lower()

    forbidden_claims = [
        "live authorization granted",
        "bounded pilot approved",
        "closeout approved",
        "signoff complete",
        "gate passed",
        "strategy ready",
        "autonomy ready",
        "externally authorized",
        "approved for live",
        "trade approved",
    ]

    for claim in forbidden_claims:
        assert claim not in serialized


def test_this_contract_test_does_not_read_real_artifact_locations() -> None:
    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "/".join(["reports", "experiments", "live_sessions"]),
        "/".join(["out", "ops"]),
        "/".join(["execution_events", "sessions"]),
        "_".join(["live", "session", "registry"]),
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source_text
