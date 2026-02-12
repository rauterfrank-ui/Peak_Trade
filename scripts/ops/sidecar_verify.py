"""Strict sidecar format validator: exactly one line '<64hex> <filename>' (fail-closed)."""

from __future__ import annotations

import re
from pathlib import Path

_SIDECAR_RE = re.compile(r"^[0-9a-f]{64}\s+\S+\n?$")


class SidecarFormatError(RuntimeError):
    """Raised when sidecar format is invalid (wrong line count, bad hex, filename mismatch)."""

    pass


def read_single_line(path: Path) -> str:
    txt = path.read_text(encoding="utf-8")
    lines = txt.splitlines(True)
    if len(lines) != 1:
        raise SidecarFormatError(f"sidecar must have exactly 1 line: {path} (got {len(lines)})")
    return lines[0]


def validate_sidecar_line(sidecar_path: Path, expected_filename: str) -> None:
    line = read_single_line(sidecar_path)

    if not _SIDECAR_RE.match(line):
        raise SidecarFormatError(
            f"sidecar line must match '<64hex> <filename>': {sidecar_path} :: {line!r}"
        )

    digest, fname = line.strip().split(None, 1)
    if fname != expected_filename:
        raise SidecarFormatError(
            f"sidecar filename mismatch: {sidecar_path} "
            f"expected={expected_filename!r} got={fname!r}"
        )
    # digest is already 64 hex via regex


def validate_json_and_sidecar(json_path: Path, sidecar_path: Path) -> None:
    """Validate that sidecar has exactly one line '<64hex> <json_path.name>' (fail-closed)."""
    if json_path.name.endswith(".sha256"):
        raise SidecarFormatError(f"json_path looks like a sidecar: {json_path}")
    if sidecar_path.suffix != ".sha256":
        raise SidecarFormatError(f"sidecar must end with .sha256: {sidecar_path}")
    validate_sidecar_line(sidecar_path, expected_filename=json_path.name)
