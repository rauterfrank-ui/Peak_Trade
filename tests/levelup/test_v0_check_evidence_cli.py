"""Subprocess tests for LevelUp v0 `check-evidence` CLI contract (exit codes + JSON on stdout)."""

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


def _bootstrap_minimal_repo_layout(root: Path) -> None:
    (root / "pyproject.toml").write_text('[project]\nname = "peak_trade"\n', encoding="utf-8")
    (root / "src" / "levelup").mkdir(parents=True)
    (root / "src" / "levelup" / "__init__.py").write_text("", encoding="utf-8")


def test_check_evidence_cli_success(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/check_ev_ok/"
    (tmp_path / ev_rel).mkdir(parents=True)
    sl = SliceContractV0(
        slice_id="E1",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence", str(manifest)])
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["checked_count"] == 1
    assert out["missing_count"] == 0
    assert out["not_dir_count"] == 0
    assert out["entries"][0]["exists"] is True
    assert out["entries"][0]["is_dir"] is True
    assert out["entries"][0]["slice_id"] == "E1"
    assert out["entries"][0]["evidence"] == ev_rel


def test_check_evidence_cli_missing_path(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/missing_dir/"
    sl = SliceContractV0(
        slice_id="M1",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence", str(manifest)])
    assert r.returncode == 3, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["exists"] is False
    assert out["entries"][0]["is_dir"] is False
    assert out["missing_count"] >= 1


def test_check_evidence_cli_not_a_directory(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/is_a_file/"
    p = tmp_path / ev_rel
    p.parent.mkdir(parents=True)
    p.write_text("x", encoding="utf-8")
    sl = SliceContractV0(
        slice_id="F1",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["exists"] is True
    assert out["entries"][0]["is_dir"] is False
    assert out["not_dir_count"] >= 1


def test_check_evidence_cli_mixed_slices(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/mixed_ok/"
    (tmp_path / ev_rel).mkdir(parents=True)
    s0 = SliceContractV0(slice_id="no_ev", title="a", contract_summary="c0")
    s1 = SliceContractV0(
        slice_id="with_ev",
        title="b",
        contract_summary="c1",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s0, s1)))

    r = _run_cli(["check-evidence", str(manifest)])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["checked_count"] == 1
    assert len(out["entries"]) == 1
    assert out["entries"][0]["slice_id"] == "with_ev"


def test_check_evidence_cli_no_evidence_slices(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    sl = SliceContractV0(slice_id="solo", title="t", contract_summary="c")
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence", str(manifest)])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["checked_count"] == 0
    assert out["entries"] == []


def test_check_evidence_cli_json_field_stability(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/stable/"
    (tmp_path / ev_rel).mkdir(parents=True)
    sl = SliceContractV0(
        slice_id="S",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence", str(manifest)])
    out = json.loads(r.stdout.strip())
    assert set(out.keys()) >= {
        "ok",
        "manifest_path",
        "checked_count",
        "entries",
        "schema",
        "command",
    }
    ent = out["entries"][0]
    assert set(ent.keys()) >= {"slice_id", "evidence", "exists", "is_dir"}
