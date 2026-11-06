"""Smoke: scripts/run_optuna_study.py --help distinguishes full runner vs J2 placeholder."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "run_optuna_study.py"


def test_help_exits_zero_and_names_placeholder_path():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "run_study_optuna_placeholder.py" in out
    assert "NO-LIVE" in out
    assert "--strategy" in out
