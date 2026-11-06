"""Bounded-pilot open-session triage characterization and CLI integration tests.

Synthetic helpers delegate to scripts.report_live_sessions (single source of truth).
Integration tests monkeypatch.chdir(tmp_path) registry overlays — no edits to tracked
workspace registries. No live authorization; no automated closeout.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal
from unittest.mock import patch

import pytest

from scripts.report_live_sessions import (
    BOUNDED_PILOT_OPEN_SESSION_TRIAGE_V0_CONTRACT,
    BOUNDED_PILOT_OPEN_SESSION_TRIAGE_V0_AUTHORITY_BOUNDARY,
    build_bounded_pilot_open_session_triage_v0_payload,
)

CONTRACT = BOUNDED_PILOT_OPEN_SESSION_TRIAGE_V0_CONTRACT
AUTHORITY_FLAGS = BOUNDED_PILOT_OPEN_SESSION_TRIAGE_V0_AUTHORITY_BOUNDARY

SessionTriageState = Literal[
    "REVIEW_WITH_EVENTS",
    "EVIDENCE_POINTER_MISSING",
    "CLOSEOUT_REVIEW_NEEDED",
]
ReportStatus = Literal["BLOCKED", "REVIEW_ONLY"]

from src.experiments.live_session_registry import LiveSessionRecord, register_live_session_run  # noqa: E402


@dataclass(frozen=True)
class SyntheticOpenSessionRow:
    session_id: str
    status: str = "started"
    execution_events_present: bool = False
    closeout_note: str | None = None
    lifecycle_state: str = "PARTIAL_NON_TERMINAL"


def build_bounded_pilot_open_session_triage_v0(
    rows: list[SyntheticOpenSessionRow],
) -> dict[str, object]:
    return build_bounded_pilot_open_session_triage_v0_payload(
        [
            {
                "session_id": r.session_id,
                "status": r.status,
                "execution_events_present": r.execution_events_present,
                "closeout_note": r.closeout_note,
                "lifecycle_state": r.lifecycle_state,
            }
            for r in rows
        ]
    )


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
    """Guardrail: contiguous production path literals are not pasted into this module body.

    (Import paths may include ``live_session_registry``; exclude that substring match.)
    """
    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "/".join(["reports", "experiments", "live_sessions"]),
        "/".join(["out", "ops"]),
        "/".join(["execution_events", "sessions"]),
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source_text


def test_bounded_pilot_open_session_triage_help_exposes_cli_flag(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from scripts.report_live_sessions import main

    with pytest.raises(SystemExit) as exc:
        with patch.object(sys, "argv", ["report_live_sessions.py", "--help"]):
            main()
    assert exc.value.code == 0
    merged = capsys.readouterr()
    combo = merged.out + merged.err
    assert "--bounded-pilot-open-session-triage" in combo


def _bp_started(session_id: str, *, started: datetime | None = None) -> LiveSessionRecord:
    t0 = started or datetime(2026, 3, 19, 15, 0, 0)
    return LiveSessionRecord(
        session_id=session_id,
        run_id="run_triage",
        run_type="live_session_bounded_pilot",
        mode="bounded_pilot",
        env_name="pilot_env",
        symbol="BTC/USDT",
        status="started",
        started_at=t0,
        finished_at=None,
        config={"strategy_name": "test"},
        metrics={"realized_pnl": 0.0},
        cli_args=[],
    )


def test_bounded_pilot_open_session_triage_integration_five_sessions_two_exec_present(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path.joinpath("reports", "experiments", "live_sessions")
    reg.mkdir(parents=True)

    from src.observability.execution_events import expected_session_scoped_events_jsonl_path  # noqa: E402

    base = datetime(2026, 3, 19, 14, 0, 0)
    ids_order = []
    for i in range(5):
        sid = f"sess_bp_triage_{i}"
        ids_order.append(sid)
        register_live_session_run(
            _bp_started(sid, started=base + timedelta(minutes=i)),
            base_dir=reg,
        )

    for sid in ids_order[:2]:
        rel = expected_session_scoped_events_jsonl_path(sid)
        path = tmp_path.joinpath(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-open-session-triage",
            "--json",
            "--registry-base",
            str(reg),
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["contract"] == CONTRACT
    assert payload["non_authorizing"] is True
    assert payload["authority_boundary"] == AUTHORITY_FLAGS
    assert payload["status"] == "BLOCKED"
    assert payload["blockers"] == ["GLB-018"]
    assert payload["counts"] == {
        "total_open_sessions": 5,
        "events_present": 2,
        "events_missing": 3,
        "closeout_review_needed": 5,
    }
    assert "bounded_pilot.open_sessions_present" in payload["missing_or_open_items"]
    serialized = json.dumps(payload, sort_keys=True).lower()
    assert all(
        forbidden not in serialized
        for forbidden in (
            "live authorization granted",
            "bounded pilot approved",
        )
    )


def test_bounded_pilot_open_session_triage_integration_empty_review_only_no_glb(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path.joinpath("reports", "experiments", "live_sessions")
    reg.mkdir(parents=True)

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-open-session-triage",
            "--json",
            "--registry-base",
            str(reg),
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "REVIEW_ONLY"
    assert payload["sessions"] == []
    assert payload["blockers"] == []
    assert payload["counts"]["total_open_sessions"] == 0
    assert payload["authority_boundary"] == AUTHORITY_FLAGS
