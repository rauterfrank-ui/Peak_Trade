"""Smoke: scripts/run_backtest.py --help (NO-LIVE scope lines)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "run_backtest.py"


def test_help_exits_zero_and_states_no_live_scope():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "NO-LIVE" in out
    assert "Evidence" in out
    assert "keine Order" in out or "keine Orders" in out
    assert "resolve_backtest_symbol" in out
