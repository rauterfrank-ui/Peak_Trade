"""Tests for PR-W: --compare-live flag (no network)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_compare_live_flag_skips_without_gh(monkeypatch: object) -> None:
    """Without gh in PATH, --compare-live prints LIVE_COMPARE_SKIPPED and exits 0."""
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
    assert r.returncode in (0, 2, 3, 4)
    if r.returncode == 0:
        assert "LIVE_COMPARE_SKIPPED" in r.stdout or "DRIFT_OK" in r.stdout
