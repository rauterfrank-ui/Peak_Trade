"""Manifest write/verify helpers for Cap 7.1 evidence packages."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.constants_v1 import (
    MANIFEST_FILENAME,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.models_v1 import sha256_hex


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def write_manifest(root: Path, relative_files: tuple[str, ...]) -> str:
    lines: list[str] = []
    for rel in sorted(relative_files):
        digest = sha256_hex((root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    body = "\n".join(lines) + "\n"
    _atomic_write_text(root / MANIFEST_FILENAME, body)
    return sha256_hex(body.encode("utf-8"))


def verify_manifest(root: Path) -> int:
    manifest = Path(root) / MANIFEST_FILENAME
    if not manifest.is_file():
        return 2
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        path = Path(root) / rel
        if not path.is_file():
            return 1
        if sha256_hex(path.read_bytes()) != digest:
            return 1
    return 0
