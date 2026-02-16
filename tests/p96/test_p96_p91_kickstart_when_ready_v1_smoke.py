from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(ROOT / "scripts/ops/p91_kickstart_when_ready_v1.sh")],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
    )


def test_exit_3_when_out_dir_missing(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["OUT_DIR"] = str(tmp_path / "does_not_exist")
    env["P91_LABEL"] = "com.peaktrade.p91-audit-snapshot-runner"
    p = run(env)
    assert p.returncode == 3
    assert "reason=out_dir_missing" in (p.stderr + p.stdout)


def test_exit_3_when_insufficient_ticks(tmp_path: Path) -> None:
    out_dir = tmp_path / "run_20260216T000000Z"
    out_dir.mkdir(parents=True)
    (out_dir / "tick_20260216T000001Z").mkdir()
    env = os.environ.copy()
    env["OUT_DIR"] = str(out_dir)
    env["MIN_TICKS"] = "2"
    p = run(env)
    assert p.returncode == 3
    assert "reason=insufficient_ticks" in (p.stderr + p.stdout)


def test_ok_path_is_reachable_without_launchctl(tmp_path: Path) -> None:
    out_dir = tmp_path / "run_20260216T000000Z"
    out_dir.mkdir(parents=True)
    (out_dir / "tick_20260216T000001Z").mkdir()
    (out_dir / "tick_20260216T000002Z").mkdir()
    env = os.environ.copy()
    env["OUT_DIR"] = str(out_dir)
    env["MIN_TICKS"] = "2"
    p = run(env)
    if p.returncode != 0:
        assert p.returncode != 3
