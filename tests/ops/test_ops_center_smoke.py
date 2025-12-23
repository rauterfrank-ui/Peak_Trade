"""
Smoke tests for ops_center.sh

Tests basic functionality without requiring full environment setup.
Safe-by-default: tests must be robust to missing tools (gh, etc).
"""

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OPS_CENTER = REPO_ROOT / "scripts" / "ops" / "ops_center.sh"


def run_ops_center(*args):
    """Run ops_center.sh with given args, return CompletedProcess."""
    return subprocess.run(
        ["bash", str(OPS_CENTER), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )


def test_ops_center_exists():
    """Script file exists."""
    assert OPS_CENTER.exists(), f"ops_center.sh not found: {OPS_CENTER}"


def test_help_command():
    """help command runs successfully."""
    result = run_ops_center("help")
    assert result.returncode == 0, f"help failed: {result.stderr}"
    assert "Ops Center" in result.stdout or "USAGE" in result.stdout
    assert "status" in result.stdout
    assert "pr" in result.stdout
    assert "doctor" in result.stdout
    assert "merge-log" in result.stdout


def test_help_flag():
    """--help flag works."""
    result = run_ops_center("--help")
    assert result.returncode == 0, f"--help failed: {result.stderr}"
    assert "Ops Center" in result.stdout or "USAGE" in result.stdout


def test_status_command():
    """status command runs (may warn about missing tools, but exits 0)."""
    result = run_ops_center("status")
    assert result.returncode == 0, f"status failed: {result.stderr}"
    # Should contain git output
    assert "Branch" in result.stdout or "branch" in result.stdout.lower()


def test_merge_log_command():
    """merge-log command runs successfully."""
    result = run_ops_center("merge-log")
    assert result.returncode == 0, f"merge-log failed: {result.stderr}"
    assert "Merge Log" in result.stdout or "MERGE_LOG" in result.stdout
    assert "docs/ops/MERGE_LOG_WORKFLOW.md" in result.stdout


def test_pr_command_no_arg():
    """pr command without PR number fails gracefully."""
    result = run_ops_center("pr")
    assert result.returncode == 1, "pr without arg should fail"
    assert "PR number required" in result.stdout or "Usage" in result.stdout


def test_unknown_command():
    """Unknown command fails with helpful message."""
    result = run_ops_center("unknown_command_xyz")
    assert result.returncode == 1, "unknown command should fail"
    assert "Unknown command" in result.stdout or "USAGE" in result.stdout


def test_doctor_command_if_available():
    """
    doctor command runs if ops_doctor.sh exists.
    If not available, should exit 0 with warning (safe-by-default).
    """
    result = run_ops_center("doctor", "--help")
    # Should either run successfully or warn gracefully
    assert result.returncode == 0, f"doctor failed: {result.stderr}"
    # If ops_doctor.sh exists, should show doctor help/output
    # If not, should show warning
    assert "Doctor" in result.stdout or "not found" in result.stdout or "Check" in result.stdout
