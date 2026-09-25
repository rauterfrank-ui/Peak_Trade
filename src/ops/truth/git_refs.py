"""Git helpers for truth checks (three-dot diff vs base ref)."""

from __future__ import annotations

import subprocess
from pathlib import Path


def git_changed_files_three_dot(repo_root: Path, base: str) -> list[str]:
    """Paths changed on HEAD vs merge-base(base, HEAD) ... HEAD (three-dot)."""
    cmd = ["git", "-C", str(repo_root), "diff", "--name-only", f"{base}...HEAD"]
    cp = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if cp.returncode != 0:
        raise RuntimeError(
            f"git diff failed (exit {cp.returncode}).\n"
            f"cmd: {' '.join(cmd)}\n"
            f"stderr: {cp.stderr.strip() or '(empty)'}"
        )
    return [ln.strip() for ln in cp.stdout.splitlines() if ln.strip()]
