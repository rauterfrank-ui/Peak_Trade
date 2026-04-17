"""Subprocess tests for LevelUp v0 `check-evidence-attestation-integrity` CLI contract."""

from __future__ import annotations

import hashlib
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


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_sha256sums(
    evidence_dir: Path, items: dict[str, bytes], file_name: str = "SHA256SUMS.txt"
) -> None:
    lines: list[str] = []
    for rel_path, content in items.items():
        target = evidence_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        lines.append(f"{_sha256_hex(content)}  {rel_path}")
    (evidence_dir / file_name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_attestation(
    evidence_dir: Path,
    *,
    slice_id: str,
    sha256sums_file: str = "SHA256SUMS.txt",
    file_name: str = "OPERATOR_ATTESTATION.txt",
) -> None:
    lines = [
        f"slice_id: {slice_id}",
        "attested_at_utc: 2026-04-17T12:34:56Z",
        "attestor: ops",
        "scope: evidence-attestation-integrity",
        f"sha256sums_file: {sha256sums_file}",
    ]
    (evidence_dir / file_name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _mk_manifest(tmp_path: Path, *slices: SliceContractV0) -> Path:
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=slices))
    return manifest


def test_check_evidence_attestation_integrity_cli_all_ok_with_canonical_valid_sha256sums(
    tmp_path: Path,
) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_integrity/all_ok/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(evidence_dir, {"artifact.bundle.tgz": b"bundle-ok", "notes.txt": b"ok"})
    _write_attestation(evidence_dir, slice_id="AI1")
    manifest = _mk_manifest(
        tmp_path,
        SliceContractV0(
            slice_id="AI1",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
        ),
    )

    r = _run_cli(["check-evidence-attestation-integrity", str(manifest)])
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["command"] == "check-evidence-attestation-integrity"
    assert out["summary"]["checked_slices"] == 1
    assert out["summary"]["ok_slices"] == 1
    assert out["summary"]["sha256_mismatch_slices"] == 0
    assert out["entries"][0]["status"] == "ok"


