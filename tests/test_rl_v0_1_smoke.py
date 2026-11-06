"""
RL v0.1 Contract Smoke Test
============================
Minimal smoke test that validates the RL v0.1 contract by running
the validation script and ensuring it exits cleanly.

The test calls `scripts/validate_rl_v0_1.sh` via subprocess and expects
exit code 0. If SB3 is missing, the script may short-circuit (exit 0)
which is acceptable per the v0.1 spec.

This test runs on Linux/Mac only and is skipped on Windows.
"""

import os
import subprocess
from pathlib import Path

import pytest


def test_rl_v0_1_contract_validation():
    """
    Smoke test: Run RL v0.1 validation script and verify exit code 0.

    This test:
    - Runs `bash scripts/validate_rl_v0_1.sh`
    - Expects exit code 0 (success or acceptable skip)
    - Captures stdout/stderr for debugging on failure
    - Times out after 180 seconds to prevent CI hangs
    - Skips on Windows (bash script not compatible)
    """
    # Skip on Windows
    if os.name == "nt":
        pytest.skip("RL v0.1 validation uses bash; skip on Windows")

    # Find repo root (tests/ is one level below repo root)
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "validate_rl_v0_1.sh"

    # Skip if script doesn't exist yet
    if not script_path.exists():
        pytest.skip(
            f"RL v0.1 validation script not found at {script_path}. "
            "This is expected if the script hasn't been created yet."
        )

    # Run validation script
    result = subprocess.run(
        ["bash", str(script_path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=180,
    )

    # Assert exit code 0
    # Include stdout/stderr in assertion message for debugging
    assert result.returncode == 0, (
        f"RL v0.1 validation failed with exit code {result.returncode}\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )
