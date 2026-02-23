"""Syntax test for fetch_prk_dashboard_artifacts.sh."""

import subprocess
from pathlib import Path


def test_fetcher_bash_syntax() -> None:
    repo = Path(__file__).resolve().parent.parent.parent
    r = subprocess.run(
        ["bash", "-n", str(repo / "scripts/ops/fetch_prk_dashboard_artifacts.sh")],
        capture_output=True,
        text=True,
        cwd=repo,
    )
    assert r.returncode == 0, r.stderr or r.stdout
