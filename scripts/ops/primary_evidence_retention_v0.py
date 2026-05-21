#!/usr/bin/env python3
"""Shared primary evidence manifest helpers (Preflight §2a; non-authorizing)."""

from __future__ import annotations

import hashlib
from pathlib import Path

MANIFEST_FILENAME = "MANIFEST.sha256"


def write_manifest_sha256(root: Path) -> None:
    """Write MANIFEST.sha256 over all files under root (excluding the manifest itself)."""
    lines: list[str] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.name == MANIFEST_FILENAME:
            continue
        rel = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {rel}")
    manifest = root / MANIFEST_FILENAME
    manifest.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def verify_manifest_sha256(root: Path) -> tuple[bool, str]:
    """Verify MANIFEST.sha256 against files under root. Fail closed on any mismatch."""
    manifest = root / MANIFEST_FILENAME
    if not manifest.is_file():
        return False, "MANIFEST.sha256 missing"
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            return False, f"invalid manifest line: {line!r}"
        digest, rel = parts
        path = root / rel
        if not path.is_file():
            return False, f"missing manifest entry: {rel}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            return False, f"checksum mismatch: {rel}"
    return True, ""
