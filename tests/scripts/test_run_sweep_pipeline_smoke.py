"""Smoke test for run_sweep_pipeline.py (Block A — Unified Sweep Pipeline CLI)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "run_sweep_pipeline.py"


def test_run_sweep_pipeline_help():
    """CLI zeigt Hilfe und beendet mit Exit 0."""
    p = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, p.stderr or p.stdout
    out = p.stdout
    assert "Unified Sweep Pipeline" in out
    assert "NO-LIVE" in out
    assert "order execution" in out.lower() or "order-ausführung" in out.lower()
    assert "--run" in out and "--report" in out and "--promote" in out
    assert "out/research" in out or "sweep_id" in out


def test_run_sweep_pipeline_requires_sweep_name():
    """Ohne --sweep-name gibt es einen Fehler."""
    p = subprocess.run(
        [sys.executable, str(SCRIPT), "--run"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert p.returncode != 0
    out = (p.stderr or "") + (p.stdout or "")
    assert "sweep-name" in out or "required" in out.lower()
