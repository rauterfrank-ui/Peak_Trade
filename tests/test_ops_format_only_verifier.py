"""Tests for scripts/ops/verify_format_only_pr.sh"""
# Dry-run: format-only guardrail validation

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


VERIFIER_SCRIPT = Path("scripts/ops/verify_format_only_pr.sh")


def _has_bash() -> bool:
    return shutil.which("bash") is not None


def test_verifier_script_exists() -> None:
    """Verify that the format-only verifier script exists."""
    assert VERIFIER_SCRIPT.exists(), f"Missing verifier script: {VERIFIER_SCRIPT}"


def test_verifier_script_is_executable() -> None:
    """Verify that the script has executable permissions."""
    assert VERIFIER_SCRIPT.exists()
    # Check executable bit (at least for owner)
    assert VERIFIER_SCRIPT.stat().st_mode & 0o100, "Script is not executable"


def test_verifier_script_bash_syntax() -> None:
    """Verify that the script has valid bash syntax."""
    if not _has_bash():
        pytest.skip("bash not available on this system")
    proc = subprocess.run(
        ["bash", "-n", str(VERIFIER_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, (
        f"Bash syntax error in {VERIFIER_SCRIPT}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}\n"
    )


def test_verifier_script_usage_without_args() -> None:
    """Verify that the script shows usage message when called without arguments."""
    if not _has_bash():
        pytest.skip("bash not available on this system")

    proc = subprocess.run(
        ["bash", str(VERIFIER_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
    )

    # Should fail with exit code 1
    assert proc.returncode == 1, "Script should fail when called without arguments"

    # Should show usage message
    assert "Usage:" in proc.stderr, "Script should show usage message in stderr"
    assert "base_sha" in proc.stderr.lower(), "Usage should mention base_sha"
    assert "head_sha" in proc.stderr.lower(), "Usage should mention head_sha"


def test_verifier_script_usage_with_one_arg() -> None:
    """Verify that the script shows usage message when called with only one argument."""
    if not _has_bash():
        pytest.skip("bash not available on this system")

    proc = subprocess.run(
        ["bash", str(VERIFIER_SCRIPT), "dummy_sha"],
        capture_output=True,
        text=True,
        check=False,
    )

    # Should fail with exit code 1
    assert proc.returncode == 1, "Script should fail when called with only one argument"

    # Should show usage message
    assert "Usage:" in proc.stderr, "Script should show usage message in stderr"
