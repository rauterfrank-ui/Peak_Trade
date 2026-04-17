"""Subprocess tests for LevelUp v0 `check-evidence-attestation-readiness` CLI contract."""

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


def _write_attestation(
    evidence_dir: Path,
    *,
    slice_id: str,
    attested_at_utc: str = "2026-04-17T12:34:56Z",
    attestor: str = "ops",
    scope: str = "evidence-readiness",
    sha256sums_file: str = "SHA256SUMS.txt",
    file_name: str = "OPERATOR_ATTESTATION.txt",
) -> None:
    lines = [
        f"slice_id: {slice_id}",
        f"attested_at_utc: {attested_at_utc}",
        f"attestor: {attestor}",
        f"scope: {scope}",
        f"sha256sums_file: {sha256sums_file}",
    ]
    (evidence_dir / file_name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _mk_manifest(tmp_path: Path, slice_id: str, evidence_rel: str) -> Path:
    sl = SliceContractV0(
        slice_id=slice_id,
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=evidence_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))
    return manifest


def test_check_evidence_attestation_readiness_cli_all_ok(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_readiness/all_ok/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "SHA256SUMS.txt").write_text("", encoding="utf-8")
    _write_attestation(evidence_dir, slice_id="R1")
    manifest = _mk_manifest(tmp_path, "R1", ev_rel)

    r = _run_cli(["check-evidence-attestation-readiness", str(manifest)])
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["command"] == "check-evidence-attestation-readiness"
    assert out["checked_count"] == 1
    assert out["ready_count"] == 1
    assert out["not_ready_count"] == 0
    assert out["input_error_count"] == 0
    assert out["domain_not_ready_count"] == 0
    assert out["entries"][0]["status"] == "ok"


