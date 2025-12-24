"""
tests/ops/test_knowledge_prod_smoke_script.py

Minimal guards for knowledge_prod_smoke.sh script.
"""

import os
import stat
from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    """Return the repository root path."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def script_path(repo_root: Path) -> Path:
    """Return the path to knowledge_prod_smoke.sh."""
    return repo_root / "scripts" / "ops" / "knowledge_prod_smoke.sh"


def test_script_exists(script_path: Path) -> None:
    """Verify that knowledge_prod_smoke.sh exists."""
    assert script_path.exists(), f"Script not found: {script_path}"
    assert script_path.is_file(), f"Path exists but is not a file: {script_path}"


def test_script_is_executable(script_path: Path) -> None:
    """Verify that knowledge_prod_smoke.sh is executable."""
    assert script_path.exists(), f"Script not found: {script_path}"

    # Check executable bit
    st = os.stat(script_path)
    is_executable = bool(st.st_mode & stat.S_IXUSR)

    assert is_executable, f"Script is not executable: {script_path}\nRun: chmod +x {script_path}"


def test_script_has_shebang(script_path: Path) -> None:
    """Verify that script starts with proper shebang."""
    assert script_path.exists(), f"Script not found: {script_path}"

    content = script_path.read_text()
    lines = content.splitlines()

    assert len(lines) > 0, "Script is empty"
    assert lines[0].startswith("#!"), "Script missing shebang"
    assert "bash" in lines[0], f"Expected bash shebang, got: {lines[0]}"


def test_script_has_strict_mode(script_path: Path) -> None:
    """Verify that script uses strict mode (set -euo pipefail)."""
    assert script_path.exists(), f"Script not found: {script_path}"

    content = script_path.read_text()

    assert "set -euo pipefail" in content, "Script should use strict mode: set -euo pipefail"


def test_script_adopts_run_helpers(script_path: Path) -> None:
    """Verify that script references run_helpers.sh (adoption guard)."""
    assert script_path.exists(), f"Script not found: {script_path}"

    content = script_path.read_text()

    # Check for run_helpers reference
    assert "run_helpers.sh" in content, "Script should reference run_helpers.sh for ops consistency"

    # Check for proper sourcing pattern (allow optional)
    assert "source" in content or "." in content, "Script should source run_helpers.sh"


def test_script_has_usage_function(script_path: Path) -> None:
    """Verify that script has usage/help function."""
    assert script_path.exists(), f"Script not found: {script_path}"

    content = script_path.read_text()

    # Check for usage function
    assert "usage()" in content, "Script should have usage() function"

    # Check for --help handling
    assert "--help" in content or "-h" in content, "Script should support --help or -h flag"


def test_script_has_cleanup_trap(script_path: Path) -> None:
    """Verify that script has cleanup trap for temp files."""
    assert script_path.exists(), f"Script not found: {script_path}"

    content = script_path.read_text()

    # Check for cleanup function and trap
    assert "cleanup()" in content, "Script should have cleanup() function"
    assert "trap cleanup" in content, "Script should use trap for cleanup on EXIT/INT/TERM"


def test_script_has_http_request_helper(script_path: Path) -> None:
    """Verify that script has http_request helper function."""
    assert script_path.exists(), f"Script not found: {script_path}"

    content = script_path.read_text()

    assert "http_request()" in content, "Script should have http_request() helper function"


def test_script_has_check_endpoint_helper(script_path: Path) -> None:
    """Verify that script has check_endpoint helper function."""
    assert script_path.exists(), f"Script not found: {script_path}"

    content = script_path.read_text()

    assert "check_endpoint()" in content, "Script should have check_endpoint() helper function"


def test_script_validates_base_url(script_path: Path) -> None:
    """Verify that script validates BASE_URL requirement."""
    assert script_path.exists(), f"Script not found: {script_path}"

    content = script_path.read_text()

    # Should check if BASE_URL is empty
    assert "BASE_URL" in content, "Script should use BASE_URL"
    assert "-z" in content or "empty" in content.lower(), (
        "Script should validate that BASE_URL is not empty"
    )


def test_script_has_summary_output(script_path: Path) -> None:
    """Verify that script outputs summary with counters."""
    assert script_path.exists(), f"Script not found: {script_path}"

    content = script_path.read_text()

    # Check for counter variables
    assert "PASS_COUNT" in content, "Script should track PASS_COUNT"
    assert "FAIL_COUNT" in content, "Script should track FAIL_COUNT"
    assert "DEGRADED_COUNT" in content, "Script should track DEGRADED_COUNT"

    # Check for summary output
    assert "Summary" in content, "Script should output summary"


def test_script_has_proper_exit_codes(script_path: Path) -> None:
    """Verify that script uses proper exit codes."""
    assert script_path.exists(), f"Script not found: {script_path}"

    content = script_path.read_text()

    # Check for explicit exit codes
    assert "exit 0" in content, "Script should exit 0 on success"
    assert "exit 1" in content, "Script should exit 1 on failure"
    assert "exit 2" in content, "Script should exit 2 on degraded (strict mode)"


def test_script_supports_verbose_mode(script_path: Path) -> None:
    """Verify that script supports verbose mode."""
    assert script_path.exists(), f"Script not found: {script_path}"

    content = script_path.read_text()

    assert "--verbose" in content, "Script should support --verbose flag"
    assert "VERBOSE" in content, "Script should have VERBOSE variable"


def test_script_supports_strict_mode(script_path: Path) -> None:
    """Verify that script supports strict mode."""
    assert script_path.exists(), f"Script not found: {script_path}"

    content = script_path.read_text()

    assert "--strict" in content, "Script should support --strict flag"
    assert "STRICT" in content, "Script should have STRICT variable"


def test_script_supports_authentication(script_path: Path) -> None:
    """Verify that script supports bearer token authentication."""
    assert script_path.exists(), f"Script not found: {script_path}"

    content = script_path.read_text()

    assert "--token" in content, "Script should support --token flag"
    assert "TOKEN" in content, "Script should have TOKEN variable"
    assert "Authorization: Bearer" in content, "Script should support Bearer token authentication"


def test_script_has_write_gating_check(script_path: Path) -> None:
    """Verify that script includes write gating probe."""
    assert script_path.exists(), f"Script not found: {script_path}"

    content = script_path.read_text()

    # Check for write test
    assert "write" in content.lower() or "post" in content.lower(), (
        "Script should test write operations"
    )

    # Check for 403 expectation (write blocked)
    assert "403" in content, "Script should expect 403 for blocked writes"


def test_script_handles_graceful_degradation(script_path: Path) -> None:
    """Verify that script handles 501 (graceful degradation)."""
    assert script_path.exists(), f"Script not found: {script_path}"

    content = script_path.read_text()

    # Check for 501 handling
    assert "501" in content, "Script should handle 501 (Not Implemented)"

    # Check for degradation logic
    assert "EXPECT_501_OK" in content or "degraded" in content.lower(), (
        "Script should have logic for handling degraded state"
    )
