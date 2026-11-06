from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_new_listings_cli_help_smoke() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "src.research.new_listings", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()


def test_new_listings_cli_run_help_smoke() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "src.research.new_listings", "run", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
