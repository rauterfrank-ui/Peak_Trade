"""Characterization tests for a future pre-live package status report mode.

These tests describe the desired read-only `report_live_sessions.py`
`--pre-live-package-status --json` surface without implementing or invoking a
production mode. They do not read real registries, generated reports, or
artifact directories.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal


CONTRACT = "pre_live_package_status_v0"
FUTURE_FLAG = "--pre-live-package-status"

AUTHORITY_FLAGS = {
    "live_authorization": False,
    "bounded_pilot_approval": False,
    "closeout_approval": False,
    "gate_passage": False,
    "strategy_readiness": False,
    "autonomy_readiness": False,
    "external_authority_completion": False,
}

Status = Literal["BLOCKED", "NOT_READY", "READY_FOR_EXTERNAL_REVIEW", "REVIEW_ONLY"]


def build_future_pre_live_package_status_report(
    *,
    open_bounded_pilot_sessions: int = 0,
    closeout_lifecycle_status: str = "TERMINAL_CLEAN",
    evidence_package_complete: bool = True,
    blocker_states: dict[str, str] | None = None,
    external_decision_present: bool = False,
) -> dict[str, object]:
    blocker_states = blocker_states or {}
    missing_or_open_items: list[str] = []
    blockers: list[str] = []

    if open_bounded_pilot_sessions:
        missing_or_open_items.append("bounded_pilot.open_sessions_present")
        blockers.append("GLB-018")

    if closeout_lifecycle_status != "TERMINAL_CLEAN":
        missing_or_open_items.append("closeout_lifecycle.non_terminal_or_partial")
        blockers.append("GLB-018")

    if not evidence_package_complete:
        missing_or_open_items.append("evidence_package.incomplete")
        blockers.append("GLB-003")

    for blocker_id, state in sorted(blocker_states.items()):
        if state in {"OPEN", "BLOCKED"}:
            missing_or_open_items.append(f"blockers.{blocker_id}.{state.lower()}")
            blockers.append(blocker_id)

    unique_blockers = sorted(set(blockers))
    unique_missing = sorted(set(missing_or_open_items))

    if unique_blockers:
        status: Status = "BLOCKED"
    elif not evidence_package_complete:
        status = "NOT_READY"
    elif not external_decision_present:
        status = "READY_FOR_EXTERNAL_REVIEW"
    else:
        status = "REVIEW_ONLY"

    return {
        "contract": CONTRACT,
        "mode": "pre_live_package_status",
        "future_flag": FUTURE_FLAG,
        "json_only": True,
        "stdout_only": True,
        "non_authorizing": True,
        "status": status,
        "open_bounded_pilot_sessions": open_bounded_pilot_sessions,
        "closeout_lifecycle_status": closeout_lifecycle_status,
        "evidence_package_complete": evidence_package_complete,
        "blocker_states": dict(sorted(blocker_states.items())),
        "blockers": unique_blockers,
        "missing_or_open_items": unique_missing,
        "authority_boundary": dict(AUTHORITY_FLAGS),
    }


def assert_non_authorizing(payload: dict[str, object]) -> None:
    assert payload["non_authorizing"] is True
    assert payload["authority_boundary"] == AUTHORITY_FLAGS


def test_future_contract_and_flag_are_explicit() -> None:
    payload = build_future_pre_live_package_status_report()

    assert payload["contract"] == CONTRACT
    assert payload["mode"] == "pre_live_package_status"
    assert payload["future_flag"] == FUTURE_FLAG
    assert payload["json_only"] is True
    assert payload["stdout_only"] is True
    assert_non_authorizing(payload)


def test_open_bounded_pilot_sessions_remain_blockers() -> None:
    payload = build_future_pre_live_package_status_report(open_bounded_pilot_sessions=5)

    assert payload["status"] == "BLOCKED"
    assert "GLB-018" in payload["blockers"]
    assert "bounded_pilot.open_sessions_present" in payload["missing_or_open_items"]
    assert_non_authorizing(payload)


def test_partial_closeout_lifecycle_remains_blocker() -> None:
    payload = build_future_pre_live_package_status_report(
        closeout_lifecycle_status="PARTIAL_NON_TERMINAL"
    )

    assert payload["status"] == "BLOCKED"
    assert "GLB-018" in payload["blockers"]
    assert "closeout_lifecycle.non_terminal_or_partial" in payload["missing_or_open_items"]
    assert_non_authorizing(payload)


def test_missing_evidence_package_blocks_status() -> None:
    payload = build_future_pre_live_package_status_report(evidence_package_complete=False)

    assert payload["status"] == "BLOCKED"
    assert "GLB-003" in payload["blockers"]
    assert "evidence_package.incomplete" in payload["missing_or_open_items"]
    assert_non_authorizing(payload)


def test_closed_blockers_without_external_decision_are_external_review_only() -> None:
    payload = build_future_pre_live_package_status_report(
        blocker_states={"GLB-003": "CLOSED", "GLB-018": "CLOSED"},
        external_decision_present=False,
    )

    assert payload["status"] == "READY_FOR_EXTERNAL_REVIEW"
    assert payload["blockers"] == []
    assert payload["missing_or_open_items"] == []
    assert_non_authorizing(payload)


def test_external_decision_does_not_turn_report_into_live_ready() -> None:
    payload = build_future_pre_live_package_status_report(
        blocker_states={"GLB-003": "CLOSED"},
        external_decision_present=True,
    )

    assert payload["status"] == "REVIEW_ONLY"
    assert_non_authorizing(payload)


def test_report_does_not_close_open_blockers_automatically() -> None:
    payload = build_future_pre_live_package_status_report(
        blocker_states={"GLB-008": "BLOCKED", "GLB-014": "OPEN"}
    )

    assert payload["status"] == "BLOCKED"
    assert payload["blocker_states"] == {"GLB-008": "BLOCKED", "GLB-014": "OPEN"}
    assert payload["blockers"] == ["GLB-008", "GLB-014"]
    assert "blockers.GLB-008.blocked" in payload["missing_or_open_items"]
    assert "blockers.GLB-014.open" in payload["missing_or_open_items"]


def test_serialized_report_contains_no_unqualified_authority_claims() -> None:
    payloads = [
        build_future_pre_live_package_status_report(),
        build_future_pre_live_package_status_report(open_bounded_pilot_sessions=5),
        build_future_pre_live_package_status_report(external_decision_present=True),
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


def test_production_report_live_sessions_parser_does_not_expose_future_flag_yet() -> None:
    source = Path("scripts/report_live_sessions.py").read_text(encoding="utf-8")

    assert FUTURE_FLAG not in source


def test_this_characterization_test_does_not_read_real_artifact_locations() -> None:
    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "/".join(["reports", "experiments", "live_sessions"]),
        "/".join(["out", "ops"]),
        "/".join(["execution_events", "sessions"]),
        "_".join(["live", "session", "registry"]),
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source_text
