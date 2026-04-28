"""Synthetic bounded-pilot open-session triage characterization tests.

These tests model a future read-only triage surface for open bounded-pilot
sessions. They do not import production report code, read real registries, read
generated artifacts, close sessions, or authorize live trading.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Literal


CONTRACT = "bounded_pilot_open_session_triage_v0"

AUTHORITY_FLAGS = {
    "live_authorization": False,
    "bounded_pilot_approval": False,
    "closeout_approval": False,
    "gate_passage": False,
    "strategy_readiness": False,
    "autonomy_readiness": False,
    "external_authority_completion": False,
}

SessionTriageState = Literal[
    "REVIEW_WITH_EVENTS",
    "EVIDENCE_POINTER_MISSING",
    "CLOSEOUT_REVIEW_NEEDED",
]
ReportStatus = Literal["BLOCKED", "REVIEW_ONLY"]


@dataclass(frozen=True)
class SyntheticOpenSessionRow:
    session_id: str
    status: str = "started"
    execution_events_present: bool = False
    closeout_note: str | None = None
    lifecycle_state: str = "PARTIAL_NON_TERMINAL"


def classify_open_session(row: SyntheticOpenSessionRow) -> SessionTriageState:
    if row.lifecycle_state != "TERMINAL_CLEAN" or not row.closeout_note:
        return "CLOSEOUT_REVIEW_NEEDED"
    if row.execution_events_present:
        return "REVIEW_WITH_EVENTS"
    return "EVIDENCE_POINTER_MISSING"


def build_bounded_pilot_open_session_triage_v0(
    rows: list[SyntheticOpenSessionRow],
) -> dict[str, object]:
    session_items: list[dict[str, object]] = []
    counts = {
        "total_open_sessions": len(rows),
        "events_present": 0,
        "events_missing": 0,
        "closeout_review_needed": 0,
    }

    for row in rows:
        if row.execution_events_present:
            counts["events_present"] += 1
        else:
            counts["events_missing"] += 1

        triage_state = classify_open_session(row)
        if triage_state == "CLOSEOUT_REVIEW_NEEDED":
            counts["closeout_review_needed"] += 1

        session_items.append(
            {
                "session_id": row.session_id,
                "status": row.status,
                "execution_events_present": row.execution_events_present,
                "closeout_note_present": row.closeout_note is not None,
                "lifecycle_state": row.lifecycle_state,
                "triage_state": triage_state,
                "suggested_operator_action": "review_or_defer_by_authority",
                "authority_boundary": dict(AUTHORITY_FLAGS),
            }
        )

    blockers: list[str] = []
    missing_or_open_items: list[str] = []
    if rows:
        blockers.append("GLB-018")
        missing_or_open_items.append("bounded_pilot.open_sessions_present")
    if counts["events_missing"]:
        missing_or_open_items.append("bounded_pilot.execution_events_missing")
    if counts["closeout_review_needed"]:
        missing_or_open_items.append("bounded_pilot.closeout_review_needed")

    status: ReportStatus = "BLOCKED" if blockers else "REVIEW_ONLY"

    return {
        "contract": CONTRACT,
        "non_authorizing": True,
        "status": status,
        "sessions": session_items,
        "counts": counts,
        "blockers": sorted(set(blockers)),
        "missing_or_open_items": sorted(set(missing_or_open_items)),
        "authority_boundary": dict(AUTHORITY_FLAGS),
    }


def assert_authority_false(payload: dict[str, object]) -> None:
    assert payload["authority_boundary"] == AUTHORITY_FLAGS
    for session in payload.get("sessions", []):
        assert session["authority_boundary"] == AUTHORITY_FLAGS


def test_session_with_events_present_can_be_reviewed_with_events() -> None:
    payload = build_bounded_pilot_open_session_triage_v0(
        [
            SyntheticOpenSessionRow(
                session_id="session_a",
                execution_events_present=True,
                closeout_note="operator reviewed",
                lifecycle_state="TERMINAL_CLEAN",
            )
        ]
    )

    assert payload["sessions"][0]["triage_state"] == "REVIEW_WITH_EVENTS"
    assert payload["counts"]["events_present"] == 1
    assert payload["counts"]["events_missing"] == 0
    assert_authority_false(payload)


def test_session_without_events_is_evidence_pointer_missing() -> None:
    payload = build_bounded_pilot_open_session_triage_v0(
        [
            SyntheticOpenSessionRow(
                session_id="session_a",
                execution_events_present=False,
                closeout_note="operator reviewed",
                lifecycle_state="TERMINAL_CLEAN",
            )
        ]
    )

    assert payload["sessions"][0]["triage_state"] == "EVIDENCE_POINTER_MISSING"
    assert "bounded_pilot.execution_events_missing" in payload["missing_or_open_items"]
    assert_authority_false(payload)


def test_non_terminal_closeout_lifecycle_keeps_glb_018() -> None:
    payload = build_bounded_pilot_open_session_triage_v0(
        [SyntheticOpenSessionRow(session_id="session_a", execution_events_present=True)]
    )

    assert payload["status"] == "BLOCKED"
    assert payload["blockers"] == ["GLB-018"]
    assert payload["sessions"][0]["triage_state"] == "CLOSEOUT_REVIEW_NEEDED"
    assert "bounded_pilot.closeout_review_needed" in payload["missing_or_open_items"]


def test_two_events_present_three_missing_counts_match_current_snapshot_shape() -> None:
    payload = build_bounded_pilot_open_session_triage_v0(
        [
            SyntheticOpenSessionRow("session_1", execution_events_present=True),
            SyntheticOpenSessionRow("session_2", execution_events_present=True),
            SyntheticOpenSessionRow("session_3", execution_events_present=False),
            SyntheticOpenSessionRow("session_4", execution_events_present=False),
            SyntheticOpenSessionRow("session_5", execution_events_present=False),
        ]
    )

    assert payload["status"] == "BLOCKED"
    assert payload["counts"] == {
        "total_open_sessions": 5,
        "events_present": 2,
        "events_missing": 3,
        "closeout_review_needed": 5,
    }
    assert payload["blockers"] == ["GLB-018"]
    assert "bounded_pilot.open_sessions_present" in payload["missing_or_open_items"]


def test_no_open_sessions_is_review_only_without_glb_018() -> None:
    payload = build_bounded_pilot_open_session_triage_v0([])

    assert payload["status"] == "REVIEW_ONLY"
    assert payload["sessions"] == []
    assert payload["blockers"] == []
    assert payload["missing_or_open_items"] == []
    assert_authority_false(payload)


def test_report_does_not_close_or_defer_sessions_automatically() -> None:
    payload = build_bounded_pilot_open_session_triage_v0(
        [SyntheticOpenSessionRow(session_id="session_a", execution_events_present=True)]
    )

    assert payload["sessions"][0]["suggested_operator_action"] == "review_or_defer_by_authority"
    assert "closed" not in json.dumps(payload, sort_keys=True).lower()
    assert "auto_deferred" not in json.dumps(payload, sort_keys=True).lower()


def test_serialized_output_contains_no_unqualified_authority_claims() -> None:
    payloads = [
        build_bounded_pilot_open_session_triage_v0([]),
        build_bounded_pilot_open_session_triage_v0(
            [SyntheticOpenSessionRow(session_id="session_a", execution_events_present=True)]
        ),
    ]

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

    for payload in payloads:
        serialized = json.dumps(payload, sort_keys=True).lower()
        for claim in forbidden_claims:
            assert claim not in serialized


def test_this_triage_test_does_not_read_real_artifact_locations() -> None:
    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "/".join(["reports", "experiments", "live_sessions"]),
        "/".join(["out", "ops"]),
        "/".join(["execution_events", "sessions"]),
        "_".join(["live", "session", "registry"]),
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source_text
