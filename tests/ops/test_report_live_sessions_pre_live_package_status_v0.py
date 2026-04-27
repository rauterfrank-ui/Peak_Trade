"""Tests for Pre-Live package status report (`--pre-live-package-status --json`).

Synthetic helpers pin intended semantics for `pre_live_package_status_v0`. Integration tests
invoke `scripts.report_live_sessions.main()` with `--registry-base` pointing at isolated
directories under ``tmp_path`` (no commits to repo registries).

These tests do not read real production artifact trees in the workspace when running under
their own ``tmp_path`` registry overlays.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal
from unittest.mock import patch

import pytest

from src.experiments.live_session_registry import LiveSessionRecord, register_live_session_run  # noqa: E402


CONTRACT = "pre_live_package_status_v0"
CLI_FLAG = "--pre-live-package-status"

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
        "future_flag": CLI_FLAG,
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
    assert payload["future_flag"] == CLI_FLAG
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


def test_production_parser_exposes_pre_live_package_status_flag_in_source() -> None:
    source = Path("scripts/report_live_sessions.py").read_text(encoding="utf-8")

    assert CLI_FLAG in source
    assert 'dest="pre_live_package_status"' in source


def test_pre_live_package_status_requires_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
            CLI_FLAG,
            "--registry-base",
            str(reg),
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 2


def test_pre_live_package_status_empty_registry_read_only_stdout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No bounded rows: closeout classify → NO_BOUNDED_PILOT; status external-review semantics."""
    monkeypatch.chdir(tmp_path)
    reg = tmp_path.joinpath("reports", "experiments", "live_sessions")
    reg.mkdir(parents=True)
    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            CLI_FLAG,
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
    assert payload["json_only"] is True
    assert payload["stdout_only"] is True
    assert payload["open_bounded_pilot_sessions"] == 0
    assert payload["status"] == "READY_FOR_EXTERNAL_REVIEW"
    low = json.dumps(payload, sort_keys=True).lower()
    assert "live authorization granted" not in low


def _bp_rec_started(session_id: str, *, started: datetime | None = None) -> LiveSessionRecord:
    t0 = started or datetime(2026, 3, 19, 12, 0, 0)
    return LiveSessionRecord(
        session_id=session_id,
        run_id="run_v0",
        run_type="live_session_live",
        mode="bounded_pilot",
        env_name="pilot_env",
        symbol="BTC/USDT",
        status="started",
        started_at=t0,
        finished_at=None,
        config={},
        metrics={},
        cli_args=[],
    )


def test_pre_live_package_status_blocked_with_open_bounded_pilot_sessions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path.joinpath("reports", "experiments", "live_sessions")
    reg.mkdir(parents=True)
    t0 = datetime(2026, 3, 19, 15, 14, 0)
    register_live_session_run(_bp_rec_started("bp_open_one", started=t0), base_dir=reg)
    register_live_session_run(
        _bp_rec_started("bp_open_two", started=t0 + timedelta(minutes=1)), base_dir=reg
    )

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            CLI_FLAG,
            "--json",
            "--registry-base",
            str(reg),
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "BLOCKED"
    assert payload["open_bounded_pilot_sessions"] == 2
    assert "GLB-018" in payload["blockers"]
    assert "bounded_pilot.open_sessions_present" in payload["missing_or_open_items"]


def test_this_characterization_test_does_not_read_real_artifact_locations() -> None:
    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "/".join(["reports", "experiments", "live_sessions"]),
        "/".join(["out", "ops"]),
        "/".join(["execution_events", "sessions"]),
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source_text
