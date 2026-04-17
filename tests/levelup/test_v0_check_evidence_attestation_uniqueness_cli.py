"""Subprocess tests for `check-evidence-attestation-uniqueness` manifest-or-target mode."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

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


def _mk_slice(slice_id: str, evidence_rel: str | None) -> SliceContractV0:
    if evidence_rel is None:
        return SliceContractV0(slice_id=slice_id, title=slice_id, contract_summary="c")
    return SliceContractV0(
        slice_id=slice_id,
        title=slice_id,
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=evidence_rel),
    )


def _write_manifest(tmp_path: Path, slices: tuple[SliceContractV0, ...]) -> Path:
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=slices))
    return manifest


def test_manifest_mode_all_ok(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_a = "out/ops/attestation_uniqueness/manifest_ok_a/"
    ev_b = "out/ops/attestation_uniqueness/manifest_ok_b/"
    (tmp_path / ev_a).mkdir(parents=True, exist_ok=True)
    (tmp_path / ev_b).mkdir(parents=True, exist_ok=True)
    (tmp_path / ev_a / "A_ATTESTATION.txt").write_text("ok", encoding="utf-8")
    (tmp_path / ev_b / "B_ATTESTATION.txt").write_text("ok", encoding="utf-8")
    manifest = _write_manifest(tmp_path, (_mk_slice("U1", ev_a), _mk_slice("U2", ev_b)))

    result = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout.strip())
    assert out["ok"] is True
    assert out["mode"] == "manifest"
    assert out["target_path"] is None
    assert out["summary"]["checked_slices"] == 2
    assert out["summary"]["ok_slices"] == 2


def test_manifest_mode_missing_attestation(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    evidence_rel = "out/ops/attestation_uniqueness/manifest_missing_attestation/"
    evidence_dir = tmp_path / evidence_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "note.txt").write_text("x", encoding="utf-8")
    manifest = _write_manifest(tmp_path, (_mk_slice("U3", evidence_rel),))

    result = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    assert result.returncode == 3, result.stderr
    out = json.loads(result.stdout.strip())
    assert out["mode"] == "manifest"
    assert out["entries"][0]["status"] == "missing_attestation"


def test_manifest_mode_multiple_attestations(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    evidence_rel = "out/ops/attestation_uniqueness/manifest_multiple_attestations/"
    evidence_dir = tmp_path / evidence_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "A_ATTESTATION.txt").write_text("ok", encoding="utf-8")
    (evidence_dir / "B_ATTESTATION.txt").write_text("ok", encoding="utf-8")
    manifest = _write_manifest(tmp_path, (_mk_slice("U4", evidence_rel),))

    result = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    assert result.returncode == 3, result.stderr
    out = json.loads(result.stdout.strip())
    assert out["mode"] == "manifest"
    assert out["entries"][0]["status"] == "multiple_attestations"


def test_target_mode_all_ok(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    evidence_rel = "out/ops/attestation_uniqueness/target_ok/"
    evidence_dir = tmp_path / evidence_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "ONLY_ATTESTATION.txt").write_text("ok", encoding="utf-8")

    result = _run_cli(["check-evidence-attestation-uniqueness", evidence_rel], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout.strip())
    assert out["ok"] is True
    assert out["mode"] == "target"
    assert out["manifest_path"] is None
    assert out["target_path"] == str(evidence_dir.resolve())
    assert out["summary"]["checked_slices"] == 1
    assert out["entries"][0]["status"] == "ok"
    assert out["entries"][0]["slice_id"] is None


def test_target_mode_missing_attestation(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    evidence_rel = "out/ops/attestation_uniqueness/target_missing_attestation/"
    evidence_dir = tmp_path / evidence_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "note.txt").write_text("x", encoding="utf-8")

    result = _run_cli(["check-evidence-attestation-uniqueness", evidence_rel], cwd=tmp_path)
    assert result.returncode == 3, result.stderr
    out = json.loads(result.stdout.strip())
    assert out["mode"] == "target"
    assert out["entries"][0]["status"] == "missing_attestation"


def test_target_mode_multiple_attestations(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    evidence_rel = "out/ops/attestation_uniqueness/target_multiple_attestations/"
    evidence_dir = tmp_path / evidence_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "A_ATTESTATION.txt").write_text("ok", encoding="utf-8")
    (evidence_dir / "B_ATTESTATION.txt").write_text("ok", encoding="utf-8")

    result = _run_cli(["check-evidence-attestation-uniqueness", evidence_rel], cwd=tmp_path)
    assert result.returncode == 3, result.stderr
    out = json.loads(result.stdout.strip())
    assert out["mode"] == "target"
    assert out["entries"][0]["status"] == "multiple_attestations"


def test_missing_path(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    evidence_rel = "out/ops/attestation_uniqueness/missing_path/"

    result = _run_cli(["check-evidence-attestation-uniqueness", evidence_rel], cwd=tmp_path)
    assert result.returncode == 3, result.stderr
    out = json.loads(result.stdout.strip())
    assert out["mode"] == "target"
    assert out["entries"][0]["status"] == "missing_path"


def test_not_a_directory(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    evidence_rel = "out/ops/attestation_uniqueness/not_a_directory"
    evidence_target = tmp_path / evidence_rel
    evidence_target.parent.mkdir(parents=True, exist_ok=True)
    evidence_target.write_text("x", encoding="utf-8")

    result = _run_cli(["check-evidence-attestation-uniqueness", evidence_rel], cwd=tmp_path)
    assert result.returncode == 3, result.stderr
    out = json.loads(result.stdout.strip())
    assert out["mode"] == "target"
    assert out["entries"][0]["status"] == "not_a_directory"


def test_repo_root_not_found_if_applicable(tmp_path: Path) -> None:
    evidence_rel = "out/ops/attestation_uniqueness/no_root/"
    (tmp_path / evidence_rel).mkdir(parents=True, exist_ok=True)

    result = _run_cli(["check-evidence-attestation-uniqueness", evidence_rel], cwd=tmp_path)
    assert result.returncode == 2, result.stderr
    out = json.loads(result.stdout.strip())
    assert out["ok"] is False
    assert out["error"] == "input"
    assert out["reason"] == "repo_root_not_found"


def test_no_evidence_slices_is_deterministically_green(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    manifest = _write_manifest(tmp_path, (_mk_slice("A", None), _mk_slice("B", None)))

    result = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout.strip())
    assert out["mode"] == "manifest"
    assert out["summary"]["checked_slices"] == 0
    assert out["entries"] == []


@pytest.mark.parametrize("mode", ["manifest", "target"])
def test_stdout_is_exactly_one_json_object(tmp_path: Path, mode: str) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    evidence_rel = f"out/ops/attestation_uniqueness/stdout_{mode}/"
    evidence_dir = tmp_path / evidence_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "ONLY_ATTESTATION.txt").write_text("ok", encoding="utf-8")

    if mode == "manifest":
        manifest = _write_manifest(tmp_path, (_mk_slice("U8", evidence_rel),))
        result = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    else:
        result = _run_cli(["check-evidence-attestation-uniqueness", evidence_rel], cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    out = json.loads(lines[0])
    assert out["ok"] is True
    assert out["command"] == "check-evidence-attestation-uniqueness"
    assert out["mode"] == mode


def test_json_field_stability(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    evidence_rel = "out/ops/attestation_uniqueness/stable/"
    evidence_dir = tmp_path / evidence_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "ONLY_ATTESTATION.txt").write_text("ok", encoding="utf-8")
    manifest = _write_manifest(tmp_path, (_mk_slice("U9", evidence_rel),))

    manifest_result = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    target_result = _run_cli(
        ["check-evidence-attestation-uniqueness", evidence_rel],
        cwd=tmp_path,
    )
    manifest_out = json.loads(manifest_result.stdout.strip())
    target_out = json.loads(target_result.stdout.strip())

    for out in (manifest_out, target_out):
        assert set(out.keys()) >= {
            "ok",
            "schema",
            "command",
            "mode",
            "manifest_path",
            "target_path",
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
        entry = out["entries"][0]
        assert set(entry.keys()) >= {
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


def test_regression_manifest_mode_and_target_mode_are_both_explicitly_supported(
    tmp_path: Path,
) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    evidence_rel = "out/ops/attestation_uniqueness/regression/"
    evidence_dir = tmp_path / evidence_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "ONLY_ATTESTATION.txt").write_text("ok", encoding="utf-8")
    manifest = _write_manifest(tmp_path, (_mk_slice("U10", evidence_rel),))

    manifest_result = _run_cli(["check-evidence-attestation-uniqueness", str(manifest)])
    target_result = _run_cli(
        ["check-evidence-attestation-uniqueness", evidence_rel],
        cwd=tmp_path,
    )
    manifest_out = json.loads(manifest_result.stdout.strip())
    target_out = json.loads(target_result.stdout.strip())

    assert manifest_result.returncode == 0
    assert target_result.returncode == 0
    assert manifest_out["mode"] == "manifest"
    assert target_out["mode"] == "target"
    assert manifest_out["summary"]["ok_slices"] == 1
    assert target_out["summary"]["ok_slices"] == 1
    assert manifest_out["entries"][0]["status"] == "ok"
    assert target_out["entries"][0]["status"] == "ok"
