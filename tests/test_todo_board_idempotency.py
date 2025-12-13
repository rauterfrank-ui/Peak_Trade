"""
Test that the TODO board generator is idempotent:
Running it multiple times with the same input should not cause diffs.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def _find_repo_root(start: Path) -> Path:
    """Robust repo-root detection without relying on git."""
    for p in (start, *start.parents):
        if (p / "pyproject.toml").exists() and (p / "scripts" / "build_todo_board_html.py").exists():
            return p
    raise RuntimeError("Could not locate repo root (pyproject.toml + scripts/build_todo_board_html.py not found)")


def _run_generator(repo_root: Path) -> subprocess.CompletedProcess:
    """Run the TODO board generator script."""
    script = repo_root / "scripts" / "build_todo_board_html.py"
    assert script.exists(), f"Generator script not found: {script}"

    return subprocess.run(
        [sys.executable, str(script)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )


def _get_git_status(repo_root: Path) -> str:
    """Get git status --porcelain output."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        pytest.fail(f"git status failed: {e.stderr}")


def test_consecutive_generator_runs_produce_no_diffs() -> None:
    """
    Verify that running the generator twice does not modify files unnecessarily.

    This ensures:
    - The generator is idempotent
    - CI pipelines stay clean
    - No spurious diffs from timestamp/formatting changes
    """
    repo_root = _find_repo_root(Path(__file__).resolve())

    # First run: establish baseline
    result1 = _run_generator(repo_root)
    assert result1.returncode == 0, (
        f"First generator run failed.\n"
        f"stdout:\n{result1.stdout}\n"
        f"stderr:\n{result1.stderr}\n"
    )

    # Capture state after first run
    status_after_first = _get_git_status(repo_root)

    # Second run: should produce no additional changes
    result2 = _run_generator(repo_root)
    assert result2.returncode == 0, (
        f"Second generator run failed.\n"
        f"stdout:\n{result2.stdout}\n"
        f"stderr:\n{result2.stderr}\n"
    )

    # Verify no new diffs were introduced
    status_after_second = _get_git_status(repo_root)

    assert status_after_first == status_after_second, (
        "Generator is NOT idempotent: second run introduced changes.\n"
        f"Status after 1st run:\n{status_after_first or '(clean)'}\n"
        f"Status after 2nd run:\n{status_after_second or '(clean)'}\n"
    )

    # If there were changes after the first run, they should still be the same after the second
    # This is OK - it just means the generator updated the output
    # What matters is that running it AGAIN doesn't create more changes
