"""Subprocess tests for LevelUp v0 `describe-slice` CLI contract (exit codes + JSON on stdout)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from src.levelup.v0_io import write_manifest
from src.levelup.v0_models import EvidenceBundleRefV0, LevelUpManifestV0, SliceContractV0

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


def test_describe_slice_cli_success_with_evidence(tmp_path: Path) -> None:
    ev = EvidenceBundleRefV0(relative_dir="out/ops/slice_demo_001/")
    sl = SliceContractV0(
        slice_id="S1-R3",
        title="Live execution gated",
        contract_summary="Without enabled+armed+token → no order.",
        evidence=ev,
    )
    m = LevelUpManifestV0(title="Test manifest", slices=(sl,))
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, m)

    r = _run_cli(["describe-slice", str(manifest), "S1-R3"])
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["schema"] == "levelup/manifest/v0"
    assert out["command"] == "describe-slice"
    assert out["slice_id"] == "S1-R3"
    assert out["title"] == "Live execution gated"
    assert out["contract_summary"] == "Without enabled+armed+token → no order."
    assert out["evidence"] == {"relative_dir": "out/ops/slice_demo_001/"}


def test_describe_slice_cli_success_without_evidence(tmp_path: Path) -> None:
    sl = SliceContractV0(
        slice_id="S0",
        title="No evidence slice",
        contract_summary="Summary only.",
    )
    m = LevelUpManifestV0(slices=(sl,))
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, m)

    r = _run_cli(["describe-slice", str(manifest), "S0"])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["slice_id"] == "S0"
    assert out["evidence"] is None


def test_describe_slice_cli_slice_not_found(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0())

    r = _run_cli(["describe-slice", str(manifest), "missing-id"])
    assert r.returncode == 3, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["error"] == "validation"
    assert out["reason"] == "slice_not_found"
    assert out["slice_id"] == "missing-id"
    assert out["schema"] == "levelup/manifest/v0"


def test_describe_slice_cli_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    r = _run_cli(["describe-slice", str(bad), "any"])
    assert r.returncode == 2
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "input"
    assert payload["reason"] == "json_parse_failed"


def test_describe_slice_cli_model_validation_failure(tmp_path: Path) -> None:
    p = tmp_path / "invalid_model.json"
    p.write_text('{"schema_version": "not-a-valid-manifest-schema"}', encoding="utf-8")
    r = _run_cli(["describe-slice", str(p), "x"])
    assert r.returncode == 3
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "validation"
    assert payload["reason"] == "model_validation_failed"


def test_describe_slice_cli_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nope.json"
    r = _run_cli(["describe-slice", str(missing), "id"])
    assert r.returncode == 2
    assert r.stderr.strip() == ""
    payload = json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"] == "input"
    assert payload["reason"] == "manifest_read_failed"
