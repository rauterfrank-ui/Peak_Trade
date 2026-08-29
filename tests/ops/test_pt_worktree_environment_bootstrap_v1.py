"""Per-worktree Python environment bootstrap and isolation contract tests."""

from __future__ import annotations

import json
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.runtime.pt_python_runtime_contract_v1 import (
    EXIT_VENV_MISSING,
    validate_runtime,
)
from scripts.runtime.pt_worktree_environment_v1 import (
    EXIT_ENV_FINGERPRINT,
    EXIT_FOREIGN_SOURCE,
    EXIT_VENV_SYMLINK,
    REASON_ENV_FINGERPRINT_MALFORMED,
    REASON_ENV_FINGERPRINT_MISSING,
    REASON_ENV_FINGERPRINT_MISMATCH,
    REASON_FOREIGN_SOURCE_BINDING,
    REASON_ISOLATION_PASS,
    REASON_SOURCE_BINDING_MISSING,
    REASON_VENV_SYMLINK,
    fingerprint_path,
    validate_fingerprint,
    validate_worktree_environment,
    write_env_fingerprint,
)
from tests.ops.pt_isolated_venv_test_support_v1 import complete_isolated_test_venv

REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = REPO_ROOT / "scripts" / "pt"
BOOTSTRAP = REPO_ROOT / "scripts" / "pt-bootstrap"
CONTRACT_PY = REPO_ROOT / "scripts" / "runtime" / "pt_python_runtime_contract_v1.py"
ENV_PY = REPO_ROOT / "scripts" / "runtime" / "pt_worktree_environment_v1.py"


def _seed_checkout(tmp: Path) -> Path:
    (tmp / "scripts" / "runtime").mkdir(parents=True)
    shutil.copy2(LAUNCHER, tmp / "scripts" / "pt")
    shutil.copy2(BOOTSTRAP, tmp / "scripts" / "pt-bootstrap")
    (tmp / "scripts" / "pt").chmod(
        (tmp / "scripts" / "pt").stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )
    (tmp / "scripts" / "pt-bootstrap").chmod(
        (tmp / "scripts" / "pt-bootstrap").stat().st_mode
        | stat.S_IXUSR
        | stat.S_IXGRP
        | stat.S_IXOTH
    )
    shutil.copy2(CONTRACT_PY, tmp / "scripts" / "runtime" / "pt_python_runtime_contract_v1.py")
    shutil.copy2(ENV_PY, tmp / "scripts" / "runtime" / "pt_worktree_environment_v1.py")
    (tmp / "pyproject.toml").write_text(
        '[project]\nname = "peak_trade"\nrequires-python = ">=3.10"\n',
        encoding="utf-8",
    )
    (tmp / "uv.lock").write_text("peak-trade-test-lock\n", encoding="utf-8")
    return tmp


def _venv_python(repo: Path) -> Path:
    venv_python = repo / ".venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.symlink_to(Path(sys.executable).resolve())
    return venv_python


def test_missing_venv_pt_fail_closed_with_bootstrap_instruction(tmp_path: Path) -> None:
    repo = _seed_checkout(tmp_path / "repo")
    proc = subprocess.run(
        [str(repo / "scripts" / "pt"), "-c", "print('should-not-run')"],
        cwd=repo,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path / "home")},
        check=False,
    )
    assert proc.returncode == EXIT_VENV_MISSING
    assert "should-not-run" not in proc.stdout
    assert "./scripts/pt-bootstrap" in proc.stderr


def test_symlink_venv_pt_fail_closed(tmp_path: Path) -> None:
    repo = _seed_checkout(tmp_path / "repo")
    foreign = tmp_path / "foreign" / ".venv"
    foreign.mkdir(parents=True)
    (repo / ".venv").symlink_to(foreign)
    proc = subprocess.run(
        [str(repo / "scripts" / "pt"), "-c", "print('should-not-run')"],
        cwd=repo,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path / "home")},
        check=False,
    )
    assert proc.returncode == EXIT_VENV_SYMLINK
    assert "should-not-run" not in proc.stdout
    assert "foreign/shared/symlinked" in proc.stderr
    assert (repo / ".venv").is_symlink()


