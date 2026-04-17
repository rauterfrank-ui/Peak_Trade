"""Subprocess tests for LevelUp v0 `check-evidence-bundle` CLI contract."""

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


def _write_bundle_ready_files(root: Path, rel: str) -> None:
    p = root / rel
    p.mkdir(parents=True, exist_ok=True)
    (p / "SHA256SUMS.txt").write_text("abc  sample.bundle.tgz\n", encoding="utf-8")
    (p / "sample.bundle.tgz").write_text("tgz", encoding="utf-8")
    (p / "A_CRAWLER_SUMMARY_1LINE.txt").write_text("summary", encoding="utf-8")


def test_check_evidence_bundle_cli_all_ready(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/bundle/all_ready/"
    _write_bundle_ready_files(tmp_path, ev_rel)
    sl = SliceContractV0(
        slice_id="E1",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-bundle", str(manifest)])
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["command"] == "check-evidence-bundle"
    assert out["checked_count"] == 1
    assert out["ready_count"] == 1
    assert out["not_ready_count"] == 0
    assert out["entries"][0]["status"] == "ok"
    assert out["entries"][0]["missing_requirements"] == []


def test_check_evidence_bundle_cli_missing_required_files(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/bundle/missing_required/"
    p = tmp_path / ev_rel
    p.mkdir(parents=True)
    (p / "only.bundle.tgz").write_text("tgz", encoding="utf-8")
    sl = SliceContractV0(
        slice_id="M1",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-bundle", str(manifest)])
    assert r.returncode == 3, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["ready_count"] == 0
    assert out["not_ready_count"] == 1
    assert out["entries"][0]["status"] == "missing_bundle_requirements"
    assert set(out["entries"][0]["missing_requirements"]) == {
        "sha256sums_txt",
        "crawler_summary_1line",
    }


def test_check_evidence_bundle_cli_missing_path(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/bundle/missing_path/"
    sl = SliceContractV0(
        slice_id="P1",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-bundle", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "missing_path"


def test_check_evidence_bundle_cli_not_a_directory(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/bundle/not_a_directory"
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

    r = _run_cli(["check-evidence-bundle", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "not_a_directory"


def test_check_evidence_bundle_cli_mixed_manifest(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ok_rel = "out/ops/bundle/mixed_ok/"
    missing_path_rel = "out/ops/bundle/mixed_missing/"
    not_dir_rel = "out/ops/bundle/mixed_not_dir"
    missing_req_rel = "out/ops/bundle/mixed_missing_requirements/"

    _write_bundle_ready_files(tmp_path, ok_rel)
    not_dir_target = tmp_path / not_dir_rel
    not_dir_target.parent.mkdir(parents=True, exist_ok=True)
    not_dir_target.write_text("x", encoding="utf-8")
    (tmp_path / missing_req_rel).mkdir(parents=True, exist_ok=True)
    (tmp_path / missing_req_rel / "SHA256SUMS.txt").write_text("abc", encoding="utf-8")

    s_ok = SliceContractV0(
        slice_id="ok",
        title="ok",
        contract_summary="ok",
        evidence=EvidenceBundleRefV0(relative_dir=ok_rel),
    )
    s_no_ev = SliceContractV0(slice_id="no_ev", title="no_ev", contract_summary="no_ev")
    s_missing = SliceContractV0(
        slice_id="missing_path",
        title="missing",
        contract_summary="missing",
        evidence=EvidenceBundleRefV0(relative_dir=missing_path_rel),
    )
    s_not_dir = SliceContractV0(
        slice_id="not_dir",
        title="not_dir",
        contract_summary="not_dir",
        evidence=EvidenceBundleRefV0(relative_dir=not_dir_rel),
    )
    s_missing_req = SliceContractV0(
        slice_id="missing_req",
        title="missing_req",
        contract_summary="missing_req",
        evidence=EvidenceBundleRefV0(relative_dir=missing_req_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        LevelUpManifestV0(slices=(s_ok, s_no_ev, s_missing, s_not_dir, s_missing_req)),
    )

    r = _run_cli(["check-evidence-bundle", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["checked_count"] == 4
    assert out["ready_count"] == 1
    assert out["not_ready_count"] == 3
    assert [e["status"] for e in out["entries"]] == [
        "ok",
        "missing_path",
        "not_a_directory",
        "missing_bundle_requirements",
    ]


def test_check_evidence_bundle_cli_repo_root_not_found(tmp_path: Path) -> None:
    ev_rel = "out/ops/bundle/no_root/"
    sl = SliceContractV0(
        slice_id="R1",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-bundle", str(manifest)])
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["error"] == "input"
    assert out["reason"] == "repo_root_not_found"


def test_check_evidence_bundle_cli_no_evidence_slices(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    s1 = SliceContractV0(slice_id="A", title="A", contract_summary="c")
    s2 = SliceContractV0(slice_id="B", title="B", contract_summary="c")
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s1, s2)))

    r = _run_cli(["check-evidence-bundle", str(manifest)])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["checked_count"] == 0
    assert out["ready_count"] == 0
    assert out["not_ready_count"] == 0
    assert out["entries"] == []


def test_check_evidence_bundle_cli_json_field_stability(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/bundle/stable/"
    _write_bundle_ready_files(tmp_path, ev_rel)
    sl = SliceContractV0(
        slice_id="S",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-bundle", str(manifest)])
    out = json.loads(r.stdout.strip())
    assert set(out.keys()) >= {
        "ok",
        "schema",
        "command",
        "manifest_path",
        "checked_count",
        "ready_count",
        "not_ready_count",
        "entries",
    }
    ent = out["entries"][0]
    assert set(ent.keys()) >= {
        "slice_id",
        "evidence",
        "exists",
        "is_dir",
        "required_checks",
        "missing_requirements",
        "status",
    }
