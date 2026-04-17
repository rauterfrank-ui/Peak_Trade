"""Subprocess tests for LevelUp v0 `check-evidence-attestation-uniqueness` CLI contract."""

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


def test_check_evidence_attestation_uniqueness_cli_all_ok_exactly_one_attestation_per_slice(
    tmp_path: Path,
) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_a = "out/ops/attestation_uniqueness/all_ok_a/"
    ev_b = "out/ops/attestation_uniqueness/all_ok_b/"
    dir_a = tmp_path / ev_a
    dir_b = tmp_path / ev_b
    dir_a.mkdir(parents=True, exist_ok=True)
    dir_b.mkdir(parents=True, exist_ok=True)
    (dir_a / "A_ATTESTATION.txt").write_text("ok", encoding="utf-8")
    (dir_b / "B_ATTESTATION.txt").write_text("ok", encoding="utf-8")

    s1 = SliceContractV0(
        slice_id="U1",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_a),
    )
    s2 = SliceContractV0(
        slice_id="U2",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_b),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s1, s2)))

    r = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["command"] == "check-evidence-attestation-uniqueness"
    assert out["summary"]["total_slices"] == 2
    assert out["summary"]["checked_slices"] == 2
    assert out["summary"]["ok_slices"] == 2
    assert out["summary"]["missing_attestation_slices"] == 0
    assert out["summary"]["multiple_attestations_slices"] == 0
    assert out["summary"]["missing_path_slices"] == 0
    assert out["summary"]["not_a_directory_slices"] == 0


