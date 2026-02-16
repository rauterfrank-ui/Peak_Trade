from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_p93_smoke(tmp_path: Path) -> None:
    # Minimal smoke: script runs and produces pin + bundle in a temp OUT_DIR
    repo = Path(__file__).resolve()
    while repo.name != "Peak_Trade" and repo.parent != repo:
        repo = repo.parent
    assert repo.name == "Peak_Trade"

    out_dir = tmp_path / "supervisor_run"
    (out_dir / "tick_20260216T000000Z" / "p76").mkdir(parents=True)
    (out_dir / "tick_20260216T000000Z" / "p76" / "P76_RESULT.txt").write_text(
        "P76_READY mode=shadow\n"
    )

    env = os.environ.copy()
    env["OUT_DIR"] = str(out_dir)
    env["TS_OVERRIDE"] = "20990101T000000Z"
    env["EVI_OVERRIDE"] = str(tmp_path / "p93_evi")

    p = subprocess.run(
        ["bash", "scripts/ops/p93_online_readiness_status_dashboard_v1.sh"],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert p.returncode == 0, p.stderr
    assert "P93_OK" in p.stdout

    evi = Path(env["EVI_OVERRIDE"])
    assert (evi / "manifest.json").exists()
    assert (evi / "SHA256SUMS.txt").exists()

    pin = repo / "out" / "ops" / "P93_STATUS_DASHBOARD_DONE_20990101T000000Z.txt"
    assert pin.exists()
    assert (
        repo / "out" / "ops" / "P93_STATUS_DASHBOARD_DONE_20990101T000000Z.txt.sha256"
    ).exists()
