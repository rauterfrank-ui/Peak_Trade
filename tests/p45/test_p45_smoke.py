"""P45 smoke tests."""

from __future__ import annotations

import subprocess
from pathlib import Path


def test_p45_smoke() -> None:
    assert True


def test_pr_ops_v1_bash_n() -> None:
    """pr_ops_v1.sh passes bash -n."""
    repo = Path(__file__).resolve().parents[2]
    script = repo / "scripts/ops/pr_ops_v1.sh"
    assert script.exists()
    subprocess.check_call(["bash", "-n", str(script)])


def test_pr_ops_v1_help() -> None:
    """pr_ops_v1.sh --help exits 1 and prints usage."""
    repo = Path(__file__).resolve().parents[2]
    script = repo / "scripts/ops/pr_ops_v1.sh"
    result = subprocess.run(
        [str(script), "--help"],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Usage:" in result.stdout or "Usage:" in result.stderr
