"""P81 smoke tests: supervisor service hardening (lock, meta, backoff)."""

import json
import subprocess
from pathlib import Path

import pytest


def test_p81_smoke() -> None:
    assert True


def test_p81_meta_json_created(tmp_path: Path) -> None:
    """One tick creates supervisor_meta.json with last_tick."""
    env = {
        "MODE": "shadow",
        "OUT_DIR": str(tmp_path / "out"),
        "PIDFILE": str(tmp_path / "p81.pid"),
        "LOCKFILE": str(tmp_path / "p81.lock"),
        "INTERVAL": "0",
        "ITERATIONS": "1",
    }
    result = subprocess.run(
        ["bash", "scripts/ops/online_readiness_supervisor_v1.sh"],
        env={**__import__("os").environ, **env},
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
        timeout=60,
    )
    assert result.returncode == 0
    meta_path = tmp_path / "out" / "supervisor_meta.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text())
    assert "version" in meta
    assert meta.get("version") == "p81_supervisor_meta_v1"
    assert "last_tick" in meta
    assert meta.get("last_tick") is not None


def test_p81_mode_live_exits_not_allowed(tmp_path: Path) -> None:
    """MODE=live -> exit 3 (not_allowed)."""
    env = {
        "MODE": "live",
        "OUT_DIR": str(tmp_path / "out"),
        "PIDFILE": str(tmp_path / "p81.pid"),
        "LOCKFILE": str(tmp_path / "p81.lock"),
    }
    result = subprocess.run(
        ["bash", "scripts/ops/online_readiness_supervisor_v1.sh"],
        env={**__import__("os").environ, **env},
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 3
    assert "live/record blocked" in result.stderr
