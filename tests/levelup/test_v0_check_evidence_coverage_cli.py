"""Subprocess tests for LevelUp v0 `check-evidence-coverage` CLI contract."""

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


def test_check_evidence_coverage_cli_full_coverage(tmp_path: Path) -> None:
    s1 = SliceContractV0(
        slice_id="A",
        title="A",
        contract_summary="c1",
        evidence=EvidenceBundleRefV0(relative_dir="out/ops/a/"),
    )
    s2 = SliceContractV0(
        slice_id="B",
        title="B",
        contract_summary="c2",
        evidence=EvidenceBundleRefV0(relative_dir="out/ops/b/"),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s1, s2)))

    r = _run_cli(["check-evidence-coverage", str(manifest)])
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["total_slices"] == 2
    assert out["with_evidence_count"] == 2
    assert out["without_evidence_count"] == 0
    assert out["coverage_ratio"] == 1.0
    assert out["entries"] == [
        {"slice_id": "A", "has_evidence": True, "evidence": "out/ops/a/"},
        {"slice_id": "B", "has_evidence": True, "evidence": "out/ops/b/"},
    ]


def test_check_evidence_coverage_cli_mixed_coverage(tmp_path: Path) -> None:
    s1 = SliceContractV0(slice_id="A", title="A", contract_summary="c1")
    s2 = SliceContractV0(
        slice_id="B",
        title="B",
        contract_summary="c2",
        evidence=EvidenceBundleRefV0(relative_dir="out/ops/b/"),
    )
    s3 = SliceContractV0(slice_id="C", title="C", contract_summary="c3")
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s1, s2, s3)))

    r = _run_cli(["check-evidence-coverage", str(manifest)])
    assert r.returncode == 3, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["total_slices"] == 3
    assert out["with_evidence_count"] == 1
    assert out["without_evidence_count"] == 2
    assert out["coverage_ratio"] == 1.0 / 3.0
    assert [e["has_evidence"] for e in out["entries"]] == [False, True, False]
    assert [e["evidence"] for e in out["entries"]] == [None, "out/ops/b/", None]


def test_check_evidence_coverage_cli_no_coverage(tmp_path: Path) -> None:
    s1 = SliceContractV0(slice_id="A", title="A", contract_summary="c1")
    s2 = SliceContractV0(slice_id="B", title="B", contract_summary="c2")
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s1, s2)))

    r = _run_cli(["check-evidence-coverage", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["total_slices"] == 2
    assert out["with_evidence_count"] == 0
    assert out["without_evidence_count"] == 2
    assert out["coverage_ratio"] == 0.0
    assert out["entries"] == [
        {"slice_id": "A", "has_evidence": False, "evidence": None},
        {"slice_id": "B", "has_evidence": False, "evidence": None},
    ]


def test_check_evidence_coverage_cli_json_field_stability(tmp_path: Path) -> None:
    sl = SliceContractV0(slice_id="S", title="t", contract_summary="c")
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-coverage", str(manifest)])
    out = json.loads(r.stdout.strip())
    assert set(out.keys()) >= {
        "ok",
        "manifest_path",
        "total_slices",
        "with_evidence_count",
        "without_evidence_count",
        "coverage_ratio",
        "entries",
    }
    ent = out["entries"][0]
    assert set(ent.keys()) >= {"slice_id", "has_evidence", "evidence"}


def test_check_evidence_coverage_cli_no_filesystem_dependency(tmp_path: Path) -> None:
    sl = SliceContractV0(
        slice_id="S",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir="out/ops/path_not_created/"),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-coverage", str(manifest)])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["with_evidence_count"] == 1
    assert out["without_evidence_count"] == 0
