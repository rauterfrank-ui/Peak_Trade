"""Subprocess tests for LevelUp v0 `validate` CLI contract (exit codes + JSON on stdout)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

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


def test_validate_cli_success(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    w = _run_cli(["dump-empty", str(manifest)])
    assert w.returncode == 0, w.stderr

    v = _run_cli(["validate", str(manifest)])
    assert v.returncode == 0, v.stderr
    assert v.stderr.strip() == ""
    out = json.loads(v.stdout.strip())
    assert out["ok"] is True
    assert out["schema"] == "levelup/manifest/v0"
    assert out["slices"] == 0


def test_validate_cli_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    r = _run_cli(["validate", str(bad)])
    assert r.returncode == 2
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "input"
    assert payload["reason"] == "json_parse_failed"


def test_validate_cli_model_validation_failure(tmp_path: Path) -> None:
    p = tmp_path / "invalid_model.json"
    p.write_text('{"schema_version": "not-a-valid-manifest-schema"}', encoding="utf-8")
    r = _run_cli(["validate", str(p)])
    assert r.returncode == 3
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "validation"
    assert payload["reason"] == "model_validation_failed"
    assert isinstance(payload.get("issues"), list)


def test_validate_cli_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nope.json"
    r = _run_cli(["validate", str(missing)])
    assert r.returncode == 2
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "input"
    assert payload["reason"] == "manifest_read_failed"


@pytest.mark.skipif(sys.platform == "win32", reason="chmod semantics differ on Windows")
def test_validate_cli_unreadable_file(tmp_path: Path) -> None:
    manifest = tmp_path / "locked.json"
    manifest.write_text('{"schema_version": "levelup/manifest/v0"}', encoding="utf-8")
    manifest.chmod(0)
    try:
        r = _run_cli(["validate", str(manifest)])
    finally:
        manifest.chmod(0o644)
    assert r.returncode == 2
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "input"
    assert payload["reason"] == "manifest_read_failed"