def test_check_evidence_attestation_integrity_cli_missing_attestation(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_integrity/missing_attestation/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(evidence_dir, {"x.txt": b"x"})
    manifest = _mk_manifest(
        tmp_path,
        SliceContractV0(
            slice_id="AI2",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
        ),
    )

    r = _run_cli(["check-evidence-attestation-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["entries"][0]["status"] == "missing_attestation"
    assert out["summary"]["missing_attestation_slices"] == 1


def test_check_evidence_attestation_integrity_cli_multiple_attestations(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_integrity/multiple_attestations/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(evidence_dir, {"x.txt": b"x"})
    _write_attestation(evidence_dir, slice_id="AI3", file_name="A_ATTESTATION.txt")
    _write_attestation(evidence_dir, slice_id="AI3", file_name="B_ATTESTATION.txt")
    manifest = _mk_manifest(
        tmp_path,
        SliceContractV0(
            slice_id="AI3",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
        ),
    )

    r = _run_cli(["check-evidence-attestation-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["entries"][0]["status"] == "multiple_attestations"
    assert out["entries"][0]["attestation_count"] == 2


def test_check_evidence_attestation_integrity_cli_missing_path(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_integrity/missing_path/"
    manifest = _mk_manifest(
        tmp_path,
        SliceContractV0(
            slice_id="AI4",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
        ),
    )

    r = _run_cli(["check-evidence-attestation-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["entries"][0]["status"] == "missing_path"


def test_check_evidence_attestation_integrity_cli_not_a_directory(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_integrity/not_a_directory"
    target = tmp_path / ev_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("x", encoding="utf-8")
    manifest = _mk_manifest(
        tmp_path,
        SliceContractV0(
            slice_id="AI5",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
        ),
    )

    r = _run_cli(["check-evidence-attestation-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["entries"][0]["status"] == "not_a_directory"


def test_check_evidence_attestation_integrity_cli_missing_sha256sums_file(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_integrity/missing_sha256sums_file/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_attestation(evidence_dir, slice_id="AI6")
    manifest = _mk_manifest(
        tmp_path,
        SliceContractV0(
            slice_id="AI6",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
        ),
    )

    r = _run_cli(["check-evidence-attestation-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["entries"][0]["status"] == "missing_sha256sums_file"


def test_check_evidence_attestation_integrity_cli_noncanonical_sha256sums_target(
    tmp_path: Path,
) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_integrity/noncanonical_target/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(evidence_dir, {"x.txt": b"x"})
    _write_sha256sums(evidence_dir, {"x.txt": b"x"}, file_name="ALT_SHA256SUMS.txt")
    _write_attestation(evidence_dir, slice_id="AI7", sha256sums_file="ALT_SHA256SUMS.txt")
    manifest = _mk_manifest(
        tmp_path,
        SliceContractV0(
            slice_id="AI7",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
        ),
    )

    r = _run_cli(["check-evidence-attestation-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["entries"][0]["status"] == "sha256sums_file_target_noncanonical"
    assert out["summary"]["noncanonical_target_slices"] == 1


def test_check_evidence_attestation_integrity_cli_invalid_sha256sums_format(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_integrity/invalid_sha256sums_format/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "SHA256SUMS.txt").write_text("not-a-sha-line\n", encoding="utf-8")
    _write_attestation(evidence_dir, slice_id="AI8")
    manifest = _mk_manifest(
        tmp_path,
        SliceContractV0(
            slice_id="AI8",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
        ),
    )

    r = _run_cli(["check-evidence-attestation-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["entries"][0]["status"] == "invalid_sha256sums_format"


def test_check_evidence_attestation_integrity_cli_sha256_mismatch(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_integrity/sha256_mismatch/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "payload.txt").write_bytes(b"actual")
    wrong_hash = _sha256_hex(b"expected")
    (evidence_dir / "SHA256SUMS.txt").write_text(f"{wrong_hash}  payload.txt\n", encoding="utf-8")
    _write_attestation(evidence_dir, slice_id="AI9")
    manifest = _mk_manifest(
        tmp_path,
        SliceContractV0(
            slice_id="AI9",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
        ),
    )

    r = _run_cli(["check-evidence-attestation-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["entries"][0]["status"] == "sha256_mismatch"
    assert out["summary"]["sha256_mismatch_slices"] == 1


def test_check_evidence_attestation_integrity_cli_mixed_manifest(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ok_rel = "out/ops/attestation_integrity/mixed_ok/"
    missing_rel = "out/ops/attestation_integrity/mixed_missing_attestation/"
    noncanonical_rel = "out/ops/attestation_integrity/mixed_noncanonical/"
    mismatch_rel = "out/ops/attestation_integrity/mixed_mismatch/"

    ok_dir = tmp_path / ok_rel
    ok_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(ok_dir, {"ok.txt": b"ok"})
    _write_attestation(ok_dir, slice_id="ok")

    missing_dir = tmp_path / missing_rel
    missing_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(missing_dir, {"x.txt": b"x"})

    noncanonical_dir = tmp_path / noncanonical_rel
    noncanonical_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(noncanonical_dir, {"x.txt": b"x"})
    _write_sha256sums(noncanonical_dir, {"x.txt": b"x"}, file_name="ALT_SHA256SUMS.txt")
    _write_attestation(
        noncanonical_dir, slice_id="noncanonical", sha256sums_file="ALT_SHA256SUMS.txt"
    )

    mismatch_dir = tmp_path / mismatch_rel
    mismatch_dir.mkdir(parents=True, exist_ok=True)
    (mismatch_dir / "p.txt").write_bytes(b"actual")
    (mismatch_dir / "SHA256SUMS.txt").write_text(
        f"{_sha256_hex(b'expected')}  p.txt\n", encoding="utf-8"
    )
    _write_attestation(mismatch_dir, slice_id="mismatch")

    manifest = _mk_manifest(
        tmp_path,
        SliceContractV0(
            slice_id="ok",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=ok_rel),
        ),
        SliceContractV0(slice_id="no_ev", title="t", contract_summary="c"),
        SliceContractV0(
            slice_id="missing_attestation",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=missing_rel),
        ),
        SliceContractV0(
            slice_id="noncanonical",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=noncanonical_rel),
        ),
        SliceContractV0(
            slice_id="mismatch",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=mismatch_rel),
        ),
    )

    r = _run_cli(["check-evidence-attestation-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["summary"]["total_slices"] == 5
    assert out["summary"]["checked_slices"] == 4
    assert out["summary"]["ok_slices"] == 1
    assert out["summary"]["missing_attestation_slices"] == 1
    assert out["summary"]["noncanonical_target_slices"] == 1
    assert out["summary"]["sha256_mismatch_slices"] == 1
    assert [e["status"] for e in out["entries"]] == [
        "ok",
        "missing_attestation",
        "sha256sums_file_target_noncanonical",
        "sha256_mismatch",
    ]


def test_check_evidence_attestation_integrity_cli_repo_root_not_found(tmp_path: Path) -> None:
    ev_rel = "out/ops/attestation_integrity/no_root/"
    manifest = _mk_manifest(
        tmp_path,
        SliceContractV0(
            slice_id="AI10",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
        ),
    )

    r = _run_cli(["check-evidence-attestation-integrity", str(manifest)])
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["error"] == "input"
    assert out["reason"] == "repo_root_not_found"


def test_check_evidence_attestation_integrity_cli_no_evidence_slices_is_deterministically_green(
    tmp_path: Path,
) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    manifest = _mk_manifest(
        tmp_path,
        SliceContractV0(slice_id="A", title="t", contract_summary="c"),
        SliceContractV0(slice_id="B", title="t", contract_summary="c"),
    )

    r = _run_cli(["check-evidence-attestation-integrity", str(manifest)])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["summary"]["total_slices"] == 2
    assert out["summary"]["checked_slices"] == 0
    assert out["entries"] == []


def test_check_evidence_attestation_integrity_cli_stdout_is_exactly_one_json_object(
    tmp_path: Path,
) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_integrity/stdout/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(evidence_dir, {"ok.txt": b"ok"})
    _write_attestation(evidence_dir, slice_id="AI11")
    manifest = _mk_manifest(
        tmp_path,
        SliceContractV0(
            slice_id="AI11",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
        ),
    )

    r = _run_cli(["check-evidence-attestation-integrity", str(manifest)])
    assert r.returncode == 0, r.stderr
    lines = r.stdout.strip().splitlines()
    assert len(lines) == 1
    out = json.loads(lines[0])
    assert out["ok"] is True


def test_check_evidence_attestation_integrity_cli_json_field_stability(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_integrity/stability/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(evidence_dir, {"ok.txt": b"ok"})
    _write_attestation(evidence_dir, slice_id="AI12")
    manifest = _mk_manifest(
        tmp_path,
        SliceContractV0(
            slice_id="AI12",
            title="t",
            contract_summary="c",
            evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
        ),
    )

    r = _run_cli(["check-evidence-attestation-integrity", str(manifest)])
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
        "missing_sha256sums_file_slices",
        "noncanonical_target_slices",
        "invalid_sha256sums_format_slices",
        "sha256_mismatch_slices",
    }
    ent = out["entries"][0]
    assert set(ent.keys()) >= {
        "slice_id",
        "evidence",
        "status",
        "attestation_matches",
        "attestation_count",
        "sha256sums_file",
        "resolved_sha256sums_path",
        "repo_root",
        "resolved_path",
        "exists",
        "is_dir",
    }
