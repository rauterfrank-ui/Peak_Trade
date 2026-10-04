"""Verify repository identity matches Run contract before any run transition."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FixpointSelfCheckResultV1:
    ok: bool
    head_sha: str
    head_tree_sha: str
    expected_fixpoint_sha: str
    expected_tree_sha: str
    settings_digest: str
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "FIXPOINT_MATCH": self.ok,
            "HEAD_SHA": self.head_sha,
            "HEAD_TREE_SHA": self.head_tree_sha,
            "EXPECTED_FIXPOINT_SHA": self.expected_fixpoint_sha,
            "EXPECTED_TREE_SHA": self.expected_tree_sha,
            "SETTINGS_DIGEST": self.settings_digest,
            "blockers": list(self.blockers),
            "FIXPOINT_SELF_CHECK_READY": True,
        }


def _git_rev(repo_root: Path, spec: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", spec],
        cwd=str(repo_root),
        text=True,
    ).strip()


def evaluate_fixpoint_self_check_v1(
    *,
    repo_root: Path,
    expected_fixpoint_sha: str,
    expected_tree_sha: str,
    settings_digest: str,
) -> FixpointSelfCheckResultV1:
    root = Path(repo_root).resolve()
    blockers: list[str] = []
    try:
        head = _git_rev(root, "HEAD")
        tree = _git_rev(root, "HEAD^{tree}")
    except (subprocess.CalledProcessError, OSError) as exc:
        return FixpointSelfCheckResultV1(
            ok=False,
            head_sha="",
            head_tree_sha="",
            expected_fixpoint_sha=expected_fixpoint_sha,
            expected_tree_sha=expected_tree_sha,
            settings_digest=settings_digest,
            blockers=(f"GIT_REV_PARSE_FAILED:{exc}",),
        )
    if head != expected_fixpoint_sha:
        blockers.append("FIXPOINT_SHA_MISMATCH")
    if tree != expected_tree_sha:
        blockers.append("FIXPOINT_TREE_MISMATCH")
    if not settings_digest:
        blockers.append("SETTINGS_DIGEST_MISSING")
    return FixpointSelfCheckResultV1(
        ok=not blockers,
        head_sha=head,
        head_tree_sha=tree,
        expected_fixpoint_sha=expected_fixpoint_sha,
        expected_tree_sha=expected_tree_sha,
        settings_digest=settings_digest,
        blockers=tuple(blockers),
    )
