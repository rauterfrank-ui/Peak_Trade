from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _run(cmd: list[str], env: dict[str, str], cwd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, env=env, cwd=cwd, text=True, capture_output=True, check=False)


def test_p94_retention_keeps_last_n(tmp_path: Path) -> None:
    repo = Path(__file__).resolve()
    while repo.name != "Peak_Trade" and repo.parent != repo:
        repo = repo.parent
    assert repo.name == "Peak_Trade"

    ops = tmp_path / "ops"
    ops.mkdir()

    # create 5 fake snapshots
    tss = [
        "20260216T090000Z",
        "20260216T090500Z",
        "20260216T091000Z",
        "20260216T091500Z",
        "20260216T092000Z",
    ]
    for ts in tss:
        d = ops / f"p93_online_readiness_status_{ts}"
        d.mkdir()
        (ops / f"p93_online_readiness_status_{ts}.bundle.tgz").write_text("x")
        (ops / f"p93_online_readiness_status_{ts}.bundle.tgz.sha256").write_text("x")
        (ops / f"P93_STATUS_DASHBOARD_DONE_{ts}.txt").write_text("x")
        (ops / f"P93_STATUS_DASHBOARD_DONE_{ts}.txt.sha256").write_text("x")

    env = os.environ.copy()
    env["KEEP_N"] = "2"
    env["OPS_DIR"] = str(ops)

    p = _run(
        ["bash", "scripts/ops/p94_p93_status_dashboard_retention_v1.sh"],
        env,
        cwd=str(repo),
    )
    assert p.returncode == 0, (p.stdout, p.stderr)

    remaining_dirs = sorted(
        [
            p.name
            for p in ops.iterdir()
            if p.is_dir() and p.name.startswith("p93_online_readiness_status_")
        ]
    )
    assert remaining_dirs == [
        f"p93_online_readiness_status_{tss[-2]}",
        f"p93_online_readiness_status_{tss[-1]}",
    ]

    # matching pins/bundles also remain for last 2 only
    for ts in tss[:-2]:
        assert not (ops / f"p93_online_readiness_status_{ts}.bundle.tgz").exists()
        assert not (ops / f"P93_STATUS_DASHBOARD_DONE_{ts}.txt").exists()
