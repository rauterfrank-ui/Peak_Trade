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


def test_status_json_flag():
    """status --json returns valid JSON."""
    result = run_ops_center("status", "--json")
    assert result.returncode == 0, f"status --json failed: {result.stderr}"

    # Parse JSON
    import json

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Invalid JSON output: {e}\nOutput: {result.stdout}")

    # Check required keys
    required_keys = [
        "repo_root",
        "branch",
        "working_tree_clean",
        "untracked_count",
        "modified_count",
        "ahead",
        "behind",
        "remote",
        "recent_commits",
        "gh_available",
        "gh_authenticated",
    ]
    for key in required_keys:
        assert key in data, f"Missing key in JSON output: {key}"

    # Type checks
    assert isinstance(data["repo_root"], str)
    assert isinstance(data["branch"], str)
    assert isinstance(data["working_tree_clean"], bool)
    assert isinstance(data["untracked_count"], int)
    assert isinstance(data["modified_count"], int)
    assert isinstance(data["ahead"], int)
    assert isinstance(data["behind"], int)
    assert data["remote"] is None or isinstance(data["remote"], str)
    assert isinstance(data["recent_commits"], list)
    assert isinstance(data["gh_available"], bool)
    assert data["gh_authenticated"] in (True, False, None)


def test_status_json_no_ansi():
    """status --json output contains no ANSI codes or emojis."""
    result = run_ops_center("status", "--json")
    assert result.returncode == 0, f"status --json failed: {result.stderr}"

    # Check for ANSI escape sequences (basic check)
    assert "\x1b[" not in result.stdout, "ANSI codes found in JSON output"

    # Check for common emojis (basic check)
    emojis = ["📊", "🔹", "✅", "⚠️", "❌", "🎯"]
    for emoji in emojis:
        assert emoji not in result.stdout, f"Emoji {emoji} found in JSON output"


def test_status_json_single_object():
    """status --json outputs exactly one JSON object (no extra lines)."""
    result = run_ops_center("status", "--json")
    assert result.returncode == 0, f"status --json failed: {result.stderr}"

    # Should be parseable as single JSON object
    import json

    lines = result.stdout.strip().split("\n")

    # Join all lines and parse
    full_output = "\n".join(lines)
    data = json.loads(full_output)

    # Should be a dict (object)
    assert isinstance(data, dict), "JSON output is not an object"


def test_selftest_command():
    """selftest command runs and reports results."""
    result = run_ops_center("selftest")
    # Should exit 0 if all tests pass, or 1 if any fail
    assert result.returncode in (0, 1), f"selftest unexpected exit code: {result.returncode}"

    # Should contain test output
    assert "Selftest" in result.stdout or "Test:" in result.stdout

    # Should show pass/fail indicators
    assert "PASS" in result.stdout or "FAIL" in result.stdout


def test_status_invalid_flag():
    """status with invalid flag fails gracefully."""
    result = run_ops_center("status", "--invalid-flag")
    assert result.returncode == 1, "status with invalid flag should fail"
    assert "Unknown flag" in result.stderr or "Usage" in result.stderr
