"""Guardrail tests for retired legacy drift detector arguments."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_compare_live_flag_is_no_longer_supported() -> None:
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/required_checks_drift_detector.py",
            "--compare-live",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 2
    assert "retired and unsupported" in r.stderr
