"""Subprocess tests for LevelUp v0 `check-evidence-readiness-overall` CLI contract."""

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


def _write_bundle_files(evidence_dir: Path) -> None:
    (evidence_dir / "sample.bundle.tgz").write_bytes(b"bundle")
    (evidence_dir / "A_CRAWLER_SUMMARY_1LINE.txt").write_text("summary\n", encoding="utf-8")


def _write_sha256sums_for_existing_files(evidence_dir: Path) -> None:
    bundle_bytes = (evidence_dir / "sample.bundle.tgz").read_bytes()
    summary_bytes = (evidence_dir / "A_CRAWLER_SUMMARY_1LINE.txt").read_bytes()
    lines = [
        f"{_sha256_hex(bundle_bytes)}  sample.bundle.tgz",
        f"{_sha256_hex(summary_bytes)}  A_CRAWLER_SUMMARY_1LINE.txt",
    ]
    (evidence_dir / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_attestation(
    evidence_dir: Path, *, slice_id: str, sha256sums_file: str = "SHA256SUMS.txt"
) -> None:
    lines = [
        f"slice_id: {slice_id}",
        "attested_at_utc: 2026-04-17T12:34:56Z",
        "attestor: ops",
        "scope: evidence-readiness-overall",
        f"sha256sums_file: {sha256sums_file}",
    ]
    (evidence_dir / "OPERATOR_ATTESTATION.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _mk_slice(slice_id: str, evidence_rel: str | None) -> SliceContractV0:
    kwargs: dict[str, object] = {
        "slice_id": slice_id,
        "title": slice_id,
        "contract_summary": f"summary-{slice_id}",
    }
    if evidence_rel is not None:
        kwargs["evidence"] = EvidenceBundleRefV0(relative_dir=evidence_rel)
    return SliceContractV0(**kwargs)


def _mk_manifest(tmp_path: Path, slices: tuple[SliceContractV0, ...]) -> Path:
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=slices))
    return manifest


def _prepare_fully_ready_evidence(root: Path, rel: str, *, slice_id: str) -> None:
    evidence_dir = root / rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_bundle_files(evidence_dir)
    _write_sha256sums_for_existing_files(evidence_dir)
    _write_attestation(evidence_dir, slice_id=slice_id)


