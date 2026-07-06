"""Contract tests for squash_merge_post_merge_closeout_guard_v0.sh.

Proves post-merge pytest/ruff tee+log guards fail-closed on collection errors and nonzero rc.
Uses temporary fixture repos only; never mutates the real repository.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "squash_merge_post_merge_closeout_guard_v0.sh"
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
TASK_PACKET = REPO_ROOT / "docs" / "ops" / "TASK_PACKET_EVIDENCE_PYTEST.md"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _init_fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "fixture@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Fixture"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "base"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "branch", "-M", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", head],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "remote", "add", "origin", str(repo)],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return repo


def _stub_bin(tmp_path: Path, *, pytest_exit: int = 0, ruff_exit: int = 0) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_executable(
        bin_dir / "python3",
        f"""#!/usr/bin/env bash
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "pytest" ]]; then
  echo "ERROR collecting tests/meta"
  echo "Interrupted: 1 error during collection"
  exit {pytest_exit}
fi
exec {shutil.which("python3")!r} "$@"
""",
    )
    _write_executable(
        bin_dir / "ruff",
        f"""#!/usr/bin/env bash
echo "stub ruff $*"
exit {ruff_exit}
""",
    )
    return bin_dir


def _run_guard(
    repo: Path,
    evidence_dir: Path,
    *,
    extra_args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        "bash",
        str(SCRIPT),
        "post-merge-validate",
        "--evidence-dir",
        str(evidence_dir),
        "--skip-ruff",
        *(extra_args or []),
    ]
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=repo,
        env=merged,
        capture_output=True,
        text=True,
        check=False,
    )


def test_guard_script_exists_with_pipefail_and_marker() -> None:
    assert SCRIPT.is_file()
    text = SCRIPT.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in text
    assert "SQUASH_MERGE_POST_MERGE_CLOSEOUT_GUARD_V0=true" in text
    assert "PIPESTATUS[0]" in text
    assert "run_teed" in text


def test_guard_script_uses_pipefail_inside_tee_helper() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "set -o pipefail" in text
    assert 'return "${PIPESTATUS[0]}"' in text


def test_ci_audit_crosslink_present() -> None:
    text = CI_AUDIT.read_text(encoding="utf-8")
    assert "squash_merge_post_merge_closeout_guard_v0.sh" in text
    assert "SQUASH_MERGE_POST_MERGE_CLOSEOUT_GUARD_V0=true" in text


def test_task_packet_references_fail_closed_tee_semantics() -> None:
    text = TASK_PACKET.read_text(encoding="utf-8")
    assert "set -o pipefail" in text
    assert "PIPESTATUS[0]" in text


def test_post_merge_validate_fails_closed_on_pytest_collection_error(tmp_path: Path) -> None:
    repo = _init_fixture_repo(tmp_path)
    evidence = tmp_path / "evidence"
    bin_dir = _stub_bin(tmp_path, pytest_exit=2)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["REMOTE"] = "origin"
    env["MAIN_BRANCH"] = "main"

    result = _run_guard(repo, evidence, env=env)

    assert result.returncode == 6
    log = (evidence / "pytest_targeted_post_merge.log").read_text(encoding="utf-8")
    assert "ERROR collecting tests/meta" in log
    assert (evidence / "pytest_targeted_post_merge.rc").read_text(encoding="utf-8").strip() == "6"


def test_post_merge_validate_fails_closed_on_nonzero_pytest_rc(tmp_path: Path) -> None:
    repo = _init_fixture_repo(tmp_path)
    evidence = tmp_path / "evidence2"
    bin_dir = _stub_bin(tmp_path, pytest_exit=1)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = _run_guard(repo, evidence, env=env)

    assert result.returncode != 0
    rc_file = evidence / "pytest_targeted_post_merge.rc"
    assert rc_file.is_file()
    assert int(rc_file.read_text(encoding="utf-8").strip()) != 0


def test_post_merge_validate_passes_when_pytest_and_manifest_ok(tmp_path: Path) -> None:
    repo = _init_fixture_repo(tmp_path)
    evidence = tmp_path / "evidence3"
    bin_dir = _stub_bin(tmp_path, pytest_exit=0)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = _run_guard(repo, evidence, env=env)

    assert result.returncode == 0
    assert "HEAD_EQUALS_ORIGIN_MAIN=true" in (evidence / "head_equals_origin_main.txt").read_text(
        encoding="utf-8"
    )
    assert (evidence / "pytest_targeted_post_merge.log").is_file()


def test_meta_conftest_pytest_plugins_collection_no_longer_errors() -> None:
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests",
            "-q",
            "-k",
            "evidence or manifest or docs or governance",
            "--collect-only",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert "ERROR collecting tests/meta" not in proc.stdout + proc.stderr
    assert "Interrupted: 1 error during collection" not in proc.stdout + proc.stderr
