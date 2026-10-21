"""Bounded execution boundary inspector. Fixtures do not edit productive files."""

from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.ops.execution_parent_instruments_v1.boundary_inspector_v1 import (
    run_execution_boundary_inspector_v1,
)
from scripts.ops.execution_parent_instruments_v1.run_v1 import run_execution_parent_toolchain_v1

_REPO = Path(__file__).resolve().parents[2]
_DECISION = "execution.decision.runtime_cycle"
_SEND = "execution.submission.send_seam"
_REPLAY = "execution.boundary.trading_replay"
_DK = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_runtime_cycle_to_exact_envelope_bound_single_use_"
    "post_boundary_v1.py"
)
_CALLERS = {
    "execution.caller.persisted_cursor",
    "execution.caller.envelope_post_boundary",
    "execution.caller.non_executable_v1",
    "execution.caller.non_executable_v2",
    "execution.caller.non_executable_v3",
    "execution.caller.flatten_occupancy",
    "execution.caller.layered_long",
    "execution.caller.n5_invoke",
    "execution.caller.n5_carry",
    "execution.caller.n5_restore",
}


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(_REPO), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _pin() -> tuple[str, str]:
    commit = _git("rev-parse", "HEAD")
    return commit, _git("rev-parse", f"{commit}^{{tree}}")


def _run(**overrides: object) -> dict[str, object]:
    commit, tree = _pin()
    payload: dict[str, object] = {
        "current_commit_sha": commit,
        "current_tree_sha": tree,
        "repo_root": _REPO,
    }
    payload.update(overrides)
    return run_execution_boundary_inspector_v1(**payload)  # type: ignore[arg-type]


def test_additional_callers_are_visible_and_do_not_reach_submission() -> None:
    result = _run()
    ids = {subject["subject_id"] for subject in result["subjects"]}

    assert result["status"] == "ACCEPTED"
    assert _CALLERS <= ids
    assert set(result["reverse_from_decision_cycle"]) >= _CALLERS
    assert result["forward_from_envelope_post_boundary"] == [_DECISION]
    assert _SEND not in result["forward_from_envelope_post_boundary"]
    assert _REPLAY in result["transitive_from_envelope_post_boundary"]
    assert result["decision_to_submission"] == "UNKNOWN"


def test_permit_durable_submission_and_ack_stay_separate() -> None:
    result = _run()
    roles = {subject["role"]: subject["subject_id"] for subject in result["subjects"]}

    assert roles["PERMIT"] == "execution.permit.issue"
    assert roles["DURABLE_CONSUME"] == "execution.persistence.durable_consume"
    assert roles["SUBMISSION_SEAM"] == _SEND
    assert roles["ACK"] == "execution.ack.lifecycle_join"
    assert (
        len({roles["PERMIT"], roles["DURABLE_CONSUME"], roles["SUBMISSION_SEAM"], roles["ACK"]})
        == 4
    )


def test_must_not_post_probes_are_not_submission_edges() -> None:
    result = _run()

    assert result["probes"]
    assert all(probe["role"] == "MUST_NOT_POST_PROBE" for probe in result["probes"])
    assert all(probe["submission_edge"] is False for probe in result["probes"])
    assert all(probe["target_subject_id"] != _SEND for probe in result["probes"])
    assert all(probe["runtime_status"] == "UNKNOWN" for probe in result["probes"])
    submission = [edge for edge in result["edges"] if edge["submission_edge"] is True]
    assert submission
    assert all(edge["role"] != "MUST_NOT_POST_PROBE" for edge in submission)


def test_declared_change_is_detected_and_handed_to_impact() -> None:
    result = _run(changed_paths=[_DK])

    assert result["status"] == "ACCEPTED"
    assert result["changed_subject_ids"] == ["execution.caller.envelope_post_boundary"]
    impact = result["impact"]
    assert impact["binding"] == "propagate_change_impact_v1"
    assert _DECISION in impact["impacted_native_ids"]
    assert impact["propagation_status"] == "UNKNOWN"
    assert impact["safety_classification"] == "UNKNOWN"
    assert impact["runtime_proven"] is False
    assert result["safety_classification"] == "UNKNOWN"
    assert "SAFE" not in {impact["propagation_status"], result["safety_classification"]}
    assert "PASS" not in {impact["propagation_status"], result["status"]}


