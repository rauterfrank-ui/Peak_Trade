"""CLI contract tests for scripts/ops/check_ops_docs_navigation.sh (fixture repo + copied helper)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SOURCE_SH = ROOT / "scripts" / "ops" / "check_ops_docs_navigation.sh"
_SOURCE_PY = ROOT / "scripts" / "ops" / "check_markdown_links.py"


def _install_guard_and_helper(fake_repo: Path) -> Path:
    """Copy shell wrapper + check_markdown_links.py so ROOT_DIR resolves to fake_repo."""
    ops = fake_repo / "scripts" / "ops"
    ops.mkdir(parents=True, exist_ok=True)
    dest_sh = ops / "check_ops_docs_navigation.sh"
    shutil.copyfile(_SOURCE_SH, dest_sh)
    shutil.copyfile(_SOURCE_PY, ops / "check_markdown_links.py")
    dest_sh.chmod(0o755)
    return dest_sh


def _write_minimal_pass_tree(fake_repo: Path) -> None:
    (fake_repo / "docs" / "ops").mkdir(parents=True, exist_ok=True)
    (fake_repo / "README.md").write_text("# Fixture README\n\nNo links.\n", encoding="utf-8")
    (fake_repo / "docs" / "PEAK_TRADE_STATUS_OVERVIEW.md").write_text(
        "# Status\n\nSee [readme](../README.md).\n",
        encoding="utf-8",
    )


def _run(script: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_passes_when_internal_links_resolve(tmp_path: Path) -> None:
    script = _install_guard_and_helper(tmp_path)
    _write_minimal_pass_tree(tmp_path)
    p = _run(script)
    assert p.returncode == 0
    assert "✅ Markdown link check: OK" in p.stdout
    assert p.stderr == ""


def test_fails_when_readme_points_to_missing_file(tmp_path: Path) -> None:
    script = _install_guard_and_helper(tmp_path)
    (tmp_path / "docs" / "ops").mkdir(parents=True, exist_ok=True)
    (tmp_path / "README.md").write_text(
        "# Bad\n\nLink to [missing](./THIS_FILE_DOES_NOT_EXIST.md).\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "PEAK_TRADE_STATUS_OVERVIEW.md").write_text("# Ok\n", encoding="utf-8")
    p = _run(script)
    assert p.returncode == 1
    assert "❌ Markdown link check: BROKEN LINKS FOUND" in p.stdout
    assert "THIS_FILE_DOES_NOT_EXIST" in p.stdout
    assert p.stderr == ""


def test_fails_when_anchor_missing_in_target(tmp_path: Path) -> None:
    script = _install_guard_and_helper(tmp_path)
    (tmp_path / "docs" / "ops").mkdir(parents=True, exist_ok=True)
    (tmp_path / "README.md").write_text("# Root\n\nBody.\n", encoding="utf-8")
    (tmp_path / "docs" / "PEAK_TRADE_STATUS_OVERVIEW.md").write_text(
        "# Status\n\nJump to [no such anchor](../README.md#this-heading-is-not-there).\n",
        encoding="utf-8",
    )
    p = _run(script)
    assert p.returncode == 1
    assert "anchor '#this-heading-is-not-there'" in p.stdout or "not found" in p.stdout
    assert p.stderr == ""


def test_fails_when_broken_link_under_docs_ops(tmp_path: Path) -> None:
    script = _install_guard_and_helper(tmp_path)
    ops = tmp_path / "docs" / "ops"
    ops.mkdir(parents=True, exist_ok=True)
    (tmp_path / "README.md").write_text("# R\n", encoding="utf-8")
    (tmp_path / "docs" / "PEAK_TRADE_STATUS_OVERVIEW.md").write_text("# S\n", encoding="utf-8")
    (ops / "note.md").write_text("[x](../NOPE_MISSING.md)\n", encoding="utf-8")
    p = _run(script)
    assert p.returncode == 1
    assert "NOPE_MISSING" in p.stdout
    assert p.stderr == ""
