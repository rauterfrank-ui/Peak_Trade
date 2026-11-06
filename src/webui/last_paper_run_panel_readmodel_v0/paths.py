"""Pfadvalidierung für durable run bundles (read-only, stdlib)."""

from __future__ import annotations

from pathlib import Path


def path_is_under_root(bundle_root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(bundle_root.resolve())
        return True
    except ValueError:
        return False


def safe_read_path(bundle_root: Path, relative: str) -> Path | None:
    p = (bundle_root / relative).resolve()
    if not path_is_under_root(bundle_root, p):
        return None
    return p
