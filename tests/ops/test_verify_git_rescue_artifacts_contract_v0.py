"""Contract tests for scripts/ops/verify_git_rescue_artifacts.sh.

The verifier is exercised only against temporary fixture directories/repos.
No real repository rescue artifact, Live/Testnet path, or paper test data is touched.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "ops" / "verify_git_rescue_artifacts.sh"


def _run(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    (path / "README.md").write_text("# fixture\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"], cwd=path, check=True, capture_output=True, text=True
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "user.name=Fixture",
            "commit",
            "-m",
            "fixture init",
        ],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    return path


def test_verify_git_rescue_script_exists_and_is_bash() -> None:
    assert SCRIPT.exists()
    text = SCRIPT.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env bash")
    assert "set -u" in text
    assert "set -o pipefail" in text


def test_verify_git_rescue_fails_for_missing_backup_dir(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")

    result = _run(["--backup-dir", str(tmp_path / "nonexistent")], cwd=repo)

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "backup directory not found" in combined.lower()


def test_verify_git_rescue_fails_for_empty_backup_dir(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")
    backup = tmp_path / "backup"
    backup.mkdir()

    result = _run(["--backup-dir", str(backup)], cwd=repo)

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "no bundle" in combined.lower() or "*.bundle" in combined.lower()


def test_verify_git_rescue_does_not_mutate_fixture_repo_on_failure(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")
    backup = tmp_path / "backup"
    backup.mkdir()

    before = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    result = _run(["--backup-dir", str(backup)], cwd=repo)

    after = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    assert result.returncode != 0
    assert before == ""
    assert after == ""


def test_verify_git_rescue_non_git_cwd_errors_without_bundle(tmp_path: Path) -> None:
    backup = tmp_path / "backup"
    backup.mkdir()

    result = _run(["--backup-dir", str(backup)], cwd=tmp_path)

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "git" in combined.lower()
