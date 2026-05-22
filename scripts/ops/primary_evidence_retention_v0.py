#!/usr/bin/env python3
"""Shared primary evidence manifest helpers (Preflight §2a/§2a.1; non-authorizing).

Machine markers (stable literals for contract tests):

```
PRIMARY_EVIDENCE_SHARED_HELPER_V0=true
FUTURE_RUNS_REQUIRE_DURABLE_ARCHIVE_ROOT=true
TMP_ONLY_EVIDENCE_INVALID=true
MANIFEST_VERIFY_REQUIRED=true
CLOSEOUT_REFERENCE_REQUIRED=true
RUN_INCOMPLETE_WITHOUT_PRIMARY_EVIDENCE=true
EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true
```
"""

from __future__ import annotations

import hashlib
from pathlib import Path

MANIFEST_FILENAME = "MANIFEST.sha256"

# Closeout filenames referenced by §2a.1 hard gate (index only; owners remain canonical).
KNOWN_CLOSEOUT_FILENAMES = (
    "scheduler_completion_closeout_v0.json",
    "supervisor_session_closeout_v0.json",
)


def is_under_tmp(path: Path) -> bool:
    """Return True when path resolves under /tmp (including /private/tmp on macOS)."""
    try:
        resolved = path.resolve()
        for tmp_root in (Path("/tmp").resolve(), Path("/private/tmp").resolve()):
            if resolved == tmp_root or tmp_root in resolved.parents:
                return True
        return False
    except OSError:
        text = str(path)
        return text.startswith("/tmp") or text.startswith("/private/tmp")


def require_durable_archive_root(path: Path) -> tuple[bool, str]:
    """Fail closed when primary evidence root is missing or under /tmp."""
    if is_under_tmp(path):
        return False, "archive root must be outside /tmp"
    if not path.exists():
        return False, f"archive root missing: {path}"
    return True, ""


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


def finalize_primary_evidence_root(root: Path) -> tuple[bool, str]:
    """Write MANIFEST.sha256 then verify. Fail closed on verify failure."""
    write_manifest_sha256(root)
    return verify_manifest_sha256(root)
