"""Contract tests for preflight_pre_pr_ruff_and_diff_guard_v0 (v0)."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD_MODULE = REPO_ROOT / "scripts" / "ops" / "preflight_pre_pr_ruff_and_diff_guard_v0.py"
GUARD_SCRIPT = GUARD_MODULE
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"

sys.path.insert(0, str(REPO_ROOT / "scripts" / "ops"))
import preflight_pre_pr_ruff_and_diff_guard_v0 as guard  # noqa: E402


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "git failed")
    return proc


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "base")
    _git(repo, "branch", "-M", "main")
    return repo


def _commit_all(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message)


def _run_guard(
    repo: Path,
    *extra_args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(GUARD_SCRIPT), "--repo-root", str(repo), *extra_args]
    return subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_package_marker_present() -> None:
    text = GUARD_MODULE.read_text(encoding="utf-8")
    assert guard.PACKAGE_MARKER in text
    assert "PREFLIGHT_PRE_PR_RUFF_AND_DIFF_GUARD_V0" in text


def test_ci_audit_crosslink_present() -> None:
    text = CI_AUDIT.read_text(encoding="utf-8")
    assert "preflight_pre_pr_ruff_and_diff_guard_v0.py" in text
    assert "PREFLIGHT_PRE_PR_RUFF_AND_DIFF_GUARD_V0" in text


def test_no_forbidden_imports_in_guard_module() -> None:
    tree = ast.parse(GUARD_MODULE.read_text(encoding="utf-8"))
    forbidden = {"requests", "httpx", "urllib3", "socket", "credentials"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(token in alias.name for token in forbidden)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not any(token in node.module for token in forbidden)


def test_no_changed_files_passes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    proc = _run_guard(repo, "--base-ref", "main", "--head-ref", "HEAD")
    assert proc.returncode == 0
    assert "VERDICT=PASS" in proc.stdout
    assert "PYTHON_PATH_COUNT=0" in proc.stdout


def test_modified_python_file(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    py = repo / "module.py"
    py.write_text("x=1\n", encoding="utf-8")
    _commit_all(repo, "add module")
    py.write_text("x = 1\n", encoding="utf-8")
    proc = _run_guard(
        repo,
        "--base-ref",
        "main",
        "--head-ref",
        "HEAD",
        "--include-unstaged",
    )
    assert proc.returncode == 0
    assert "PYTHON_PATH_COUNT=1" in proc.stdout


def test_added_python_file(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "new_module.py").write_text("value = 2\n", encoding="utf-8")
    proc = _run_guard(repo, "--base-ref", "main", "--include-unstaged")
    assert proc.returncode == 0
    assert "PYTHON_PATH_COUNT=1" in proc.stdout


def test_deleted_python_file_not_passed_to_ruff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path)
    target = repo / "remove_me.py"
    target.write_text("a = 1\n", encoding="utf-8")
    _commit_all(repo, "track file")
    target.unlink()
    _commit_all(repo, "delete file")

    seen: list[list[str]] = []

    def fake_ruff(args: Sequence[str], *, repo_root: Path) -> int:
        seen.append(list(args))
        return 0

    monkeypatch.setattr(guard, "_run_ruff", fake_ruff)
    result = guard.run_guard(repo_root=repo, base_ref="main~1", head_ref="HEAD")
    assert result.summary.deleted_paths == ("remove_me.py",)
    assert result.summary.python_paths == ()
    assert not any("remove_me.py" in call for call in seen)


def test_renamed_python_file_checks_destination(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    src = repo / "old_name.py"
    src.write_text("val = 1\n", encoding="utf-8")
    _commit_all(repo, "old")
    dst = repo / "new name.py"
    _git(repo, "mv", "old_name.py", "new name.py")
    _commit_all(repo, "rename")
    proc = _run_guard(repo, "--base-ref", "main~1", "--head-ref", "HEAD")
    assert proc.returncode == 0
    assert "RENAMED_PATH_COUNT=1" in proc.stdout
    assert "PYTHON_PATH_COUNT=1" in proc.stdout


def test_rename_python_to_non_python(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _init_repo(tmp_path)
    (repo / "code.py").write_text("x = 1\n", encoding="utf-8")
    _commit_all(repo, "py")
    _git(repo, "mv", "code.py", "code.txt")
    _commit_all(repo, "to txt")

    seen: list[list[str]] = []

    def fake_ruff(args: Sequence[str], *, repo_root: Path) -> int:
        seen.append(list(args))
        return 0

    monkeypatch.setattr(guard, "_run_ruff", fake_ruff)
    result = guard.run_guard(repo_root=repo, base_ref="main~1", head_ref="HEAD")
    assert result.summary.python_paths == ()
    assert "code.py" in result.summary.deleted_paths
    assert not any("code.py" in call for call in seen)


def test_rename_non_python_to_python(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "notes.txt").write_text("note\n", encoding="utf-8")
    _commit_all(repo, "txt")
    _git(repo, "mv", "notes.txt", "notes.py")
    (repo / "notes.py").write_text("value = 3\n", encoding="utf-8")
    _commit_all(repo, "to py")
    proc = _run_guard(repo, "--base-ref", "main~1", "--head-ref", "HEAD")
    assert proc.returncode == 0
    assert "PYTHON_PATH_COUNT=1" in proc.stdout


def test_non_python_only_diff(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _init_repo(tmp_path)
    (repo / "doc.md").write_text("hello\n", encoding="utf-8")
    _commit_all(repo, "doc")

    seen: list[list[str]] = []

    def fake_ruff(args: Sequence[str], *, repo_root: Path) -> int:
        seen.append(list(args))
        return 0

    monkeypatch.setattr(guard, "_run_ruff", fake_ruff)
    result = guard.run_guard(repo_root=repo, base_ref="main~1", head_ref="HEAD")
    assert result.summary.python_paths == ()
    assert seen == []


def test_mixed_diff(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "a.py").write_text("a = 1\n", encoding="utf-8")
    (repo / "b.md").write_text("b\n", encoding="utf-8")
    _commit_all(repo, "mixed")
    proc = _run_guard(repo, "--base-ref", "main~1", "--head-ref", "HEAD")
    assert proc.returncode == 0
    assert "PYTHON_PATH_COUNT=1" in proc.stdout
    assert "CHANGED_PATH_COUNT=2" in proc.stdout


def test_path_with_spaces(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    spaced = repo / "my module.py"
    spaced.write_text("z = 0\n", encoding="utf-8")
    _commit_all(repo, "space")
    proc = _run_guard(repo, "--base-ref", "main~1", "--head-ref", "HEAD")
    assert proc.returncode == 0
    assert "PYTHON_PATH_COUNT=1" in proc.stdout


def test_staged_changes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "staged.py").write_text("s = 1\n", encoding="utf-8")
    _git(repo, "add", "staged.py")
    proc = _run_guard(repo, "--base-ref", "main", "--include-staged")
    assert proc.returncode == 0
    assert "PYTHON_PATH_COUNT=1" in proc.stdout


def test_unstaged_changes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "tracked.py").write_text("t = 1\n", encoding="utf-8")
    _commit_all(repo, "track")
    (repo / "tracked.py").write_text("t = 2\n", encoding="utf-8")
    proc = _run_guard(repo, "--base-ref", "main", "--include-unstaged")
    assert proc.returncode == 0
    assert "PYTHON_PATH_COUNT=1" in proc.stdout


def test_staged_and_unstaged_deduplicated(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    target = repo / "dup.py"
    target.write_text("d = 1\n", encoding="utf-8")
    _git(repo, "add", "dup.py")
    target.write_text("d = 2\n", encoding="utf-8")
    proc = _run_guard(repo, "--base-ref", "main", "--include-staged", "--include-unstaged")
    assert proc.returncode == 0
    assert "PYTHON_PATH_COUNT=1" in proc.stdout


def test_invalid_base_ref_fails_closed(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    proc = _run_guard(repo, "--base-ref", "does-not-exist", "--head-ref", "HEAD")
    assert proc.returncode == 1
    assert "VERDICT=FAIL" in proc.stdout or "VERDICT" in proc.stdout


def test_git_command_error_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _init_repo(tmp_path)

    def boom(
        args: Sequence[str], *, repo_root: Path, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        raise guard.PreflightGuardError("simulated git failure")

    monkeypatch.setattr(guard, "_run_git", boom)
    rc = guard.main(["--repo-root", str(repo), "--base-ref", "main", "--head-ref", "HEAD"])
    assert rc == 1


def test_ruff_format_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _init_repo(tmp_path)
    (repo / "bad.py").write_text("x=1\n", encoding="utf-8")
    _commit_all(repo, "bad")

    def fake_ruff(args: Sequence[str], *, repo_root: Path) -> int:
        if "format" in args and "--check" in args:
            return 1
        return 0

    monkeypatch.setattr(guard, "_run_ruff", fake_ruff)
    result = guard.run_guard(repo_root=repo, base_ref="main~1", head_ref="HEAD")
    assert result.ruff_format_check_rc == 1
    assert result.verdict == "FAIL"


def test_ruff_check_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _init_repo(tmp_path)
    (repo / "lint.py").write_text("x=1\n", encoding="utf-8")
    _commit_all(repo, "lint")

    def fake_ruff(args: Sequence[str], *, repo_root: Path) -> int:
        if args[:1] == ["check"]:
            return 1
        return 0

    monkeypatch.setattr(guard, "_run_ruff", fake_ruff)
    result = guard.run_guard(repo_root=repo, base_ref="main~1", head_ref="HEAD")
    assert result.ruff_check_rc == 1
    assert result.verdict == "FAIL"


def test_git_diff_check_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _init_repo(tmp_path)
    (repo / "ws.py").write_text("x=1\n", encoding="utf-8")
    _commit_all(repo, "ws")

    def fake_diff(
        *, repo_root: Path, base: str, head: str, include_staged: bool, include_unstaged: bool
    ) -> int:
        return 2

    monkeypatch.setattr(guard, "_run_git_diff_check_scopes", fake_diff)
    result = guard.run_guard(repo_root=repo, base_ref="main~1", head_ref="HEAD")
    assert result.git_diff_check_rc == 2
    assert result.verdict == "FAIL"


def test_stable_path_ordering(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "b.py").write_text("b = 1\n", encoding="utf-8")
    (repo / "a.py").write_text("a = 1\n", encoding="utf-8")
    _commit_all(repo, "two files")
    summary = guard._collect_name_status_paths(
        repo_root=repo,
        base=_git(repo, "rev-parse", "main~1").stdout.strip(),
        head=_git(repo, "rev-parse", "HEAD").stdout.strip(),
        include_staged=False,
        include_unstaged=False,
    )
    assert summary.python_paths == ("a.py", "b.py")
    assert summary.changed_paths == ("a.py", "b.py")


def test_json_output(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    proc = _run_guard(repo, "--base-ref", "main", "--json-output")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["VERDICT"] == "PASS"
    assert payload["CHANGED_PATH_COUNT"] == 0


def test_format_flag_applies_then_rechecks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _init_repo(tmp_path)
    target = repo / "fmt.py"
    target.write_text("x=1\n", encoding="utf-8")
    _commit_all(repo, "fmt")
    calls: list[list[str]] = []

    def fake_ruff(args: Sequence[str], *, repo_root: Path) -> int:
        calls.append(list(args))
        return 0

    monkeypatch.setattr(guard, "_run_ruff", fake_ruff)
    result = guard.run_guard(
        repo_root=repo,
        base_ref="main~1",
        head_ref="HEAD",
        apply_format=True,
    )
    assert result.verdict == "PASS"
    assert calls[0][:1] == ["format"]
    assert ["format", "--check"] == calls[1][:2]
    assert calls[2][:1] == ["check"]
