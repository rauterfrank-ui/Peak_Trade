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


def test_cli_validate_and_dump_empty(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    exe = subprocess.run(
        [sys.executable, "-m", "src.levelup.cli", "dump-empty", str(manifest)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    assert exe.returncode == 0, exe.stderr
    out = json.loads(exe.stdout.strip())
    assert out["ok"] is True

    v = subprocess.run(
        [sys.executable, "-m", "src.levelup.cli", "validate", str(manifest)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    assert v.returncode == 0, v.stderr
    meta = json.loads(v.stdout.strip())
    assert meta["ok"] is True
    assert meta["slices"] == 0
