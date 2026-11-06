"""CLI contract tests for scripts/ops/check_required_ci_contexts_present.sh (fixture ci.yml + cwd)."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "ops" / "check_required_ci_contexts_present.sh"

_CI_REL = Path(".github/workflows/ci.yml")


def _write_ci(fake_repo: Path, content: str) -> Path:
    ci = fake_repo / _CI_REL
    ci.parent.mkdir(parents=True, exist_ok=True)
    ci.write_text(content, encoding="utf-8")
    return ci


def _run(fake_repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(_SCRIPT)],
        cwd=fake_repo,
        capture_output=True,
        text=True,
        check=False,
    )


_MINIMAL_PASS_CI = """concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number }}-gate

jobs:
  tests:
    name: tests (${{ matrix.python-version }})
    strategy:
      matrix:
        python-version: ['3.9', '3.11']
    steps:
      - run: echo ok
"""


def test_passes_minimal_valid_workflow(tmp_path: Path) -> None:
    _write_ci(tmp_path, _MINIMAL_PASS_CI)
    p = _run(tmp_path)
    assert p.returncode == 0
    assert "✅ CI required context contract looks good." in p.stdout
    assert "✅ Concurrency group is PR-isolated" in p.stdout
    assert "ℹ️  Job 'strategy-smoke' not found" in p.stdout
    assert p.stderr == ""


def test_fails_when_ci_file_missing(tmp_path: Path) -> None:
    (tmp_path / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
    p = _run(tmp_path)
    assert p.returncode == 1
    assert "Missing .github/workflows/ci.yml" in p.stderr
    assert "❌" in p.stderr


def test_fails_when_no_concurrency_block(tmp_path: Path) -> None:
    _write_ci(
        tmp_path,
        """jobs:
  tests:
    name: tests (${{ matrix.python-version }})
    strategy:
      matrix:
        python-version: ['3.11']
    steps:
      - run: echo ok
""",
    )
    p = _run(tmp_path)
    assert p.returncode == 1
    assert "No concurrency block found" in p.stderr


def test_fails_when_concurrency_group_not_pr_isolated(tmp_path: Path) -> None:
    _write_ci(
        tmp_path,
        """concurrency:
  group: static-group-name

jobs:
  tests:
    name: tests (${{ matrix.python-version }})
    strategy:
      matrix:
        python-version: ['3.11']
    steps:
      - run: echo ok
""",
    )
    p = _run(tmp_path)
    assert p.returncode == 1
    assert "Concurrency group must include PR number" in p.stderr


def test_fails_when_tests_job_absent(tmp_path: Path) -> None:
    _write_ci(
        tmp_path,
        """concurrency:
  group: ${{ github.event.pull_request.number }}-x

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: echo ok
""",
    )
    p = _run(tmp_path)
    assert p.returncode == 1
    assert "Job 'tests' not found" in p.stderr


def test_fails_when_tests_name_not_matrix_templated(tmp_path: Path) -> None:
    _write_ci(
        tmp_path,
        """concurrency:
  group: ${{ github.event.pull_request.number }}-x

jobs:
  tests:
    name: tests
    strategy:
      matrix:
        python-version: ['3.11']
    steps:
      - run: echo ok
""",
    )
    p = _run(tmp_path)
    assert p.returncode == 1
    assert "Job 'tests' must set: name: tests" in p.stderr


def test_fails_when_tests_has_job_level_if(tmp_path: Path) -> None:
    _write_ci(
        tmp_path,
        """concurrency:
  group: ${{ github.event.pull_request.number }}-x

jobs:
  tests:
    if: always()
    name: tests (${{ matrix.python-version }})
    strategy:
      matrix:
        python-version: ['3.11']
    steps:
      - run: echo ok
""",
    )
    p = _run(tmp_path)
    assert p.returncode == 1
    assert "Job-level if detected on 'tests'" in p.stderr


def test_fails_when_strategy_smoke_has_job_level_if(tmp_path: Path) -> None:
    _write_ci(
        tmp_path,
        """name: synthetic-ci

on:
  pull_request:

concurrency:
  group: ${{ github.event.pull_request.number }}-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  tests:
    name: tests (${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11"]
    steps:
      - run: echo tests

  strategy-smoke:
    name: strategy-smoke
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - run: echo strategy
""",
    )
    p = _run(tmp_path)
    assert p.returncode == 1
    assert "Job-level if detected on 'strategy-smoke'" in p.stderr
    assert "Concurrency group is PR-isolated" in p.stdout
    assert "tests job naming + no job-level if: OK" in p.stdout


def test_fails_when_matrix_missing_python_311(tmp_path: Path) -> None:
    _write_ci(
        tmp_path,
        """concurrency:
  group: ${{ github.event.pull_request.number }}-x

jobs:
  tests:
    name: tests (${{ matrix.python-version }})
    strategy:
      matrix:
        python-version: ['3.9', '3.10']
    steps:
      - run: echo ok
""",
    )
    p = _run(tmp_path)
    assert p.returncode == 1
    assert "must include '3.11'" in p.stderr


def test_fails_when_strategy_smoke_has_wrong_step_name(tmp_path: Path) -> None:
    _write_ci(
        tmp_path,
        """concurrency:
  group: ${{ github.event.pull_request.number }}-x

jobs:
  tests:
    name: tests (${{ matrix.python-version }})
    strategy:
      matrix:
        python-version: ['3.11']
    steps:
      - run: echo ok
  strategy-smoke:
    name: strategy-smoke-wrong
    runs-on: ubuntu-latest
    steps:
      - run: echo smoke
""",
    )
    p = _run(tmp_path)
    assert p.returncode == 1
    assert "strategy-smoke' must set explicit: name: strategy-smoke" in p.stderr
