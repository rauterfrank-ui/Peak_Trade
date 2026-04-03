"""Smoke tests for scripts/ops/ma.py (NO-LIVE)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "ops" / "ma.py"


def _load_ma():
    spec = importlib.util.spec_from_file_location("peak_trade_ma_ops", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ma_help_contains_no_live() -> None:
    p = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, p.stderr
    assert "NO-LIVE" in p.stdout.replace("\n", "")


def test_ma_main_help_returns_zero() -> None:
    ma_mod = _load_ma()
    assert ma_mod.main(["--help"]) == 0
