"""Smoke: dev_workflow nested Python calls use sys.executable."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "dev_workflow.py"


def test_dev_workflow_dev_python_matches_current_interpreter() -> None:
    spec = importlib.util.spec_from_file_location("dev_workflow_smoke", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.DEV_PYTHON == sys.executable
