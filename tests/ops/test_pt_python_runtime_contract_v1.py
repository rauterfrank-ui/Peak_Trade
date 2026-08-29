"""Deterministic Python runtime contract v1 tests (non-authorizing)."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from tests.ops.pt_isolated_venv_test_support_v1 import complete_isolated_test_venv
from scripts.runtime.pt_python_runtime_contract_v1 import (
    CANONICAL_INTERPRETER_REL,
    CONTRACT_VERSION,
    EXIT_INTERPRETER_MISMATCH,
    EXIT_PROVISIONED_REFUSED,
    EXIT_UNSUPPORTED_PYTHON,
    EXIT_VENV_MISSING,
    MODE_PROVISIONED,
    REASON_PASS,
    REASON_PROVISIONED_REFUSED,
    REASON_UNSUPPORTED_PYTHON,
    REASON_VENV_MISSING,
    REQUIRES_PYTHON,
    pyproject_requires_python,
    repo_root_from_this_file,
    validate_runtime,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = REPO_ROOT / "scripts" / "pt"
CONTRACT_PY = REPO_ROOT / "scripts" / "runtime" / "pt_python_runtime_contract_v1.py"
SYSTEM_CLT_PYTHON = Path("/Library/Developer/CommandLineTools/usr/bin/python3")
POISON_BIN_HINT = "/Library/Developer/CommandLineTools/usr/bin"


def _write_executable(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _seed_fake_repo(tmp: Path) -> Path:
    (tmp / "scripts" / "runtime").mkdir(parents=True)
    shutil.copy2(LAUNCHER, tmp / "scripts" / "pt")
    (tmp / "scripts" / "pt").chmod(
        (tmp / "scripts" / "pt").stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )
    shutil.copy2(CONTRACT_PY, tmp / "scripts" / "runtime" / "pt_python_runtime_contract_v1.py")
    shutil.copy2(
        REPO_ROOT / "scripts" / "runtime" / "pt_worktree_environment_v1.py",
        tmp / "scripts" / "runtime" / "pt_worktree_environment_v1.py",
    )
    (tmp / "pyproject.toml").write_text(
        '[project]\nname = "peak_trade_runtime_fixture"\nrequires-python = ">=3.10"\n',
        encoding="utf-8",
    )
    return tmp


def test_contract_floor_matches_pyproject() -> None:
    declared = pyproject_requires_python(REPO_ROOT)
    assert declared == REQUIRES_PYTHON
    assert CONTRACT_VERSION == "v1"


def test_repo_root_resolver_finds_launcher() -> None:
    root = repo_root_from_this_file(CONTRACT_PY)
    assert root == REPO_ROOT


def test_missing_venv_fails_closed(tmp_path: Path) -> None:
    repo = _seed_fake_repo(tmp_path)
    result = validate_runtime(
        repo_root=repo,
        require_trading_import=False,
        check_running_identity=False,
    )
    assert result.ok is False
    assert result.reason_code == REASON_VENV_MISSING
    assert result.exit_code == EXIT_VENV_MISSING


def test_launcher_missing_venv_fail_closed(tmp_path: Path) -> None:
    repo = _seed_fake_repo(tmp_path)
    proc = subprocess.run(
        [str(repo / "scripts" / "pt"), "-c", "print('should-not-run')"],
        cwd=repo / "scripts",
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path / "home")},
        check=False,
    )
    assert proc.returncode == EXIT_VENV_MISSING
    assert "should-not-run" not in proc.stdout
    assert "canonical interpreter missing" in proc.stderr


@pytest.mark.skipif(not SYSTEM_CLT_PYTHON.is_file(), reason="CLT python not present")
def test_unsupported_python_in_venv_slot_fails_closed(tmp_path: Path) -> None:
    repo = _seed_fake_repo(tmp_path)
    venv_python = repo / CANONICAL_INTERPRETER_REL
    venv_python.parent.mkdir(parents=True)
    venv_python.symlink_to(SYSTEM_CLT_PYTHON)
    proc = subprocess.run(
        [str(repo / "scripts" / "pt"), "-c", "print('should-not-run')"],
        cwd=repo,
        capture_output=True,
        text=True,
        env={"PATH": f"{POISON_BIN_HINT}:/usr/bin:/bin", "HOME": str(tmp_path / "home")},
        check=False,
    )
    assert proc.returncode == EXIT_UNSUPPORTED_PYTHON
    assert "should-not-run" not in proc.stdout


def test_path_poisoning_does_not_select_system_python(tmp_path: Path) -> None:
    if sys.version_info < (3, 10):
        pytest.skip("host interpreter below project floor")
    repo = _seed_fake_repo(tmp_path)
    venv_python = repo / CANONICAL_INTERPRETER_REL
    venv_python.parent.mkdir(parents=True)
    venv_python.symlink_to(Path(sys.executable).resolve())
    complete_isolated_test_venv(repo)
    poison = tmp_path / "poison" / "bin"
    poison.mkdir(parents=True)
    _write_executable(
        poison / "python3",
        "#!/bin/sh\necho POISONED >&2\nexit 99\n",
    )
    _write_executable(
        poison / "python",
        "#!/bin/sh\necho POISONED >&2\nexit 99\n",
    )
    proc = subprocess.run(
        [str(repo / "scripts" / "pt"), "-c", "import sys; print(sys.executable)"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={
            "PATH": f"{poison}:{POISON_BIN_HINT}:/usr/bin:/bin",
            "HOME": str(tmp_path / "home"),
            "PT_SKIP_TRADING_PREFLIGHT": "1",
        },
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "POISONED" not in proc.stderr
    assert str(venv_python.resolve()) in Path(proc.stdout.strip()).resolve().as_posix() or (
        Path(proc.stdout.strip()).resolve() == Path(sys.executable).resolve()
    )


def test_nested_cwd_and_no_activation(tmp_path: Path) -> None:
    if sys.version_info < (3, 10):
        pytest.skip("host interpreter below project floor")
    repo = _seed_fake_repo(tmp_path)
    nested = repo / "docs" / "runtime"
    nested.mkdir(parents=True)
    venv_python = repo / CANONICAL_INTERPRETER_REL
    venv_python.parent.mkdir(parents=True)
    venv_python.symlink_to(Path(sys.executable).resolve())
    complete_isolated_test_venv(repo)
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(tmp_path / "home"),
        "PT_SKIP_TRADING_PREFLIGHT": "1",
    }
    env.pop("VIRTUAL_ENV", None)
    proc = subprocess.run(
        [str(repo / "scripts" / "pt"), "-c", "import os, pathlib; print(pathlib.Path.cwd())"],
        cwd=nested,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert Path(proc.stdout.strip()).resolve() == repo.resolve()


def test_empty_path_still_uses_canonical_interpreter(tmp_path: Path) -> None:
    if sys.version_info < (3, 10):
        pytest.skip("host interpreter below project floor")
    repo = _seed_fake_repo(tmp_path)
    venv_python = repo / CANONICAL_INTERPRETER_REL
    venv_python.parent.mkdir(parents=True)
    venv_python.symlink_to(Path(sys.executable).resolve())
    complete_isolated_test_venv(repo)
    proc = subprocess.run(
        [str(repo / "scripts" / "pt"), "-c", "print('ok')"],
        cwd=repo,
        capture_output=True,
        text=True,
        env={"PATH": "", "HOME": str(tmp_path / "home"), "PT_SKIP_TRADING_PREFLIGHT": "1"},
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "ok"


def test_direct_contract_module_on_path_python_fails_identity() -> None:
    if not (REPO_ROOT / CANONICAL_INTERPRETER_REL).is_file():
        pytest.skip("worktree has no provisioned .venv")
    proc = subprocess.run(
        [sys.executable, str(CONTRACT_PY), "validate"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={
            "PATH": f"{POISON_BIN_HINT}:/usr/bin:/bin",
            "HOME": str(Path.home()),
            "PT_RUNTIME_MODE": "",
        },
        check=False,
    )
    if Path(sys.executable).parent.parent.resolve() == (REPO_ROOT / ".venv").resolve():
        pytest.skip("pytest already running under canonical interpreter")
    assert proc.returncode == EXIT_INTERPRETER_MISMATCH


def test_launcher_provisioned_refused_without_ci_flag(tmp_path: Path) -> None:
    repo = _seed_fake_repo(tmp_path)
    poison = tmp_path / "poison" / "bin"
    poison.mkdir(parents=True)
    _write_executable(poison / "python", "#!/bin/sh\necho POISONED >&2\nexit 99\n")
    _write_executable(poison / "python3", "#!/bin/sh\necho POISONED >&2\nexit 99\n")
    proc = subprocess.run(
        [str(repo / "scripts" / "pt"), "-c", "print('should-not-run')"],
        cwd=repo,
        capture_output=True,
        text=True,
        env={
            "PATH": f"{poison}:/usr/bin:/bin",
            "HOME": str(tmp_path / "home"),
            "PT_RUNTIME_MODE": MODE_PROVISIONED,
            "GITHUB_ACTIONS": "",
            "PT_RUNTIME_PROVISIONED_OK": "",
            "PT_SKIP_TRADING_PREFLIGHT": "1",
        },
        check=False,
    )
    assert proc.returncode == EXIT_PROVISIONED_REFUSED
    assert "should-not-run" not in proc.stdout
    assert "POISONED" not in proc.stderr


def test_launcher_provisioned_uses_bound_interpreter(tmp_path: Path) -> None:
    if sys.version_info < (3, 10):
        pytest.skip("host interpreter below project floor")
    repo = _seed_fake_repo(tmp_path)
    poison = tmp_path / "poison" / "bin"
    poison.mkdir(parents=True)
    _write_executable(poison / "python", "#!/bin/sh\necho POISONED >&2\nexit 99\n")
    _write_executable(poison / "python3", "#!/bin/sh\necho POISONED >&2\nexit 99\n")
    proc = subprocess.run(
        [str(repo / "scripts" / "pt"), "-c", "import sys; print(sys.executable)"],
        cwd=repo,
        capture_output=True,
        text=True,
        env={
            "PATH": f"{poison}:/usr/bin:/bin",
            "HOME": str(tmp_path / "home"),
            "PT_RUNTIME_MODE": MODE_PROVISIONED,
            "PT_RUNTIME_PROVISIONED_OK": "1",
            "PT_PROVISIONED_PYTHON": sys.executable,
            "PT_SKIP_TRADING_PREFLIGHT": "1",
        },
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "POISONED" not in proc.stderr
    assert Path(proc.stdout.strip()).resolve() == Path(sys.executable).resolve()


def test_launcher_provisioned_unbound_without_python_location(tmp_path: Path) -> None:
    repo = _seed_fake_repo(tmp_path)
    proc = subprocess.run(
        [str(repo / "scripts" / "pt"), "-c", "print('should-not-run')"],
        cwd=repo,
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": str(tmp_path / "home"),
            "PT_RUNTIME_MODE": MODE_PROVISIONED,
            "PT_RUNTIME_PROVISIONED_OK": "1",
            "PT_SKIP_TRADING_PREFLIGHT": "1",
        },
        check=False,
    )
    assert proc.returncode == EXIT_PROVISIONED_REFUSED
    assert "should-not-run" not in proc.stdout
    assert "unbound" in proc.stderr


def test_lint_gate_binds_provisioned_runtime() -> None:
    text = (REPO_ROOT / ".github" / "workflows" / "lint_gate.yml").read_text(encoding="utf-8")
    assert "PT_RUNTIME_MODE: provisioned" in text
    assert "PT_SKIP_TRADING_PREFLIGHT" in text
    assert "PT_PROVISIONED_PYTHON" in text
    assert "ai_matrix_consistency_gate.sh" in text


def test_provisioned_mode_refused_without_ci_flag() -> None:
    result = validate_runtime(
        repo_root=REPO_ROOT,
        env={"PT_RUNTIME_MODE": MODE_PROVISIONED},
        require_trading_import=False,
        check_running_identity=False,
    )
    assert result.ok is False
    assert result.reason_code == REASON_PROVISIONED_REFUSED


def test_provisioned_mode_accepted_with_explicit_ok() -> None:
    if sys.version_info < (3, 10):
        pytest.skip("host interpreter below project floor")
    result = validate_runtime(
        repo_root=REPO_ROOT,
        env={"PT_RUNTIME_MODE": MODE_PROVISIONED, "PT_RUNTIME_PROVISIONED_OK": "1"},
        require_trading_import=False,
        check_running_identity=False,
        running_executable=Path(sys.executable),
    )
    assert result.ok is True
    assert result.reason_code == REASON_PASS
    assert result.mode == MODE_PROVISIONED


def test_makefile_delegates_to_canonical_launcher() -> None:
    text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "PT :=" in text or "PT:=" in text
    assert "scripts/pt" in text
    assert "PYTHONPATH=." not in text
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith(".PHONY"):
            continue
        if stripped.startswith("python3 ") or " python3 " in f" {stripped}":
            pytest.fail(f"Makefile still contains bare python3: {stripped}")
        if stripped.startswith("python ") and "python-version" not in stripped:
            pytest.fail(f"Makefile still contains bare python: {stripped}")


def test_agent_guidance_points_at_canonical_launcher() -> None:
    agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    rule = (REPO_ROOT / ".cursor" / "rules" / "peak-trade-python-runtime.mdc").read_text(
        encoding="utf-8"
    )
    helper = (REPO_ROOT / "docs" / "ai" / "PEAK_TRADE_AI_HELPER_GUIDE.md").read_text(
        encoding="utf-8"
    )
    claude = (REPO_ROOT / "docs" / "ai" / "CLAUDE_GUIDE.md").read_text(encoding="utf-8")
    for text in (agents, rule, helper, claude):
        assert "scripts/pt" in text
        assert "never execute Peak_Trade Python using PATH" in text or "scripts/pt" in text
    assert "Python 3.9+" not in claude
    assert "source .venv/bin/activate" not in claude.split("##")[0]


def test_active_docs_do_not_claim_python_39_supported() -> None:
    for rel in (
        "README.md",
        "docs/GETTING_STARTED.md",
        "docs/DEV_SETUP.md",
        "docs/DEVELOPER_WORKFLOW_GUIDE.md",
        "docs/ai/CLAUDE_GUIDE.md",
        "docs/runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md",
    ):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert "Python 3.9+" not in text
        assert 'requires-python = ">=3.10"' in text or ">=3.10" in text or "3.10" in text


def test_operative_surface_manifest_exists() -> None:
    path = REPO_ROOT / "config" / "runtime" / "pt_python_operative_surfaces_v1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["contract_id"] == "pt_python_operative_surfaces_v1"
    classes = {item["path"]: item["class"] for item in payload["surfaces"]}
    assert classes["scripts/pt"] == "OPERATIVE_CANONICAL"
    assert classes["scripts/pt-bootstrap"] == "OPERATIVE_CANONICAL"
    assert classes["tests/conftest.py"] == "TEST_ONLY"
    assert classes["docs/ops/PYTHON_VERSION_PLAN.md"] == "HISTORICAL"


def test_ci_active_python_versions_meet_floor() -> None:
    root = REPO_ROOT / ".github" / "workflows"
    offenders: list[str] = []
    for path in sorted(root.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        if 'python-version: ["3.9"' in text or "python-version: ['3.9'" in text:
            offenders.append(path.name)
        if 'python-version: "3.9"' in text or "python-version: '3.9'" in text:
            if "NEGATIVE" not in text and "unsupported" not in text.lower():
                offenders.append(path.name)
    assert offenders == []


def test_pyenv_system_does_not_alter_selected_runtime(tmp_path: Path) -> None:
    if sys.version_info < (3, 10):
        pytest.skip("host interpreter below project floor")
    repo = _seed_fake_repo(tmp_path)
    venv_python = repo / CANONICAL_INTERPRETER_REL
    venv_python.parent.mkdir(parents=True)
    venv_python.symlink_to(Path(sys.executable).resolve())
    complete_isolated_test_venv(repo)
    poison = tmp_path / "pyenv" / "shims"
    poison.mkdir(parents=True)
    _write_executable(poison / "python3", "#!/bin/sh\necho PYENV_SYSTEM >&2\nexit 99\n")
    _write_executable(poison / "python", "#!/bin/sh\necho PYENV_SYSTEM >&2\nexit 99\n")
    proc = subprocess.run(
        [str(repo / "scripts" / "pt"), "-c", "print('ok')"],
        cwd=repo,
        capture_output=True,
        text=True,
        env={
            "PATH": f"{poison}:/usr/bin:/bin",
            "HOME": str(tmp_path / "home"),
            "PYENV_VERSION": "system",
            "PYENV_ROOT": str(tmp_path / "pyenv"),
            "PT_SKIP_TRADING_PREFLIGHT": "1",
        },
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "PYENV_SYSTEM" not in proc.stderr
    assert proc.stdout.strip() == "ok"


def test_makefile_runtime_check_target() -> None:
    text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "runtime-check:" in text
    assert "$(PT) runtime-check" in text


def test_scheduler_bare_python3_binds_process_interpreter() -> None:
    from src.scheduler.models import JobDefinition, JobSchedule
    from src.scheduler.runner import run_job

    job = JobDefinition(
        name="runtime_contract_python3",
        command="python3",
        args={"script": "scripts/run_backtest.py"},
        schedule=JobSchedule(type="once"),
        enabled=True,
    )
    result = run_job(job, dry_run=True)
    assert result.success is True
    assert sys.executable in result.stdout
    assert result.stdout.endswith(f"{sys.executable} scripts/run_backtest.py") or (
        sys.executable in result.stdout and "scripts/run_backtest.py" in result.stdout
    )


def test_operative_docs_do_not_endorse_direct_src_python3() -> None:
    for rel in (
        "README.md",
        "docs/GETTING_STARTED.md",
        "docs/DEV_SETUP.md",
        "docs/DEVELOPER_WORKFLOW_GUIDE.md",
        "docs/ai/CLAUDE_GUIDE.md",
        "docs/runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md",
        "AGENTS.md",
    ):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if "prohibited" in stripped.lower() or stripped.startswith("- "):
                if "package code" in stripped:
                    continue
            assert "python3 src/" not in stripped
            assert "python src/" not in stripped


@pytest.mark.skipif(
    not (REPO_ROOT / CANONICAL_INTERPRETER_REL).is_file(),
    reason="worktree has no provisioned .venv",
)
def test_trading_imports_under_canonical_launcher() -> None:
    proc = subprocess.run(
        [str(LAUNCHER), "-c", "import trading; print('trading-ok')"],
        cwd=REPO_ROOT / "docs",
        capture_output=True,
        text=True,
        env={"PATH": f"{POISON_BIN_HINT}:/usr/bin:/bin", "HOME": str(Path.home())},
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "trading-ok" in proc.stdout


def test_fingerprint_payload_has_no_secrets() -> None:
    from scripts.runtime.pt_python_runtime_contract_v1 import fingerprint_payload

    result = validate_runtime(
        repo_root=REPO_ROOT,
        require_trading_import=False,
        check_running_identity=False,
        env={"PT_RUNTIME_MODE": MODE_PROVISIONED, "PT_RUNTIME_PROVISIONED_OK": "1"},
    )
    payload = fingerprint_payload(result)
    blob = json.dumps(payload)
    assert "SECRET" not in blob
    assert "API_KEY" not in blob
    assert "path_python_fallback_allowed" in payload
    assert payload["path_python_fallback_allowed"] is False
    assert "contract_version" in payload
