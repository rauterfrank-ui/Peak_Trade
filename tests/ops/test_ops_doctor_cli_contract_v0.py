"""CLI contract tests for scripts/ops/ops_doctor.sh (JSON + --repo-root)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "ops_doctor.sh"


def test_ops_doctor_json_reporoot_stdout_is_pure_json(tmp_path: Path) -> None:
    repo = tmp_path / "synthetic_repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    repo_resolved = str(repo.resolve())

    result = subprocess.run(
        [
            "bash",
            str(SCRIPT),
            "--json",
            "--repo-root",
            str(repo),
            "--check",
            "repo.git_root",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert "Peak_Trade Ops Doctor" not in result.stdout
    assert "Repository:" not in result.stdout

    payload = json.loads(result.stdout)
    assert payload["tool"] == "ops_inspector"
    assert payload["mode"] == "doctor"

    checks = payload["checks"]
    assert isinstance(checks, list)
    repo_git_root = next(c for c in checks if c["id"] == "repo.git_root")
    assert repo_git_root["status"] == "ok"
    assert repo_resolved in repo_git_root["message"] or any(
        repo_resolved in str(ev) for ev in repo_git_root.get("evidence", [])
    )
