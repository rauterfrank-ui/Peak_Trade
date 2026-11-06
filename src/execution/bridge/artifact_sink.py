from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ArtifactSink(Protocol):
    def write_bytes(self, relpath: str, data: bytes) -> None:  # pragma: no cover
        ...


class FileSystemArtifactSink:
    """
    Deterministic filesystem sink.

    Contract:
    - No timestamps/randomness in filenames.
    - Atomic write: write temp + rename.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)

    def write_bytes(self, relpath: str, data: bytes) -> None:
        target = self.base_dir / relpath
        target.parent.mkdir(parents=True, exist_ok=True)

        # Deterministic temp path (no randomness). Safe for sequential CI runs.
        tmp = target.with_name(target.name + ".tmp")
        if tmp.exists():
            tmp.unlink()
        tmp.write_bytes(data)
        tmp.replace(target)
