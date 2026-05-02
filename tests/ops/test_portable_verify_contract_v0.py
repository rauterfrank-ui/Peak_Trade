"""Contract tests for scripts/ops/portable_verify.sh.

These tests execute the shell wrapper only inside temporary fixture repos.
They never run against the real repository, never touch Live/Testnet paths,
and stub ruff/pytest when command execution is required.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "ops" / "portable_verify.sh"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _init_fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    (repo / "src").mkdir()
    (repo / "tests").mkdir()
    (repo / "scripts").mkdir()
    (repo / "tests" / "test_example.py").write_text(
        "def test_example():\n    assert True\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=fixture@example.com",
            "-c",
            "user.name=Fixture",
            "commit",
            "-m",
            "init",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return repo


def _stub_path(tmp_path: Path, *, pytest_exit: int = 0) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    _write_executable(
        bin_dir / "ruff",
        """#!/usr/bin/env bash
set -euo pipefail
echo "stub ruff $*"
exit 0
""",
    )

    _write_executable(
        bin_dir / "python3",
        f"""#!/usr/bin/env bash
set -euo pipefail
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "pytest" ]]; then
  echo "stub pytest $*"
  exit {pytest_exit}
fi
exec {shutil.which("python3")!r} "$@"
""",
    )

    return bin_dir


def test_portable_verify_script_exists_and_is_bash() -> None:
    assert SCRIPT.exists()
    text = SCRIPT.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in text


def test_portable_verify_requires_git_repository(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PATH"] = f"{_stub_path(tmp_path)}:{env['PATH']}"

    result = subprocess.run(
        ["bash", str(SCRIPT), "--no-ruff"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "not a git repository" in combined.lower() or "git rev-parse" in combined.lower()


def test_portable_verify_runs_pytest_with_no_ruff_inside_tmp_repo(tmp_path: Path) -> None:
    repo = _init_fixture_repo(tmp_path)
    env = os.environ.copy()
    env["PATH"] = f"{_stub_path(tmp_path)}:{env['PATH']}"

    result = subprocess.run(
        ["bash", str(SCRIPT), "--no-ruff", "tests/test_example.py"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "stub pytest -m pytest tests/test_example.py" in result.stdout
    assert "stub ruff" not in result.stdout
    assert (
        subprocess.run(
            ["git", "status", "--short"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        == ""
    )


def test_portable_verify_runs_ruff_format_check_by_default(tmp_path: Path) -> None:
    repo = _init_fixture_repo(tmp_path)
    env = os.environ.copy()
    env["PATH"] = f"{_stub_path(tmp_path)}:{env['PATH']}"

    result = subprocess.run(
        ["bash", str(SCRIPT), "tests/test_example.py"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "stub ruff format --check src tests scripts" in result.stdout
    assert "stub pytest -m pytest tests/test_example.py" in result.stdout


def test_portable_verify_fix_mode_uses_ruff_format_without_check(tmp_path: Path) -> None:
    repo = _init_fixture_repo(tmp_path)
    env = os.environ.copy()
    env["PATH"] = f"{_stub_path(tmp_path)}:{env['PATH']}"

    result = subprocess.run(
        ["bash", str(SCRIPT), "--fix", "tests/test_example.py"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "stub ruff format src tests scripts" in result.stdout
    assert "stub ruff format --check" not in result.stdout


def test_portable_verify_propagates_pytest_failure(tmp_path: Path) -> None:
    repo = _init_fixture_repo(tmp_path)
    env = os.environ.copy()
    env["PATH"] = f"{_stub_path(tmp_path, pytest_exit=7)}:{env['PATH']}"

    result = subprocess.run(
        ["bash", str(SCRIPT), "--no-ruff", "tests/test_example.py"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 7
    assert "stub pytest -m pytest tests/test_example.py" in result.stdout
