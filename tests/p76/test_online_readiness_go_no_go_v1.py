"""P76: Online Readiness Go/No-Go v1 — exit code + evidence contract tests."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _run(env: dict[str, str], cwd: Path, *, clear_p76_vars: bool = False) -> subprocess.CompletedProcess[str]:
    base = os.environ.copy()
    if clear_p76_vars:
        for k in ("OUT_DIR", "RUN_ID", "OUT_DIR_OVERRIDE", "RUN_ID_OVERRIDE"):
            base.pop(k, None)
    return subprocess.run(
        ["bash", "scripts/ops/online_readiness_go_no_go_v1.sh"],
        cwd=str(cwd),
        env={**base, **env},
        text=True,
        capture_output=True,
        check=False,
    )


def test_p76_ready_exit_0(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    out_dir = tmp_path / "p76_ready"
    env = {
        "OUT_DIR_OVERRIDE": str(out_dir),
        "RUN_ID_OVERRIDE": "p76_test",
        "MODE_OVERRIDE": "shadow",
        "ITERATIONS_OVERRIDE": "1",
        "INTERVAL_OVERRIDE": "0",
        "PYTHONPATH": str(root),
    }
    proc = _run(env, root)
    assert proc.returncode == 0, f"rc={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
    assert "P76_READY" in proc.stdout
    assert (out_dir / "P76_RESULT.txt").exists()
    assert (out_dir / "ONLINE_READINESS_ENV.json").exists()
    assert "P76_READY" in (out_dir / "P76_RESULT.txt").read_text()


def test_p76_usage_exit_2() -> None:
    root = Path(__file__).resolve().parents[2]
    proc = _run({"PYTHONPATH": str(root)}, root, clear_p76_vars=True)
    assert proc.returncode == 2
    assert "ERR:" in proc.stderr or "ERR:" in proc.stdout
