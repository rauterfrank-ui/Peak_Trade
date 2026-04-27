"""Characterization tests for future Session Review Pack report contracts.

These tests intentionally do not implement a session-review-pack mode. They pin
the current non-authorizing/read-only posture around existing report surfaces so
a future additive report can be introduced safely.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_SCRIPT = REPO_ROOT / "scripts" / "report_live_sessions.py"


def run_report_live_sessions(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPORT_SCRIPT), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_report_live_sessions_help_does_not_expose_session_review_pack_mode_yet() -> None:
    """The Session Review Pack is currently a docs-only contract, not a CLI mode."""

    result = run_report_live_sessions("--help")

    assert result.returncode == 0, result.stderr
    help_text = result.stdout + result.stderr

    assert "session-review-pack" not in help_text
    assert "live authorization" not in help_text.lower()
    assert "signoff complete" not in help_text.lower()
    assert "autonomous-ready" not in help_text.lower()


@pytest.mark.parametrize(
    "mode_flag",
    [
        "--evidence-pointers",
        "--bounded-pilot-readiness-summary",
        "--bounded-pilot-gate-index",
        "--bounded-pilot-operator-overview",
        "--bounded-pilot-closeout-status-summary",
    ],
)
def test_existing_report_modes_are_not_described_as_authority_surfaces(mode_flag: str) -> None:
    """Existing related report modes should not be advertised as approvals."""

    result = run_report_live_sessions("--help")
    assert result.returncode == 0, result.stderr

    help_text = result.stdout + result.stderr

    if mode_flag not in help_text:
        pytest.skip(f"{mode_flag} is not exposed by this repo version")

    forbidden_claims = [
        "approve live",
        "authorizes live",
        "live authorization",
        "signoff complete",
        "gate passed",
        "autonomous-ready",
        "externally authorized",
    ]

    lowered = help_text.lower()
    for claim in forbidden_claims:
        assert claim not in lowered


def test_unknown_session_review_pack_flag_fails_closed() -> None:
    """A future mode is not silently accepted before implementation."""

    result = run_report_live_sessions("--session-review-pack")

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "session-review-pack" in combined or "unrecognized" in combined.lower()


def test_help_keeps_report_script_read_or_report_oriented() -> None:
    """The current CLI is report-oriented and should not advertise order actions."""

    result = run_report_live_sessions("--help")
    assert result.returncode == 0, result.stderr

    help_text = result.stdout + result.stderr
    lowered = help_text.lower()

    expected_report_terms = ["report", "session"]
    assert any(term in lowered for term in expected_report_terms)

    forbidden_order_terms = [
        "place order",
        "submit order",
        "execute trade",
        "open position",
        "close position",
    ]
    for term in forbidden_order_terms:
        assert term not in lowered
