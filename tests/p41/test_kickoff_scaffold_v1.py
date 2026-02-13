from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_kickoff_scaffold_creates_expected_files(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[2]
    script = repo / "scripts" / "ops" / "p41_kickoff_scaffold_v1.sh"
    assert script.exists()

    env = os.environ.copy()
    env["PT_ALLOW_DIRTY"] = "YES"  # test should not depend on git cleanliness
    ts = "20990101T000000Z"
    phase = "p41"
    slug = "scaffold-test"

    subprocess.check_call(
        ["bash", str(script), phase, slug, "--no-branch", "--ts", ts],
        cwd=str(repo),
        env=env,
    )

    ops_dir = repo / "out" / "ops" / f"{phase}_{slug}_{ts}"
    assert ops_dir.exists()

    assert (ops_dir / "P41_BASELINE.txt").exists()
    assert (ops_dir / "P41_TASK.md").exists()
    assert (ops_dir / "P41_WORKLOG.ndjson").exists()
    assert (ops_dir / "p41_worklog_append.sh").exists()

    assert (repo / "docs" / "analysis" / phase / "README.md").exists()
    assert (repo / "src" / "ops" / phase).exists()
    assert (repo / "tests" / phase / f"test_{phase}_smoke.py").exists()
