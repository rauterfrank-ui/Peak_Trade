"""Read one declared commit from Git objects. The worktree is not a source."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class GitEntryV1:
    path: str
    object_sha: str
    mode: str
    object_type: str


def _git(
    repo: Path, args: list[str], *, binary: bool = False
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        env={
            **os.environ,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_OPTIONAL_LOCKS": "0",
        },
    )


def resolve_commit_v1(repo: Path, commit: str) -> str:
    proc = _git(repo, ["rev-parse", "--verify", f"{commit}^{{commit}}"])
    if proc.returncode != 0:
        raise ValueError("COMMIT_NOT_FOUND")
    return proc.stdout.decode("utf-8").strip()


def list_entries_v1(
    repo: Path,
    commit: str,
    prefixes: Sequence[str] | None = None,
) -> list[GitEntryV1]:
    """List one commit. None indexes the whole tree once. A prefix list is a slice."""
    if prefixes is not None and len(prefixes) == 0:
        return []
    args = ["ls-tree", "-r", commit]
    if prefixes:
        args.append("--")
        args.extend(prefixes)
    proc = _git(repo, args)
    if proc.returncode != 0:
        raise ValueError("TREE_UNREADABLE")
    by_path: dict[str, GitEntryV1] = {}
    for line in proc.stdout.decode("utf-8").splitlines():
        meta, path = line.split("\t", 1)
        mode, object_type, object_sha = meta.split(" ")
        by_path[path] = GitEntryV1(path, object_sha, mode, object_type)
    return [by_path[path] for path in sorted(by_path)]


def read_blob_v1(repo: Path, blob_sha: str) -> bytes:
    proc = _git(repo, ["cat-file", "blob", blob_sha])
    if proc.returncode != 0:
        raise ValueError("BLOB_UNREADABLE")
    return proc.stdout