def test_check_evidence_attestation_uniqueness_cli_missing_attestation(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_uniqueness/missing_attestation/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "note.txt").write_text("x", encoding="utf-8")

    sl = SliceContractV0(
        slice_id="U3",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "missing_attestation"
    assert out["entries"][0]["attestation_count"] == 0


def test_check_evidence_attestation_uniqueness_cli_multiple_attestations(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_uniqueness/multiple_attestations/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "A_ATTESTATION.txt").write_text("ok", encoding="utf-8")
    (evidence_dir / "B_ATTESTATION.txt").write_text("ok", encoding="utf-8")

    sl = SliceContractV0(
        slice_id="U4",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "multiple_attestations"
    assert out["entries"][0]["attestation_matches"] == [
        "A_ATTESTATION.txt",
        "B_ATTESTATION.txt",
    ]
    assert out["entries"][0]["attestation_count"] == 2


def test_check_evidence_attestation_uniqueness_cli_missing_path(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_uniqueness/missing_path/"
    sl = SliceContractV0(
        slice_id="U5",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "missing_path"


def test_check_evidence_attestation_uniqueness_cli_not_a_directory(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_uniqueness/not_a_directory"
    target = tmp_path / ev_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("x", encoding="utf-8")

    sl = SliceContractV0(
        slice_id="U6",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "not_a_directory"


def test_check_evidence_attestation_uniqueness_cli_mixed_manifest(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ok_rel = "out/ops/attestation_uniqueness/mixed_ok/"
    missing_rel = "out/ops/attestation_uniqueness/mixed_missing/"
    multi_rel = "out/ops/attestation_uniqueness/mixed_multiple/"
    missing_path_rel = "out/ops/attestation_uniqueness/mixed_missing_path/"
    not_dir_rel = "out/ops/attestation_uniqueness/mixed_not_dir"

    ok_dir = tmp_path / ok_rel
    ok_dir.mkdir(parents=True, exist_ok=True)
    (ok_dir / "ONLY_ATTESTATION.txt").write_text("ok", encoding="utf-8")

    missing_dir = tmp_path / missing_rel
    missing_dir.mkdir(parents=True, exist_ok=True)
    (missing_dir / "x.txt").write_text("x", encoding="utf-8")

    multi_dir = tmp_path / multi_rel
    multi_dir.mkdir(parents=True, exist_ok=True)
    (multi_dir / "A_ATTESTATION.txt").write_text("ok", encoding="utf-8")
    (multi_dir / "B_ATTESTATION.txt").write_text("ok", encoding="utf-8")

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
        slice_id="missing_att",
        title="missing_att",
        contract_summary="missing_att",
        evidence=EvidenceBundleRefV0(relative_dir=missing_rel),
    )
    s_multi = SliceContractV0(
        slice_id="multi",
        title="multi",
        contract_summary="multi",
        evidence=EvidenceBundleRefV0(relative_dir=multi_rel),
    )
    s_missing_path = SliceContractV0(
        slice_id="missing_path",
        title="missing_path",
        contract_summary="missing_path",
        evidence=EvidenceBundleRefV0(relative_dir=missing_path_rel),
    )
    s_not_dir = SliceContractV0(
        slice_id="not_dir",
        title="not_dir",
        contract_summary="not_dir",
        evidence=EvidenceBundleRefV0(relative_dir=not_dir_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        LevelUpManifestV0(slices=(s_ok, s_no_ev, s_missing, s_multi, s_missing_path, s_not_dir)),
    )

    r = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["summary"]["total_slices"] == 6
    assert out["summary"]["checked_slices"] == 5
    assert out["summary"]["ok_slices"] == 1
    assert out["summary"]["missing_attestation_slices"] == 1
    assert out["summary"]["multiple_attestations_slices"] == 1
    assert out["summary"]["missing_path_slices"] == 1
    assert out["summary"]["not_a_directory_slices"] == 1
    assert [e["status"] for e in out["entries"]] == [
        "ok",
        "missing_attestation",
        "multiple_attestations",
        "missing_path",
        "not_a_directory",
    ]


def test_check_evidence_attestation_uniqueness_cli_repo_root_not_found(tmp_path: Path) -> None:
    ev_rel = "out/ops/attestation_uniqueness/no_root/"
    sl = SliceContractV0(
        slice_id="U7",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["error"] == "input"
    assert out["reason"] == "repo_root_not_found"


def test_check_evidence_attestation_uniqueness_cli_no_evidence_slices_is_deterministically_green(
    tmp_path: Path,
) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    s1 = SliceContractV0(slice_id="A", title="A", contract_summary="c")
    s2 = SliceContractV0(slice_id="B", title="B", contract_summary="c")
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s1, s2)))

    r = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["summary"]["total_slices"] == 2
    assert out["summary"]["checked_slices"] == 0
    assert out["summary"]["ok_slices"] == 0
    assert out["summary"]["missing_attestation_slices"] == 0
    assert out["summary"]["multiple_attestations_slices"] == 0
    assert out["summary"]["missing_path_slices"] == 0
    assert out["summary"]["not_a_directory_slices"] == 0
    assert out["entries"] == []


def test_check_evidence_attestation_uniqueness_cli_stdout_is_exactly_one_json_object(
    tmp_path: Path,
) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_uniqueness/stdout/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "ONLY_ATTESTATION.txt").write_text("ok", encoding="utf-8")
    sl = SliceContractV0(
        slice_id="U8",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    assert r.returncode == 0, r.stderr
    lines = r.stdout.strip().splitlines()
    assert len(lines) == 1
    out = json.loads(lines[0])
    assert out["ok"] is True
    assert out["command"] == "check-evidence-attestation-uniqueness"


def test_check_evidence_attestation_uniqueness_cli_json_field_stability(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_uniqueness/stable/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "ONLY_ATTESTATION.txt").write_text("ok", encoding="utf-8")
    sl = SliceContractV0(
        slice_id="U9",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    out = json.loads(r.stdout.strip())
    assert set(out.keys()) >= {
        "ok",
        "schema",
        "command",
        "manifest_path",
        "summary",
        "entries",
    }
    assert set(out["summary"].keys()) >= {
        "total_slices",
        "checked_slices",
        "ok_slices",
        "missing_attestation_slices",
        "multiple_attestations_slices",
        "missing_path_slices",
        "not_a_directory_slices",
    }
    ent = out["entries"][0]
    assert set(ent.keys()) >= {
        "slice_id",
        "evidence",
        "status",
        "attestation_matches",
        "attestation_count",
        "repo_root",
        "resolved_path",
        "exists",
        "is_dir",
    }
