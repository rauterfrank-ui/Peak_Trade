# tests/trading/master_v2/test_dry_smoke_dev_script_v1.py
"""Lokale Tests für scripts/dev/master_v2_dry_smoke_v1.py (nur in-memory, kein I/O)."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

_REPO = Path(__file__).resolve().parent.parent.parent.parent


def _load_smoke_module() -> ModuleType:
    path = _REPO / "scripts" / "dev" / "master_v2_dry_smoke_v1.py"
    name = "master_v2_dry_smoke_v1"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load dry smoke module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_run_dry_smoke_in_memory() -> None:
    smoke = _load_smoke_module()
    out = smoke.run_master_v2_dry_smoke_v1()
    assert out["ok"] is True
    assert out["scenario_count"] == 5
    assert "happy_live_gated" in out["scenarios"]
    assert out["wire_path_ok"] is True
    assert out["wire_smoke_version"] == "v1"


def test_main_no_run_is_noop(capsys) -> None:
    smoke = _load_smoke_module()
    assert smoke.main([]) == 0
    captured = capsys.readouterr()
    assert "nichts ausgefuehrt" in captured.out
    assert "--run" in captured.out


def test_main_run_ok(capsys) -> None:
    smoke = _load_smoke_module()
    assert smoke.main(["--run"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["scenario_count"] == 5
    assert out["wire_path_ok"] is True
    assert out["wire_smoke_version"] == "v1"


def test_subprocess_invocation_repo_root() -> None:
    """Wie in CI/lokal: Skript per Python mit PYTHONPATH=src starten."""
    repo = _REPO
    script = repo / "scripts" / "dev" / "master_v2_dry_smoke_v1.py"
    env = {**os.environ, "PYTHONPATH": str(repo / "src")}
    r = subprocess.run(
        [sys.executable, str(script), "--run"],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    o = json.loads(r.stdout)
    assert o["ok"] is True
    assert o["wire_path_ok"] is True
    assert o["wire_smoke_version"] == "v1"
