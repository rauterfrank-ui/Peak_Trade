"""Strict sidecar format gate: exactly one line '<64hex> <filename>' (fail-closed)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ops.sidecar_verify import (
    SidecarFormatError,
    validate_json_and_sidecar,
)


def test_valid_sidecar_line(tmp_path: Path) -> None:
    j = tmp_path / "a.json"
    s = tmp_path / "a.json.sha256"
    j.write_text("{}", encoding="utf-8")
    s.write_text("0" * 64 + "  a.json\n", encoding="utf-8")
    validate_json_and_sidecar(j, s)


def test_rejects_multi_line(tmp_path: Path) -> None:
    j = tmp_path / "a.json"
    s = tmp_path / "a.json.sha256"
    j.write_text("{}", encoding="utf-8")
    s.write_text(("0" * 64 + "  a.json\n") * 2, encoding="utf-8")
    with pytest.raises(SidecarFormatError):
        validate_json_and_sidecar(j, s)


def test_rejects_bad_hex(tmp_path: Path) -> None:
    j = tmp_path / "a.json"
    s = tmp_path / "a.json.sha256"
    j.write_text("{}", encoding="utf-8")
    s.write_text("z" * 64 + "  a.json\n", encoding="utf-8")
    with pytest.raises(SidecarFormatError):
        validate_json_and_sidecar(j, s)


def test_rejects_filename_mismatch(tmp_path: Path) -> None:
    j = tmp_path / "a.json"
    s = tmp_path / "a.json.sha256"
    j.write_text("{}", encoding="utf-8")
    s.write_text("0" * 64 + "  b.json\n", encoding="utf-8")
    with pytest.raises(SidecarFormatError):
        validate_json_and_sidecar(j, s)
