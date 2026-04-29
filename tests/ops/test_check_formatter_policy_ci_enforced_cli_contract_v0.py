"""CLI contract tests for scripts/ops/check_formatter_policy_ci_enforced.sh."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "ops" / "check_formatter_policy_ci_enforced.sh"

_WORKFLOW_REL = Path(".github/workflows/lint_gate.yml")
_NEEDLE = "scripts/ops/check_no_black_enforcement.sh"


def _write_workflow(root: Path, body: str) -> None:
    wf = root / _WORKFLOW_REL
    wf.parent.mkdir(parents=True, exist_ok=True)
    wf.write_text(body, encoding="utf-8")


def _run_in(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(_SCRIPT)],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )


def test_missing_workflow_exits_1(tmp_path: Path) -> None:
    p = _run_in(tmp_path)
    assert p.returncode == 1
    assert "Workflow not found" in p.stdout
    assert _WORKFLOW_REL.as_posix() in p.stdout
    assert p.stderr == ""


def test_workflow_without_needle_exits_1(tmp_path: Path) -> None:
    _write_workflow(tmp_path, "name: lint\njobs: {}\n")
    p = _run_in(tmp_path)
    assert p.returncode == 1
    assert "CI enforcement missing" in p.stdout
    assert _NEEDLE in p.stdout
    assert p.stderr == ""


def test_workflow_with_needle_exits_0(tmp_path: Path) -> None:
    _write_workflow(
        tmp_path,
        f"name: lint\njobs:\n  x:\n    run: bash {_NEEDLE}\n",
    )
    p = _run_in(tmp_path)
    assert p.returncode == 0
    assert "PASS" in p.stdout
    assert _NEEDLE in p.stdout
    assert p.stderr == ""
