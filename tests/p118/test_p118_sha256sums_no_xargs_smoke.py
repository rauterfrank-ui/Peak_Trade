from __future__ import annotations

import os
from pathlib import Path
import subprocess


def test_sha256sums_no_xargs_smoke(tmp_path: Path) -> None:
    # Arrange
    d = tmp_path / "evi"
    d.mkdir()
    (d / "a.txt").write_text("a")
    (d / "b.txt").write_text("b")
    out = d / "SHA256SUMS.txt"

    repo_root = Path(os.getcwd())
    # Act: run from repo root so paths are relative to repo
    proc = subprocess.run(
        ["bash", "scripts/ops/sha256sums_no_xargs_v1.sh", str(d)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert out.exists()
    # Verify
    verify = subprocess.run(
        ["shasum", "-a", "256", "-c", str(out)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert verify.returncode == 0, verify.stderr
