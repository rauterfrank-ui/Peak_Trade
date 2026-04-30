"""CLI contract tests for scripts/ops/check_run_helpers_adoption.sh (fixture repo + script copy)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_SOURCE_SCRIPT = ROOT / "scripts" / "ops" / "check_run_helpers_adoption.sh"


def _install_script(fake_repo: Path) -> Path:
    """Copy the guard script under fake_repo so ROOT resolves to fake_repo."""
    dest = fake_repo / "scripts" / "ops" / "check_run_helpers_adoption.sh"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(_SOURCE_SCRIPT, dest)
    dest.chmod(0o755)
    return dest


def _curated_paths(fake_repo: Path) -> tuple[Path, Path]:
    ops = fake_repo / "scripts" / "ops"
    return ops / "pr_inventory_full.sh", ops / "label_merge_log_prs.sh"


def _write_curated_ok(fake_repo: Path) -> None:
    a, b = _curated_paths(fake_repo)
    ops = fake_repo / "scripts" / "ops"
    ops.mkdir(parents=True, exist_ok=True)
    snippet = '# shellcheck source=run_helpers.sh\nsource "${SCRIPT_DIR}/run_helpers.sh"\n'
    a.write_text(snippet, encoding="utf-8")
    b.write_text(snippet, encoding="utf-8")


def _run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_passes_curated_when_helpers_referenced(tmp_path: Path) -> None:
    _install_script(tmp_path)
    _write_curated_ok(tmp_path)
    script = tmp_path / "scripts" / "ops" / "check_run_helpers_adoption.sh"
    p = _run(script)
    assert p.returncode == 0
    assert "🎉 Adoption guard OK." in p.stdout
    assert "helpers referenced:" in p.stdout
    assert p.stderr == ""


def test_fails_curated_when_helpers_missing(tmp_path: Path) -> None:
    _install_script(tmp_path)
    a, b = _curated_paths(tmp_path)
    a.parent.mkdir(parents=True, exist_ok=True)
    a.write_text("# no helpers here\n", encoding="utf-8")
    b.write_text(
        '# shellcheck source=run_helpers.sh\nsource "${SCRIPT_DIR}/run_helpers.sh"\n',
        encoding="utf-8",
    )
    script = tmp_path / "scripts" / "ops" / "check_run_helpers_adoption.sh"
    p = _run(script)
    assert p.returncode == 1
    assert "❌ missing helpers include (run_helpers.sh):" in p.stdout
    assert "❌ Adoption guard failed." in p.stdout
    assert p.stderr == ""


def test_fails_curated_when_expected_file_absent(tmp_path: Path) -> None:
    _install_script(tmp_path)
    a, _b = _curated_paths(tmp_path)
    a.parent.mkdir(parents=True, exist_ok=True)
    a.write_text(
        '# shellcheck source=run_helpers.sh\nsource "${SCRIPT_DIR}/run_helpers.sh"\n',
        encoding="utf-8",
    )
    script = tmp_path / "scripts" / "ops" / "check_run_helpers_adoption.sh"
    p = _run(script)
    assert p.returncode == 1
    assert "⚠️  missing file:" in p.stdout
    assert "label_merge_log_prs.sh" in p.stdout
    assert p.stderr == ""


def test_warn_only_exits_zero_when_curated_bad(tmp_path: Path) -> None:
    _install_script(tmp_path)
    a, b = _curated_paths(tmp_path)
    a.parent.mkdir(parents=True, exist_ok=True)
    a.write_text("# bad\n", encoding="utf-8")
    b.write_text("# bad\n", encoding="utf-8")
    script = tmp_path / "scripts" / "ops" / "check_run_helpers_adoption.sh"
    p = _run(script, "--warn-only")
    assert p.returncode == 0
    assert "WARN-ONLY: adoption issues found" in p.stdout
    assert p.stderr == ""


@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_help_exits_zero(tmp_path: Path, flag: str) -> None:
    script = _install_script(tmp_path)
    p = _run(script, flag)
    assert p.returncode == 0
    assert "Usage:" in p.stdout
    assert p.stderr == ""


def test_all_ops_passes_when_only_guard_script_in_ops(tmp_path: Path) -> None:
    """Sole *.sh is the guard copy; its source mentions run_helpers.sh (HELPERS=… and messages)."""
    script = _install_script(tmp_path)
    p = _run(script, "--all-ops")
    assert p.returncode == 0
    assert "🎉 Adoption guard OK." in p.stdout
    assert "helpers referenced:" in p.stdout
    assert "check_run_helpers_adoption.sh" in p.stdout
    assert p.stderr == ""


def test_all_ops_fails_when_script_missing_helpers(tmp_path: Path) -> None:
    _install_script(tmp_path)
    ops = tmp_path / "scripts" / "ops"
    (ops / "bad.sh").write_text("# no run_helpers include\n", encoding="utf-8")
    script = ops / "check_run_helpers_adoption.sh"
    p = _run(script, "--all-ops")
    assert p.returncode == 1
    assert "bad.sh" in p.stdout
    assert "❌ Adoption guard failed." in p.stdout
    assert p.stderr == ""
