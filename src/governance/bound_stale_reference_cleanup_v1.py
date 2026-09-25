"""Bound stale reference cleanup for forbidden-surface docs during bulk repository cuts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping, Sequence

REASON_STALE_REFERENCE_CLEANUP_AUTHORIZED = "BOUND_STALE_REFERENCE_CLEANUP_AUTHORIZED"
REASON_STALE_REFERENCE_CLEANUP_INVALID = "BOUND_STALE_REFERENCE_CLEANUP_INVALID"
REASON_STALE_REFERENCE_CLEANUP_INSUFFICIENT = "BOUND_STALE_REFERENCE_CLEANUP_INSUFFICIENT"

_REPO_PATH_RE = re.compile(r"(?:src|tests|scripts|config|docs)/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+")
_MARKDOWN_PAREN_REL_PATH_RE = re.compile(r"\(\.\./([^)]+)\)")
_CAPABILITY_INCREASE_RE = re.compile(
    r"\b(LIVE_AUTHORIZED|TESTNET_AUTHORIZED|CANARY_AUTHORIZED)\s*=\s*True"
    r"|\b(place_order|submit_order)\s*\(",
    re.I,
)
_BEHAVIOR_ADDED_RE = re.compile(r"^\s*(def |class |return |yield |import |from )")


def _normalize_path(path: str) -> str:
    return str(path).replace("\\", "/").strip().lstrip("./")


def _repo_paths_in_line(*, line: str, diff_path: str) -> list[str]:
    found = list(_REPO_PATH_RE.findall(line))
    parent = (
        _normalize_path(diff_path).rsplit("/", 1)[0] if "/" in _normalize_path(diff_path) else ""
    )
    for rel in _MARKDOWN_PAREN_REL_PATH_RE.findall(line):
        resolved = _normalize_path(str(PurePosixPath(parent) / rel))
        if resolved.startswith(("src/", "docs/", "scripts/", "config/", "tests/")):
            found.append(resolved)
    return found


def _content_lines(diff_text: str) -> tuple[list[str], list[str]]:
    removed: list[str] = []
    added: list[str] = []
    for raw in (diff_text or "").splitlines():
        if raw.startswith(("+++", "---", "@@", "diff ", "index ", "new file", "deleted file")):
            continue
        if raw.startswith("+"):
            added.append(raw[1:])
        elif raw.startswith("-"):
            removed.append(raw[1:])
    return removed, added


def _is_comment_or_blank(text: str) -> bool:
    stripped = text.strip()
    return (not stripped) or stripped.startswith("#")


@dataclass(frozen=True)
class StaleReferenceCleanupEvidence:
    valid: bool
    insufficient: bool
    notes: tuple[str, ...]


def classify_bound_stale_reference_cleanup_diff(
    *,
    path: str,
    diff_text: str,
    repo_root: Path,
    proven_removal_paths: frozenset[str],
) -> StaleReferenceCleanupEvidence:
    """Docs-only stale locator cleanup: removed refs must target absent paths."""
    notes: list[str] = []
    normalized = _normalize_path(path)
    if not normalized.endswith(".md"):
        return StaleReferenceCleanupEvidence(
            valid=False, insufficient=True, notes=("NOT_MARKDOWN",)
        )
    if not (repo_root / normalized).is_file():
        return StaleReferenceCleanupEvidence(
            valid=False, insufficient=True, notes=("FILE_NOT_PRESENT",)
        )

    removed, added = _content_lines(diff_text)
    for line in added:
        if _is_comment_or_blank(line):
            continue
        if _CAPABILITY_INCREASE_RE.search(line) or _BEHAVIOR_ADDED_RE.search(line):
            notes.append("FORBIDDEN_CAPABILITY_OR_BEHAVIOR_ADDED")
            return StaleReferenceCleanupEvidence(valid=False, insufficient=True, notes=tuple(notes))
        paths = _repo_paths_in_line(line=line, diff_path=normalized)
        for ref in paths:
            if (repo_root / ref).is_file() and ref not in proven_removal_paths:
                notes.append(f"ADDED_REFERENCE_TO_PRESENT_PATH:{ref}")
                return StaleReferenceCleanupEvidence(
                    valid=False, insufficient=True, notes=tuple(notes)
                )

    for line in removed:
        if _is_comment_or_blank(line):
            continue
        paths = _repo_paths_in_line(line=line, diff_path=normalized)
        if paths:
            for ref in paths:
                if (repo_root / ref).is_file():
                    notes.append(f"REMOVED_REFERENCE_STILL_PRESENT:{ref}")
                    return StaleReferenceCleanupEvidence(
                        valid=False, insufficient=True, notes=tuple(notes)
                    )
            continue
        notes.append("UNEXPLAINED_REMOVED_LINE")
        return StaleReferenceCleanupEvidence(valid=False, insufficient=True, notes=tuple(notes))

    if not removed and not added:
        return StaleReferenceCleanupEvidence(valid=False, insufficient=True, notes=("DIFF_EMPTY",))

    for line in added:
        if not _is_comment_or_blank(line):
            notes.append("ADDED_LINE_MUST_BE_COMMENT_FOR_STALE_CLEANUP")
            return StaleReferenceCleanupEvidence(valid=False, insufficient=True, notes=tuple(notes))

    return StaleReferenceCleanupEvidence(valid=True, insufficient=False, notes=tuple(notes))


@dataclass(frozen=True)
class BoundStaleReferenceCleanupDecision:
    applied: bool
    authorized_forbidden_paths: tuple[str, ...]
    reason_codes: tuple[str, ...]


def evaluate_bound_stale_reference_cleanup(
    forbidden_paths: Sequence[str],
    *,
    file_diffs: Mapping[str, str] | None,
    repo_root: Path,
    proven_removal_paths: frozenset[str],
    bulk_decommission_applied: bool,
) -> BoundStaleReferenceCleanupDecision:
    if not bulk_decommission_applied or file_diffs is None or not forbidden_paths:
        return BoundStaleReferenceCleanupDecision(
            applied=False,
            authorized_forbidden_paths=(),
            reason_codes=(),
        )

    authorized: list[str] = []
    for raw in forbidden_paths:
        path = _normalize_path(raw)
        evidence = classify_bound_stale_reference_cleanup_diff(
            path=path,
            diff_text=file_diffs.get(path) or file_diffs.get(raw) or "",
            repo_root=repo_root,
            proven_removal_paths=proven_removal_paths,
        )
        if evidence.valid:
            authorized.append(path)

    if not authorized:
        return BoundStaleReferenceCleanupDecision(
            applied=False,
            authorized_forbidden_paths=(),
            reason_codes=(REASON_STALE_REFERENCE_CLEANUP_INSUFFICIENT,),
        )

    return BoundStaleReferenceCleanupDecision(
        applied=True,
        authorized_forbidden_paths=tuple(sorted(set(authorized))),
        reason_codes=(REASON_STALE_REFERENCE_CLEANUP_AUTHORIZED,),
    )
