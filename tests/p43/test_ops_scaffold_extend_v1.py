"""Integration test for p41 generator --with-pr-ops flag."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def test_generator_with_pr_ops_creates_scripts(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[2]
    script = repo / "scripts/ops/p41_kickoff_scaffold_v1.sh"

    ts = "20990101T000000Z"
    p = "p99"
    topic = "tmp-pr-ops"
    env = os.environ.copy()
    env["PT_ALLOW_DIRTY"] = "YES"

    subprocess.check_call(
        [str(script), p, topic, "--ts", ts, "--no-branch", "--with-pr-ops"],
        cwd=str(repo),
        env=env,
    )

    watch = repo / f"scripts/ops/{p}_pr_watch.sh"
    closeout = repo / f"scripts/ops/{p}_oneshot_closeout.sh"
    req = repo / f"scripts/ops/{p}_required_checks_snapshot.sh"
    assert watch.exists()
    assert closeout.exists()
    assert req.exists()

    subprocess.check_call(["bash", "-n", str(watch)], cwd=str(repo))
    subprocess.check_call(["bash", "-n", str(closeout)], cwd=str(repo))
    subprocess.check_call(["bash", "-n", str(req)], cwd=str(repo))

    outdir = repo / f"out/ops/{p}_{topic}_{ts}"
    if outdir.exists():
        shutil.rmtree(outdir, ignore_errors=True)
