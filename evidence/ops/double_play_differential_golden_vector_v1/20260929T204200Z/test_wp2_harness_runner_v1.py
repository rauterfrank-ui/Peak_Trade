"""Pytest entrypoints for WP-2 side executor (evidence-only)."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

_BASE = Path(__file__).resolve().parent
_EXECUTOR = _BASE / "wp2_side_executor_v1.py"


def _run_executor(side: str, out_name: str) -> None:
    spec = importlib.util.spec_from_file_location("wp2_side_executor_v1", _EXECUTOR)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    os.environ["WP2_SIDE"] = side
    os.environ["WP2_OUTPUT_JSON"] = str(_BASE / out_name)
    spec.loader.exec_module(mod)
    rc = mod.main()
    assert rc == 0


def test_wp2_side_current() -> None:
    _run_executor("current", "side_current.json")


def test_wp2_side_historical() -> None:
    _run_executor("historical", "side_historical.json")
