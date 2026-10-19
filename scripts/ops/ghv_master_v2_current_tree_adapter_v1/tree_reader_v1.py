"""Read blobs from an explicit git tree. Never reads HEAD or worktree files."""

from __future__ import annotations

import subprocess
from pathlib import Path

_HEX40 = frozenset("0123456789abcdef")


class AdapterRejected(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class PinRejected(AdapterRejected):
    pass


class TreeReadError(AdapterRejected):
    pass


def require_explicit_oid(value: str) -> str:
    if not isinstance(value, str) or len(value) != 40 or any(ch not in _HEX40 for ch in value):
        raise PinRejected("EXPLICIT_OBJECT_ID_REQUIRED")
    return value


def _reject_head_arg(arg: str) -> None:
    if "HEAD" in arg:
        raise PinRejected("HEAD_FALLBACK_FORBIDDEN")


def git_object_text(*, repo_root: Path, args: list[str]) -> str:
    for arg in args:
        _reject_head_arg(arg)
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise TreeReadError(detail or "GIT_OBJECT_READ_FAILED")
    return completed.stdout.decode("utf-8")


def git_object_line(*, repo_root: Path, args: list[str]) -> str:
    return git_object_text(repo_root=repo_root, args=args).strip()


def assert_commit_matches_tree(*, repo_root: Path, commit_sha: str, tree_sha: str) -> None:
    require_explicit_oid(commit_sha)
    require_explicit_oid(tree_sha)
    commit_kind = git_object_line(repo_root=repo_root, args=["cat-file", "-t", commit_sha])
    if commit_kind != "commit":
        raise PinRejected(f"COMMIT_OBJECT_REQUIRED:{commit_kind}")
    tree_kind = git_object_line(repo_root=repo_root, args=["cat-file", "-t", tree_sha])
    if tree_kind != "tree":
        raise PinRejected(f"TREE_OBJECT_REQUIRED:{tree_kind}")
    actual_tree = git_object_line(
        repo_root=repo_root,
        args=["rev-parse", "--verify", f"{commit_sha}^{{tree}}"],
    )
    if actual_tree != tree_sha:
        raise PinRejected("COMMIT_TREE_MISMATCH")


class TreeBlobReader:
    """Blob reader bound to one explicit tree. Filesystem source paths are not opened."""

    def __init__(self, *, repo_root: Path, tree_sha: str) -> None:
        self.repo_root = repo_root
        self.tree_sha = require_explicit_oid(tree_sha)
        self._exists: dict[str, bool] = {}
        self._text: dict[str, str] = {}
        self._blob: dict[str, str] = {}

    def exists(self, path: str) -> bool:
        if path in self._exists:
            return self._exists[path]
        _reject_head_arg(path)
        spec = f"{self.tree_sha}:{path}"
        completed = subprocess.run(
            ["git", "-C", str(self.repo_root), "cat-file", "-e", spec],
            check=False,
            capture_output=True,
        )
        found = completed.returncode == 0
        self._exists[path] = found
        return found

    def blob_sha(self, path: str) -> str | None:
        if path in self._blob:
            return self._blob[path]
        if not self.exists(path):
            return None
        blob = git_object_line(
            repo_root=self.repo_root,
            args=["rev-parse", "--verify", f"{self.tree_sha}:{path}"],
        )
        self._blob[path] = blob
        return blob

    def text(self, path: str) -> str | None:
        if path in self._text:
            return self._text[path]
        blob = self.blob_sha(path)
        if blob is None:
            return None
        try:
            source = git_object_text(repo_root=self.repo_root, args=["cat-file", "-p", blob])
        except (TreeReadError, UnicodeDecodeError):
            return None
        self._text[path] = source
        return source