def test_check_evidence_readiness_overall_cli_all_ok(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/readiness_overall/all_ok/"
    _prepare_fully_ready_evidence(tmp_path, ev_rel, slice_id="S1")
    manifest = _mk_manifest(tmp_path, (_mk_slice("S1", ev_rel),))

    r = _run_cli(["check-evidence-readiness-overall", str(manifest)])
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["command"] == "check-evidence-readiness-overall"
    assert out["checked_count"] == 1
    assert out["ready_count"] == 1
    assert out["not_ready_count"] == 0
    assert out["domain_not_ready_count"] == 0
    assert out["input_error_count"] == 0
    assert out["entries"][0]["status"] == "ok"
    assert out["entries"][0]["ready"] is True
    assert out["entries"][0]["input_error"] is False


def test_check_evidence_readiness_overall_cli_missing_path(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/readiness_overall/missing_path/"
    manifest = _mk_manifest(tmp_path, (_mk_slice("S2", ev_rel),))

    r = _run_cli(["check-evidence-readiness-overall", str(manifest)])
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["input_error_count"] == 1
    assert out["domain_not_ready_count"] == 0
    assert out["entries"][0]["status"] == "missing_path"
    assert out["entries"][0]["input_error"] is True


def test_check_evidence_readiness_overall_cli_not_a_directory(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/readiness_overall/not_a_directory"
    target = tmp_path / ev_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("x", encoding="utf-8")
    manifest = _mk_manifest(tmp_path, (_mk_slice("S3", ev_rel),))

    r = _run_cli(["check-evidence-readiness-overall", str(manifest)])
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["input_error_count"] == 1
    assert out["entries"][0]["status"] == "not_a_directory"
    assert out["entries"][0]["input_error"] is True


def test_check_evidence_readiness_overall_cli_missing_evidence(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    manifest = _mk_manifest(tmp_path, (_mk_slice("S4", None),))

    r = _run_cli(["check-evidence-readiness-overall", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["input_error_count"] == 0
    assert out["domain_not_ready_count"] == 1
    assert out["entries"][0]["status"] == "missing_evidence"
    assert out["entries"][0]["coverage_path"]["status"] == "missing_evidence"


def test_check_evidence_readiness_overall_cli_bundle_incomplete(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/readiness_overall/bundle_incomplete/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "sample.bundle.tgz").write_bytes(b"bundle")
    manifest = _mk_manifest(tmp_path, (_mk_slice("S5", ev_rel),))

    r = _run_cli(["check-evidence-readiness-overall", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["bundle"]["status"] == "missing_bundle_requirements"
    assert out["entries"][0]["status"] == "missing_bundle_requirements"
    assert out["input_error_count"] == 0


def test_check_evidence_readiness_overall_cli_integrity_mismatch(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/readiness_overall/integrity_mismatch/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_bundle_files(evidence_dir)
    wrong_hash = _sha256_hex(b"wrong-content")
    (evidence_dir / "SHA256SUMS.txt").write_text(
        f"{wrong_hash}  sample.bundle.tgz\n", encoding="utf-8"
    )
    _write_attestation(evidence_dir, slice_id="S6")
    manifest = _mk_manifest(tmp_path, (_mk_slice("S6", ev_rel),))

    r = _run_cli(["check-evidence-readiness-overall", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["integrity"]["status"] == "hash_mismatch"
    assert out["entries"][0]["status"] == "hash_mismatch"
    assert out["input_error_count"] == 0


def test_check_evidence_readiness_overall_cli_attestation_not_ready(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/readiness_overall/attestation_not_ready/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_bundle_files(evidence_dir)
    _write_sha256sums_for_existing_files(evidence_dir)
    manifest = _mk_manifest(tmp_path, (_mk_slice("S7", ev_rel),))

    r = _run_cli(["check-evidence-readiness-overall", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["attestation_readiness"]["status"] == "missing_attestation"
    assert out["entries"][0]["status"] == "missing_attestation"
    assert out["input_error_count"] == 0


def test_readiness_overall_marks_noncanonical_sha256sums_target_not_ready(
    tmp_path: Path,
) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/readiness_overall/noncanonical_sha_target/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_bundle_files(evidence_dir)
    _write_sha256sums_for_existing_files(evidence_dir)
    (evidence_dir / "ALT_SHA256SUMS.txt").write_text("", encoding="utf-8")
    _write_attestation(evidence_dir, slice_id="S_NONCANON", sha256sums_file="ALT_SHA256SUMS.txt")
    manifest = _mk_manifest(tmp_path, (_mk_slice("S_NONCANON", ev_rel),))

    r = _run_cli(["check-evidence-readiness-overall", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["ready_count"] == 0
    assert out["not_ready_count"] == 1
    assert out["domain_not_ready_count"] == 1
    assert out["entries"][0]["attestation_readiness"]["status"] == "sha256sums_file_target_noncanonical"
    assert out["entries"][0]["status"] == "sha256sums_file_target_noncanonical"


def test_readiness_overall_marks_multiple_attestations_as_not_ready(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/readiness_overall/multiple_attestations/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_bundle_files(evidence_dir)
    _write_sha256sums_for_existing_files(evidence_dir)
    _write_attestation(evidence_dir, slice_id="S_MULTI")
    (evidence_dir / "SECOND_ATTESTATION.txt").write_text(
        "\n".join(
            [
                "slice_id: S_MULTI",
                "attested_at_utc: 2026-04-17T12:34:56Z",
                "attestor: ops",
                "scope: evidence-readiness-overall",
                "sha256sums_file: SHA256SUMS.txt",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = _mk_manifest(tmp_path, (_mk_slice("S_MULTI", ev_rel),))

    r = _run_cli(["check-evidence-readiness-overall", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["ready_count"] == 0
    assert out["not_ready_count"] == 1
    assert out["domain_not_ready_count"] == 1
    assert out["input_error_count"] == 0
    assert out["entries"][0]["attestation_readiness"]["status"] == "multiple_attestations"
    assert out["entries"][0]["status"] == "multiple_attestations"
    assert out["entries"][0]["ready"] is False


def test_check_evidence_readiness_overall_cli_mixed_manifest(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ok_rel = "out/ops/readiness_overall/mixed_ok/"
    missing_path_rel = "out/ops/readiness_overall/mixed_missing_path/"
    bundle_incomplete_rel = "out/ops/readiness_overall/mixed_bundle_incomplete/"
    integrity_mismatch_rel = "out/ops/readiness_overall/mixed_integrity_mismatch/"
    attestation_missing_rel = "out/ops/readiness_overall/mixed_attestation_missing/"

    _prepare_fully_ready_evidence(tmp_path, ok_rel, slice_id="ok")

    bundle_dir = tmp_path / bundle_incomplete_rel
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "sample.bundle.tgz").write_bytes(b"bundle")

    integrity_dir = tmp_path / integrity_mismatch_rel
    integrity_dir.mkdir(parents=True, exist_ok=True)
    _write_bundle_files(integrity_dir)
    (integrity_dir / "SHA256SUMS.txt").write_text(
        f"{_sha256_hex(b'wrong')}  sample.bundle.tgz\n", encoding="utf-8"
    )
    _write_attestation(integrity_dir, slice_id="integrity_mismatch")

    att_missing_dir = tmp_path / attestation_missing_rel
    att_missing_dir.mkdir(parents=True, exist_ok=True)
    _write_bundle_files(att_missing_dir)
    _write_sha256sums_for_existing_files(att_missing_dir)

    manifest = _mk_manifest(
        tmp_path,
        (
            _mk_slice("ok", ok_rel),
            _mk_slice("missing_evidence", None),
            _mk_slice("missing_path", missing_path_rel),
            _mk_slice("bundle_incomplete", bundle_incomplete_rel),
            _mk_slice("integrity_mismatch", integrity_mismatch_rel),
            _mk_slice("attestation_missing", attestation_missing_rel),
        ),
    )

    r = _run_cli(["check-evidence-readiness-overall", str(manifest)])
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["checked_count"] == 6
    assert out["ready_count"] == 1
    assert out["not_ready_count"] == 5
    assert out["input_error_count"] == 1
    assert out["domain_not_ready_count"] == 4
    assert [e["status"] for e in out["entries"]] == [
        "ok",
        "missing_evidence",
        "missing_path",
        "missing_bundle_requirements",
        "hash_mismatch",
        "missing_attestation",
    ]


def test_check_evidence_readiness_overall_cli_repo_root_not_found(tmp_path: Path) -> None:
    manifest = _mk_manifest(tmp_path, (_mk_slice("S9", "out/ops/readiness_overall/no_root/"),))

    r = _run_cli(["check-evidence-readiness-overall", str(manifest)])
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["error"] == "input"
    assert out["reason"] == "repo_root_not_found"


def test_check_evidence_readiness_overall_cli_no_evidence_slices(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    manifest = _mk_manifest(tmp_path, ())

    r = _run_cli(["check-evidence-readiness-overall", str(manifest)])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["checked_count"] == 0
    assert out["ready_count"] == 0
    assert out["not_ready_count"] == 0
    assert out["domain_not_ready_count"] == 0
    assert out["input_error_count"] == 0
    assert out["entries"] == []


def test_check_evidence_readiness_overall_cli_json_field_stability(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/readiness_overall/stability/"
    _prepare_fully_ready_evidence(tmp_path, ev_rel, slice_id="S10")
    manifest = _mk_manifest(tmp_path, (_mk_slice("S10", ev_rel),))

    r = _run_cli(["check-evidence-readiness-overall", str(manifest)])
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
        "coverage_path",
        "bundle",
        "integrity",
        "attestation_readiness",
        "status",
        "ready",
        "input_error",
    }


def test_check_evidence_readiness_overall_cli_exit_priority_input_error_over_not_ready(
    tmp_path: Path,
) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    missing_path_rel = "out/ops/readiness_overall/priority_missing_path/"
    bundle_incomplete_rel = "out/ops/readiness_overall/priority_bundle_incomplete/"
    bundle_dir = tmp_path / bundle_incomplete_rel
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "sample.bundle.tgz").write_bytes(b"bundle")
    manifest = _mk_manifest(
        tmp_path,
        (
            _mk_slice("missing_path", missing_path_rel),
            _mk_slice("bundle_incomplete", bundle_incomplete_rel),
        ),
    )

    r = _run_cli(["check-evidence-readiness-overall", str(manifest)])
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["input_error_count"] == 1
    assert out["domain_not_ready_count"] == 1
    assert [e["status"] for e in out["entries"]] == [
        "missing_path",
        "missing_bundle_requirements",
    ]
