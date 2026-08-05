"""Worktree-safe repository SHA resolution."""

from __future__ import annotations

from pathlib import Path

from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.models_v1 import (
    InputAuthorityErrorV1,
)


def _resolve_gitdir(repo_root: Path) -> Path:
    git_entry = repo_root / ".git"
    if git_entry.is_dir():
        return git_entry
    if git_entry.is_file():
        content = git_entry.read_text(encoding="utf-8").strip()
        if not content.startswith("gitdir:"):
            raise InputAuthorityErrorV1("git_entry_invalid")
        gitdir = content.split(":", 1)[1].strip()
        path = Path(gitdir)
        if not path.is_absolute():
            path = (repo_root / path).resolve()
        if not path.is_dir():
            raise InputAuthorityErrorV1("worktree_gitdir_missing")
        return path
    raise InputAuthorityErrorV1("git_head_missing")


def resolve_repository_sha(repo_root: Path) -> str:
    """Resolve HEAD SHA for normal repos and linked worktrees (`gitdir:` files)."""
    gitdir = _resolve_gitdir(Path(repo_root).resolve())
    head = gitdir / "HEAD"
    if not head.is_file():
        raise InputAuthorityErrorV1("git_head_missing")
    content = head.read_text(encoding="utf-8").strip()
    if content.startswith("ref:"):
        ref = content.split(" ", 1)[1].strip()
        ref_path = gitdir / ref
        if not ref_path.is_file():
            # Common worktree layout: refs may live in commondir.
            common = gitdir / "commondir"
            if common.is_file():
                common_root = (gitdir / common.read_text(encoding="utf-8").strip()).resolve()
                ref_path = common_root / ref
        if not ref_path.is_file():
            raise InputAuthorityErrorV1("git_ref_missing")
        sha = ref_path.read_text(encoding="utf-8").strip()
    else:
        sha = content
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha.lower()):
        raise InputAuthorityErrorV1("git_sha_invalid")
    return sha.lower()
