"""Tests for Level-Up v0 manifest contracts (offline, no live I/O)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
from pydantic import ValidationError

from src.levelup.v0_io import read_manifest, write_manifest
from src.levelup.v0_models import EvidenceBundleRefV0, LevelUpManifestV0, SliceContractV0


def _run_levelup_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "src.levelup.cli", *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
    )


def test_manifest_roundtrip_empty(tmp_path: Path) -> None:
    m = LevelUpManifestV0()
    p = tmp_path / "m.json"
    write_manifest(p, m)
    loaded = read_manifest(p)
    assert loaded == m
    assert loaded.schema_version == "levelup/manifest/v0"


def test_manifest_with_slice_and_evidence(tmp_path: Path) -> None:
    ev = EvidenceBundleRefV0(relative_dir="out/ops/slice_demo_001/")
    sl = SliceContractV0(
        slice_id="S1-R3",
        title="Live execution gated",
        contract_summary="Without enabled+armed+token → no order.",
        evidence=ev,
    )
    m = LevelUpManifestV0(title="Test", slices=(sl,))
    p = tmp_path / "m.json"
    write_manifest(p, m)
    loaded = read_manifest(p)
    assert loaded.slices[0].evidence is not None
    assert loaded.slices[0].evidence.relative_dir == "out/ops/slice_demo_001/"


@pytest.mark.parametrize(
    "bad",
    [
        "out/evidence/x",
        "../out/ops/x",
        "out/ops/../other",
        "out/ops/",
    ],
)
def test_evidence_path_rejected(bad: str) -> None:
    with pytest.raises(ValidationError):
        EvidenceBundleRefV0(relative_dir=bad)


def test_manifest_rejects_duplicate_slice_id() -> None:
    sl_a = SliceContractV0(
        slice_id="SAME",
        title="First",
        contract_summary="x",
    )
    sl_b = SliceContractV0(
        slice_id="SAME",
        title="Second",
        contract_summary="y",
    )
    with pytest.raises(ValidationError) as exc:
        LevelUpManifestV0(slices=(sl_a, sl_b))
    assert "duplicate slice_id" in str(exc.value).lower()


@pytest.mark.parametrize("bad_title", ["", "   ", "\t\n"])
def test_manifest_root_title_rejects_empty_after_strip(bad_title: str) -> None:
    with pytest.raises(ValidationError):
        LevelUpManifestV0(title=bad_title)


def test_manifest_root_title_strips_surrounding_whitespace() -> None:
    m = LevelUpManifestV0(title="  Trimmed  ")
    assert m.title == "Trimmed"


def test_cli_validate_and_dump_empty(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    exe = _run_levelup_cli(["dump-empty", str(manifest)])
    assert exe.returncode == 0, exe.stderr
    out = json.loads(exe.stdout.strip())
    assert out["ok"] is True

    v = _run_levelup_cli(["validate", str(manifest)])
    assert v.returncode == 0, v.stderr
    meta = json.loads(v.stdout.strip())
    assert meta["ok"] is True
    assert meta["slices"] == 0


def test_cli_dump_empty_target_path_is_directory(tmp_path: Path) -> None:
    """Directory as output path → exit 2, reason target_path_is_directory."""
    d = tmp_path / "out_dir"
    d.mkdir()
    r = _run_levelup_cli(["dump-empty", str(d)])
    assert r.returncode == 2, r.stderr
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "input"
    assert payload["reason"] == "target_path_is_directory"


@pytest.mark.skipif(sys.platform == "win32", reason="chmod write-deny semantics differ on Windows")
def test_cli_dump_empty_not_writable_target_file(tmp_path: Path) -> None:
    """Existing file without write permission → exit 2, reason manifest_write_failed."""
    manifest = tmp_path / "locked.json"
    manifest.write_text("{}", encoding="utf-8")
    manifest.chmod(0o444)
    try:
        r = _run_levelup_cli(["dump-empty", str(manifest)])
    finally:
        manifest.chmod(0o644)
    assert r.returncode == 2, r.stderr
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "input"
    assert payload["reason"] == "manifest_write_failed"


def test_cli_validate_utf8_decode_failed(tmp_path: Path) -> None:
    """Invalid UTF-8 bytes → exit 2, reason utf8_decode_failed (Path.read_text)."""
    bad = tmp_path / "not_utf8.json"
    bad.write_bytes(b"\xff\xfe\x00")
    r = _run_levelup_cli(["validate", str(bad)])
    assert r.returncode == 2, r.stderr
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "input"
    assert payload["reason"] == "utf8_decode_failed"


def test_cli_validate_path_is_directory(tmp_path: Path) -> None:
    """A directory path is not a readable manifest file → OSError, manifest_read_failed."""
    d = tmp_path / "not_a_file"
    d.mkdir()
    r = _run_levelup_cli(["validate", str(d)])
    assert r.returncode == 2, r.stderr
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "input"
    assert payload["reason"] == "manifest_read_failed"


def test_cli_validate_empty_file_json_parse_failed(tmp_path: Path) -> None:
    """Empty file is not valid JSON → exit 2, json_parse_failed."""
    empty = tmp_path / "empty.json"
    empty.write_text("", encoding="utf-8")
    r = _run_levelup_cli(["validate", str(empty)])
    assert r.returncode == 2, r.stderr
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "input"
    assert payload["reason"] == "json_parse_failed"


def test_cli_format_success_canonical_rewrite(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"title":"  Trimmed title  ","schema_version":"levelup/manifest/v0","slices":[]}',
        encoding="utf-8",
    )
    r = _run_levelup_cli(["format", str(manifest)])
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is True
    assert payload["wrote"] == str(manifest)
    assert payload["schema"] == "levelup/manifest/v0"
    assert payload["slices"] == 0

    expected = LevelUpManifestV0(title="  Trimmed title  ").model_dump_json(indent=2) + "\n"
    assert manifest.read_text(encoding="utf-8") == expected


def test_cli_format_invalid_manifest_model_validation_failed(tmp_path: Path) -> None:
    bad = tmp_path / "bad_manifest.json"
    bad.write_text('{"schema_version":"not-a-valid-manifest-schema"}', encoding="utf-8")
    r = _run_levelup_cli(["format", str(bad)])
    assert r.returncode == 3, r.stderr
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "validation"
    assert payload["reason"] == "model_validation_failed"


@pytest.mark.skipif(sys.platform == "win32", reason="chmod write-deny semantics differ on Windows")
def test_cli_format_not_writable_target_file(tmp_path: Path) -> None:
    manifest = tmp_path / "locked.json"
    write_manifest(manifest, LevelUpManifestV0())
    manifest.chmod(0o444)
    try:
        r = _run_levelup_cli(["format", str(manifest)])
    finally:
        manifest.chmod(0o644)
    assert r.returncode == 2, r.stderr
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "input"
    assert payload["reason"] == "manifest_write_failed"


def test_cli_canonical_check_already_canonical(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0())
    r = _run_levelup_cli(["canonical-check", str(manifest)])
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is True
    assert payload["canonical"] is True
    assert payload["schema"] == "levelup/manifest/v0"
    assert payload["slices"] == 0


def test_cli_canonical_check_valid_but_not_canonical(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"title":"  Trim me  ","schema_version":"levelup/manifest/v0","slices":[]}',
        encoding="utf-8",
    )
    r = _run_levelup_cli(["canonical-check", str(manifest)])
    assert r.returncode == 3, r.stderr
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "validation"
    assert payload["reason"] == "manifest_not_canonical"
    assert payload["canonical"] is False
    assert payload["schema"] == "levelup/manifest/v0"
    assert payload["slices"] == 0


def test_cli_canonical_check_invalid_manifest_model_validation_failed(tmp_path: Path) -> None:
    bad = tmp_path / "bad_manifest.json"
    bad.write_text('{"schema_version":"not-a-valid-manifest-schema"}', encoding="utf-8")
    r = _run_levelup_cli(["canonical-check", str(bad)])
    assert r.returncode == 3, r.stderr
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "validation"
    assert payload["reason"] == "model_validation_failed"


def test_cli_canonical_check_empty_file_json_parse_failed(tmp_path: Path) -> None:
    """Leere Datei ist kein gültiges JSON → Exit 2, json_parse_failed (wie validate)."""
    empty = tmp_path / "empty.json"
    empty.write_text("", encoding="utf-8")
    r = _run_levelup_cli(["canonical-check", str(empty)])
    assert r.returncode == 2, r.stderr
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "input"
    assert payload["reason"] == "json_parse_failed"


def test_cli_export_json_schema_success() -> None:
    r = _run_levelup_cli(["export-json-schema"])
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is True
    assert payload["schema"] == "levelup/manifest/v0"
    schema = payload["json_schema"]
    assert schema["title"] == "LevelUpManifestV0"
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "schema_version" in schema["properties"]
