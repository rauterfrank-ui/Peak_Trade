"""CLI contract tests for scripts/ops/check_optional_deps_leaks.sh (fixture repo + script copy)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SOURCE_SCRIPT = ROOT / "scripts" / "ops" / "check_optional_deps_leaks.sh"


def _install_script(fake_repo: Path) -> Path:
    """Copy the guard script under fake_repo so ROOT_DIR resolves to fake_repo."""
    dest = fake_repo / "scripts" / "ops" / "check_optional_deps_leaks.sh"
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


def test_passes_clean_tree_only_guard_script(tmp_path: Path) -> None:
    script = _install_script(tmp_path)
    p = _run(script)
    assert p.returncode == 0
    assert "PASS: optional deps leak scan (ccxt)" in p.stdout
    assert p.stderr == ""


def test_fails_when_ccxt_import_outside_allowlist(tmp_path: Path) -> None:
    _install_script(tmp_path)
    leak = tmp_path / "src" / "leak.py"
    leak.parent.mkdir(parents=True, exist_ok=True)
    leak.write_text("import ccxt\n", encoding="utf-8")
    script = tmp_path / "scripts" / "ops" / "check_optional_deps_leaks.sh"
    p = _run(script)
    assert p.returncode == 1
    assert "FAIL: optional dependency leak scan (ccxt)" in p.stdout
    assert "leak.py" in p.stdout
    assert p.stderr == ""


def test_passes_when_ccxt_only_under_tests_tree(tmp_path: Path) -> None:
    _install_script(tmp_path)
    t = tmp_path / "tests" / "stub.py"
    t.parent.mkdir(parents=True, exist_ok=True)
    t.write_text("from ccxt import base\n", encoding="utf-8")
    script = tmp_path / "scripts" / "ops" / "check_optional_deps_leaks.sh"
    p = _run(script)
    assert p.returncode == 0
    assert "PASS: optional deps leak scan (ccxt)" in p.stdout
    assert p.stderr == ""


def test_passes_when_ccxt_only_under_allowlisted_providers(tmp_path: Path) -> None:
    _install_script(tmp_path)
    ok_file = tmp_path / "src" / "data" / "providers" / "x.py"
    ok_file.parent.mkdir(parents=True, exist_ok=True)
    ok_file.write_text("import ccxt\n", encoding="utf-8")
    script = tmp_path / "scripts" / "ops" / "check_optional_deps_leaks.sh"
    p = _run(script)
    assert p.returncode == 0
    assert "PASS: optional deps leak scan (ccxt)" in p.stdout
    assert p.stderr == ""


def test_passes_when_ccxt_only_under_allowlisted_new_listings(tmp_path: Path) -> None:
    _install_script(tmp_path)
    ok_file = tmp_path / "src" / "research" / "new_listings" / "collector.py"
    ok_file.parent.mkdir(parents=True, exist_ok=True)
    ok_file.write_text("from ccxt import binance\n", encoding="utf-8")
    script = tmp_path / "scripts" / "ops" / "check_optional_deps_leaks.sh"
    p = _run(script)
    assert p.returncode == 0
    assert "PASS: optional deps leak scan (ccxt)" in p.stdout
    assert p.stderr == ""
