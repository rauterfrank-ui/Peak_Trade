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
    pr = payload["paper_robustness_evidence_v0"]
    assert isinstance(pr, dict)
    assert pr["accepted"] is False
    assert pr["non_authorizing"] is True
    assert pr["contributes_to"] == "paper_robustness_only"


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


def test_paper_runtime_closeout_review_surfaces_in_json_and_stays_blocked(tmp_path: Path) -> None:
    closeout = tmp_path / "closeout.md"
    closeout.write_text(
        "\n".join(
            [
                "# x",
                "VERDICT=7200S_SCHEDULER_PAPER_RUNTIME_EVIDENCE_PASS",
                "",
            ]
        ),
        encoding="utf-8",
    )
    proc = run_report("--paper-runtime-evidence-review", str(closeout))
    assert proc.returncode == 0
    payload = parse_payload(proc)

    assert payload["status"] == "BLOCKED"
    assert payload["testnet_authorized"] is False
    assert payload["live_authorized"] is False
    assert payload["paper"]["evidence_present"] is True
    pr = payload["paper_runtime_evidence_v0"]
    assert isinstance(pr, dict)
    assert pr["accepted"] is True
    assert pr["non_authorizing"] is True
    assert pr["verdict"] == "7200S_SCHEDULER_PAPER_RUNTIME_EVIDENCE_PASS"
    assert pr["does_not_authorize"] == [
        "testnet",
        "live",
        "broker",
        "exchange",
        "order_submission",
    ]
    assert_non_authorizing(payload)


def test_paper_runtime_review_json_pass_surfaces_accepted(tmp_path: Path) -> None:
    review = tmp_path / "review.json"
    review.write_text(
        '{"issues": [], "metrics": {"fills_count": 1}, "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = run_report("--paper-runtime-evidence-review", str(review))
    assert proc.returncode == 0
    payload = parse_payload(proc)
    pr = payload["paper_runtime_evidence_v0"]
    assert pr["accepted"] is True
    assert pr["verdict"] == "PASS"
    assert payload["status"] == "BLOCKED"
    assert payload["testnet_authorized"] is False


def test_paper_runtime_review_missing_file_exits_2(tmp_path: Path) -> None:
    missing = tmp_path / "nope.md"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--paper-runtime-evidence-review", str(missing)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert proc.stdout.strip() == ""


def test_paper_runtime_review_invalid_content_exits_2(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("VERDICT=NOT_A_REAL_CLOSEOUT\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--paper-runtime-evidence-review", str(bad)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_human_summary_includes_evidence_line_without_json(tmp_path: Path) -> None:
    closeout = tmp_path / "c.md"
    closeout.write_text(
        "VERDICT=SIXTY_MIN_SCHEDULER_PAPER_RUNTIME_EVIDENCE_PASS\n", encoding="utf-8"
    )
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--paper-runtime-evidence-review", str(closeout)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "paper_runtime_evidence_accepted=true" in proc.stdout
    assert "paper_robustness_evidence_accepted=false" in proc.stdout
    assert "testnet_authorized=false" in proc.stdout
    assert "live_authorized=false" in proc.stdout
    assert "testnet ready" not in proc.stdout.lower()


def test_paper_robustness_closeout_review_surfaces_in_json_and_stays_blocked(
    tmp_path: Path,
) -> None:
    closeout = tmp_path / "robustness.md"
    closeout.write_text(
        "\n".join(
            [
                "# x",
                "VERDICT=PAPER_ROBUSTNESS_EVIDENCE_PASS",
                "",
            ]
        ),
        encoding="utf-8",
    )
    proc = run_report("--paper-robustness-evidence-review", str(closeout))
    assert proc.returncode == 0
    payload = parse_payload(proc)

    assert payload["status"] == "BLOCKED"
    assert payload["testnet_authorized"] is False
    assert payload["live_authorized"] is False
    assert payload["paper"]["robustness_present"] is True
    assert payload["paper"]["evidence_present"] is False
    pr = payload["paper_robustness_evidence_v0"]
    assert isinstance(pr, dict)
    assert pr["accepted"] is True
    assert pr["non_authorizing"] is True
    assert pr["verdict"] == "PAPER_ROBUSTNESS_EVIDENCE_PASS"
    assert pr["contributes_to"] == "paper_robustness_only"
    assert pr["does_not_authorize"] == [
        "testnet",
        "live",
        "broker",
        "exchange",
        "order_submission",
    ]
    assert_non_authorizing(payload)


def test_paper_robustness_review_json_pass_surfaces_accepted(tmp_path: Path) -> None:
    review = tmp_path / "review.json"
    review.write_text(
        '{"issues": [], "evidence_kind": "paper_robustness", "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = run_report("--paper-robustness-evidence-review", str(review))
    assert proc.returncode == 0
    payload = parse_payload(proc)
    pr = payload["paper_robustness_evidence_v0"]
    assert pr["accepted"] is True
    assert pr["verdict"] == "PASS"
    assert payload["status"] == "BLOCKED"
    assert payload["testnet_authorized"] is False


def test_paper_robustness_still_blocked_when_stress_and_testnet_missing(tmp_path: Path) -> None:
    closeout = tmp_path / "r.md"
    closeout.write_text("VERDICT=ROBUSTNESS_EVIDENCE_PASS\n", encoding="utf-8")
    proc = run_report("--paper-robustness-evidence-review", str(closeout))
    payload = parse_payload(proc)
    assert payload["status"] == "BLOCKED"
    assert "paper.stress_missing" in payload["blockers"]
    assert "paper.evidence_missing" in payload["blockers"]
    assert payload["testnet_authorized"] is False


def test_paper_robustness_review_missing_file_exits_2(tmp_path: Path) -> None:
    missing = tmp_path / "nope.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--json",
            "--paper-robustness-evidence-review",
            str(missing),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert proc.stdout.strip() == ""


def test_paper_robustness_review_invalid_content_exits_2(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("VERDICT=7200S_SCHEDULER_PAPER_RUNTIME_EVIDENCE_PASS\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--paper-robustness-evidence-review", str(bad)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_runtime_json_not_accepted_as_robustness_evidence(tmp_path: Path) -> None:
    review = tmp_path / "runtime_style.json"
    review.write_text(
        '{"issues": [], "metrics": {"fills_count": 1}, "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--paper-robustness-evidence-review", str(review)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_human_summary_includes_robustness_evidence_line(tmp_path: Path) -> None:
    closeout = tmp_path / "c.md"
    closeout.write_text("VERDICT=ROBUSTNESS_EVIDENCE_PASS\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--paper-robustness-evidence-review", str(closeout)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "paper_robustness_evidence_accepted=true" in proc.stdout
    assert "testnet_authorized=false" in proc.stdout
    assert "live_authorized=false" in proc.stdout


def test_combined_runtime_and_robustness_accepted_still_blocked_without_stress(
    tmp_path: Path,
) -> None:
    rt = tmp_path / "rt.md"
    rt.write_text("VERDICT=7200S_SCHEDULER_PAPER_RUNTIME_EVIDENCE_PASS\n", encoding="utf-8")
    rb = tmp_path / "rb.md"
    rb.write_text("VERDICT=PAPER_ROBUSTNESS_EVIDENCE_PASS\n", encoding="utf-8")
    proc = run_report(
        "--paper-runtime-evidence-review",
        str(rt),
        "--paper-robustness-evidence-review",
        str(rb),
    )
    assert proc.returncode == 0
    payload = parse_payload(proc)
    assert payload["status"] == "BLOCKED"
    assert payload["paper"]["evidence_present"] is True
    assert payload["paper"]["robustness_present"] is True
    assert payload["paper"]["stress_present"] is False
    assert "paper.stress_missing" in payload["blockers"]
    assert payload["paper_runtime_evidence_v0"]["accepted"] is True
    assert payload["paper_robustness_evidence_v0"]["accepted"] is True
    assert payload["testnet_authorized"] is False
    assert payload["live_authorized"] is False
