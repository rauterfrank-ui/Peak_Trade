"""Characterization tests for Session Review Pack report contracts.

`--session-review-pack` is a read-only, non-authorizing post-hoc review bundle
(see `docs/ops/specs/MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md`).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

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


def load_session_review_pack() -> dict[str, Any]:
    """Load JSON pack with INFO logs suppressed (stderr)."""
    result = run_report_live_sessions(
        "--session-review-pack",
        "--json",
        "--log-level",
        "ERROR",
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


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


def test_session_review_pack_json_top_level_keys_are_stable() -> None:
    pack = load_session_review_pack()

    expected_keys = {
        "authority_boundary",
        "contract",
        "disclaimer",
        "missing_fields",
        "mode",
        "non_authorizing",
        "references",
        "schema_version",
        "session",
        "source_contract",
    }
    assert set(pack) == expected_keys


def test_session_review_pack_contract_identifiers_are_stable() -> None:
    pack = load_session_review_pack()

    assert pack["contract"] == "report_live_sessions.session_review_pack_v0"
    assert pack["schema_version"] == "master_v2/session_review_pack/v0"
    assert pack["source_contract"] == (
        "docs/ops/specs/MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md"
    )


def test_session_review_pack_authority_boundary_shape_is_exactly_false() -> None:
    pack = load_session_review_pack()

    expected_boundary = {
        "autonomy_ready": False,
        "gate_passed": False,
        "live_authorization": False,
        "signoff_complete": False,
        "strategy_ready": False,
    }
    assert pack["authority_boundary"] == expected_boundary
    assert all(value is False for value in pack["authority_boundary"].values())


def test_session_review_pack_session_and_reference_key_sets_are_stable() -> None:
    pack = load_session_review_pack()

    assert set(pack["session"]) == {
        "mode_or_environment",
        "run_timestamp",
        "session_id",
    }
    assert set(pack["references"]) == {
        "artifacts_manifest_reference",
        "dashboard_observer_summary_reference",
        "evidence_references",
        "execution_gate_summary_reference",
        "handoff_reference",
        "learning_loop_feedback_reference",
        "operator_notes",
        "provenance_reference",
        "readiness_summary_reference",
        "registry_reference",
        "risk_kill_switch_summary_reference",
        "strategy_context_summary_reference",
    }


def test_session_review_pack_missing_fields_are_sorted_and_cover_empty_values() -> None:
    pack = load_session_review_pack()

    missing_fields = pack["missing_fields"]
    assert missing_fields == sorted(missing_fields)

    for key, value in pack["session"].items():
        if value is None:
            assert f"session.{key}" in missing_fields

    for key, value in pack["references"].items():
        if value is None or value == []:
            assert f"references.{key}" in missing_fields


def test_session_review_pack_disclaimer_is_non_authorizing_without_positive_claims() -> None:
    pack = load_session_review_pack()

    disclaimer = pack["disclaimer"]
    assert isinstance(disclaimer, str)
    lowered = disclaimer.lower()

    assert "read-only" in lowered
    assert "not live authorization" in lowered
    # Negations for gate/signoff; must not use unqualified success phrases.
    forbidden_positive_claims = [
        "live authorization granted",
        "signoff complete",
        "gate passed",
        "autonomy ready",
        "strategy ready",
        "externally authorized",
    ]
    for claim in forbidden_positive_claims:
        assert claim not in lowered


def test_session_review_pack_json_stdout_is_clean_and_round_trippable() -> None:
    result = run_report_live_sessions(
        "--session-review-pack",
        "--json",
        "--log-level",
        "ERROR",
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""

    parsed = json.loads(result.stdout)
    round_trip = json.loads(json.dumps(parsed, sort_keys=True))
    assert round_trip == parsed
    assert parsed["mode"] == "session_review_pack"


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


def test_session_review_pack_json_stdout_contains_single_clean_object() -> None:
    result = run_report_live_sessions(
        "--session-review-pack",
        "--json",
        "--log-level",
        "ERROR",
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""

    stdout = result.stdout.strip()
    assert stdout.startswith("{")
    assert stdout.endswith("}")
    assert stdout.count("{") >= 1
    assert json.loads(stdout)["mode"] == "session_review_pack"


def test_session_review_pack_serialized_json_has_no_positive_authority_claims() -> None:
    result = run_report_live_sessions(
        "--session-review-pack",
        "--json",
        "--log-level",
        "ERROR",
    )

    assert result.returncode == 0, result.stderr
    serialized = result.stdout.lower()

    forbidden_positive_claims = [
        "live authorization granted",
        "live authorized",
        "signoff complete",
        "gate passed",
        "autonomy ready",
        "autonomous-ready",
        "strategy ready",
        "externally authorized",
        "approved for live",
        "trade approved",
    ]
    for claim in forbidden_positive_claims:
        assert claim not in serialized


def test_session_review_pack_authority_values_are_booleans_not_strings() -> None:
    pack = load_session_review_pack()

    authority_boundary = pack["authority_boundary"]
    assert authority_boundary
    for key, value in authority_boundary.items():
        assert isinstance(value, bool), key
        assert value is False, key


def test_session_review_pack_missing_fields_are_unique_and_known_paths() -> None:
    pack = load_session_review_pack()

    missing_fields = pack["missing_fields"]
    assert len(missing_fields) == len(set(missing_fields))

    known_paths = {
        *(f"session.{key}" for key in pack["session"]),
        *(f"references.{key}" for key in pack["references"]),
    }
    assert set(missing_fields) <= known_paths


def test_session_review_pack_missing_fields_match_null_or_empty_values() -> None:
    pack = load_session_review_pack()

    for path in pack["missing_fields"]:
        section_name, key = path.split(".", 1)
        section = pack[section_name]
        value = section[key]
        assert value is None or value == []


def test_session_review_pack_no_unexpected_missing_null_or_empty_values() -> None:
    pack = load_session_review_pack()

    expected_missing_fields = set()
    for key, value in pack["session"].items():
        if value is None or value == []:
            expected_missing_fields.add(f"session.{key}")

    for key, value in pack["references"].items():
        if value is None or value == []:
            expected_missing_fields.add(f"references.{key}")

    assert set(pack["missing_fields"]) == expected_missing_fields


def test_session_review_pack_rejects_registry_base_in_v0() -> None:
    result = run_report_live_sessions(
        "--session-review-pack",
        "--json",
        "--registry-base",
        "/tmp/should-not-be-read",
    )

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "session-review-pack" in combined
