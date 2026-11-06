"""Static cleanup/git-mutation scope contract for scripts/ops/p61_full_workflow.sh.

Reads the script as UTF-8 text only. Static assertions only (no subprocess/OS hooks,
no runtime mutation of repo or trading surfaces).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "p61_full_workflow.sh"


def _script_text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_p61_full_workflow_cleanup_scope_contract_has_target_script() -> None:
    assert SCRIPT.exists()
    assert SCRIPT.is_file()


def test_p61_full_workflow_cleanup_scope_contract_preserves_static_test_scope() -> None:
    test_source = Path(__file__).read_text(encoding="utf-8")

    forbidden_fragments = [
        "subprocess" + ".",
        "os" + ".system",
        "runpy" + ".",
        "importlib" + ".import_module",
        "requests" + ".",
        "httpx" + ".",
        "urllib" + ".",
        "socket" + ".",
        "gh " + "pr",
        "shutil" + ".rmtree",
        "unlink" + "(",
        "remove" + "(",
        "chmod" + "(",
    ]

    found = [fragment for fragment in forbidden_fragments if fragment in test_source]
    assert not found, f"static p61 contract must not use execution/mutation hooks: {found}"


def test_p61_full_workflow_cleanup_scope_contract_freezes_git_reset_surface() -> None:
    text = _script_text()

    assert "git reset --hard origin/main" in text
    assert text.count("git reset --hard") == 1


def test_p61_full_workflow_cleanup_scope_contract_freezes_pr_merge_delete_branch_surface() -> None:
    text = _script_text()

    assert "gh_tls_wrap.sh" in text
    assert "pr merge" in text
    assert "--delete-branch" in text


def test_p61_full_workflow_cleanup_scope_contract_rejects_broad_filesystem_delete_patterns() -> (
    None
):
    text = _script_text()

    forbidden_filesystem_patterns = [
        "rm -rf /",
        "rm -rf .",
        "rm -rf $REPO_ROOT",
        "rm -rf ${REPO_ROOT}",
        "shutil" + ".rmtree(REPO_ROOT",
        "shutil" + ".rmtree(repo_root",
        "shutil" + ".rmtree(Path.cwd()",
    ]

    found = [pattern for pattern in forbidden_filesystem_patterns if pattern in text]
    assert not found, f"script must not gain broad filesystem cleanup patterns: {found}"


def test_p61_full_workflow_cleanup_scope_contract_rejects_git_clean_surface() -> None:
    text = _script_text()

    assert "git clean -fdx" not in text
    assert "git clean -xdf" not in text


def test_p61_full_workflow_cleanup_scope_contract_documents_workflow_owner_surface() -> None:
    text = _script_text().lower()

    assert "workflow" in text
    assert "merge" in text
    assert "main" in text
    assert "origin/main" in text


def test_p61_full_workflow_cleanup_scope_contract_keeps_git_mutation_owner_review_surface_visible() -> (
    None
):
    text = _script_text()

    assert "git status" in text
    assert "git fetch" in text
    assert "git checkout main" in text
