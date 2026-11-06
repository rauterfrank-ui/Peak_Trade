"""Discover archive and repo canary evidence locations (read-only)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .constants_v1 import (
    ARCHIVE_RUN_CLASSES,
    CANARY_EVIDENCE_CAPABILITY_EXACT,
    CANARY_EVIDENCE_CAPABILITY_PREFIXES,
    RUN_CLASS_PAPER,
    RUN_CLASS_SHADOW,
    RUN_CLASS_TESTNET,
)

_TIMESTAMP_DIR_RE = re.compile(r"^\d{8}T\d{6}Z$")

_RUN_ID_LANE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^(p\d+|.*_paper_)", re.IGNORECASE), RUN_CLASS_PAPER),
    (re.compile(r"^(s\d+|.*_shadow_)", re.IGNORECASE), RUN_CLASS_SHADOW),
    (re.compile(r"^(t\d+|.*_testnet_)", re.IGNORECASE), RUN_CLASS_TESTNET),
)


def infer_run_class_from_run_id(run_id: str) -> str | None:
    for pattern, run_class in _RUN_ID_LANE_PATTERNS:
        if pattern.search(run_id):
            return run_class
    return None


@dataclass(frozen=True)
class ArchiveRunRef:
    run_class: str
    run_id: str
    run_dir: Path
    archive_root: Path


@dataclass(frozen=True)
class CanaryEvidenceRef:
    capability_id: str
    timestamp_dir: str
    evidence_dir: Path


def discover_archive_runs(archive_root: Path) -> list[ArchiveRunRef]:
    runs_root = archive_root / "runs"
    if not runs_root.is_dir():
        return []
    out: list[ArchiveRunRef] = []
    child_dirs = [p for p in runs_root.iterdir() if p.is_dir()]
    canonical_lane_layout = any(p.name in ARCHIVE_RUN_CLASSES for p in child_dirs)
    if canonical_lane_layout:
        for lane_dir in sorted(child_dirs):
            lane_id = lane_dir.name
            if lane_id not in ARCHIVE_RUN_CLASSES:
                continue
            for run_dir in sorted(lane_dir.iterdir()):
                if run_dir.is_dir():
                    out.append(
                        ArchiveRunRef(
                            run_class=lane_id,
                            run_id=run_dir.name,
                            run_dir=run_dir,
                            archive_root=archive_root,
                        )
                    )
        return out

    for run_dir in sorted(child_dirs):
        run_class = infer_run_class_from_run_id(run_dir.name)
        if run_class is None:
            continue
        out.append(
            ArchiveRunRef(
                run_class=run_class,
                run_id=run_dir.name,
                run_dir=run_dir,
                archive_root=archive_root,
            )
        )
    return out


def _is_canary_capability(name: str) -> bool:
    if name in CANARY_EVIDENCE_CAPABILITY_EXACT:
        return True
    lowered = name.lower()
    if "canary" in lowered and name.startswith("section_11_13"):
        return True
    return any(name.startswith(prefix) for prefix in CANARY_EVIDENCE_CAPABILITY_PREFIXES)


def discover_repo_canary_evidence(repo_root: Path) -> list[CanaryEvidenceRef]:
    ops_root = repo_root / "evidence" / "ops"
    if not ops_root.is_dir():
        return []
    out: list[CanaryEvidenceRef] = []
    for capability_dir in sorted(ops_root.iterdir()):
        if not capability_dir.is_dir():
            continue
        cap_id = capability_dir.name
        if cap_id.startswith("_"):
            continue
        if not _is_canary_capability(cap_id):
            continue
        for ts_dir in sorted(capability_dir.iterdir()):
            if not ts_dir.is_dir():
                continue
            if not _TIMESTAMP_DIR_RE.match(ts_dir.name):
                continue
            out.append(
                CanaryEvidenceRef(
                    capability_id=cap_id,
                    timestamp_dir=ts_dir.name,
                    evidence_dir=ts_dir,
                )
            )
    return out


def archive_evidence_locator(run_class: str, run_id: str, *, flat_layout: bool = False) -> str:
    if flat_layout:
        return f"runs/{run_id}"
    return f"runs/{run_class}/{run_id}"


def repo_canary_evidence_locator(capability_id: str, timestamp_dir: str) -> str:
    return f"evidence/ops/{capability_id}/{timestamp_dir}"


def synthetic_canary_run_id(capability_id: str, timestamp_dir: str) -> str:
    return f"{capability_id}__{timestamp_dir}"
