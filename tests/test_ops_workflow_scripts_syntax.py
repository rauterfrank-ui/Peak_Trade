from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


SCRIPTS = [
    Path("scripts/post_merge_workflow_pr203.sh"),
    Path("scripts/quick_pr_merge.sh"),
    Path("scripts/post_merge_workflow.sh"),
    Path("scripts/finalize_workflow_docs_pr.sh"),
    Path("scripts/workflows/pr_merge_with_ops_audit.sh"),
    Path("scripts/ops/run_ops_convenience_pack_pr.sh"),
    Path("scripts/ops/verify_format_only_pr.sh"),
    Path("scripts/git_push_and_pr.sh"),
]


def _has_bash() -> bool:
    return shutil.which("bash") is not None


@pytest.mark.parametrize("script_path", SCRIPTS)
def test_ops_workflow_script_exists(script_path: Path) -> None:
    assert script_path.exists(), f"Missing workflow script: {script_path}"


@pytest.mark.parametrize("script_path", SCRIPTS)
def test_ops_workflow_script_bash_syntax_ok(script_path: Path) -> None:
    if not _has_bash():
        pytest.skip("bash not available on this system")
    # Syntax check only (no execution)
    proc = subprocess.run(
        ["bash", "-n", str(script_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, (
        f"Bash syntax error in {script_path}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}\n"
    )
