"""CLI contract tests for scripts/ops/check_no_black_enforcement.sh (isolated fixture repos)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_SOURCE_SCRIPT = ROOT / "scripts" / "ops" / "check_no_black_enforcement.sh"


def _install_script(fake_repo: Path) -> Path:
    """Copy the guard script under fake_repo so REPO_ROOT resolves to fake_repo."""
    dest = fake_repo / "scripts" / "ops" / "check_no_black_enforcement.sh"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(_SOURCE_SCRIPT, dest)
    dest.chmod(0o755)
    return dest


def _run(script: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_passes_when_only_guard_script_present(tmp_path: Path) -> None:
    script = _install_script(tmp_path)
    p = _run(script)
    assert p.returncode == 0
    assert "No black enforcement found" in p.stdout
    assert "ruff format --check" in p.stdout
    assert p.stderr == ""


@pytest.mark.parametrize(
    "snippet,path_parts",
    [
        ("black --check", (".github", "workflows", "ci.yml")),
        ("python -m black --check", ("scripts", "bad_tooling.sh")),
    ],
)
def test_fails_when_forbidden_pattern_found(
    tmp_path: Path, snippet: str, path_parts: tuple[str, ...]
) -> None:
    _install_script(tmp_path)
    target = tmp_path.joinpath(*path_parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"run: {snippet}\n", encoding="utf-8")
    script = tmp_path / "scripts" / "ops" / "check_no_black_enforcement.sh"
    p = _run(script)
    assert p.returncode == 1
    assert "FAIL: Found black enforcement" in p.stdout
    assert snippet in p.stdout
    assert p.stderr == ""
