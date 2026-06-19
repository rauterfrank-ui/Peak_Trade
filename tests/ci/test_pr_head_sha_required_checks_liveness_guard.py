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
            (set(), {}, []),
            ({"tests (3.11)"}, {}, []),
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
            (set(), {}, []),
            ({"tests (3.11)"}, {}, []),
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
    assert '--subject-kind "merge_group"' in workflow
    assert '--head-sha "${{ github.sha }}"' in workflow


def _write_config(tmp_path: Path) -> Path:
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
    return config_path


def _run_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    head_runs: list[dict[str, str]],
    on_head: set[str] | None = None,
    rollup_states: dict[str, str] | None = None,
    prior_seen: dict[str, str | None] | None = None,
    head_sha: str = "deadbeef",
) -> tuple[int, dict]:
    config_path = _write_config(tmp_path)
    report_path = tmp_path / "report.json"
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr(
        guard,
        "_parse_args",
        lambda: Namespace(
            subject_kind="pull_request",
            repo="acme/repo",
            pr_number=4455,
            head_sha=head_sha,
            required_config=str(config_path),
            max_prior_commits=5,
            report_json=str(report_path),
            liveness_wait_seconds=0,
            poll_interval_seconds=1,
        ),
    )
    monkeypatch.setattr(
        guard,
        "_collect_head_snapshot",
        lambda repo, head_sha, pr_number, token: (
            on_head if on_head is not None else set(),
            rollup_states or {},
            head_runs,
        ),
    )
    monkeypatch.setattr(
        guard, "_fetch_pr_commits", lambda repo, pr_number, token: [head_sha, "cafebabe"]
    )
    monkeypatch.setattr(
        guard,
        "_prior_sha_presence",
        lambda repo, prior_shas, contexts, token: prior_seen or {},
    )
    rc = guard.main()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    return rc, report


def test_queued_full_shards_make_stable_tests_context_live(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rc, report = _run_guard(
        tmp_path,
        monkeypatch,
        head_runs=[{"name": "full-shard (3.11, 1/8)", "status": "queued", "conclusion": ""}],
    )
    assert rc == 0
    row = report["rows"][0]
    assert row["classification"] == "LIVE_PENDING_AGGREGATOR_VIA_SHARDS"


def test_in_progress_full_shards_make_stable_tests_context_live(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rc, report = _run_guard(
        tmp_path,
        monkeypatch,
        head_runs=[{"name": "full-shard (3.11, 2/8)", "status": "in_progress", "conclusion": ""}],
    )
    assert rc == 0
    assert report["rows"][0]["classification"] == "LIVE_PENDING_AGGREGATOR_VIA_SHARDS"


def test_mixed_shard_states_keep_stable_tests_context_live(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rc, report = _run_guard(
        tmp_path,
        monkeypatch,
        head_runs=[
            {"name": "full-shard (3.11, 1/8)", "status": "completed", "conclusion": "success"},
            {"name": "full-shard (3.11, 2/8)", "status": "queued", "conclusion": ""},
            {"name": "full-shard (3.11, 3/8)", "status": "in_progress", "conclusion": ""},
        ],
    )
    assert rc == 0
    assert report["rows"][0]["classification"] == "LIVE_PENDING_AGGREGATOR_VIA_SHARDS"


def test_rollup_in_progress_counts_as_live(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rc, report = _run_guard(
        tmp_path,
        monkeypatch,
        head_runs=[],
        rollup_states={"tests (3.11)": "IN_PROGRESS"},
    )
    assert rc == 0
    assert report["rows"][0]["classification"] == "ROLLUP_LIVE_PENDING_ON_HEAD_SHA"


def test_prior_sha_without_live_shards_stays_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rc, report = _run_guard(
        tmp_path,
        monkeypatch,
        head_runs=[],
        prior_seen={"tests (3.11)": "cafebabe"},
    )
    assert rc == 2
    assert report["rows"][0]["classification"] == "HEAD_SHA_COUPLING_SUSPECT"


def test_prior_sha_with_live_shards_does_not_coupling_suspect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rc, report = _run_guard(
        tmp_path,
        monkeypatch,
        head_runs=[{"name": "full-shard (3.11, 4/8)", "status": "queued", "conclusion": ""}],
        prior_seen={"tests (3.11)": "cafebabe"},
    )
    assert rc == 0
    assert report["rows"][0]["classification"] == "LIVE_PENDING_AGGREGATOR_VIA_SHARDS"


def test_dynamic_full_shard_names_are_not_required_contexts(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "required_status_checks.json"
    config_path.write_text(
        json.dumps({"required_contexts": ["tests (3.11)"], "ignored_contexts": []}) + "\n",
        encoding="utf-8",
    )
    from required_checks_config import load_required_checks_config

    effective = load_required_checks_config(str(config_path))["effective_required_contexts"]
    assert "full-shard (3.11, 1/8)" not in effective


def test_missing_stable_context_without_shards_is_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rc, report = _run_guard(tmp_path, monkeypatch, head_runs=[])
    assert rc == 2
    assert report["rows"][0]["classification"] == "MISSING_ON_HEAD_SHA"
