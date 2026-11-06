"""Repository binding gates for DELEGATED_CURSOR_SECURE_CONFIRM.

Requires HEAD == origin/main and tracked worktree clean (untracked ignored).
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _git_out_v1(repo_root: Path, *args: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()


def prove_head_equals_origin_main_v1(*, repo_root: Path) -> dict[str, Any]:
    root = Path(repo_root)
    rc_h, head, err_h = _git_out_v1(root, "rev-parse", "HEAD")
    rc_o, origin_main, err_o = _git_out_v1(root, "rev-parse", "origin/main")
    blockers: list[str] = []
    if rc_h != 0 or not head:
        blockers.append("HEAD_SHA_UNAVAILABLE")
        if err_h:
            blockers.append("GIT_REV_PARSE_HEAD_FAILED")
    if rc_o != 0 or not origin_main:
        blockers.append("ORIGIN_MAIN_SHA_UNAVAILABLE")
        if err_o:
            blockers.append("GIT_REV_PARSE_ORIGIN_MAIN_FAILED")
    if head and origin_main and head != origin_main:
        blockers.append("HEAD_NOT_EQUAL_ORIGIN_MAIN")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "head_sha": head,
        "origin_main_sha": origin_main,
        "HEAD_EQUALS_ORIGIN_MAIN": bool(head and origin_main and head == origin_main),
    }


def prove_tracked_worktree_clean_v1(*, repo_root: Path) -> dict[str, Any]:
    root = Path(repo_root)
    rc, out, err = _git_out_v1(root, "status", "--porcelain=v1")
    blockers: list[str] = []
    if rc != 0:
        blockers.append("GIT_STATUS_FAILED")
        if err:
            blockers.append("GIT_STATUS_UNAVAILABLE")
        return {
            "ok": False,
            "blockers": blockers,
            "tracked_worktree_clean": False,
            "dirty_tracked_paths": [],
        }
    dirty: list[str] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        if line.startswith("??"):
            continue
        dirty.append(line[:80])
    if dirty:
        blockers.append("TRACKED_WORKTREE_DIRTY")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "tracked_worktree_clean": not dirty,
        "dirty_tracked_count": len(dirty),
        # paths only as short porcelain prefixes — never secrets
        "dirty_tracked_paths": dirty[:20],
    }


def evaluate_delegated_cursor_repository_binding_v1(*, repo_root: Path) -> dict[str, Any]:
    head = prove_head_equals_origin_main_v1(repo_root=repo_root)
    clean = prove_tracked_worktree_clean_v1(repo_root=repo_root)
    blockers = list(head.get("blockers") or []) + list(clean.get("blockers") or [])
    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "HEAD_EQUALS_ORIGIN_MAIN": bool(head.get("HEAD_EQUALS_ORIGIN_MAIN")),
        "tracked_worktree_clean": bool(clean.get("tracked_worktree_clean")),
        "head_sha": head.get("head_sha"),
        "origin_main_sha": head.get("origin_main_sha"),
        "dirty_tracked_count": clean.get("dirty_tracked_count"),
    }
