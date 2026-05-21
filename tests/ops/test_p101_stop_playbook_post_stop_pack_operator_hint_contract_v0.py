"""Contract tests for P101 post-stop pack/P79 archive operator hints (static; no runtime)."""

from __future__ import annotations

from pathlib import Path

P101_SCRIPT = Path("scripts/ops/p101_stop_playbook_v1.sh")
WRAPPER_SCRIPT = "run_online_readiness_post_stop_pack_v0.sh"
PACK_SCRIPT = "pack_online_readiness_supervisor_evidence_v0.py"
P79_SCRIPT = "p79_supervisor_health_gate_v1.sh"

HINT_MARKERS = (
    "P101_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS_v0",
    "HINT_ONLY=true",
    "WRAPPER_REFERENCED=true",
    "WRAPPER_NOT_EXECUTED_BY_P101=true",
    "PACK_NOT_EXECUTED_BY_P101=true",
    "P79_ARCHIVE_VERIFY_NOT_EXECUTED_BY_P101=true",
    "OPERATOR_MUST_RUN_EXPLICITLY=true",
    "EVIDENCE_NON_AUTHORIZING=true",
)


def _script_lines() -> list[str]:
    return P101_SCRIPT.read_text(encoding="utf-8").splitlines()


def test_p101_hint_block_present_with_required_markers() -> None:
    text = P101_SCRIPT.read_text(encoding="utf-8")
    assert "P101_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS.txt" in text
    for marker in HINT_MARKERS:
        assert marker in text


def test_p101_hint_references_wrapper_and_optional_p79_verify() -> None:
    text = P101_SCRIPT.read_text(encoding="utf-8")
    assert WRAPPER_SCRIPT in text
    assert "--p79-archive-verify" in text
    assert "--out-dir" in text
    assert "--archive-root" in text
    assert "--primary-evidence-enforce" in text


def test_p101_does_not_execute_wrapper_automatically() -> None:
    offenders = [
        line
        for line in _script_lines()
        if WRAPPER_SCRIPT in line
        and not line.strip().startswith("#")
        and not line.strip().startswith("echo")
    ]
    assert offenders == []


def test_p101_does_not_execute_pack_script_automatically() -> None:
    offenders = [
        line
        for line in _script_lines()
        if PACK_SCRIPT in line
        and not line.strip().startswith("#")
        and not line.strip().startswith("echo")
    ]
    assert offenders == []


def test_p101_does_not_execute_p79_archive_verify_automatically() -> None:
    offenders = [
        line
        for line in _script_lines()
        if P79_SCRIPT in line and "ARCHIVE_ROOT" in line and not line.strip().startswith("echo")
    ]
    assert offenders == []


def test_p101_preserves_non_authorizing_semantics() -> None:
    text = P101_SCRIPT.read_text(encoding="utf-8")
    assert "EVIDENCE_NON_AUTHORIZING=true" in text
    assert "OPERATOR_MUST_RUN_EXPLICITLY=true" in text
    assert "deny_vars=" in text


def test_p101_does_not_add_new_launchctl_or_supervisor_start() -> None:
    text = P101_SCRIPT.read_text(encoding="utf-8")
    assert "launchctl bootstrap" not in text
    assert "launchctl kickstart" not in text
    assert "online_readiness_supervisor_v1.sh start" not in text
    assert "online_readiness_daemon_v1.sh" not in text
