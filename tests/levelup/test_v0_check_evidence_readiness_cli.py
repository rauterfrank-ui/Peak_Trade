"""Subprocess tests for LevelUp v0 `check-evidence-readiness` CLI contract."""

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


def test_check_evidence_readiness_cli_full_readiness(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    p1 = "out/ops/readiness/a/"
    p2 = "out/ops/readiness/b/"
    (tmp_path / p1).mkdir(parents=True)
    (tmp_path / p2).mkdir(parents=True)
    s1 = SliceContractV0(
        slice_id="A",
        title="A",
        contract_summary="c1",
        evidence=EvidenceBundleRefV0(relative_dir=p1),
    )
    s2 = SliceContractV0(
        slice_id="B",
        title="B",
        contract_summary="c2",
        evidence=EvidenceBundleRefV0(relative_dir=p2),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s1, s2)))

    r = _run_cli(["check-evidence-readiness", str(manifest)])
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["total_slices"] == 2
    assert out["with_evidence_count"] == 2
    assert out["without_evidence_count"] == 0
    assert out["checked_path_count"] == 2
    assert out["missing_path_count"] == 0
    assert out["not_dir_count"] == 0
    assert [e["status"] for e in out["entries"]] == ["ok", "ok"]


def test_check_evidence_readiness_cli_mixed_coverage(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    p1 = "out/ops/readiness/only_one/"
    (tmp_path / p1).mkdir(parents=True)
    s1 = SliceContractV0(slice_id="A", title="A", contract_summary="c1")
    s2 = SliceContractV0(
        slice_id="B",
        title="B",
        contract_summary="c2",
        evidence=EvidenceBundleRefV0(relative_dir=p1),
    )
    s3 = SliceContractV0(slice_id="C", title="C", contract_summary="c3")
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s1, s2, s3)))

    r = _run_cli(["check-evidence-readiness", str(manifest)])
    assert r.returncode == 3, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["total_slices"] == 3
    assert out["with_evidence_count"] == 1
    assert out["without_evidence_count"] == 2
    assert out["checked_path_count"] == 1
    assert out["missing_path_count"] == 0
    assert out["not_dir_count"] == 0
    assert [e["status"] for e in out["entries"]] == ["missing_evidence", "ok", "missing_evidence"]
    assert out["entries"][0]["exists"] is None
    assert out["entries"][0]["is_dir"] is None


def test_check_evidence_readiness_cli_missing_path(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    missing = "out/ops/readiness/missing/"
    s1 = SliceContractV0(
        slice_id="M1",
        title="M1",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=missing),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s1,)))

    r = _run_cli(["check-evidence-readiness", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["missing_path_count"] == 1
    assert out["not_dir_count"] == 0
    assert out["entries"][0]["status"] == "missing_path"


def test_check_evidence_readiness_cli_not_a_directory(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    file_rel = "out/ops/readiness/not_dir"
    p = tmp_path / file_rel
    p.parent.mkdir(parents=True)
    p.write_text("x", encoding="utf-8")
    s1 = SliceContractV0(
        slice_id="F1",
        title="F1",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=file_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s1,)))

    r = _run_cli(["check-evidence-readiness", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["missing_path_count"] == 0
    assert out["not_dir_count"] == 1
    assert out["entries"][0]["status"] == "not_a_directory"


def test_check_evidence_readiness_cli_mixed_manifest_statuses(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ok_rel = "out/ops/readiness/ok/"
    missing_rel = "out/ops/readiness/missing/"
    not_dir_rel = "out/ops/readiness/not_dir"
    (tmp_path / ok_rel).mkdir(parents=True)
    not_dir_target = tmp_path / not_dir_rel
    not_dir_target.parent.mkdir(parents=True, exist_ok=True)
    not_dir_target.write_text("x", encoding="utf-8")
    s_ok = SliceContractV0(
        slice_id="ok",
        title="ok",
        contract_summary="ok",
        evidence=EvidenceBundleRefV0(relative_dir=ok_rel),
    )
    s_no_ev = SliceContractV0(slice_id="no_ev", title="no_ev", contract_summary="no_ev")
    s_missing = SliceContractV0(
        slice_id="missing",
        title="missing",
        contract_summary="missing",
        evidence=EvidenceBundleRefV0(relative_dir=missing_rel),
    )
    s_not_dir = SliceContractV0(
        slice_id="not_dir",
        title="not_dir",
        contract_summary="not_dir",
        evidence=EvidenceBundleRefV0(relative_dir=not_dir_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s_ok, s_no_ev, s_missing, s_not_dir)))

    r = _run_cli(["check-evidence-readiness", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["total_slices"] == 4
    assert out["with_evidence_count"] == 3
    assert out["without_evidence_count"] == 1
    assert out["checked_path_count"] == 3
    assert out["missing_path_count"] == 1
    assert out["not_dir_count"] == 1
    assert [e["status"] for e in out["entries"]] == [
        "ok",
        "missing_evidence",
        "missing_path",
        "not_a_directory",
    ]


def test_check_evidence_readiness_cli_no_slices_is_ready(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0())

    r = _run_cli(["check-evidence-readiness", str(manifest)])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["total_slices"] == 0
    assert out["with_evidence_count"] == 0
    assert out["without_evidence_count"] == 0
    assert out["checked_path_count"] == 0
    assert out["missing_path_count"] == 0
    assert out["not_dir_count"] == 0
    assert out["entries"] == []


def test_check_evidence_readiness_cli_json_field_stability(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    rel = "out/ops/readiness/stable/"
    (tmp_path / rel).mkdir(parents=True)
    s1 = SliceContractV0(
        slice_id="S",
        title="S",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s1,)))

    r = _run_cli(["check-evidence-readiness", str(manifest)])
    out = json.loads(r.stdout.strip())
    assert set(out.keys()) >= {
        "ok",
        "schema",
        "command",
        "manifest_path",
        "total_slices",
        "with_evidence_count",
        "without_evidence_count",
        "checked_path_count",
        "missing_path_count",
        "not_dir_count",
        "entries",
    }
    ent = out["entries"][0]
    assert set(ent.keys()) >= {"slice_id", "has_evidence", "evidence", "exists", "is_dir", "status"}