def test_symlink_venv_bootstrap_fail_closed_does_not_unlink(tmp_path: Path) -> None:
    repo = _seed_checkout(tmp_path / "repo")
    foreign = tmp_path / "foreign" / ".venv"
    foreign.mkdir(parents=True)
    (repo / ".venv").symlink_to(foreign)
    proc = subprocess.run(
        [str(repo / "scripts" / "pt-bootstrap")],
        cwd=repo,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path / "home")},
        check=False,
    )
    assert proc.returncode == EXIT_VENV_SYMLINK
    assert "will not unlink automatically" in proc.stderr
    assert (repo / ".venv").is_symlink()
    assert (repo / ".venv").exists()


def test_foreign_editable_binding_fail_closed(tmp_path: Path) -> None:
    repo = _seed_checkout(tmp_path / "repo")
    _venv_python(repo)
    complete_isolated_test_venv(repo)
    site = (
        repo
        / ".venv"
        / "lib"
        / f"python{sys.version_info.major}.{sys.version_info.minor}"
        / "site-packages"
    )
    (site / "__editable__.peak_trade-0.1.0.pth").write_text(
        f"{tmp_path / 'other' / 'src'}\n", encoding="utf-8"
    )
    result = validate_worktree_environment(repo, python_version=sys.version.split()[0])
    assert result.ok is False
    assert result.reason_code == REASON_FOREIGN_SOURCE_BINDING
    assert result.exit_code == EXIT_FOREIGN_SOURCE


def test_correct_local_env_accepted(tmp_path: Path) -> None:
    repo = _seed_checkout(tmp_path / "repo")
    _venv_python(repo)
    complete_isolated_test_venv(repo)
    result = validate_worktree_environment(repo, python_version=sys.version.split()[0])
    assert result.ok is True
    assert result.reason_code == REASON_ISOLATION_PASS
    proc = subprocess.run(
        [str(repo / "scripts" / "pt"), "-c", "print('ok')"],
        cwd=repo,
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": str(tmp_path / "home"),
            "PT_SKIP_TRADING_PREFLIGHT": "1",
        },
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "ok"


def test_uv_lock_hash_mismatch_fail_closed(tmp_path: Path) -> None:
    repo = _seed_checkout(tmp_path / "repo")
    _venv_python(repo)
    complete_isolated_test_venv(repo)
    (repo / "uv.lock").write_text("changed-lock\n", encoding="utf-8")
    result = validate_fingerprint(repo, python_version=sys.version.split()[0])
    assert result.ok is False
    assert result.reason_code == REASON_ENV_FINGERPRINT_MISMATCH
    assert result.exit_code == EXIT_ENV_FINGERPRINT


def test_pyproject_hash_mismatch_fail_closed(tmp_path: Path) -> None:
    repo = _seed_checkout(tmp_path / "repo")
    _venv_python(repo)
    complete_isolated_test_venv(repo)
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "peak_trade"\nrequires-python = ">=3.11"\n',
        encoding="utf-8",
    )
    result = validate_fingerprint(repo, python_version=sys.version.split()[0])
    assert result.ok is False
    assert result.reason_code == REASON_ENV_FINGERPRINT_MISMATCH


def test_missing_fingerprint_fail_closed(tmp_path: Path) -> None:
    repo = _seed_checkout(tmp_path / "repo")
    _venv_python(repo)
    complete_isolated_test_venv(repo)
    fingerprint_path(repo).unlink()
    result = validate_fingerprint(repo, python_version=sys.version.split()[0])
    assert result.ok is False
    assert result.reason_code == REASON_ENV_FINGERPRINT_MISSING


