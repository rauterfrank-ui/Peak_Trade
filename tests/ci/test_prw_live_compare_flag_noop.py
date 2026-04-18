"""Compatibility tests for legacy --compare-live flag on redirect wrapper."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_compare_live_flag_is_accepted_and_fails_closed_without_gh(monkeypatch: object) -> None:
    """Legacy --compare-live remains accepted, but canonical check is fail-closed."""
    monkeypatch.setenv("PATH", "")
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
    assert r.returncode == 1
    assert "DEPRECATED:" in r.stderr
    assert "--compare-live is deprecated" in r.stderr
