from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def test_sha256sums_no_xargs_smoke(tmp_path: Path) -> None:
    # Arrange: use dir INSIDE repo with RELATIVE path so sha256sums emits
    # repo-root-relative paths (find returns paths as given; style guard rejects absolute)
    repo_root = Path(__file__).resolve().parents[2]
    rel_d = Path("out") / "ops" / "_scratch" / f"p118_smoke_{tmp_path.name}"
    d = repo_root / rel_d
    d.mkdir(parents=True, exist_ok=True)
    try:
        (d / "a.txt").write_text("a")
        (d / "b.txt").write_text("b")
        out = d / "SHA256SUMS.txt"

        # Act: pass RELATIVE path so find emits relative paths
        proc = subprocess.run(
            ["bash", "scripts/ops/sha256sums_no_xargs_v1.sh", str(rel_d)],
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
    finally:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
