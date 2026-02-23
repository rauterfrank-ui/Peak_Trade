"""Tests for PR-Y: CI trigger script syntax."""

from __future__ import annotations

import subprocess
from pathlib import Path


def test_ci_trigger_bash_syntax() -> None:
    """Bash -n validates script syntax."""
    r = subprocess.run(
        ["bash", "-n", "scripts/ops/ci_trigger_required_checks.sh"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 0, r.stderr
