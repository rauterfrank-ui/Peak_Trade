"""Immutable merged-main / SHA / dirty tracked-worktree execution preflight.

Untracked files (including local ops evidence) do not fail this preflight.
Tracked dirty state, detached HEAD drift from origin/main, or SHA mismatch
fail closed. Network fetch is never performed.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ImmutableBaselinePreflightError(RuntimeError):
    """Fail-closed immutable baseline preflight violation."""


@dataclass(frozen=True)
class ImmutableBaselinePreflightResultV1:
    ok: bool
    head_sha: str
    origin_main_sha: str
    head_equals_origin_main: bool
    expected_sha: str | None
    expected_sha_match: bool | None
    tracked_worktree_clean: bool
    untracked_ignored_for_preflight: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "HEAD_SHA": self.head_sha,
            "ORIGIN_MAIN_SHA": self.origin_main_sha,
            "HEAD_EQUALS_ORIGIN_MAIN": self.head_equals_origin_main,
            "EXPECTED_SHA": self.expected_sha,
            "EXPECTED_SHA_MATCH": self.expected_sha_match,
            "TRACKED_WORKTREE_CLEAN": self.tracked_worktree_clean,
            "UNTRACKED_IGNORED_FOR_PREFLIGHT": self.untracked_ignored_for_preflight,
            "REASON": self.reason,
        }


def _run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        err = (completed.stderr or completed.stdout or "").strip()
        raise ImmutableBaselinePreflightError(f"GIT_COMMAND_FAILED:{args[0]}:{err}")
    return (completed.stdout or "").strip()


def _tracked_dirty(repo_root: Path) -> bool:
    # Porcelain entries starting with '??' are untracked — ignored by policy.
    raw = _run_git(repo_root, "status", "--porcelain=v1")
    if not raw:
        return False
    for line in raw.splitlines():
        if not line:
            continue
        if line.startswith("??"):
            continue
        return True
    return False


def evaluate_immutable_baseline_preflight_v1(
    *,
    repo_root: Path | None = None,
    expected_origin_main_sha: str | None = None,
) -> ImmutableBaselinePreflightResultV1:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    if not (root / ".git").exists():
        raise ImmutableBaselinePreflightError("GIT_REPOSITORY_REQUIRED")

    head_sha = _run_git(root, "rev-parse", "HEAD")
    origin_main_sha = _run_git(root, "rev-parse", "origin/main")
    head_eq = head_sha == origin_main_sha
    tracked_dirty = _tracked_dirty(root)
    tracked_clean = not tracked_dirty

    expected = str(expected_origin_main_sha).strip() if expected_origin_main_sha else None
    expected_match: bool | None
    if expected:
        expected_match = origin_main_sha == expected and head_sha == expected
    else:
        expected_match = None

    reasons: list[str] = []
    if not head_eq:
        reasons.append("HEAD_NE_ORIGIN_MAIN")
    if not tracked_clean:
        reasons.append("TRACKED_WORKTREE_DIRTY")
    if expected is not None and not expected_match:
        reasons.append("EXPECTED_SHA_MISMATCH")

    ok = len(reasons) == 0
    return ImmutableBaselinePreflightResultV1(
        ok=ok,
        head_sha=head_sha,
        origin_main_sha=origin_main_sha,
        head_equals_origin_main=head_eq,
        expected_sha=expected,
        expected_sha_match=expected_match,
        tracked_worktree_clean=tracked_clean,
        untracked_ignored_for_preflight=True,
        reason="PASS" if ok else "|".join(reasons),
    )


def assert_immutable_baseline_preflight_v1(
    *,
    repo_root: Path | None = None,
    expected_origin_main_sha: str | None = None,
) -> ImmutableBaselinePreflightResultV1:
    result = evaluate_immutable_baseline_preflight_v1(
        repo_root=repo_root,
        expected_origin_main_sha=expected_origin_main_sha,
    )
    if not result.ok:
        raise ImmutableBaselinePreflightError(f"IMMUTABLE_BASELINE_PREFLIGHT_FAIL:{result.reason}")
    return result
