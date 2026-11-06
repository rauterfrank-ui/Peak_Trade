"""Tests for src/ops/truth (loaders, repo claims, git path safety)."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

from ops.truth import (
    TruthStatus,
    evaluate_repo_truth_claims,
    git_changed_files_three_dot,
    load_repo_truth_claims,
)


def test_repo_truth_path_exists_passes(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("x", encoding="utf-8")
    cfg = {
        "version": 1,
        "claims": [{"id": "a", "check": "path_exists", "path": "a.txt"}],
    }
    r = evaluate_repo_truth_claims(tmp_path, cfg)
    assert r.status is TruthStatus.PASS
    assert len(r.results) == 1
    assert r.results[0].check_id == "a"


def test_repo_truth_missing_path_fails(tmp_path: Path) -> None:
    cfg = {
        "version": 1,
        "claims": [{"id": "missing", "check": "path_exists", "path": "nope.txt"}],
    }
    r = evaluate_repo_truth_claims(tmp_path, cfg)
    assert r.status is TruthStatus.FAIL


def test_repo_truth_unknown_check_kind() -> None:
    cfg = {
        "version": 1,
        "claims": [{"id": "x", "check": "future_magic", "path": "a"}],
    }
    r = evaluate_repo_truth_claims(Path("."), cfg)
    assert r.status is TruthStatus.UNKNOWN


def test_repo_truth_path_traversal_rejected(tmp_path: Path) -> None:
    cfg = {
        "version": 1,
        "claims": [{"id": "bad", "check": "path_exists", "path": "../outside"}],
    }
    r = evaluate_repo_truth_claims(tmp_path, cfg)
    assert r.status is TruthStatus.FAIL
    assert any("escapes" in x.message for x in r.results)


def test_git_changed_files_three_dot_parses_stdout() -> None:
    repo = Path("/tmp/repo")
    with mock.patch("ops.truth.git_refs.subprocess.run") as run:
        run.return_value = mock.Mock(returncode=0, stdout="a.py\nb.py\n\n")
        out = git_changed_files_three_dot(repo, "origin/main")
        assert out == ["a.py", "b.py"]
        run.assert_called_once()
        args, kwargs = run.call_args
        assert kwargs["capture_output"] is True
        assert "origin/main...HEAD" in args[0][-1]


def test_git_changed_files_three_dot_raises_on_git_error() -> None:
    repo = Path("/tmp/repo")
    with mock.patch("ops.truth.git_refs.subprocess.run") as run:
        run.return_value = mock.Mock(returncode=1, stdout="", stderr="fatal")
        try:
            git_changed_files_three_dot(repo, "bad")
        except RuntimeError as e:
            assert "git diff failed" in str(e)
        else:
            raise AssertionError("expected RuntimeError")


def test_load_repo_truth_claims_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "c.yaml"
    p.write_text(
        "version: 1\nclaims:\n  - id: x\n    check: path_exists\n    path: a\n",
        encoding="utf-8",
    )
    data = load_repo_truth_claims(p)
    assert data["version"] == 1
    assert isinstance(data["claims"], list)
