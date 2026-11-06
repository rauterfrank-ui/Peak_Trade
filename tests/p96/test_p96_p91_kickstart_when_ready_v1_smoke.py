from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/ops/p91_kickstart_when_ready_v1.sh"


def _run(env: dict) -> subprocess.CompletedProcess[str]:
    e = os.environ.copy()
    e.update(env)
    return subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=str(ROOT),
        env=e,
        capture_output=True,
        text=True,
    )


def test_exit_3_when_out_dir_missing(tmp_path: Path) -> None:
    out = _run({"OUT_DIR": str(tmp_path / "missing"), "MIN_TICKS": "2"})
    assert out.returncode == 3
    assert "out_dir_missing" in (out.stdout + out.stderr)


def test_exit_3_when_insufficient_ticks(tmp_path: Path) -> None:
    out_dir = tmp_path / "run_test"
    out_dir.mkdir()
    (out_dir / "tick_20260216T000000Z").mkdir()
    out = _run({"OUT_DIR": str(out_dir), "MIN_TICKS": "2"})
    assert out.returncode == 3
    assert "insufficient_ticks" in (out.stdout + out.stderr)


def test_ok_path_is_reachable_without_launchctl(tmp_path: Path) -> None:
    # Guard passes, but we do not require launchctl in tests.
    out_dir = tmp_path / "run_test"
    out_dir.mkdir()
    (out_dir / "tick_20260216T000000Z").mkdir()
    (out_dir / "tick_20260216T000001Z").mkdir()
    out = _run({"OUT_DIR": str(out_dir), "MIN_TICKS": "2", "DRY_RUN": "YES"})
    assert out.returncode == 0
    assert "P91_DRY_RUN_OK" in out.stdout
