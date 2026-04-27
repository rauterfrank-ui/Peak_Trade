"""Characterization tests for Session Review Pack report contracts.

`--session-review-pack` is a read-only, non-authorizing post-hoc review bundle
(see `docs/ops/specs/MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md`).
"""

from __future__ import annotations

import json
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


def test_report_live_sessions_help_exposes_session_review_pack_read_only() -> None:
    """Help documents the read-only pack mode without authority claims."""

    result = run_report_live_sessions("--help")

    assert result.returncode == 0, result.stderr
    help_text = result.stdout + result.stderr

    assert "session-review-pack" in help_text
    assert "Read-only" in help_text or "read-only" in help_text.lower()
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


def test_session_review_pack_requires_json() -> None:
    """V0 is JSON-only; --session-review-pack without --json fails closed."""

    result = run_report_live_sessions("--session-review-pack")

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "session-review-pack" in combined
    assert "--json" in combined


def test_session_review_pack_json_shape() -> None:
    """Static v0 pack matches contract-oriented keys and non-authorizing posture."""

    result = run_report_live_sessions("--session-review-pack", "--json")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["contract"] == "report_live_sessions.session_review_pack_v0"
    assert data["schema_version"] == "master_v2/session_review_pack/v0"
    assert data["non_authorizing"] is True
    assert data["mode"] == "session_review_pack"
    assert data["source_contract"] == "docs/ops/specs/MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md"
    ab = data["authority_boundary"]
    assert ab["live_authorization"] is False
    assert ab["signoff_complete"] is False
    assert ab["gate_passed"] is False
    assert ab["autonomy_ready"] is False
    assert ab["strategy_ready"] is False
    assert "session" in data and "references" in data
    assert isinstance(data["missing_fields"], list)
    assert "session.session_id" in data["missing_fields"]


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
