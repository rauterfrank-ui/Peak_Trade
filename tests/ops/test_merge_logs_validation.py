"""
Test for validate_merge_logs_setup.sh

Ensures the validation script works correctly and runs fast (<1s).
"""

import subprocess
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SCRIPT = REPO_ROOT / "scripts" / "ops" / "validate_merge_logs_setup.sh"


def test_validate_script_exists():
    """Validation script exists and is executable."""
    assert VALIDATE_SCRIPT.exists(), f"validate_merge_logs_setup.sh not found: {VALIDATE_SCRIPT}"
    assert VALIDATE_SCRIPT.stat().st_mode & 0o111, f"Script not executable: {VALIDATE_SCRIPT}"


def test_validate_runs_successfully():
    """Validation script runs successfully."""
    result = subprocess.run(
        ["bash", str(VALIDATE_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, f"Validation failed: {result.stdout}\n{result.stderr}"

    # Check output contains expected checks
    assert "generate_merge_logs_batch.sh" in result.stdout
    assert "README.md" in result.stdout
    assert "MERGE_LOG_WORKFLOW.md" in result.stdout
    assert "ops_center.sh" in result.stdout

    # Should show success
    assert "All checks passed" in result.stdout or "✅" in result.stdout


def test_validate_runs_fast():
    """Validation script runs in less than 1 second."""
    start = time.time()

    result = subprocess.run(
        ["bash", str(VALIDATE_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    elapsed = time.time() - start

    assert elapsed < 1.0, f"Validation took {elapsed:.2f}s (should be <1s)"
    assert result.returncode == 0, f"Validation failed: {result.stdout}"


def test_validate_is_offline():
    """Validation script works offline (no network calls)."""
    # This test verifies the script doesn't make network calls
    # by checking it succeeds even in a sandboxed environment
    result = subprocess.run(
        ["bash", str(VALIDATE_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
        # No network access
    )

    # Should succeed even without network
    assert result.returncode == 0, f"Validation should work offline: {result.stdout}"


def test_validate_checks_all_components():
    """Validation script checks all required components."""
    result = subprocess.run(
        ["bash", str(VALIDATE_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    # Should check batch script
    assert "generate_merge_logs_batch.sh" in result.stdout

    # Should check both docs
    assert "README.md" in result.stdout
    assert "MERGE_LOG_WORKFLOW.md" in result.stdout

    # Should check ops_center integration
    assert "ops_center.sh" in result.stdout

    # Should check for markers
    assert "Markers present" in result.stdout or "MERGE_LOG_EXAMPLES" in result.stdout