def test_check_evidence_attestation_readiness_cli_missing_attestation(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_readiness/missing_attestation/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "SHA256SUMS.txt").write_text("", encoding="utf-8")
    manifest = _mk_manifest(tmp_path, "R2", ev_rel)

    r = _run_cli(["check-evidence-attestation-readiness", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["domain_not_ready_count"] == 1
    assert out["input_error_count"] == 0
    assert out["entries"][0]["status"] == "missing_attestation"


def test_attestation_readiness_marks_multiple_attestations_as_not_ready(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_readiness/multiple_attestations/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "SHA256SUMS.txt").write_text("", encoding="utf-8")
    _write_attestation(evidence_dir, slice_id="WRONG", file_name="A_ATTESTATION.txt")
    _write_attestation(evidence_dir, slice_id="R_MULTI", file_name="Z_ATTESTATION.txt")
    manifest = _mk_manifest(tmp_path, "R_MULTI", ev_rel)

    r = _run_cli(["check-evidence-attestation-readiness", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["ready_count"] == 0
    assert out["not_ready_count"] == 1
    assert out["domain_not_ready_count"] == 1
    assert out["input_error_count"] == 0
    assert out["entries"][0]["status"] == "multiple_attestations"
    assert out["entries"][0]["ready"] is False
    assert out["entries"][0]["input_error"] is False
    assert out["entries"][0]["attestation_file"] is None
    assert "attestation_uniqueness" in out["entries"][0]["missing_requirements"]


def test_check_evidence_attestation_readiness_cli_unreadable_attestation(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_readiness/unreadable/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "SHA256SUMS.txt").write_text("", encoding="utf-8")
    (evidence_dir / "BAD_ATTESTATION.txt").write_bytes(b"\xff\xfe\x00")
    manifest = _mk_manifest(tmp_path, "R3", ev_rel)

    r = _run_cli(["check-evidence-attestation-readiness", str(manifest)])
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["input_error_count"] == 1
    assert out["entries"][0]["status"] == "unreadable_attestation"
    assert out["entries"][0]["input_error"] is True


def test_check_evidence_attestation_readiness_cli_invalid_contract_fields(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_readiness/invalid_contract/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "OPERATOR_ATTESTATION.txt").write_text(
        "\n".join(
            [
                "slice_id: R4",
                "attested_at_utc: 2026-04-17 12:34:56",
                "attestor:   ",
                "scope: operator",
                "sha256sums_file: checksum.txt",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = _mk_manifest(tmp_path, "R4", ev_rel)

    r = _run_cli(["check-evidence-attestation-readiness", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "invalid_attestation_contract"
    assert "attestor_non_empty" in out["entries"][0]["missing_requirements"]
    assert "attested_at_utc_iso8601_like" in out["entries"][0]["missing_requirements"]
    assert "sha256sums_file_reference" in out["entries"][0]["missing_requirements"]


def test_check_evidence_attestation_readiness_cli_slice_id_mismatch(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_readiness/slice_id_mismatch/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "SHA256SUMS.txt").write_text("", encoding="utf-8")
    _write_attestation(evidence_dir, slice_id="OTHER")
    manifest = _mk_manifest(tmp_path, "R5", ev_rel)

    r = _run_cli(["check-evidence-attestation-readiness", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "slice_id_mismatch"
    assert out["entries"][0]["attestation_slice_id_matches_manifest"] is False


def test_check_evidence_attestation_readiness_cli_sha256sums_file_reference_missing_target(
    tmp_path: Path,
) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_readiness/missing_sha_target/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_attestation(evidence_dir, slice_id="R6", sha256sums_file="MISSING_SHA256SUMS.txt")
    manifest = _mk_manifest(tmp_path, "R6", ev_rel)

    r = _run_cli(["check-evidence-attestation-readiness", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "sha256sums_file_target_missing"
    assert out["entries"][0]["sha256sums_file_target_exists"] is False


def test_check_evidence_attestation_readiness_cli_missing_path(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_readiness/missing_path/"
    manifest = _mk_manifest(tmp_path, "R7", ev_rel)

    r = _run_cli(["check-evidence-attestation-readiness", str(manifest)])
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["input_error_count"] == 1
    assert out["entries"][0]["status"] == "missing_path"


def test_check_evidence_attestation_readiness_cli_not_a_directory(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_readiness/not_a_directory"
    target = tmp_path / ev_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("x", encoding="utf-8")
    manifest = _mk_manifest(tmp_path, "R8", ev_rel)

    r = _run_cli(["check-evidence-attestation-readiness", str(manifest)])
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["input_error_count"] == 1
    assert out["entries"][0]["status"] == "not_a_directory"


def test_check_evidence_attestation_readiness_cli_mixed_manifest(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ok_rel = "out/ops/attestation_readiness/mixed_ok/"
    missing_path_rel = "out/ops/attestation_readiness/mixed_missing_path/"
    mismatch_rel = "out/ops/attestation_readiness/mixed_mismatch/"
    missing_att_rel = "out/ops/attestation_readiness/mixed_missing_att/"
    unreadable_rel = "out/ops/attestation_readiness/mixed_unreadable/"

    ok_dir = tmp_path / ok_rel
    ok_dir.mkdir(parents=True, exist_ok=True)
    (ok_dir / "SHA256SUMS.txt").write_text("", encoding="utf-8")
    _write_attestation(ok_dir, slice_id="ok")

    mismatch_dir = tmp_path / mismatch_rel
    mismatch_dir.mkdir(parents=True, exist_ok=True)
    (mismatch_dir / "SHA256SUMS.txt").write_text("", encoding="utf-8")
    _write_attestation(mismatch_dir, slice_id="wrong")

    missing_att_dir = tmp_path / missing_att_rel
    missing_att_dir.mkdir(parents=True, exist_ok=True)
    (missing_att_dir / "SHA256SUMS.txt").write_text("", encoding="utf-8")

    unreadable_dir = tmp_path / unreadable_rel
    unreadable_dir.mkdir(parents=True, exist_ok=True)
    (unreadable_dir / "SHA256SUMS.txt").write_text("", encoding="utf-8")
    (unreadable_dir / "BROKEN_ATTESTATION.txt").write_bytes(b"\xff\xfe\x00")

    s_ok = SliceContractV0(
        slice_id="ok",
        title="ok",
        contract_summary="ok",
        evidence=EvidenceBundleRefV0(relative_dir=ok_rel),
    )
    s_no_ev = SliceContractV0(slice_id="no_ev", title="no_ev", contract_summary="no_ev")
    s_missing = SliceContractV0(
        slice_id="missing_path",
        title="missing_path",
        contract_summary="missing_path",
        evidence=EvidenceBundleRefV0(relative_dir=missing_path_rel),
    )
    s_mismatch = SliceContractV0(
        slice_id="mismatch",
        title="mismatch",
        contract_summary="mismatch",
        evidence=EvidenceBundleRefV0(relative_dir=mismatch_rel),
    )
    s_missing_att = SliceContractV0(
        slice_id="missing_att",
        title="missing_att",
        contract_summary="missing_att",
        evidence=EvidenceBundleRefV0(relative_dir=missing_att_rel),
    )
    s_unreadable = SliceContractV0(
        slice_id="unreadable",
        title="unreadable",
        contract_summary="unreadable",
        evidence=EvidenceBundleRefV0(relative_dir=unreadable_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        LevelUpManifestV0(
            slices=(s_ok, s_no_ev, s_missing, s_mismatch, s_missing_att, s_unreadable)
        ),
    )

    r = _run_cli(["check-evidence-attestation-readiness", str(manifest)])
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["checked_count"] == 5
    assert out["ready_count"] == 1
    assert out["not_ready_count"] == 4
    assert out["domain_not_ready_count"] == 2
    assert out["input_error_count"] == 2
    assert [e["status"] for e in out["entries"]] == [
        "ok",
        "missing_path",
        "slice_id_mismatch",
        "missing_attestation",
        "unreadable_attestation",
    ]


def test_check_evidence_attestation_readiness_cli_repo_root_not_found(tmp_path: Path) -> None:
    ev_rel = "out/ops/attestation_readiness/no_root/"
    sl = SliceContractV0(
        slice_id="R9",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-readiness", str(manifest)])
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["error"] == "input"
    assert out["reason"] == "repo_root_not_found"


def test_check_evidence_attestation_readiness_cli_no_evidence_slices(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    s1 = SliceContractV0(slice_id="A", title="A", contract_summary="c")
    s2 = SliceContractV0(slice_id="B", title="B", contract_summary="c")
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s1, s2)))

    r = _run_cli(["check-evidence-attestation-readiness", str(manifest)])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["checked_count"] == 0
    assert out["ready_count"] == 0
    assert out["not_ready_count"] == 0
    assert out["domain_not_ready_count"] == 0
    assert out["input_error_count"] == 0
    assert out["entries"] == []


def test_check_evidence_attestation_readiness_cli_json_field_stability(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_readiness/stability/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "SHA256SUMS.txt").write_text("", encoding="utf-8")
    _write_attestation(evidence_dir, slice_id="R10", file_name="FINAL_ATTESTATION.txt")
    manifest = _mk_manifest(tmp_path, "R10", ev_rel)

    r = _run_cli(["check-evidence-attestation-readiness", str(manifest)])
    out = json.loads(r.stdout.strip())
    assert set(out.keys()) >= {
        "ok",
        "schema",
        "command",
        "manifest_path",
        "checked_count",
        "ready_count",
        "not_ready_count",
        "domain_not_ready_count",
        "input_error_count",
        "entries",
    }
    ent = out["entries"][0]
    assert set(ent.keys()) >= {
        "slice_id",
        "evidence",
        "exists",
        "is_dir",
        "attestation_present",
        "attestation_matches",
        "attestation_file",
        "attestation_readable_utf8",
        "attestation_contract_valid",
        "attestation_slice_id",
        "attestation_slice_id_matches_manifest",
        "attestation_sha256sums_file",
        "sha256sums_file_reference_resolved",
        "sha256sums_file_target",
        "sha256sums_file_target_exists",
        "missing_requirements",
        "contract_details",
        "status",
        "ready",
        "input_error",
    }
