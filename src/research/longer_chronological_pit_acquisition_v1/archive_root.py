"""External archive root contract — fail-closed writes outside git."""

from __future__ import annotations

import os
from pathlib import Path

from src.research.longer_chronological_pit_acquisition_v1 import ENV_ARCHIVE_ROOT


class ArchiveRootError(ValueError):
    """Raised when archive root is missing or unsafe."""


def _repo_root() -> Path:
    # src/research/<pkg>/archive_root.py → parents[3] = repo root
    return Path(__file__).resolve().parents[3]


def resolve_archive_root(
    *,
    explicit: str | Path | None = None,
    env: dict[str, str] | None = None,
    require_for_write: bool = True,
) -> Path | None:
    """Resolve external archive root.

    Returns None when not set and ``require_for_write`` is False (read-only/plan).
    Raises ArchiveRootError when required for write or when path is unsafe.
    """
    env_map = env if env is not None else os.environ
    raw = ""
    if explicit is not None:
        raw = str(explicit).strip()
    else:
        raw = str(env_map.get(ENV_ARCHIVE_ROOT, "") or "").strip()

    if not raw:
        if require_for_write:
            raise ArchiveRootError(
                f"MISSING_{ENV_ARCHIVE_ROOT}: writes require an external archive root"
            )
        return None

    root = Path(raw).expanduser().resolve()
    validate_archive_root(root)
    return root


def validate_archive_root(root: Path) -> None:
    """Reject repo-relative, filesystem root, and home-directory roots."""
    if not root.is_absolute():
        raise ArchiveRootError("ARCHIVE_ROOT_NOT_ABSOLUTE")

    # Bare filesystem root
    if root == Path(root.anchor):
        raise ArchiveRootError("ARCHIVE_ROOT_IS_FILESYSTEM_ROOT")

    home = Path.home().resolve()
    if root == home:
        raise ArchiveRootError("ARCHIVE_ROOT_IS_HOME_DIRECTORY")

    repo = _repo_root().resolve()
    try:
        root.relative_to(repo)
    except ValueError:
        pass
    else:
        # equal to repo root or nested under it
        raise ArchiveRootError("ARCHIVE_ROOT_INSIDE_GIT_REPO")


def archive_layout(root: Path) -> dict[str, Path]:
    """Canonical subdirectories under the external archive root."""
    base = root / "longer_chronological_pit" / "chrono_3y_v1"
    return {
        "base": base,
        "raw": base / "raw",
        "normalized": base / "normalized",
        "manifests": base / "manifests",
        "quarantine": base / "quarantine",
        "state": base / "state",
        "logs": base / "logs",
    }


def assert_path_under_archive(path: Path, root: Path) -> Path:
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ArchiveRootError("PATH_OUTSIDE_ARCHIVE_ROOT") from exc
    # Refuse if somehow also under git repo
    repo = _repo_root().resolve()
    try:
        resolved.relative_to(repo)
        raise ArchiveRootError("PATH_RESOLVES_INTO_GIT_REPO")
    except ValueError:
        pass
    return resolved
