"""Tests for PR head SHA required checks liveness guard semantics."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts" / "ci"))
import pr_head_sha_required_checks_liveness_guard as guard


def test_ignored_context_on_head_gap_is_non_blocking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "required_status_checks.json"
    config_path.write_text(
        json.dumps(
            {
                "required_contexts": ["tests (3.11)", "strategy-smoke"],
                "ignored_contexts": ["strategy-smoke"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "report.json"

    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr(
        guard,
        "_parse_args",
        lambda: Namespace(
            subject_kind="pull_request",
            repo="acme/repo",
            pr_number=2701,
            head_sha="deadbeef",
            required_config=str(config_path),
            max_prior_commits=5,
            report_json=str(report_path),
            liveness_wait_seconds=0,
            poll_interval_seconds=1,
        ),
    )
    monkeypatch.setattr(
        guard,
        "_fetch_head_check_runs",
        lambda repo, sha, token: [{"name": "tests (3.11)"}],
    )
    monkeypatch.setattr(guard, "_fetch_head_status_contexts", lambda repo, sha, token: [])
    monkeypatch.setattr(guard, "_fetch_pr_checks_states", lambda repo, pr_number, token: {})
    monkeypatch.setattr(guard, "_fetch_pr_commits", lambda repo, pr_number, token: ["deadbeef"])
    monkeypatch.setattr(guard, "_prior_sha_presence", lambda repo, prior_shas, contexts, token: {})

    assert guard.main() == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    rows = {row["context"]: row for row in report["rows"]}
    assert rows["strategy-smoke"]["classification"] == "IGNORED_BY_CONFIG_NON_BLOCKING"
    assert rows["tests (3.11)"]["classification"] == "REPORTED_ON_HEAD_SHA"


def test_head_sha_coupling_suspect_stays_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "required_status_checks.json"
    config_path.write_text(
        json.dumps(
            {
                "required_contexts": ["tests (3.11)"],
                "ignored_contexts": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "report.json"

    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr(
        guard,
        "_parse_args",
        lambda: Namespace(
            subject_kind="pull_request",
            repo="acme/repo",
            pr_number=2701,
            head_sha="deadbeef",
            required_config=str(config_path),
            max_prior_commits=5,
            report_json=str(report_path),
            liveness_wait_seconds=0,
            poll_interval_seconds=1,
        ),
    )
    monkeypatch.setattr(guard, "_fetch_head_check_runs", lambda repo, sha, token: [])
    monkeypatch.setattr(guard, "_fetch_head_status_contexts", lambda repo, sha, token: [])
    monkeypatch.setattr(guard, "_fetch_pr_checks_states", lambda repo, pr_number, token: {})
    monkeypatch.setattr(
        guard, "_fetch_pr_commits", lambda repo, pr_number, token: ["deadbeef", "cafebabe"]
    )
    monkeypatch.setattr(
        guard,
        "_prior_sha_presence",
        lambda repo, prior_shas, contexts, token: {"tests (3.11)": "cafebabe"},
    )

    assert guard.main() == 2
    report = json.loads(report_path.read_text(encoding="utf-8"))
    rows = {row["context"]: row for row in report["rows"]}
    assert rows["tests (3.11)"]["classification"] == "HEAD_SHA_COUPLING_SUSPECT"


def test_wait_window_allows_late_required_context_on_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "required_status_checks.json"
    config_path.write_text(
        json.dumps(
            {
                "required_contexts": ["tests (3.11)"],
                "ignored_contexts": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "report.json"

    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr(
        guard,
        "_parse_args",
        lambda: Namespace(
            subject_kind="pull_request",
            repo="acme/repo",
            pr_number=2701,
            head_sha="deadbeef",
            required_config=str(config_path),
            max_prior_commits=5,
            report_json=str(report_path),
            liveness_wait_seconds=10,
            poll_interval_seconds=2,
        ),
    )
    snapshots = iter(
        [
            (set(), {}),
            ({"tests (3.11)"}, {}),
        ]
    )
    monkeypatch.setattr(
        guard, "_collect_head_snapshot", lambda repo, head_sha, pr_number, token: next(snapshots)
    )
    monkeypatch.setattr(guard, "_fetch_pr_commits", lambda repo, pr_number, token: ["deadbeef"])
    monkeypatch.setattr(guard, "_prior_sha_presence", lambda repo, prior_shas, contexts, token: {})
    monkeypatch.setattr(guard.time, "sleep", lambda _: None)
    monotonic_values = iter([0.0, 0.5, 0.6])
    monkeypatch.setattr(guard.time, "monotonic", lambda: next(monotonic_values))

    assert guard.main() == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    rows = {row["context"]: row for row in report["rows"]}
    assert rows["tests (3.11)"]["classification"] == "REPORTED_ON_HEAD_SHA"
    assert report["waited_for_liveness_window"] is True


def test_merge_group_missing_context_is_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "required_status_checks.json"
    config_path.write_text(
        json.dumps(
            {
                "required_contexts": ["tests (3.11)"],
                "ignored_contexts": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "report.json"

    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr(
        guard,
        "_parse_args",
        lambda: Namespace(
            subject_kind="merge_group",
            repo="acme/repo",
            pr_number=None,
            head_sha="deadbeef",
            required_config=str(config_path),
            max_prior_commits=5,
            report_json=str(report_path),
            liveness_wait_seconds=0,
            poll_interval_seconds=1,
        ),
    )
    monkeypatch.setattr(guard, "_fetch_head_check_runs", lambda repo, sha, token: [])
    monkeypatch.setattr(guard, "_fetch_head_status_contexts", lambda repo, sha, token: [])

    def _no_pr_rollup(*args, **kwargs):
        raise AssertionError("merge_group must not call PR rollup fetch")

    def _no_pr_commits(*args, **kwargs):
        raise AssertionError("merge_group must not call PR commits fetch")

    monkeypatch.setattr(guard, "_fetch_pr_checks_states", _no_pr_rollup)
    monkeypatch.setattr(guard, "_fetch_pr_commits", _no_pr_commits)

    assert guard.main() == 2
    report = json.loads(report_path.read_text(encoding="utf-8"))
    rows = {row["context"]: row for row in report["rows"]}
    assert report["subject_kind"] == "merge_group"
    assert rows["tests (3.11)"]["classification"] == "MISSING_ON_HEAD_SHA"


def test_merge_group_wait_window_allows_late_required_context_on_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "required_status_checks.json"
    config_path.write_text(
        json.dumps(
            {
                "required_contexts": ["tests (3.11)"],
                "ignored_contexts": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "report.json"

    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr(
        guard,
        "_parse_args",
        lambda: Namespace(
            subject_kind="merge_group",
            repo="acme/repo",
            pr_number=None,
            head_sha="deadbeef",
            required_config=str(config_path),
            max_prior_commits=5,
            report_json=str(report_path),
            liveness_wait_seconds=10,
            poll_interval_seconds=2,
        ),
    )
    snapshots = iter(
        [
            (set(), {}),
            ({"tests (3.11)"}, {}),
        ]
    )
    monkeypatch.setattr(
        guard, "_collect_head_snapshot", lambda repo, head_sha, pr_number, token: next(snapshots)
    )
    monkeypatch.setattr(guard.time, "sleep", lambda _: None)
    monotonic_values = iter([0.0, 0.5, 0.6])
    monkeypatch.setattr(guard.time, "monotonic", lambda: next(monotonic_values))

    assert guard.main() == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    rows = {row["context"]: row for row in report["rows"]}
    assert report["subject_kind"] == "merge_group"
    assert rows["tests (3.11)"]["classification"] == "REPORTED_ON_HEAD_SHA"
    assert report["waited_for_liveness_window"] is True


def test_liveness_workflow_includes_merge_group_path() -> None:
    workflow = Path(".github/workflows/pr-head-sha-required-checks-liveness-guard.yml").read_text(
        encoding="utf-8"
    )
    assert "merge_group:" in workflow
    assert "--subject-kind \"merge_group\"" in workflow
    assert "--head-sha \"${{ github.sha }}\"" in workflow
