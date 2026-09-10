"""PIT archive root — re-exports the shared resolver; keeps chrono layout."""

from __future__ import annotations

from pathlib import Path

from src.research.external_data_archive_root_v1 import (
    ArchiveRootError,
    assert_path_under_archive,
    resolve_archive_root,
    validate_archive_root,
)

__all__ = [
    "ArchiveRootError",
    "resolve_archive_root",
    "validate_archive_root",
    "archive_layout",
    "assert_path_under_archive",
]


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
