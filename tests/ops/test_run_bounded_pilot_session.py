"""Tests for scripts/ops/run_bounded_pilot_session.py — Bounded Pilot Entry Gate."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "ops" / "run_bounded_pilot_session.py"


def test_script_exists() -> None:
    """Script file exists."""
    assert SCRIPT.is_file()


def test_script_runs_with_repo_root() -> None:
    """Script runs with --repo-root and produces output."""
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(ROOT), "--no-invoke"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert r.returncode in (0, 1, 2), f"stderr: {r.stderr}"
    assert (
        "Bounded pilot" in r.stdout
        or "GATES_RED" in r.stderr
        or "entry_permitted" in r.stdout
        or "Gates GREEN" in r.stdout
    )


def test_script_json_output() -> None:
    """Script --json produces valid JSON with contract and entry_permitted."""
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(ROOT), "--json", "--no-invoke"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert r.returncode in (0, 1)
    data = json.loads(r.stdout)
    assert data["contract"] == "run_bounded_pilot_session"
    assert "entry_permitted" in data
    assert "verdict" in data
    assert "go_no_go" in data
    assert data["go_no_go"]["contract"] == "pilot_go_no_go_eval_v1"


def test_main_importable() -> None:
    """main() can be imported and returns int."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_bounded_pilot_session",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "main")
    assert callable(mod.main)
