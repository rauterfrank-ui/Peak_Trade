"""P80 smoke tests: supervisor stop + idempotent start."""

import subprocess
from pathlib import Path

import pytest


def test_p80_smoke() -> None:
    assert True


def test_p80_stop_mode_no_pidfile(tmp_path: Path) -> None:
    """STOP=1 with no pidfile -> P80_STOP_OK (already absent)."""
    env = {
        "MODE": "shadow",
        "OUT_DIR": str(tmp_path / "out"),
        "PIDFILE": str(tmp_path / "nonexistent.pid"),
        "STOP": "1",
    }
    result = subprocess.run(
        ["bash", "scripts/ops/online_readiness_supervisor_v1.sh"],
        env={**__import__("os").environ, **env},
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 0
    assert "P80_STOP_OK" in result.stdout


def test_p80_stop_mode_stale_pidfile(tmp_path: Path) -> None:
    """STOP=1 with stale pidfile (dead pid) -> P80_STOP_OK."""
    pidfile = tmp_path / "stale.pid"
    pidfile.write_text("999999")  # non-existent pid
    env = {
        "MODE": "shadow",
        "OUT_DIR": str(tmp_path / "out"),
        "PIDFILE": str(pidfile),
        "STOP": "1",
    }
    result = subprocess.run(
        ["bash", "scripts/ops/online_readiness_supervisor_v1.sh"],
        env={**__import__("os").environ, **env},
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 0
    assert "P80_STOP_OK" in result.stdout
    assert not pidfile.exists()


def test_p80_double_start_refused(tmp_path: Path) -> None:
    """Pidfile with live pid (self) -> refuse start, exit 3 (not_allowed)."""
    root = Path(__file__).resolve().parents[2]
    out_dir = root / "out" / "ops" / f"p80_test_double_{tmp_path.name}"
    out_dir.mkdir(parents=True, exist_ok=True)
    pidfile = tmp_path / "live.pid"
    pidfile.write_text(str(__import__("os").getpid()))
    env = {
        "MODE": "shadow",
        "OUT_DIR": str(out_dir),
        "SUPERVISOR_ENABLE": "YES",
        "PIDFILE": str(pidfile),
        "LOCKFILE": str(tmp_path / "test.lock"),
    }
    result = subprocess.run(
        ["bash", "scripts/ops/online_readiness_supervisor_v1.sh"],
        env={**__import__("os").environ, **env},
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 3
    assert "already running" in result.stderr


def test_p80_smoke_one_tick(tmp_path: Path) -> None:
    """INTERVAL=0 ITERATIONS=1 runs one tick and exits."""
    root = Path(__file__).resolve().parents[2]
    out_dir = root / "out" / "ops" / f"p80_test_tick_{tmp_path.name}"
    out_dir.mkdir(parents=True, exist_ok=True)
    pidfile = tmp_path / "p80_test.pid"
    env = {
        "MODE": "shadow",
        "OUT_DIR": str(out_dir),
        "SUPERVISOR_ENABLE": "YES",
        "PIDFILE": str(pidfile),
        "LOCKFILE": str(tmp_path / "test.lock"),
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
    tick_dirs = list(out_dir.glob("tick_*"))
    assert len(tick_dirs) >= 1
