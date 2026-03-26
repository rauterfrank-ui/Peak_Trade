from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT = Path("scripts/ops/drill_kill_switch.py")


def test_drill_kill_switch_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "kill-switch drill" in result.stdout.lower()
    assert "--mode" in result.stdout


def test_drill_kill_switch_dry_run_message() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--mode", "dry-run"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "dry-run only" in result.stdout.lower()
