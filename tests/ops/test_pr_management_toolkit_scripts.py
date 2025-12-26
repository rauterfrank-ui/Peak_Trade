"""
CI guard tests for PR management toolkit scripts.

Ensures:
- Scripts exist
- Executable bit set
- Bash syntax valid (bash -n)
"""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "scripts" / "ops"

TOOLKIT_SCRIPTS = [
    OPS / "review_and_merge_pr.sh",
    OPS / "pr_review_merge_workflow.sh",
    OPS / "pr_review_merge_workflow_template.sh",
]


def test_pr_management_toolkit_scripts_exist():
    """Guard: PR management toolkit scripts must exist."""
    missing = []
    for script in TOOLKIT_SCRIPTS:
        if not script.exists():
            missing.append(f"Missing: {script.relative_to(ROOT)}")

    assert not missing, "PR management toolkit scripts not found:\n" + "\n".join(missing)


def test_pr_management_toolkit_scripts_executable():
    """Guard: PR management toolkit scripts must be executable."""
    non_executable = []
    for script in TOOLKIT_SCRIPTS:
        if not script.exists():
            continue  # Covered by existence test

        if not os.access(script, os.X_OK):
            non_executable.append(f"Not executable: {script.relative_to(ROOT)}")

    assert not non_executable, "PR management toolkit scripts not executable:\n" + "\n".join(
        non_executable
    )


@pytest.mark.parametrize("script", TOOLKIT_SCRIPTS, ids=lambda p: p.name)
def test_pr_management_toolkit_script_bash_syntax(script):
    """Guard: PR management toolkit scripts must have valid bash syntax."""
    if not script.exists():
        pytest.skip(f"Script does not exist: {script}")

    result = subprocess.run(
        ["bash", "-n", str(script)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"Bash syntax error in {script.name}:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
