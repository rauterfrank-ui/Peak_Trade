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

EVIDENCE_INPUTS_DO_NOT_AUTHORIZE = [
    "testnet",
    "live",
    "broker",
    "exchange",
    "order_submission",
]


def run_report(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--json", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def parse_payload(proc: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return json.loads(proc.stdout)


def assert_authorization_boundary_v0(payload: dict[str, object]) -> None:
    b = payload["authorization_boundary_v0"]
    assert isinstance(b, dict)
    assert b["schema_version"] == "peak_trade.authorization_boundary.v0"
    assert b["non_authorizing_evidence_inputs"] is True
    assert b["evidence_inputs_do_not_authorize"] == EVIDENCE_INPUTS_DO_NOT_AUTHORIZE
    assert b["testnet_authorized"] is False
    assert b["live_authorized"] is False
    assert b["broker_exchange_order_paths_authorized"] is False
    assert b["order_submission_authorized"] is False
    assert b["authorization_requires_external_operator_gate"] is True
    assert b["readiness_status_is_not_execution_authority"] is True


def assert_non_authorizing(payload: dict[str, object]) -> None:
    assert payload["non_authorizing"] is True
    assert payload["authority_boundary"] == AUTHORITY_FLAGS
    assert_authorization_boundary_v0(payload)


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
    ps = payload["paper_stress_evidence_v0"]
    assert isinstance(ps, dict)
    assert ps["accepted"] is False
    assert ps["non_authorizing"] is True
    assert ps["contributes_to"] == "paper_stress_only"
    tp = payload["testnet_prerequisites_evidence_v0"]
    assert isinstance(tp, dict)
    assert tp["accepted"] is False
    assert tp["non_authorizing"] is True
    assert tp["contributes_to"] == "testnet_prerequisites_only"
    cr = payload["testnet_prerequisite_checker_report_v0"]
    assert isinstance(cr, dict)
    assert cr["schema_version"] == "peak_trade.testnet_prerequisite_checker_report.v0"
    assert cr["record_present"] is False
    assert cr["accepted"] is False
    assert cr["non_authorizing"] is True
    assert cr["contributes_to"] == "testnet_prerequisite_checker_context_only"
    assert cr["does_not_authorize"] == EVIDENCE_INPUTS_DO_NOT_AUTHORIZE
    te = payload["testnet_evidence_v0"]
    assert isinstance(te, dict)
    assert te["accepted"] is False
    assert te["contributes_to"] == "testnet_evidence_only"
    assert te["schema_version"] == "peak_trade.testnet_evidence_input.v0"
    trb = payload["testnet_robustness_evidence_v0"]
    assert isinstance(trb, dict)
    assert trb["accepted"] is False
    assert trb["contributes_to"] == "testnet_robustness_only"
    assert trb["schema_version"] == "peak_trade.testnet_robustness_evidence_input.v0"
    tst = payload["testnet_stress_evidence_v0"]
    assert isinstance(tst, dict)
    assert tst["accepted"] is False
    assert tst["contributes_to"] == "testnet_stress_only"
    assert tst["schema_version"] == "peak_trade.testnet_stress_evidence_input.v0"


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
    assert "paper_stress_evidence_accepted=false" in proc.stdout
    assert "testnet_evidence_accepted=false" in proc.stdout
    assert "testnet_robustness_evidence_accepted=false" in proc.stdout
    assert "testnet_stress_evidence_accepted=false" in proc.stdout
    assert "testnet_prerequisites_evidence_accepted=false" in proc.stdout
    assert "testnet_prerequisite_checker_report_accepted=false" in proc.stdout
    assert "testnet_authorized=false" in proc.stdout
    assert "live_authorized=false" in proc.stdout
    assert "authorization_boundary_non_authorizing_evidence_inputs=true" in proc.stdout
    assert "authorization_boundary_testnet_authorized=false" in proc.stdout
    assert "authorization_boundary_order_submission_authorized=false" in proc.stdout
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
    assert "paper_stress_evidence_accepted=false" in proc.stdout
    assert "testnet_evidence_accepted=false" in proc.stdout
    assert "testnet_robustness_evidence_accepted=false" in proc.stdout
    assert "testnet_stress_evidence_accepted=false" in proc.stdout
    assert "testnet_prerequisites_evidence_accepted=false" in proc.stdout
    assert "testnet_prerequisite_checker_report_accepted=false" in proc.stdout
    assert "testnet_authorized=false" in proc.stdout
    assert "live_authorized=false" in proc.stdout
    assert "authorization_boundary_non_authorizing_evidence_inputs=true" in proc.stdout
    assert "authorization_boundary_testnet_authorized=false" in proc.stdout
    assert "authorization_boundary_order_submission_authorized=false" in proc.stdout


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


def test_paper_stress_closeout_review_surfaces_in_json_and_stays_blocked(tmp_path: Path) -> None:
    closeout = tmp_path / "stress.md"
    closeout.write_text(
        "\n".join(
            [
                "# x",
                "VERDICT=PAPER_STRESS_EVIDENCE_PASS",
                "",
            ]
        ),
        encoding="utf-8",
    )
    proc = run_report("--paper-stress-evidence-review", str(closeout))
    assert proc.returncode == 0
    payload = parse_payload(proc)

    assert payload["status"] == "BLOCKED"
    assert payload["testnet_authorized"] is False
    assert payload["live_authorized"] is False
    assert payload["paper"]["stress_present"] is True
    assert payload["paper"]["evidence_present"] is False
    ps = payload["paper_stress_evidence_v0"]
    assert isinstance(ps, dict)
    assert ps["accepted"] is True
    assert ps["non_authorizing"] is True
    assert ps["verdict"] == "PAPER_STRESS_EVIDENCE_PASS"
    assert ps["contributes_to"] == "paper_stress_only"
    assert ps["does_not_authorize"] == [
        "testnet",
        "live",
        "broker",
        "exchange",
        "order_submission",
    ]
    assert_non_authorizing(payload)


def test_paper_stress_review_json_pass_surfaces_accepted(tmp_path: Path) -> None:
    review = tmp_path / "review.json"
    review.write_text(
        '{"issues": [], "evidence_kind": "paper_stress", "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = run_report("--paper-stress-evidence-review", str(review))
    assert proc.returncode == 0
    payload = parse_payload(proc)
    ps = payload["paper_stress_evidence_v0"]
    assert ps["accepted"] is True
    assert ps["verdict"] == "PASS"
    assert payload["status"] == "BLOCKED"
    assert payload["testnet_authorized"] is False


def test_paper_stress_review_missing_file_exits_2(tmp_path: Path) -> None:
    missing = tmp_path / "nope.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--json",
            "--paper-stress-evidence-review",
            str(missing),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert proc.stdout.strip() == ""


def test_paper_stress_review_invalid_content_exits_2(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("VERDICT=PAPER_ROBUSTNESS_EVIDENCE_PASS\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--paper-stress-evidence-review", str(bad)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_runtime_json_not_accepted_as_stress_evidence(tmp_path: Path) -> None:
    review = tmp_path / "runtime_style.json"
    review.write_text(
        '{"issues": [], "metrics": {"fills_count": 1}, "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--paper-stress-evidence-review", str(review)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_robustness_json_not_accepted_as_stress_evidence(tmp_path: Path) -> None:
    review = tmp_path / "robustness_style.json"
    review.write_text(
        '{"issues": [], "evidence_kind": "paper_robustness", "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--paper-stress-evidence-review", str(review)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_human_summary_includes_stress_evidence_line(tmp_path: Path) -> None:
    closeout = tmp_path / "c.md"
    closeout.write_text("VERDICT=STRESS_EVIDENCE_PASS\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--paper-stress-evidence-review", str(closeout)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "paper_stress_evidence_accepted=true" in proc.stdout
    assert "paper_stress_evidence_verdict=STRESS_EVIDENCE_PASS" in proc.stdout
    assert "testnet_evidence_accepted=false" in proc.stdout
    assert "testnet_robustness_evidence_accepted=false" in proc.stdout
    assert "testnet_stress_evidence_accepted=false" in proc.stdout
    assert "testnet_prerequisites_evidence_accepted=false" in proc.stdout
    assert "testnet_prerequisite_checker_report_accepted=false" in proc.stdout
    assert "testnet_authorized=false" in proc.stdout
    assert "live_authorized=false" in proc.stdout
    assert "authorization_boundary_non_authorizing_evidence_inputs=true" in proc.stdout
    assert "authorization_boundary_testnet_authorized=false" in proc.stdout
    assert "authorization_boundary_order_submission_authorized=false" in proc.stdout


def test_combined_runtime_robustness_and_stress_accepted_still_blocked_on_testnet(
    tmp_path: Path,
) -> None:
    rt = tmp_path / "rt.md"
    rt.write_text("VERDICT=7200S_SCHEDULER_PAPER_RUNTIME_EVIDENCE_PASS\n", encoding="utf-8")
    rb = tmp_path / "rb.md"
    rb.write_text("VERDICT=PAPER_ROBUSTNESS_EVIDENCE_PASS\n", encoding="utf-8")
    st = tmp_path / "st.md"
    st.write_text("VERDICT=PAPER_STRESS_EVIDENCE_PASS\n", encoding="utf-8")
    proc = run_report(
        "--paper-runtime-evidence-review",
        str(rt),
        "--paper-robustness-evidence-review",
        str(rb),
        "--paper-stress-evidence-review",
        str(st),
    )
    assert proc.returncode == 0
    payload = parse_payload(proc)
    assert payload["status"] == "BLOCKED"
    assert payload["paper"]["evidence_present"] is True
    assert payload["paper"]["robustness_present"] is True
    assert payload["paper"]["stress_present"] is True
    assert "testnet.evidence_missing" in payload["blockers"]
    assert payload["paper_runtime_evidence_v0"]["accepted"] is True
    assert payload["paper_robustness_evidence_v0"]["accepted"] is True
    assert payload["paper_stress_evidence_v0"]["accepted"] is True
    assert payload["testnet_authorized"] is False
    assert payload["live_authorized"] is False


def test_testnet_prerequisites_closeout_review_surfaces_in_json_and_stays_blocked(
    tmp_path: Path,
) -> None:
    closeout = tmp_path / "tp.md"
    closeout.write_text(
        "\n".join(
            [
                "# x",
                "VERDICT=TESTNET_PREREQUISITES_EVIDENCE_PASS",
                "",
            ]
        ),
        encoding="utf-8",
    )
    proc = run_report("--testnet-prerequisites-review", str(closeout))
    assert proc.returncode == 0
    payload = parse_payload(proc)

    assert payload["status"] == "BLOCKED"
    assert payload["testnet_authorized"] is False
    assert payload["live_authorized"] is False
    tp = payload["testnet_prerequisites_evidence_v0"]
    assert isinstance(tp, dict)
    assert tp["accepted"] is True
    assert tp["non_authorizing"] is True
    assert tp["verdict"] == "TESTNET_PREREQUISITES_EVIDENCE_PASS"
    assert tp["contributes_to"] == "testnet_prerequisites_only"
    assert tp["does_not_authorize"] == [
        "testnet",
        "live",
        "broker",
        "exchange",
        "order_submission",
    ]
    assert_non_authorizing(payload)


def test_testnet_prerequisites_review_json_pass_surfaces_accepted(tmp_path: Path) -> None:
    review = tmp_path / "tp.json"
    review.write_text(
        '{"issues": [], "evidence_kind": "testnet_prerequisites", "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = run_report("--testnet-prerequisites-review", str(review))
    assert proc.returncode == 0
    payload = parse_payload(proc)
    tp = payload["testnet_prerequisites_evidence_v0"]
    assert tp["accepted"] is True
    assert tp["verdict"] == "PASS"
    assert payload["status"] == "BLOCKED"
    assert payload["testnet_authorized"] is False


def test_testnet_prerequisites_review_missing_file_exits_2(tmp_path: Path) -> None:
    missing = tmp_path / "nope.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--json",
            "--testnet-prerequisites-review",
            str(missing),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert proc.stdout.strip() == ""


def test_testnet_prerequisites_review_invalid_content_exits_2(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("VERDICT=PAPER_STRESS_EVIDENCE_PASS\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--testnet-prerequisites-review", str(bad)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_runtime_json_not_accepted_as_testnet_prerequisites_evidence(tmp_path: Path) -> None:
    review = tmp_path / "runtime_style.json"
    review.write_text(
        '{"issues": [], "metrics": {"fills_count": 1}, "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--testnet-prerequisites-review", str(review)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_robustness_json_not_accepted_as_testnet_prerequisites_evidence(
    tmp_path: Path,
) -> None:
    review = tmp_path / "rb.json"
    review.write_text(
        '{"issues": [], "evidence_kind": "paper_robustness", "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--testnet-prerequisites-review", str(review)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_stress_json_not_accepted_as_testnet_prerequisites_evidence(tmp_path: Path) -> None:
    review = tmp_path / "st.json"
    review.write_text(
        '{"issues": [], "evidence_kind": "paper_stress", "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--testnet-prerequisites-review", str(review)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_human_summary_includes_testnet_prerequisites_evidence_line(tmp_path: Path) -> None:
    closeout = tmp_path / "c.md"
    closeout.write_text("VERDICT=TESTNET_PREREQUISITES_REVIEW_PASS\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--testnet-prerequisites-review", str(closeout)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "testnet_prerequisites_evidence_accepted=true" in proc.stdout
    assert "testnet_prerequisites_evidence_verdict=TESTNET_PREREQUISITES_REVIEW_PASS" in proc.stdout
    assert "testnet_evidence_accepted=false" in proc.stdout
    assert "testnet_robustness_evidence_accepted=false" in proc.stdout
    assert "testnet_stress_evidence_accepted=false" in proc.stdout
    assert "testnet_prerequisite_checker_report_accepted=false" in proc.stdout
    assert "testnet_authorized=false" in proc.stdout
    assert "live_authorized=false" in proc.stdout
    assert "authorization_boundary_non_authorizing_evidence_inputs=true" in proc.stdout
    assert "authorization_boundary_testnet_authorized=false" in proc.stdout
    assert "authorization_boundary_order_submission_authorized=false" in proc.stdout


def test_combined_all_paper_reviews_and_testnet_prerequisites_still_blocked_on_testnet(
    tmp_path: Path,
) -> None:
    rt = tmp_path / "rt.md"
    rt.write_text("VERDICT=7200S_SCHEDULER_PAPER_RUNTIME_EVIDENCE_PASS\n", encoding="utf-8")
    rb = tmp_path / "rb.md"
    rb.write_text("VERDICT=PAPER_ROBUSTNESS_EVIDENCE_PASS\n", encoding="utf-8")
    st = tmp_path / "st.md"
    st.write_text("VERDICT=PAPER_STRESS_EVIDENCE_PASS\n", encoding="utf-8")
    tp = tmp_path / "tp.md"
    tp.write_text("VERDICT=TESTNET_PREREQUISITES_REVIEW_PASS\n", encoding="utf-8")
    proc = run_report(
        "--paper-runtime-evidence-review",
        str(rt),
        "--paper-robustness-evidence-review",
        str(rb),
        "--paper-stress-evidence-review",
        str(st),
        "--testnet-prerequisites-review",
        str(tp),
    )
    assert proc.returncode == 0
    payload = parse_payload(proc)
    assert payload["status"] == "BLOCKED"
    assert payload["paper"]["evidence_present"] is True
    assert payload["paper"]["robustness_present"] is True
    assert payload["paper"]["stress_present"] is True
    assert "testnet.evidence_missing" in payload["blockers"]
    assert payload["paper_runtime_evidence_v0"]["accepted"] is True
    assert payload["paper_robustness_evidence_v0"]["accepted"] is True
    assert payload["paper_stress_evidence_v0"]["accepted"] is True
    assert payload["testnet_prerequisites_evidence_v0"]["accepted"] is True
    assert payload["testnet_authorized"] is False
    assert payload["live_authorized"] is False
    assert_non_authorizing(payload)


def test_human_summary_includes_authorization_boundary_when_all_evidence_inputs_accepted(
    tmp_path: Path,
) -> None:
    rt = tmp_path / "rt.md"
    rt.write_text("VERDICT=7200S_SCHEDULER_PAPER_RUNTIME_EVIDENCE_PASS\n", encoding="utf-8")
    rb = tmp_path / "rb.md"
    rb.write_text("VERDICT=PAPER_ROBUSTNESS_EVIDENCE_PASS\n", encoding="utf-8")
    st = tmp_path / "st.md"
    st.write_text("VERDICT=PAPER_STRESS_EVIDENCE_PASS\n", encoding="utf-8")
    tp = tmp_path / "tp.md"
    tp.write_text("VERDICT=TESTNET_PREREQUISITES_REVIEW_PASS\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--paper-runtime-evidence-review",
            str(rt),
            "--paper-robustness-evidence-review",
            str(rb),
            "--paper-stress-evidence-review",
            str(st),
            "--testnet-prerequisites-review",
            str(tp),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "testnet_prerequisite_checker_report_accepted=false" in proc.stdout
    assert "testnet_evidence_accepted=false" in proc.stdout
    assert "testnet_robustness_evidence_accepted=false" in proc.stdout
    assert "testnet_stress_evidence_accepted=false" in proc.stdout
    assert "authorization_boundary_non_authorizing_evidence_inputs=true" in proc.stdout
    assert "authorization_boundary_testnet_authorized=false" in proc.stdout
    assert "authorization_boundary_order_submission_authorized=false" in proc.stdout


CHECKER_READONLY_SCHEMA = "peak_trade.testnet_prerequisites_readonly.v0"

_CHECKER_BOUNDARY_OK: dict[str, bool] = {
    "non_authorizing": True,
    "testnet_authorized": False,
    "live_authorized": False,
    "broker_exchange_order_paths_authorized": False,
    "order_submission_authorized": False,
    "checker_does_not_connect_to_exchange": True,
    "checker_does_not_validate_credentials": True,
}


def _checker_payload_blocked_extra_note() -> dict[str, object]:
    return {
        "schema_version": CHECKER_READONLY_SCHEMA,
        "status": "BLOCKED",
        "required_key_count": 2,
        "required_present_count": 0,
        "missing_count": 2,
        "prerequisites": [],
        "missing": [
            "PEAK_TRADE_TESTNET_OPERATOR_GATE_ACK",
            "PEAK_TRADE_TESTNET_CONFIG_DECLARED",
        ],
        "checker_boundary_v0": dict(_CHECKER_BOUNDARY_OK),
        "_archive_note": "SHOULD_NOT_LEAK_IN_READINESS_OUTPUT_99zz",
    }


def _write_checker_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_valid_testnet_prerequisite_checker_report_surfaces_in_json(
    tmp_path: Path,
) -> None:
    rep = tmp_path / "checker.json"
    _write_checker_json(rep, _checker_payload_blocked_extra_note())
    proc = run_report("--testnet-prerequisites-checker-report", str(rep))
    assert proc.returncode == 0
    out = parse_payload(proc)
    cr = out["testnet_prerequisite_checker_report_v0"]
    assert isinstance(cr, dict)
    assert cr["accepted"] is True
    assert cr["schema_version"] == "peak_trade.testnet_prerequisite_checker_report.v0"
    assert cr["record_present"] is True
    assert cr["checker_status"] == "BLOCKED"
    assert cr["missing_count"] == 2
    assert cr["required_count"] == 2
    assert cr["non_authorizing"] is True
    assert cr["contributes_to"] == "testnet_prerequisite_checker_context_only"
    assert cr["does_not_authorize"] == EVIDENCE_INPUTS_DO_NOT_AUTHORIZE
    assert "SHOULD_NOT_LEAK" not in proc.stdout
    assert_non_authorizing(out)


def test_valid_checker_report_ready_for_operator_review_keeps_auth_false(
    tmp_path: Path,
) -> None:
    rep = tmp_path / "c.json"
    payload: dict[str, object] = {
        "schema_version": CHECKER_READONLY_SCHEMA,
        "status": "READY_FOR_OPERATOR_REVIEW",
        "required_key_count": 2,
        "required_present_count": 2,
        "missing_count": 0,
        "prerequisites": [],
        "missing": [],
        "checker_boundary_v0": dict(_CHECKER_BOUNDARY_OK),
    }
    _write_checker_json(rep, payload)
    proc = run_report("--testnet-prerequisites-checker-report", str(rep))
    out = parse_payload(proc)
    assert out["testnet_authorized"] is False
    assert out["live_authorized"] is False
    cr = out["testnet_prerequisite_checker_report_v0"]
    assert cr["accepted"] is True
    assert cr["checker_status"] == "READY_FOR_OPERATOR_REVIEW"
    assert cr["missing_count"] == 0
    assert_non_authorizing(out)


def test_checker_report_missing_file_exits_2(tmp_path: Path) -> None:
    missing = tmp_path / "no.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--json",
            "--testnet-prerequisites-checker-report",
            str(missing),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert proc.stdout.strip() == ""


def test_runtime_review_json_not_accepted_as_checker_report(
    tmp_path: Path,
) -> None:
    rep = tmp_path / "runtime.json"
    rep.write_text(
        '{"issues": [], "metrics": {"fills_count": 1}, "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--json",
            "--testnet-prerequisites-checker-report",
            str(rep),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert proc.stdout.strip() == ""


def test_checker_report_invalid_boundary_exits_2(tmp_path: Path) -> None:
    rep = tmp_path / "bad.json"
    p = dict(_checker_payload_blocked_extra_note())
    b = dict(_CHECKER_BOUNDARY_OK)
    b["testnet_authorized"] = True
    p["checker_boundary_v0"] = b
    del p["_archive_note"]
    _write_checker_json(rep, p)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--json",
            "--testnet-prerequisites-checker-report",
            str(rep),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert proc.stdout.strip() == ""


def test_wrong_checker_schema_version_exits_2(tmp_path: Path) -> None:
    rep = tmp_path / "wrong.json"
    p = dict(_checker_payload_blocked_extra_note())
    p["schema_version"] = "peak_trade.other.v0"
    del p["_archive_note"]
    _write_checker_json(rep, p)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--json",
            "--testnet-prerequisites-checker-report",
            str(rep),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert proc.stdout.strip() == ""


def test_human_summary_includes_checker_report_lines(
    tmp_path: Path,
) -> None:
    rep = tmp_path / "c.json"
    p = dict(_checker_payload_blocked_extra_note())
    del p["_archive_note"]
    _write_checker_json(rep, p)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--testnet-prerequisites-checker-report", str(rep)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "testnet_prerequisite_checker_report_accepted=true" in proc.stdout
    assert "testnet_prerequisite_checker_status=BLOCKED" in proc.stdout
    assert "testnet_prerequisite_checker_missing_count=2" in proc.stdout
    assert "testnet_evidence_accepted=false" in proc.stdout
    assert "testnet_robustness_evidence_accepted=false" in proc.stdout
    assert "testnet_stress_evidence_accepted=false" in proc.stdout
    assert "testnet_authorized=false" in proc.stdout
    assert "live_authorized=false" in proc.stdout


def test_combined_all_evidence_reviews_and_checker_report_still_blocked_non_authorizing(
    tmp_path: Path,
) -> None:
    rt = tmp_path / "rt.md"
    rt.write_text("VERDICT=7200S_SCHEDULER_PAPER_RUNTIME_EVIDENCE_PASS\n", encoding="utf-8")
    rb = tmp_path / "rb.md"
    rb.write_text("VERDICT=PAPER_ROBUSTNESS_EVIDENCE_PASS\n", encoding="utf-8")
    st = tmp_path / "st.md"
    st.write_text("VERDICT=PAPER_STRESS_EVIDENCE_PASS\n", encoding="utf-8")
    tp = tmp_path / "tp.md"
    tp.write_text("VERDICT=TESTNET_PREREQUISITES_REVIEW_PASS\n", encoding="utf-8")
    chk = tmp_path / "chk.json"
    p = dict(_checker_payload_blocked_extra_note())
    del p["_archive_note"]
    _write_checker_json(chk, p)
    proc = run_report(
        "--paper-runtime-evidence-review",
        str(rt),
        "--paper-robustness-evidence-review",
        str(rb),
        "--paper-stress-evidence-review",
        str(st),
        "--testnet-prerequisites-review",
        str(tp),
        "--testnet-prerequisites-checker-report",
        str(chk),
    )
    assert proc.returncode == 0
    out = parse_payload(proc)
    assert out["status"] == "BLOCKED"
    assert out["testnet_prerequisite_checker_report_v0"]["accepted"] is True
    assert out["testnet_authorized"] is False
    assert out["live_authorized"] is False
    assert_non_authorizing(out)


def test_combined_all_evidence_including_testnet_layer_ready_for_review_non_authorizing(
    tmp_path: Path,
) -> None:
    rt = tmp_path / "rt.md"
    rt.write_text("VERDICT=7200S_SCHEDULER_PAPER_RUNTIME_EVIDENCE_PASS\n", encoding="utf-8")
    rb = tmp_path / "rb.md"
    rb.write_text("VERDICT=PAPER_ROBUSTNESS_EVIDENCE_PASS\n", encoding="utf-8")
    st = tmp_path / "st.md"
    st.write_text("VERDICT=PAPER_STRESS_EVIDENCE_PASS\n", encoding="utf-8")
    tp = tmp_path / "tp.md"
    tp.write_text("VERDICT=TESTNET_PREREQUISITES_REVIEW_PASS\n", encoding="utf-8")
    chk = tmp_path / "chk.json"
    p = dict(_checker_payload_blocked_extra_note())
    del p["_archive_note"]
    _write_checker_json(chk, p)
    tne = tmp_path / "tne.md"
    tne.write_text("VERDICT=TESTNET_EVIDENCE_PASS\n", encoding="utf-8")
    tnr = tmp_path / "tnr.md"
    tnr.write_text("VERDICT=TESTNET_ROBUSTNESS_EVIDENCE_PASS\n", encoding="utf-8")
    tns = tmp_path / "tns.md"
    tns.write_text("VERDICT=TESTNET_STRESS_EVIDENCE_PASS\n", encoding="utf-8")
    proc = run_report(
        "--paper-runtime-evidence-review",
        str(rt),
        "--paper-robustness-evidence-review",
        str(rb),
        "--paper-stress-evidence-review",
        str(st),
        "--testnet-prerequisites-review",
        str(tp),
        "--testnet-prerequisites-checker-report",
        str(chk),
        "--testnet-evidence-review",
        str(tne),
        "--testnet-robustness-evidence-review",
        str(tnr),
        "--testnet-stress-evidence-review",
        str(tns),
    )
    assert proc.returncode == 0
    out = parse_payload(proc)
    assert out["status"] == "READY_FOR_REVIEW"
    assert out["blockers"] == []
    assert out["testnet_prerequisite_checker_report_v0"]["accepted"] is True
    assert out["testnet_evidence_v0"]["accepted"] is True
    assert out["testnet_robustness_evidence_v0"]["accepted"] is True
    assert out["testnet_stress_evidence_v0"]["accepted"] is True
    assert out["testnet_authorized"] is False
    assert out["live_authorized"] is False
    assert_non_authorizing(out)


def test_testnet_evidence_closeout_surfaces_in_json_and_completes_modeled_flag(
    tmp_path: Path,
) -> None:
    md = tmp_path / "te.md"
    md.write_text("VERDICT=TESTNET_EVIDENCE_PASS\n", encoding="utf-8")
    proc = run_report(
        "--paper-evidence-present",
        "--paper-robustness-present",
        "--paper-stress-present",
        "--testnet-robustness-present",
        "--testnet-stress-present",
        "--testnet-evidence-review",
        str(md),
    )
    assert proc.returncode == 0
    out = parse_payload(proc)
    assert out["testnet"]["evidence_present"] is True
    te = out["testnet_evidence_v0"]
    assert te["accepted"] is True
    assert te["verdict"] == "TESTNET_EVIDENCE_PASS"
    assert te["contributes_to"] == "testnet_evidence_only"
    assert out["testnet_authorized"] is False
    assert_non_authorizing(out)


def test_testnet_evidence_json_pass_surfaces_accepted(tmp_path: Path) -> None:
    js = tmp_path / "te.json"
    js.write_text(
        '{"evidence_kind": "testnet_evidence", "issues": [], "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = run_report("--testnet-evidence-review", str(js))
    out = parse_payload(proc)
    assert out["testnet_evidence_v0"]["accepted"] is True
    assert out["testnet_evidence_v0"]["verdict"] == "PASS"
    assert out["testnet_authorized"] is False


def test_testnet_robustness_closeout_surfaces_accepted(tmp_path: Path) -> None:
    md = tmp_path / "tr.md"
    md.write_text("VERDICT=TESTNET_ROBUSTNESS_EVIDENCE_PASS\n", encoding="utf-8")
    proc = run_report("--testnet-robustness-evidence-review", str(md))
    out = parse_payload(proc)
    trb = out["testnet_robustness_evidence_v0"]
    assert trb["accepted"] is True
    assert trb["verdict"] == "TESTNET_ROBUSTNESS_EVIDENCE_PASS"
    assert out["testnet"]["robustness_present"] is True


def test_testnet_robustness_json_pass_surfaces_accepted(tmp_path: Path) -> None:
    js = tmp_path / "tr.json"
    js.write_text(
        '{"issues": [], "kind": "testnet_robustness", "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = run_report("--testnet-robustness-evidence-review", str(js))
    out = parse_payload(proc)
    assert out["testnet_robustness_evidence_v0"]["accepted"] is True


def test_testnet_stress_closeout_surfaces_accepted(tmp_path: Path) -> None:
    md = tmp_path / "ts.md"
    md.write_text("VERDICT=TESTNET_STRESS_EVIDENCE_PASS\n", encoding="utf-8")
    proc = run_report("--testnet-stress-evidence-review", str(md))
    out = parse_payload(proc)
    ts = out["testnet_stress_evidence_v0"]
    assert ts["accepted"] is True
    assert ts["verdict"] == "TESTNET_STRESS_EVIDENCE_PASS"
    assert out["testnet"]["stress_present"] is True


def test_testnet_stress_json_pass_surfaces_accepted(tmp_path: Path) -> None:
    js = tmp_path / "ts.json"
    js.write_text(
        '{"issues": [], "testnet_stress_evidence": true, "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = run_report("--testnet-stress-evidence-review", str(js))
    out = parse_payload(proc)
    assert out["testnet_stress_evidence_v0"]["accepted"] is True


def test_testnet_evidence_review_missing_file_exits_2(tmp_path: Path) -> None:
    missing = tmp_path / "nope.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--json",
            "--testnet-evidence-review",
            str(missing),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert proc.stdout.strip() == ""


def test_testnet_evidence_review_invalid_markdown_exits_2(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("VERDICT=PAPER_STRESS_EVIDENCE_PASS\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--testnet-evidence-review", str(bad)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert proc.stdout.strip() == ""


def test_paper_runtime_json_not_accepted_as_testnet_evidence(tmp_path: Path) -> None:
    js = tmp_path / "x.json"
    js.write_text(
        '{"issues": [], "metrics": {}, "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", "--testnet-evidence-review", str(js)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_testnet_evidence_json_not_accepted_as_robustness_path(tmp_path: Path) -> None:
    js = tmp_path / "x.json"
    js.write_text(
        '{"evidence_kind": "testnet_evidence", "issues": [], "verdict": "PASS"}\n',
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--json",
            "--testnet-robustness-evidence-review",
            str(js),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_testnet_prerequisite_checker_json_not_accepted_as_testnet_stress_path(
    tmp_path: Path,
) -> None:
    rep = tmp_path / "chk.json"
    _write_checker_json(rep, dict(_checker_payload_blocked_extra_note()))
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--json",
            "--testnet-stress-evidence-review",
            str(rep),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_human_summary_includes_testnet_layer_evidence_verdict_lines(
    tmp_path: Path,
) -> None:
    te = tmp_path / "te.md"
    te.write_text("VERDICT=TESTNET_EVIDENCE_PASS\n", encoding="utf-8")
    tr = tmp_path / "tr.md"
    tr.write_text("VERDICT=TESTNET_ROBUSTNESS_EVIDENCE_PASS\n", encoding="utf-8")
    ts = tmp_path / "ts.md"
    ts.write_text("VERDICT=TESTNET_STRESS_EVIDENCE_PASS\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--testnet-evidence-review",
            str(te),
            "--testnet-robustness-evidence-review",
            str(tr),
            "--testnet-stress-evidence-review",
            str(ts),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "testnet_evidence_accepted=true" in proc.stdout
    assert "testnet_robustness_evidence_accepted=true" in proc.stdout
    assert "testnet_stress_evidence_accepted=true" in proc.stdout
    assert "testnet_evidence_verdict=TESTNET_EVIDENCE_PASS" in proc.stdout
    assert "testnet_robustness_evidence_verdict=TESTNET_ROBUSTNESS_EVIDENCE_PASS" in proc.stdout
    assert "testnet_stress_evidence_verdict=TESTNET_STRESS_EVIDENCE_PASS" in proc.stdout
    assert "testnet_authorized=false" in proc.stdout


def test_testnet_evidence_json_does_not_copy_extra_fields_to_readiness_output(
    tmp_path: Path,
) -> None:
    js = tmp_path / "te.json"
    js.write_text(
        "".join(
            [
                '{"evidence_kind": "testnet_evidence", "issues": [], ',
                '"verdict": "PASS", "operator_secret_note": "LEAK_MARKER_XYZZY99"}\n',
            ]
        ),
        encoding="utf-8",
    )
    proc = run_report("--testnet-evidence-review", str(js))
    assert "LEAK_MARKER_XYZZY99" not in proc.stdout
    out = parse_payload(proc)
    assert "operator_secret_note" not in json.dumps(out)
