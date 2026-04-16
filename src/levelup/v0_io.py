"""JSON persistence for :class:`LevelUpManifestV0` (offline, repo-local files only)."""

from __future__ import annotations

from pathlib import Path

from src.levelup.v0_models import LevelUpManifestV0


def read_manifest(path: Path) -> LevelUpManifestV0:
    raw = path.read_text(encoding="utf-8")
    return LevelUpManifestV0.model_validate_json(raw)


def canonical_manifest_json(manifest: LevelUpManifestV0) -> str:
    return manifest.model_dump_json(indent=2) + "\n"


def write_manifest(path: Path, manifest: LevelUpManifestV0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_manifest_json(manifest), encoding="utf-8")