def test_unbound_change_stays_unknown() -> None:
    result = _run(changed_paths=["src/trading/unbound_fixture.py"])

    assert result["unbound_changed_paths"] == ["src/trading/unbound_fixture.py"]
    assert result["changed_subject_ids"] == []
    assert result["impact"]["propagation_status"] == "NOT_RUN"
    assert result["safety_classification"] == "UNKNOWN"


def test_hash_mismatch_fails_closed_and_still_reports_impact() -> None:
    lines = (_REPO / _DK).read_text(encoding="utf-8").splitlines()
    lines[203] = lines[203] + "  # fixture-change"
    result = _run(fixture_blobs={_DK: "\n".join(lines)})

    assert result["status"] == "FAIL_CLOSED"
    assert "subject_hash_mismatch:execution.caller.envelope_post_boundary" in result["reasons"]
    assert "execution.caller.envelope_post_boundary" in result["changed_subject_ids"]
    assert result["impact"]["propagation_status"] == "UNKNOWN"
    assert result["safety_classification"] == "UNKNOWN"
    assert result["current_runtime_proven"] is False


def test_static_edges_do_not_become_runtime_proof() -> None:
    result = _run()

    assert result["edges"]
    assert all(edge["proof_status"] == "STATIC_SOURCE_PROVEN" for edge in result["edges"])
    assert all(edge["runtime_status"] == "UNKNOWN" for edge in result["edges"])
    assert result["current_runtime_proven"] is False
    assert result["productive_runtime_reachability"] == "UNKNOWN"
    assert all(edge["proof_status"] == "UNKNOWN" for edge in result["unknown_edges"])


def test_stale_commit_tree_fails_closed() -> None:
    commit, _tree = _pin()
    result = _run(current_commit_sha=commit, current_tree_sha="f" * 40)

    assert result["status"] == "FAIL_CLOSED"
    assert result["reasons"] == ["stale_commit_tree"]
    assert result["safety_classification"] == "UNKNOWN"


def test_missing_evidence_fails_closed() -> None:
    result = _run(fixture_blobs={_DK: None})

    assert result["status"] == "FAIL_CLOSED"
    assert result["reasons"] == [f"missing_evidence:{_DK}"]
    assert result["post_allowed"] is False
    assert result["external_effect_authorized"] is False
    assert result["files_written"] is False


def test_inspector_does_not_change_trading_decisions_or_the_worktree() -> None:
    before = _git("status", "--porcelain")
    result = _run()
    after = _git("status", "--porcelain")
    source = (
        _REPO / "scripts/ops/execution_parent_instruments_v1/boundary_inspector_v1.py"
    ).read_text(encoding="utf-8")

    assert result["trading_decision_semantics_delta"] == "ZERO"
    assert "src.trading" not in source
    assert "src.risk" not in source
    assert result["guardian_ratified"] is False
    assert before == after


def test_runner_keeps_existing_instruments_and_adds_inspector() -> None:
    commit, tree = _pin()
    result = run_execution_parent_toolchain_v1(
        current_commit_sha=commit,
        current_tree_sha=tree,
        baseline_currency="CURRENT",
        repo_root=_REPO,
    )

    assert result["status"] == "ACCEPTED"
    assert result["ghv"]["mission"]["decision_to_submission"] == "UNKNOWN"
    assert result["graph"]["current_verified"] is False
    assert result["ghosv"]["counts_as_proof"] is False
    assert result["readiness"]["MISSION_SCOPE_COVERED"] is False
    inspector = result["boundary_inspector"]
    assert inspector["status"] == "ACCEPTED"
    assert inspector["files_written"] is False
    assert "execution.caller.n5_invoke" in {
        subject["subject_id"] for subject in inspector["subjects"]
    }