def test_malformed_fingerprint_fail_closed(tmp_path: Path) -> None:
    repo = _seed_checkout(tmp_path / "repo")
    _venv_python(repo)
    complete_isolated_test_venv(repo)
    fingerprint_path(repo).write_text("{not-json", encoding="utf-8")
    result = validate_fingerprint(repo, python_version=sys.version.split()[0])
    assert result.ok is False
    assert result.reason_code == REASON_ENV_FINGERPRINT_MALFORMED


def test_correct_fingerprint_accepted(tmp_path: Path) -> None:
    repo = _seed_checkout(tmp_path / "repo")
    _venv_python(repo)
    complete_isolated_test_venv(repo)
    path = write_env_fingerprint(repo, python_version=sys.version.split()[0])
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_id"] == "peak_trade_env_fingerprint_v1"
    result = validate_fingerprint(repo, python_version=sys.version.split()[0])
    assert result.ok is True


def test_virtual_env_does_not_override_correctness(tmp_path: Path) -> None:
    repo = _seed_checkout(tmp_path / "repo")
    _venv_python(repo)
    complete_isolated_test_venv(repo)
    foreign = tmp_path / "foreign-venv"
    foreign.mkdir()
    proc = subprocess.run(
        [str(repo / "scripts" / "pt"), "-c", "import os; print(os.environ.get('VIRTUAL_ENV', ''))"],
        cwd=repo,
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": str(tmp_path / "home"),
            "PT_SKIP_TRADING_PREFLIGHT": "1",
            "VIRTUAL_ENV": str(foreign),
        },
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == str(foreign)
    result = validate_worktree_environment(repo, python_version=sys.version.split()[0])
    assert result.ok is True
    assert result.source_binding == str(repo / "src")


def test_worktree_local_source_import_proven(tmp_path: Path) -> None:
    repo = _seed_checkout(tmp_path / "repo")
    proc_venv = subprocess.run(
        [sys.executable, "-m", "venv", str(repo / ".venv")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc_venv.returncode == 0, proc_venv.stderr
    complete_isolated_test_venv(repo)
    pkg = repo / "src" / "ops" / "section_marker"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("MARKER = 'feature-worktree'\n", encoding="utf-8")
    proc = subprocess.run(
        [
            str(repo / "scripts" / "pt"),
            "-c",
            "import ops.section_marker as m; print(m.__file__); print(m.MARKER)",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": str(tmp_path / "home"),
            "PT_SKIP_TRADING_PREFLIGHT": "1",
        },
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    assert str(pkg / "__init__.py") in lines[0]
    assert lines[1] == "feature-worktree"


def test_source_binding_missing_fail_closed(tmp_path: Path) -> None:
    repo = _seed_checkout(tmp_path / "repo")
    _venv_python(repo)
    (repo / "uv.lock").write_text("peak-trade-test-lock\n", encoding="utf-8")
    write_env_fingerprint(repo, python_version=sys.version.split()[0])
    result = validate_worktree_environment(repo, python_version=sys.version.split()[0])
    assert result.ok is False
    assert result.reason_code == REASON_SOURCE_BINDING_MISSING


def test_validate_runtime_rejects_symlink(tmp_path: Path) -> None:
    repo = _seed_checkout(tmp_path / "repo")
    foreign = tmp_path / "foreign" / ".venv"
    foreign.mkdir(parents=True)
    (repo / ".venv").symlink_to(foreign)
    result = validate_runtime(
        repo_root=repo,
        require_trading_import=False,
        check_running_identity=False,
    )
    assert result.ok is False
    assert result.reason_code == REASON_VENV_SYMLINK


def test_gitignore_still_ignores_venv_directory_only() -> None:
    text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".venv/" in text
    lines = [line.strip() for line in text.splitlines() if line.strip() == ".venv"]
    assert lines == []


@pytest.mark.skipif(
    not (REPO_ROOT / ".venv" / "bin" / "python").is_file(),
    reason="no local .venv",
)
def test_repo_venv_is_not_symlink_when_present() -> None:
    venv = REPO_ROOT / ".venv"
    if venv.exists():
        assert venv.is_symlink() is False
        assert venv.is_dir() is True
