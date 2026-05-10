"""Static cleanup-scope contract for scripts/ops/bundle_prbj_exec_events.py.

Reads the script as UTF-8 text only. Never executes the script, never downloads
artifacts, never calls GitHub APIs, never dispatches workflows, and never deletes,
moves, archives, chmods, or mutates repository files.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "bundle_prbj_exec_events.py"


def _script_text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_bundle_prbj_exec_events_cleanup_scope_contract_has_target_script() -> None:
    assert SCRIPT.exists()
    assert SCRIPT.is_file()


def test_bundle_prbj_exec_events_cleanup_scope_contract_preserves_static_scope() -> None:
    test_text = Path(__file__).read_text(encoding="utf-8")

    forbidden_fragments = [
        "subprocess" + ".",
        "os" + ".system",
        "runpy" + ".",
        "importlib" + ".import_module",
        "requests" + ".",
        "httpx" + ".",
        "urllib" + ".",
        "socket" + ".",
        "gh" + " run",
        "gh" + " api",
        "shutil" + ".rmtree(",
        "unlink" + "(",
        "remove" + "(",
        "chmod" + "(",
    ]

    found = [fragment for fragment in forbidden_fragments if fragment in test_text]
    assert not found, (
        f"static cleanup-scope contract must not use mutation/execution hooks: {found}"
    )


def test_bundle_prbj_exec_events_cleanup_scope_contract_freezes_cleanup_marker() -> None:
    text = _script_text()

    assert "dl_root" in text
    assert "shutil" + ".rmtree(dl_root)" in text


def test_bundle_prbj_exec_events_cleanup_scope_contract_keeps_cleanup_specific_to_download_root() -> (
    None
):
    text = _script_text()

    assert text.count("shutil" + ".rmtree(") == 1
    assert "shutil" + ".rmtree(dl_root)" in text
    assert "shutil" + ".rmtree(REPO_ROOT" not in text
    assert "shutil" + ".rmtree(repo_root" not in text
    assert "shutil" + ".rmtree(Path.cwd()" not in text


def test_bundle_prbj_exec_events_cleanup_scope_contract_preserves_workflow_and_download_surface() -> (
    None
):
    text = _script_text()

    assert "prbj-testnet-exec-events.yml" in text
    assert "--workflow" in text
    assert "download" in text.lower()
    assert "dl_root" in text


def test_bundle_prbj_exec_events_cleanup_scope_contract_rejects_broad_shell_delete_patterns() -> (
    None
):
    text = _script_text()

    forbidden_shell_patterns = [
        "rm -rf /",
        "rm -rf .",
        "rm -rf $REPO_ROOT",
        "rm -rf ${REPO_ROOT}",
        "git clean -fdx",
        "git reset --hard",
    ]

    found = [pattern for pattern in forbidden_shell_patterns if pattern in text]
    assert not found, f"script must not gain broad destructive shell cleanup patterns: {found}"


def test_bundle_prbj_exec_events_cleanup_scope_contract_documents_owner_review_surface() -> None:
    text = _script_text().lower()

    assert "argparse" in text
    assert "workflow" in text
    assert "download" in text
    assert "events" in text
