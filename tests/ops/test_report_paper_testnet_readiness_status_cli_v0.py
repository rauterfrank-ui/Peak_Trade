"""CLI tests for the Paper/Testnet readiness status report."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


SCRIPT = Path("scripts/ops/report_paper_testnet_readiness_status.py")

AUTHORITY_FLAGS = {
    "live_authorization": False,
    "bounded_pilot_approval": False,
    "closeout_approval": False,
    "gate_passage": False,
    "strategy_readiness": False,
    "autonomy_readiness": False,
    "external_authority_completion": False,
}


def run_report(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--json", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def parse_payload(proc: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return json.loads(proc.stdout)


def assert_non_authorizing(payload: dict[str, object]) -> None:
    assert payload["non_authorizing"] is True
    assert payload["authority_boundary"] == AUTHORITY_FLAGS


def test_default_invocation_is_blocked_with_missing_paper_and_testnet_items() -> None:
    proc = run_report()
    payload = parse_payload(proc)

    assert proc.returncode == 0
    assert payload["contract"] == "paper_testnet_readiness_status_v0"
    assert payload["status"] == "BLOCKED"
    assert payload["blockers"] == [
        "paper.evidence_missing",
        "paper.robustness_missing",
        "paper.stress_missing",
        "testnet.evidence_missing",
        "testnet.robustness_missing",
        "testnet.stress_missing",
    ]
    assert_non_authorizing(payload)


def test_complete_paper_only_still_blocks_on_testnet() -> None:
    proc = run_report(
        "--paper-evidence-present",
        "--paper-robustness-present",
        "--paper-stress-present",
    )
    payload = parse_payload(proc)

    assert payload["status"] == "BLOCKED"
    assert payload["paper"] == {
        "evidence_present": True,
        "robustness_present": True,
        "stress_present": True,
    }
    assert payload["testnet"] == {
        "evidence_present": False,
        "robustness_present": False,
        "stress_present": False,
    }
    assert payload["blockers"] == [
        "testnet.evidence_missing",
        "testnet.robustness_missing",
        "testnet.stress_missing",
    ]
    assert_non_authorizing(payload)


def test_blocked_when_only_paper_evidence_missing() -> None:
    proc = run_report(
        "--paper-robustness-present",
        "--paper-stress-present",
        "--testnet-evidence-present",
        "--testnet-robustness-present",
        "--testnet-stress-present",
    )
    payload = parse_payload(proc)

    assert proc.returncode == 0
    assert payload["status"] == "BLOCKED"
    assert payload["blockers"] == ["paper.evidence_missing"]
    assert_non_authorizing(payload)


def test_blocked_when_only_testnet_evidence_missing() -> None:
    proc = run_report(
        "--paper-evidence-present",
        "--paper-robustness-present",
        "--paper-stress-present",
        "--testnet-robustness-present",
        "--testnet-stress-present",
    )
    payload = parse_payload(proc)

    assert proc.returncode == 0
    assert payload["status"] == "BLOCKED"
    assert payload["blockers"] == ["testnet.evidence_missing"]
    assert_non_authorizing(payload)


def test_blocked_when_robustness_and_stress_missing_but_evidence_present() -> None:
    proc = run_report(
        "--paper-evidence-present",
        "--testnet-evidence-present",
    )
    payload = parse_payload(proc)

    assert proc.returncode == 0
    assert payload["status"] == "BLOCKED"
    assert payload["blockers"] == [
        "paper.robustness_missing",
        "paper.stress_missing",
        "testnet.robustness_missing",
        "testnet.stress_missing",
    ]
    assert payload["paper"] == {
        "evidence_present": True,
        "robustness_present": False,
        "stress_present": False,
    }
    assert payload["testnet"] == {
        "evidence_present": True,
        "robustness_present": False,
        "stress_present": False,
    }
    assert_non_authorizing(payload)


def test_blocked_when_only_paper_evidence_missing() -> None:
    proc = run_report(
        "--paper-robustness-present",
        "--paper-stress-present",
        "--testnet-evidence-present",
        "--testnet-robustness-present",
        "--testnet-stress-present",
    )
    payload = parse_payload(proc)

    assert proc.returncode == 0
    assert payload["status"] == "BLOCKED"
    assert payload["blockers"] == ["paper.evidence_missing"]
    assert_non_authorizing(payload)


def test_blocked_when_only_testnet_evidence_missing() -> None:
    proc = run_report(
        "--paper-evidence-present",
        "--paper-robustness-present",
        "--paper-stress-present",
        "--testnet-robustness-present",
        "--testnet-stress-present",
    )
    payload = parse_payload(proc)

    assert proc.returncode == 0
    assert payload["status"] == "BLOCKED"
    assert payload["blockers"] == ["testnet.evidence_missing"]
    assert_non_authorizing(payload)


def test_blocked_when_robustness_and_stress_missing_but_evidence_present() -> None:
    proc = run_report(
        "--paper-evidence-present",
        "--testnet-evidence-present",
    )
    payload = parse_payload(proc)

    assert proc.returncode == 0
    assert payload["status"] == "BLOCKED"
    assert payload["blockers"] == [
        "paper.robustness_missing",
        "paper.stress_missing",
        "testnet.robustness_missing",
        "testnet.stress_missing",
    ]
    assert payload["paper"] == {
        "evidence_present": True,
        "robustness_present": False,
        "stress_present": False,
    }
    assert payload["testnet"] == {
        "evidence_present": True,
        "robustness_present": False,
        "stress_present": False,
    }
    assert_non_authorizing(payload)


def test_complete_paper_and_testnet_without_external_decision_is_ready_for_review() -> None:
    proc = run_report(
        "--paper-evidence-present",
        "--paper-robustness-present",
        "--paper-stress-present",
        "--testnet-evidence-present",
        "--testnet-robustness-present",
        "--testnet-stress-present",
    )
    payload = parse_payload(proc)

    assert payload["status"] == "READY_FOR_REVIEW"
    assert payload["blockers"] == []
    assert payload["missing_or_open_items"] == []
    assert payload["external_review_decision_present"] is False
    assert_non_authorizing(payload)


def test_complete_paper_and_testnet_with_external_decision_is_review_only() -> None:
    proc = run_report(
        "--paper-evidence-present",
        "--paper-robustness-present",
        "--paper-stress-present",
        "--testnet-evidence-present",
        "--testnet-robustness-present",
        "--testnet-stress-present",
        "--external-review-decision-present",
    )
    payload = parse_payload(proc)

    assert payload["status"] == "REVIEW_ONLY"
    assert payload["external_review_decision_present"] is True
    assert_non_authorizing(payload)


def test_output_contains_no_unqualified_authority_claims() -> None:
    proc = run_report(
        "--paper-evidence-present",
        "--paper-robustness-present",
        "--paper-stress-present",
        "--testnet-evidence-present",
        "--testnet-robustness-present",
        "--testnet-stress-present",
        "--external-review-decision-present",
    )

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
        "live ready",
    ]

    serialized = proc.stdout.lower()
    for claim in forbidden_claims:
        assert claim not in serialized


def test_this_cli_test_does_not_read_real_artifact_locations() -> None:
    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "/".join(["reports", "experiments", "live_sessions"]),
        "/".join(["out", "ops"]),
        "/".join(["execution_events", "sessions"]),
        "_".join(["paper", "testnet", "artifact"]),
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source_text
