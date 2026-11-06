"""CODE_SNAPSHOT and EVIDENCE_SNAPSHOT isolation."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CodeSnapshotV1:
    repository_path: str
    git_head: str
    worktree_identity: str
    dirty_fingerprint: str
    census_revision: str
    landscape_revision: str
    atlas_revision: str

    def bindings_for_snapshot_id(self) -> dict[str, str]:
        return {
            "git_head": self.git_head,
            "census_revision": self.census_revision,
            "landscape_revision": self.landscape_revision,
            "atlas_revision": self.atlas_revision,
            "dirty_fingerprint": self.dirty_fingerprint,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "CODE_SNAPSHOT",
            "repository_path": self.repository_path,
            "git_head": self.git_head,
            "worktree_identity": self.worktree_identity,
            "dirty_fingerprint": self.dirty_fingerprint,
            "census_revision": self.census_revision,
            "landscape_revision": self.landscape_revision,
            "atlas_revision": self.atlas_revision,
        }


@dataclass(frozen=True)
class EvidenceSnapshotV1:
    evidence_root: str | None
    ghv_evidence_revision: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "EVIDENCE_SNAPSHOT",
            "evidence_root": self.evidence_root,
            "ghv_evidence_revision": self.ghv_evidence_revision,
        }


def _git_head(repo_root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def _git_porcelain(repo_root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo_root), "status", "--porcelain"],
        text=True,
    )


def dirty_fingerprint(repo_root: Path) -> str:
    return hashlib.sha256(_git_porcelain(repo_root).encode("utf-8")).hexdigest()[:16]


def worktree_identity(repo_root: Path) -> str:
    try:
        git_dir = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "--git-dir"],
            text=True,
        ).strip()
        return hashlib.sha256(git_dir.encode()).hexdigest()[:16]
    except subprocess.CalledProcessError:
        return "unknown"


def build_code_snapshot_v1(
    *,
    repo_root: Path,
    census_doc: dict[str, Any],
    landscape_doc: dict[str, Any],
    atlas_meta: dict[str, Any],
) -> CodeSnapshotV1:
    return CodeSnapshotV1(
        repository_path=str(repo_root.resolve()),
        git_head=_git_head(repo_root),
        worktree_identity=worktree_identity(repo_root),
        dirty_fingerprint=dirty_fingerprint(repo_root),
        census_revision=str(census_doc.get("source_baseline_head", "")),
        landscape_revision=str(
            landscape_doc.get("evidence_baseline_sha")
            or landscape_doc.get("universe_map_consolidation_v1", {}).get(
                "consolidation_baseline_sha", ""
            )
        ),
        atlas_revision=str(
            atlas_meta.get("origin_main_sha") or atlas_meta.get("current_reviewed_at_sha", "")
        ),
    )


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_evidence_snapshot_v1(
    *,
    evidence_root: Path | None,
) -> EvidenceSnapshotV1:
    if evidence_root is None or not evidence_root.is_dir():
        return EvidenceSnapshotV1(evidence_root=None, ghv_evidence_revision=None)
    flight = evidence_root / "ghv_pre_external_runtime_flight_record_v1.jsonl"
    rev = file_sha256(flight) if flight.is_file() else None
    return EvidenceSnapshotV1(
        evidence_root=str(evidence_root.resolve()),
        ghv_evidence_revision=rev,
    )
