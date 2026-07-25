"""Deterministic tests for exact-head Ready-for-Review reuse verifier."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "ci"))
import exact_head_ready_reuse as reuse


def _run(
    *,
    name: str,
    head_sha: str,
    status: str = "completed",
    conclusion: str = "success",
    app_id: int = 15368,
    completed_at: str = "2026-07-25T13:46:00Z",
    check_run_id: int = 1,
) -> Dict[str, Any]:
    return {
        "id": check_run_id,
        "name": name,
        "head_sha": head_sha,
        "status": status,
        "conclusion": conclusion,
        "completed_at": completed_at,
        "started_at": "2026-07-25T13:45:00Z",
        "app": {"id": app_id, "slug": "github-actions"},
    }


def _cfg(tmp_path: Path, contexts: List[str] | None = None) -> Path:
    path = tmp_path / "required_status_checks.json"
    path.write_text(
        json.dumps(
            {
                "required_contexts": contexts
                or [
                    "tests (3.11)",
                    "strategy-smoke",
                    "Lint Gate",
                    "audit",
                ],
                "ignored_contexts": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_draft_exact_head_all_success_allows_reuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    head = "da0757223519654cf486abf17216c1ce7739de71"
    cfg = _cfg(tmp_path, ["tests (3.11)", "strategy-smoke"])
    report = tmp_path / "report.json"
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setattr(
        reuse,
        "fetch_check_runs_for_sha",
        lambda repo, sha, token: [
            _run(name="tests (3.11)", head_sha=head, check_run_id=10),
            _run(name="strategy-smoke", head_sha=head, check_run_id=11),
        ],
    )
    rc = reuse.main(
        [
            "--repo",
            "acme/repo",
            "--head-sha",
            head,
            "--required-config",
            str(cfg),
            "--contexts",
            "tests (3.11)",
            "strategy-smoke",
            "--report-json",
            str(report),
            "--write-github-output",
        ]
    )
    assert rc == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["reuse_ok"] is True
    assert payload["counts"]["success"] == 2


def test_wrong_sha_rejects_prior_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    head = "aaa111"
    prior = "bbb222"
    cfg = _cfg(tmp_path, ["tests (3.11)"])
    report = tmp_path / "report.json"
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setattr(
        reuse,
        "fetch_check_runs_for_sha",
        lambda repo, sha, token: [_run(name="tests (3.11)", head_sha=prior, check_run_id=1)],
    )
    rc = reuse.main(
        [
            "--repo",
            "acme/repo",
            "--head-sha",
            head,
            "--required-config",
            str(cfg),
            "--contexts",
            "tests (3.11)",
            "--report-json",
            str(report),
        ]
    )
    assert rc == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["reuse_ok"] is False
    assert payload["decisions"][0]["decision"] == "WRONG_SHA"


def test_missing_context_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    head = "deadbeef"
    cfg = _cfg(tmp_path, ["tests (3.11)", "strategy-smoke"])
    report = tmp_path / "report.json"
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setattr(
        reuse,
        "fetch_check_runs_for_sha",
        lambda repo, sha, token: [_run(name="tests (3.11)", head_sha=head)],
    )
    rc = reuse.main(
        [
            "--repo",
            "acme/repo",
            "--head-sha",
            head,
            "--required-config",
            str(cfg),
            "--contexts",
            "tests (3.11)",
            "strategy-smoke",
            "--report-json",
            str(report),
        ]
    )
    assert rc == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["reuse_ok"] is False
    assert payload["counts"]["missing"] == 1


def test_failed_context_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    head = "deadbeef"
    cfg = _cfg(tmp_path, ["Lint Gate"])
    report = tmp_path / "report.json"
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setattr(
        reuse,
        "fetch_check_runs_for_sha",
        lambda repo, sha, token: [
            _run(name="Lint Gate", head_sha=head, conclusion="failure", check_run_id=9)
        ],
    )
    payload_rc = reuse.main(
        [
            "--repo",
            "acme/repo",
            "--head-sha",
            head,
            "--required-config",
            str(cfg),
            "--contexts",
            "Lint Gate",
            "--report-json",
            str(report),
        ]
    )
    assert payload_rc == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["reuse_ok"] is False
    assert payload["decisions"][0]["decision"] == "FAILED"


def test_pending_context_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    head = "deadbeef"
    cfg = _cfg(tmp_path, ["audit"])
    report = tmp_path / "report.json"
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setattr(
        reuse,
        "fetch_check_runs_for_sha",
        lambda repo, sha, token: [
            _run(
                name="audit",
                head_sha=head,
                status="in_progress",
                conclusion="",
                completed_at="",
                check_run_id=3,
            )
        ],
    )
    rc = reuse.main(
        [
            "--repo",
            "acme/repo",
            "--head-sha",
            head,
            "--required-config",
            str(cfg),
            "--contexts",
            "audit",
            "--report-json",
            str(report),
        ]
    )
    assert rc == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["reuse_ok"] is False
    assert payload["decisions"][0]["decision"] == "PENDING"


def test_success_only_on_previous_sha_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # fetch is by head SHA; API returns only that SHA's runs. Simulate empty for new head.
    head = "newsha"
    cfg = _cfg(tmp_path, ["tests (3.11)"])
    report = tmp_path / "report.json"
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setattr(reuse, "fetch_check_runs_for_sha", lambda repo, sha, token: [])
    rc = reuse.main(
        [
            "--repo",
            "acme/repo",
            "--head-sha",
            head,
            "--required-config",
            str(cfg),
            "--contexts",
            "tests (3.11)",
            "--report-json",
            str(report),
        ]
    )
    assert rc == 0
    assert json.loads(report.read_text(encoding="utf-8"))["reuse_ok"] is False


def test_merge_commit_sha_mismatch_rejected() -> None:
    views = [
        reuse._normalize_check_run(
            _run(name="tests (3.11)", head_sha="mergecommitsha", check_run_id=1)
        )
    ]
    assert views[0] is not None
    selected, classification, _ = reuse.select_authoritative_check_run(
        [views[0]],
        context="tests (3.11)",
        head_sha="prheadsha",
        expected_app_id=15368,
    )
    assert selected is None
    assert classification == "WRONG_SHA"


def test_duplicate_mixed_conclusions_picks_newest_completed() -> None:
    head = "abc"
    older_fail = reuse._normalize_check_run(
        _run(
            name="Lint Gate",
            head_sha=head,
            conclusion="failure",
            completed_at="2026-07-25T13:40:00Z",
            check_run_id=1,
        )
    )
    newer_success = reuse._normalize_check_run(
        _run(
            name="Lint Gate",
            head_sha=head,
            conclusion="success",
            completed_at="2026-07-25T13:50:00Z",
            check_run_id=2,
        )
    )
    assert older_fail and newer_success
    selected, classification, _ = reuse.select_authoritative_check_run(
        [older_fail, newer_success],
        context="Lint Gate",
        head_sha=head,
        expected_app_id=15368,
    )
    assert classification == "SUCCESS"
    assert selected is not None
    assert selected.check_run_id == 2

    selected2, classification2, _ = reuse.select_authoritative_check_run(
        [
            newer_success,
            reuse._normalize_check_run(
                _run(
                    name="Lint Gate",
                    head_sha=head,
                    conclusion="failure",
                    completed_at="2026-07-25T13:55:00Z",
                    check_run_id=3,
                )
            ),
        ],
        context="Lint Gate",
        head_sha=head,
        expected_app_id=15368,
    )
    assert classification2 == "FAILED"
    assert selected2 is not None
    assert selected2.check_run_id == 3


def test_wrong_app_rejected() -> None:
    head = "abc"
    view = reuse._normalize_check_run(
        _run(name="audit", head_sha=head, app_id=99999, check_run_id=7)
    )
    assert view is not None
    selected, classification, _ = reuse.select_authoritative_check_run(
        [view],
        context="audit",
        head_sha=head,
        expected_app_id=15368,
    )
    assert selected is None
    assert classification == "WRONG_APP"


def test_pagination_fetches_all_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    pages = {
        1: (
            {
                "check_runs": [
                    _run(name="tests (3.11)", head_sha="h", check_run_id=i) for i in range(100)
                ]
            },
            {"Link": '<https://api.github.com/x?page=2>; rel="next"'},
        ),
        2: (
            {
                "check_runs": [
                    _run(name="strategy-smoke", head_sha="h", check_run_id=200),
                ]
            },
            {},
        ),
    }

    def fake_api(endpoint, token, accept="application/vnd.github+json", query=None):
        page = int((query or {}).get("page", 1))
        return pages[page]

    monkeypatch.setattr(reuse, "_gh_api", fake_api)
    runs = reuse.fetch_check_runs_for_sha("acme/repo", "h", "token")
    assert len(runs) == 101
    assert runs[-1]["name"] == "strategy-smoke"


def test_api_error_fail_closed_no_reuse(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _cfg(tmp_path, ["tests (3.11)"])
    report = tmp_path / "report.json"
    monkeypatch.setenv("GITHUB_TOKEN", "t")

    def boom(repo, sha, token):
        raise RuntimeError("GitHub API 403 for /repos/x: denied")

    monkeypatch.setattr(reuse, "fetch_check_runs_for_sha", boom)
    rc = reuse.main(
        [
            "--repo",
            "acme/repo",
            "--head-sha",
            "deadbeef",
            "--required-config",
            str(cfg),
            "--contexts",
            "tests (3.11)",
            "--report-json",
            str(report),
        ]
    )
    assert rc == 0  # reuse=false, allow full validation path
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["reuse_ok"] is False
    assert payload["error"] and "api_error" in payload["error"]


def test_fail_on_unproven_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _cfg(tmp_path, ["tests (3.11)"])
    report = tmp_path / "report.json"
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setattr(reuse, "fetch_check_runs_for_sha", lambda *a, **k: [])
    rc = reuse.main(
        [
            "--repo",
            "acme/repo",
            "--head-sha",
            "deadbeef",
            "--required-config",
            str(cfg),
            "--contexts",
            "tests (3.11)",
            "--report-json",
            str(report),
            "--fail-on-unproven",
        ]
    )
    assert rc == 2


def test_skipped_conclusion_not_success() -> None:
    head = "abc"
    view = reuse._normalize_check_run(
        _run(name="Lint Gate", head_sha=head, conclusion="skipped", check_run_id=1)
    )
    assert view is not None
    _, classification, _ = reuse.select_authoritative_check_run(
        [view], context="Lint Gate", head_sha=head, expected_app_id=15368
    )
    assert classification == "NON_SUCCESS"


def test_workflow_keeps_ready_trigger_and_no_job_level_if_on_tests() -> None:
    ci = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "ready_for_review" in ci
    assert "ready-exact-head-reuse" in ci
    assert "exact_head_ready_reuse.py" in ci
    # Contract: no job-level if on tests
    import re

    block = re.search(r"\n  tests:\n(.*?)(\n  [a-zA-Z0-9_-]+:\n|\Z)", ci, re.S)
    assert block
    assert not re.search(r"^    if:", block.group(1), re.M)


def test_required_context_names_unchanged() -> None:
    data = json.loads(Path("config/ci/required_status_checks.json").read_text(encoding="utf-8"))
    assert data["required_contexts"] == [
        "Guard tracked files in reports directories",
        "Lint Gate",
        "Policy Critic Gate",
        "audit",
        "dispatch-guard",
        "docs-drift-guard",
        "docs-reference-targets-gate",
        "docs-token-policy-gate",
        "repo-truth-claims",
        "strategy-smoke",
        "tests (3.11)",
    ]
