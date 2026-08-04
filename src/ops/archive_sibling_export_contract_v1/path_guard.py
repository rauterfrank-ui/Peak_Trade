"""Path confinement for archive sibling writes under readmodels/."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath


READMODELS_DIRNAME = "readmodels"


class ArchiveSiblingPathErrorV1(ValueError):
    """Caller misuse or unusable path arguments (not an operator BLOCKED result)."""


@dataclass(frozen=True)
class ResolvedArchiveSiblingPathV1:
    """Resolved, confined target path under ``<archive_root>/readmodels``."""

    archive_root: Path
    readmodels_root: Path
    target_path: Path
    target_relative_posix: str


def _as_path(value: Path | str, *, field: str) -> Path:
    if isinstance(value, Path):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ArchiveSiblingPathErrorV1(f"{field} must be non-empty")
        return Path(text)
    raise ArchiveSiblingPathErrorV1(f"{field} must be Path or str")


def resolve_archive_sibling_target_v1(
    *,
    archive_root: Path | str,
    target_relative_path: Path | str,
) -> ResolvedArchiveSiblingPathV1:
    """Resolve and confine ``target_relative_path`` under archive ``readmodels/``.

    Fail-closed rules:
    - ``target_relative_path`` must be relative (absolute blocked)
    - no ``..`` traversal segments
    - must live under ``<archive_root>/readmodels``
    - resolved realpath must stay under resolved readmodels root (symlink escape)
    - no archive discovery / latest / fallback
    """
    root = _as_path(archive_root, field="archive_root").expanduser()
    rel = _as_path(target_relative_path, field="target_relative_path")

    if rel.is_absolute():
        raise ArchiveSiblingPathErrorV1("target_relative_path must be relative")

    # Normalize to posix segments for traversal checks (independent of OS sep).
    posix = PurePosixPath(rel.as_posix())
    if posix.is_absolute() or str(posix).startswith("/"):
        raise ArchiveSiblingPathErrorV1("target_relative_path must be relative")
    if any(part == ".." for part in posix.parts):
        raise ArchiveSiblingPathErrorV1("target_relative_path must not contain '..'")
    if not posix.parts:
        raise ArchiveSiblingPathErrorV1("target_relative_path must not be empty")
    if posix.parts[0] != READMODELS_DIRNAME:
        raise ArchiveSiblingPathErrorV1(
            f"target_relative_path must be under readmodels/ (got {posix.as_posix()!r})"
        )
    if len(posix.parts) < 2:
        raise ArchiveSiblingPathErrorV1("target_relative_path must name a file under readmodels/")

    try:
        archive_resolved = root.resolve(strict=False)
    except OSError as exc:
        raise ArchiveSiblingPathErrorV1(f"archive_root resolve failed: {exc}") from exc

    readmodels_root = (archive_resolved / READMODELS_DIRNAME).resolve(strict=False)
    # Build candidate without trusting pre-existing symlinks for relative join.
    candidate = (archive_resolved / Path(*posix.parts)).resolve(strict=False)

    try:
        candidate.relative_to(readmodels_root)
    except ValueError as exc:
        raise ArchiveSiblingPathErrorV1(
            "resolved target escaped <archive_root>/readmodels"
        ) from exc

    if candidate == readmodels_root:
        raise ArchiveSiblingPathErrorV1("target_relative_path must name a file under readmodels/")

    return ResolvedArchiveSiblingPathV1(
        archive_root=archive_resolved,
        readmodels_root=readmodels_root,
        target_path=candidate,
        target_relative_posix=posix.as_posix(),
    )
