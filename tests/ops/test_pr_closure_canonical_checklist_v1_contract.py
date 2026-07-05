"""Contract tests for scripts/ops/pr_closure_canonical_checklist_v1.py."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2] / "scripts" / "ops" / "pr_closure_canonical_checklist_v1.py"
)
DOC = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "ops"
    / "PR_CLOSURE_CANONICAL_CHECKLIST_HOOK_V1.md"
)

REQUIRED_PAYLOAD_KEYS = frozenset(
    {
        "ahead_origin_main",
        "behind_origin_main",
        "branch",
        "findings",
        "head",
        "origin_main",
        "stash_entries",
        "verdict",
        "worktree_clean",
    }
)


def _run(*, cwd: Path, script: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(script)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    (path / "README.md").write_text("# fixture\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"], cwd=path, check=True, capture_output=True, text=True
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "user.name=Fixture",
            "commit",
            "-m",
            "fixture init",
        ],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "branch", "-M", "main"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    return path


def _install_script(repo: Path) -> Path:
    script_dir = repo / "scripts" / "ops"
    script_dir.mkdir(parents=True)
    script_path = script_dir / "pr_closure_canonical_checklist_v1.py"
    script_path.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    script_path.chmod(0o755)
    subprocess.run(
        ["git", "add", str(script_path)], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "user.name=Fixture",
            "commit",
            "-m",
            "install checklist script",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return script_path


def _fetch_origin_main(repo: Path) -> None:
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def test_script_and_doc_exist() -> None:
    assert SCRIPT.exists()
    assert SCRIPT.read_text(encoding="utf-8").startswith("#!/usr/bin/env python3")
    assert DOC.exists()
    doc = DOC.read_text(encoding="utf-8")
    assert "python3 scripts/ops/pr_closure_canonical_checklist_v1.py" in doc
    assert "STASH_PRESENT_WARN_ONLY" in doc


def test_pass_on_clean_feature_branch(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")
    script = _install_script(repo)
    _fetch_origin_main(repo)
    subprocess.run(
        ["git", "checkout", "-b", "feature/clean"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    result = _run(cwd=repo, script=script)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert set(payload) == REQUIRED_PAYLOAD_KEYS
    assert payload["verdict"] == "PASS"
    assert payload["worktree_clean"] is True
    assert payload["findings"] == []


def test_fail_on_dirty_worktree(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")
    script = _install_script(repo)
    _fetch_origin_main(repo)
    (repo / "dirty.txt").write_text("pending\n", encoding="utf-8")

    result = _run(cwd=repo, script=script)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["verdict"] == "FAIL"
    assert payload["worktree_clean"] is False
    assert "WORKTREE_NOT_CLEAN" in payload["findings"]


def test_main_diverged_from_origin_main_fails(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")
    script = _install_script(repo)
    _fetch_origin_main(repo)
    (repo / "ahead.txt").write_text("ahead\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "ahead.txt"], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "user.name=Fixture",
            "commit",
            "-m",
            "ahead commit",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    result = _run(cwd=repo, script=script)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["branch"] == "main"
    assert payload["ahead_origin_main"] == 1
    assert "MAIN_DIVERGED_FROM_ORIGIN_MAIN" in payload["findings"]


def test_stash_present_is_warn_only(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path / "repo")
    script = _install_script(repo)
    _fetch_origin_main(repo)
    subprocess.run(
        ["git", "checkout", "-b", "feature/stash"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    (repo / "stash-me.txt").write_text("stash\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "stash-me.txt"], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "user.name=Fixture",
            "commit",
            "-m",
            "track stash target",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    (repo / "stash-me.txt").write_text("stashed change\n", encoding="utf-8")
    subprocess.run(
        ["git", "stash", "push", "-m", "fixture stash", "--", "stash-me.txt"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    result = _run(cwd=repo, script=script)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["verdict"] == "PASS"
    assert payload["stash_entries"] == 1
    assert "STASH_PRESENT_WARN_ONLY" in payload["findings"]
