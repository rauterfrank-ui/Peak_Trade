"""Subprocess tests for LevelUp v0 `check-evidence-integrity` CLI contract."""

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


def _write_sha256sums(evidence_dir: Path, items: dict[str, bytes]) -> None:
    lines: list[str] = []
    for rel_path, content in items.items():
        target = evidence_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        lines.append(f"{_sha256_hex(content)}  {rel_path}")
    (evidence_dir / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_check_evidence_integrity_cli_all_ok(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/integrity/all_ok/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True)
    _write_sha256sums(evidence_dir, {"sample.bundle.tgz": b"tgz", "notes.txt": b"notes"})

    sl = SliceContractV0(
        slice_id="I1",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-integrity", str(manifest)])
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["command"] == "check-evidence-integrity"
    assert out["checked_count"] == 1
    assert out["ready_count"] == 1
    assert out["not_ready_count"] == 0
    assert out["entries"][0]["status"] == "ok"
    assert out["entries"][0]["checked_files"] == 2
    assert out["entries"][0]["missing_requirements"] == []
    assert out["entries"][0]["failed_files"] == []


def test_check_evidence_integrity_cli_missing_sha_file(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/integrity/missing_sha/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "sample.bundle.tgz").write_bytes(b"tgz")

    sl = SliceContractV0(
        slice_id="I2",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "missing_sha256sums"


def test_check_evidence_integrity_cli_invalid_sha_format(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/integrity/invalid_sha/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "SHA256SUMS.txt").write_text("not a valid sha line\n", encoding="utf-8")

    sl = SliceContractV0(
        slice_id="I3",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "invalid_sha256sums_format"


def test_check_evidence_integrity_cli_missing_hashed_file(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/integrity/missing_hashed/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True)
    missing_hash = _sha256_hex(b"expected-content")
    (evidence_dir / "SHA256SUMS.txt").write_text(
        f"{missing_hash}  missing.bundle.tgz\n", encoding="utf-8"
    )

    sl = SliceContractV0(
        slice_id="I4",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "missing_hashed_file"
    assert out["entries"][0]["failed_files"][0]["status"] == "missing_hashed_file"


def test_check_evidence_integrity_cli_hash_mismatch(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/integrity/hash_mismatch/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "sample.bundle.tgz").write_bytes(b"actual")
    wrong_hash = _sha256_hex(b"other-content")
    (evidence_dir / "SHA256SUMS.txt").write_text(
        f"{wrong_hash}  sample.bundle.tgz\n", encoding="utf-8"
    )

    sl = SliceContractV0(
        slice_id="I5",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "hash_mismatch"
    assert out["entries"][0]["failed_files"][0]["status"] == "hash_mismatch"


def test_check_evidence_integrity_cli_missing_path(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/integrity/missing_path/"
    sl = SliceContractV0(
        slice_id="I6",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "missing_path"


def test_check_evidence_integrity_cli_not_a_directory(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/integrity/not_a_directory"
    target = tmp_path / ev_rel
    target.parent.mkdir(parents=True)
    target.write_text("x", encoding="utf-8")

    sl = SliceContractV0(
        slice_id="I7",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "not_a_directory"


def test_check_evidence_integrity_cli_mixed_manifest(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ok_rel = "out/ops/integrity/mixed_ok/"
    missing_path_rel = "out/ops/integrity/mixed_missing_path/"
    invalid_format_rel = "out/ops/integrity/mixed_invalid_format/"
    missing_hashed_rel = "out/ops/integrity/mixed_missing_hashed/"
    mismatch_rel = "out/ops/integrity/mixed_mismatch/"

    ok_dir = tmp_path / ok_rel
    ok_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(ok_dir, {"ok.txt": b"ok"})

    invalid_dir = tmp_path / invalid_format_rel
    invalid_dir.mkdir(parents=True, exist_ok=True)
    (invalid_dir / "SHA256SUMS.txt").write_text("bad line\n", encoding="utf-8")

    missing_hashed_dir = tmp_path / missing_hashed_rel
    missing_hashed_dir.mkdir(parents=True, exist_ok=True)
    (missing_hashed_dir / "SHA256SUMS.txt").write_text(
        f"{_sha256_hex(b'x')}  missing.txt\n", encoding="utf-8"
    )

    mismatch_dir = tmp_path / mismatch_rel
    mismatch_dir.mkdir(parents=True, exist_ok=True)
    (mismatch_dir / "file.txt").write_bytes(b"actual")
    (mismatch_dir / "SHA256SUMS.txt").write_text(
        f"{_sha256_hex(b'expected')}  file.txt\n", encoding="utf-8"
    )

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
    s_invalid = SliceContractV0(
        slice_id="invalid_sha",
        title="invalid",
        contract_summary="invalid",
        evidence=EvidenceBundleRefV0(relative_dir=invalid_format_rel),
    )
    s_missing_hashed = SliceContractV0(
        slice_id="missing_hashed",
        title="missing_hashed",
        contract_summary="missing_hashed",
        evidence=EvidenceBundleRefV0(relative_dir=missing_hashed_rel),
    )
    s_mismatch = SliceContractV0(
        slice_id="mismatch",
        title="mismatch",
        contract_summary="mismatch",
        evidence=EvidenceBundleRefV0(relative_dir=mismatch_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        LevelUpManifestV0(
            slices=(s_ok, s_no_ev, s_missing, s_invalid, s_missing_hashed, s_mismatch)
        ),
    )

    r = _run_cli(["check-evidence-integrity", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["checked_count"] == 5
    assert out["ready_count"] == 1
    assert out["not_ready_count"] == 4
    assert [e["status"] for e in out["entries"]] == [
        "ok",
        "missing_path",
        "invalid_sha256sums_format",
        "missing_hashed_file",
        "hash_mismatch",
    ]


def test_check_evidence_integrity_cli_repo_root_not_found(tmp_path: Path) -> None:
    ev_rel = "out/ops/integrity/no_root/"
    sl = SliceContractV0(
        slice_id="I8",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-integrity", str(manifest)])
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["error"] == "input"
    assert out["reason"] == "repo_root_not_found"


def test_check_evidence_integrity_cli_no_evidence_slices(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    s1 = SliceContractV0(slice_id="A", title="A", contract_summary="c")
    s2 = SliceContractV0(slice_id="B", title="B", contract_summary="c")
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s1, s2)))

    r = _run_cli(["check-evidence-integrity", str(manifest)])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["checked_count"] == 0
    assert out["ready_count"] == 0
    assert out["not_ready_count"] == 0
    assert out["entries"] == []


def test_check_evidence_integrity_cli_json_field_stability(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/integrity/stability/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True)
    _write_sha256sums(evidence_dir, {"sample.bundle.tgz": b"tgz"})
    sl = SliceContractV0(
        slice_id="S",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-integrity", str(manifest)])
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
        "status",
        "checked_files",
        "missing_requirements",
        "failed_files",
    }
