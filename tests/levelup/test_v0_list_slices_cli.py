"""Subprocess tests for LevelUp v0 `list-slices` CLI contract (exit codes + JSON on stdout)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from src.levelup.v0_io import write_manifest
from src.levelup.v0_models import LevelUpManifestV0, SliceContractV0

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_cli(args: list[str], cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "src.levelup.cli", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
    )


def test_list_slices_cli_success_ordered(tmp_path: Path) -> None:
    s1 = SliceContractV0(slice_id="A", title="First", contract_summary="c1")
    s2 = SliceContractV0(slice_id="B", title="Second", contract_summary="c2")
    m = LevelUpManifestV0(title="Multi", slices=(s1, s2))
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, m)

    r = _run_cli(["list-slices", str(manifest)])
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["schema"] == "levelup/manifest/v0"
    assert out["command"] == "list-slices"
    assert out["count"] == 2
    assert out["slices"] == ["A", "B"]


def test_list_slices_cli_success_empty(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0())

    r = _run_cli(["list-slices", str(manifest)])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["count"] == 0
    assert out["slices"] == []


def test_list_slices_cli_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    r = _run_cli(["list-slices", str(bad)])
    assert r.returncode == 2
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "input"
    assert payload["reason"] == "json_parse_failed"


def test_list_slices_cli_model_validation_failure(tmp_path: Path) -> None:
    p = tmp_path / "invalid_model.json"
    p.write_text('{"schema_version": "not-a-valid-manifest-schema"}', encoding="utf-8")
    r = _run_cli(["list-slices", str(p)])
    assert r.returncode == 3
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "validation"
    assert payload["reason"] == "model_validation_failed"


def test_list_slices_cli_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nope.json"
    r = _run_cli(["list-slices", str(missing)])
    assert r.returncode == 2
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "input"
    assert payload["reason"] == "manifest_read_failed"
