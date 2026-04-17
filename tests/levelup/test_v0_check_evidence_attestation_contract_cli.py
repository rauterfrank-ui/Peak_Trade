"""Subprocess tests for LevelUp v0 `check-evidence-attestation-contract` CLI contract."""

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
    attested_at_utc: str = "2026-04-17T12:34:56Z",
    attestor: str = "ops",
    scope: str = "evidence-minimal",
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


def test_check_evidence_attestation_contract_cli_all_ok(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/all_ok/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "SHA256SUMS.txt").write_text("", encoding="utf-8")
    _write_attestation(evidence_dir, slice_id="C1")

    sl = SliceContractV0(
        slice_id="C1",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 0, r.stderr
    assert r.stderr.strip() == ""
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["command"] == "check-evidence-attestation-contract"
    assert out["checked_count"] == 1
    assert out["ready_count"] == 1
    assert out["not_ready_count"] == 0
    assert out["entries"][0]["status"] == "ok"
    assert out["entries"][0]["missing_requirements"] == []


def test_check_evidence_attestation_contract_cli_missing_attestation(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/missing_attestation/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "unrelated.txt").write_text("x", encoding="utf-8")

    sl = SliceContractV0(
        slice_id="C2",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "missing_attestation"


def test_contract_returns_multiple_attestations_without_parsing_first_file(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/multiple_attestations/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "A_ATTESTATION.txt").write_text(
        "\n".join(
            [
                "slice_id: C_MULTI",
                "attested_at_utc: not-iso",
                "attestor: ",
                "scope: operator",
                "sha256sums_file: bad.file",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_attestation(evidence_dir, slice_id="C_MULTI", file_name="Z_ATTESTATION.txt")

    sl = SliceContractV0(
        slice_id="C_MULTI",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "multiple_attestations"
    assert out["entries"][0]["contract_details"]["checked_file"] is None
    assert "attestation_uniqueness" in out["entries"][0]["missing_requirements"]


def test_check_evidence_attestation_contract_cli_unreadable_attestation(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/unreadable/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "BAD_ATTESTATION.txt").write_bytes(b"\xff\xfe\x00")

    sl = SliceContractV0(
        slice_id="C3",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "unreadable_attestation"


def test_check_evidence_attestation_contract_cli_invalid_contract_fields(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/invalid_contract/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "OPERATOR_ATTESTATION.txt").write_text(
        "\n".join(
            [
                "slice_id: C4",
                "attested_at_utc: 2026-04-17 12:34:56",
                "attestor:   ",
                "scope: operator",
                "sha256sums_file: checksum.txt",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    sl = SliceContractV0(
        slice_id="C4",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "invalid_attestation_contract"
    assert "attestor_non_empty" in out["entries"][0]["missing_requirements"]
    assert "attested_at_utc_iso8601_like" in out["entries"][0]["missing_requirements"]
    assert "sha256sums_file_reference" in out["entries"][0]["missing_requirements"]


def test_check_evidence_attestation_contract_cli_missing_path(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/missing_path/"
    sl = SliceContractV0(
        slice_id="C5",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "missing_path"


def test_check_evidence_attestation_contract_cli_not_a_directory(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/not_a_directory"
    target = tmp_path / ev_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("x", encoding="utf-8")

    sl = SliceContractV0(
        slice_id="C6",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "not_a_directory"


def test_check_evidence_attestation_contract_cli_mixed_manifest(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ok_rel = "out/ops/attestation_contract/mixed_ok/"
    missing_path_rel = "out/ops/attestation_contract/mixed_missing_path/"
    not_dir_rel = "out/ops/attestation_contract/mixed_not_dir"
    missing_att_rel = "out/ops/attestation_contract/mixed_missing_att/"
    invalid_rel = "out/ops/attestation_contract/mixed_invalid/"

    ok_dir = tmp_path / ok_rel
    ok_dir.mkdir(parents=True, exist_ok=True)
    (ok_dir / "SHA256SUMS.txt").write_text("", encoding="utf-8")
    _write_attestation(ok_dir, slice_id="ok")

    not_dir_target = tmp_path / not_dir_rel
    not_dir_target.parent.mkdir(parents=True, exist_ok=True)
    not_dir_target.write_text("x", encoding="utf-8")

    missing_att_dir = tmp_path / missing_att_rel
    missing_att_dir.mkdir(parents=True, exist_ok=True)
    (missing_att_dir / "SOME_OTHER_FILE.txt").write_text("x", encoding="utf-8")

    invalid_dir = tmp_path / invalid_rel
    invalid_dir.mkdir(parents=True, exist_ok=True)
    (invalid_dir / "OPERATOR_ATTESTATION.txt").write_text(
        "\n".join(
            [
                "slice_id: invalid",
                "attested_at_utc: not-a-time",
                "attestor: reviewer",
                "scope: scope",
                "sha256sums_file: not_sha_file.log",
            ]
        )
        + "\n",
        encoding="utf-8",
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
    s_missing_att = SliceContractV0(
        slice_id="missing_att",
        title="missing_att",
        contract_summary="missing_att",
        evidence=EvidenceBundleRefV0(relative_dir=missing_att_rel),
    )
    s_invalid = SliceContractV0(
        slice_id="invalid",
        title="invalid",
        contract_summary="invalid",
        evidence=EvidenceBundleRefV0(relative_dir=invalid_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        LevelUpManifestV0(slices=(s_ok, s_no_ev, s_missing, s_not_dir, s_missing_att, s_invalid)),
    )

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["checked_count"] == 5
    assert out["ready_count"] == 1
    assert out["not_ready_count"] == 4
    assert [e["status"] for e in out["entries"]] == [
        "ok",
        "missing_path",
        "not_a_directory",
        "missing_attestation",
        "invalid_attestation_contract",
    ]


def test_check_evidence_attestation_contract_cli_repo_root_not_found(tmp_path: Path) -> None:
    ev_rel = "out/ops/attestation_contract/no_root/"
    sl = SliceContractV0(
        slice_id="C7",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["error"] == "input"
    assert out["reason"] == "repo_root_not_found"


def test_check_evidence_attestation_contract_cli_no_evidence_slices(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    s1 = SliceContractV0(slice_id="A", title="A", contract_summary="c")
    s2 = SliceContractV0(slice_id="B", title="B", contract_summary="c")
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(s1, s2)))

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is True
    assert out["checked_count"] == 0
    assert out["ready_count"] == 0
    assert out["not_ready_count"] == 0
    assert out["entries"] == []


def test_check_evidence_attestation_contract_cli_json_field_stability(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/stability/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "SHA256SUMS.txt").write_text("", encoding="utf-8")
    _write_attestation(evidence_dir, slice_id="C8", file_name="FINAL_ATTESTATION.txt")
    sl = SliceContractV0(
        slice_id="C8",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
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
        "attestation_matches",
        "status",
        "missing_requirements",
        "contract_details",
    }


def test_attestation_contract_rejects_noncanonical_sha256sums_target(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/noncanonical_target/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "SHA256SUMS.txt").write_text("", encoding="utf-8")
    (evidence_dir / "ALT_SHA256SUMS.txt").write_text("", encoding="utf-8")
    _write_attestation(evidence_dir, slice_id="C_NONCANON", sha256sums_file="ALT_SHA256SUMS.txt")

    sl = SliceContractV0(
        slice_id="C_NONCANON",
        title="t",
        contract_summary="c",
        evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
    )
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, LevelUpManifestV0(slices=(sl,)))

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["entries"][0]["status"] == "invalid_attestation_contract"
    assert (
        "sha256sums_file_targets_canonical_integrity_anchor"
        in out["entries"][0]["missing_requirements"]
    )


def test_manifest_mode_all_ok(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/manifest_mode_all_ok/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(evidence_dir, {"artifact.bundle.tgz": b"bundle-ok"})
    _write_attestation(evidence_dir, slice_id="MC1")
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        LevelUpManifestV0(
            slices=(
                SliceContractV0(
                    slice_id="MC1",
                    title="t",
                    contract_summary="c",
                    evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
                ),
            )
        ),
    )

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["mode"] == "manifest"
    assert out["entries"][0]["status"] == "ok"


def test_manifest_mode_missing_attestation(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/manifest_mode_missing_attestation/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(evidence_dir, {"x.txt": b"x"})
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        LevelUpManifestV0(
            slices=(
                SliceContractV0(
                    slice_id="MC2",
                    title="t",
                    contract_summary="c",
                    evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
                ),
            )
        ),
    )

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["mode"] == "manifest"
    assert out["entries"][0]["status"] == "missing_attestation"


def test_manifest_mode_multiple_attestations(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/manifest_mode_multiple_attestations/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(evidence_dir, {"x.txt": b"x"})
    _write_attestation(evidence_dir, slice_id="MC3", file_name="A_ATTESTATION.txt")
    _write_attestation(evidence_dir, slice_id="MC3", file_name="B_ATTESTATION.txt")
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        LevelUpManifestV0(
            slices=(
                SliceContractV0(
                    slice_id="MC3",
                    title="t",
                    contract_summary="c",
                    evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
                ),
            )
        ),
    )

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["mode"] == "manifest"
    assert out["entries"][0]["status"] == "multiple_attestations"


def test_manifest_mode_noncanonical_target(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/manifest_mode_noncanonical_target/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(evidence_dir, {"x.txt": b"x"})
    _write_sha256sums(evidence_dir, {"x.txt": b"x"}, file_name="ALT_SHA256SUMS.txt")
    _write_attestation(evidence_dir, slice_id="MC4", sha256sums_file="ALT_SHA256SUMS.txt")
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        LevelUpManifestV0(
            slices=(
                SliceContractV0(
                    slice_id="MC4",
                    title="t",
                    contract_summary="c",
                    evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
                ),
            )
        ),
    )

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["mode"] == "manifest"
    assert out["entries"][0]["status"] == "invalid_attestation_contract"
    assert (
        "sha256sums_file_targets_canonical_integrity_anchor"
        in out["entries"][0]["missing_requirements"]
    )


def test_manifest_mode_invalid_sha256sums_format(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/manifest_mode_invalid_sha256sums_format/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "SHA256SUMS.txt").write_text("not-a-sha-line\n", encoding="utf-8")
    _write_attestation(evidence_dir, slice_id="MC5")
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        LevelUpManifestV0(
            slices=(
                SliceContractV0(
                    slice_id="MC5",
                    title="t",
                    contract_summary="c",
                    evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
                ),
            )
        ),
    )

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["mode"] == "manifest"
    assert out["entries"][0]["status"] == "invalid_sha256sums_format"


def test_manifest_mode_sha256_mismatch(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/manifest_mode_sha256_mismatch/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "payload.txt").write_bytes(b"actual")
    (evidence_dir / "SHA256SUMS.txt").write_text(
        f"{_sha256_hex(b'expected')}  payload.txt\n", encoding="utf-8"
    )
    _write_attestation(evidence_dir, slice_id="MC6")
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        LevelUpManifestV0(
            slices=(
                SliceContractV0(
                    slice_id="MC6",
                    title="t",
                    contract_summary="c",
                    evidence=EvidenceBundleRefV0(relative_dir=ev_rel),
                ),
            )
        ),
    )

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["mode"] == "manifest"
    assert out["entries"][0]["status"] == "sha256_mismatch"


def test_target_mode_all_ok(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/target_mode_all_ok/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(evidence_dir, {"artifact.bundle.tgz": b"bundle-ok"})
    _write_attestation(evidence_dir, slice_id="TC1")

    r = _run_cli(["check-evidence-attestation-contract", ev_rel], cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["mode"] == "target"
    assert out["manifest_path"] is None
    assert out["target_path"] == str(evidence_dir.resolve())
    assert out["entries"][0]["slice_id"] is None
    assert out["entries"][0]["status"] == "ok"


def test_target_mode_missing_attestation(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/target_mode_missing_attestation/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(evidence_dir, {"x.txt": b"x"})

    r = _run_cli(["check-evidence-attestation-contract", ev_rel], cwd=tmp_path)
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["mode"] == "target"
    assert out["entries"][0]["status"] == "missing_attestation"


def test_target_mode_multiple_attestations(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/target_mode_multiple_attestations/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(evidence_dir, {"x.txt": b"x"})
    _write_attestation(evidence_dir, slice_id="TC3", file_name="A_ATTESTATION.txt")
    _write_attestation(evidence_dir, slice_id="TC3", file_name="B_ATTESTATION.txt")

    r = _run_cli(["check-evidence-attestation-contract", ev_rel], cwd=tmp_path)
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["mode"] == "target"
    assert out["entries"][0]["status"] == "multiple_attestations"


def test_target_mode_noncanonical_target(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/target_mode_noncanonical_target/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(evidence_dir, {"x.txt": b"x"})
    _write_sha256sums(evidence_dir, {"x.txt": b"x"}, file_name="ALT_SHA256SUMS.txt")
    _write_attestation(evidence_dir, slice_id="TC4", sha256sums_file="ALT_SHA256SUMS.txt")

    r = _run_cli(["check-evidence-attestation-contract", ev_rel], cwd=tmp_path)
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["mode"] == "target"
    assert out["entries"][0]["status"] == "invalid_attestation_contract"
    assert (
        "sha256sums_file_targets_canonical_integrity_anchor"
        in out["entries"][0]["missing_requirements"]
    )


def test_target_mode_invalid_sha256sums_format(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/target_mode_invalid_sha256sums_format/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "SHA256SUMS.txt").write_text("not-a-sha-line\n", encoding="utf-8")
    _write_attestation(evidence_dir, slice_id="TC5")

    r = _run_cli(["check-evidence-attestation-contract", ev_rel], cwd=tmp_path)
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["mode"] == "target"
    assert out["entries"][0]["status"] == "invalid_sha256sums_format"


def test_target_mode_sha256_mismatch(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/target_mode_sha256_mismatch/"
    evidence_dir = tmp_path / ev_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "payload.txt").write_bytes(b"actual")
    (evidence_dir / "SHA256SUMS.txt").write_text(
        f"{_sha256_hex(b'expected')}  payload.txt\n", encoding="utf-8"
    )
    _write_attestation(evidence_dir, slice_id="TC6")

    r = _run_cli(["check-evidence-attestation-contract", ev_rel], cwd=tmp_path)
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["mode"] == "target"
    assert out["entries"][0]["status"] == "sha256_mismatch"


def test_missing_path(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/missing_path_target_mode/"

    r = _run_cli(["check-evidence-attestation-contract", ev_rel], cwd=tmp_path)
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["mode"] == "target"
    assert out["entries"][0]["status"] == "missing_path"


def test_not_a_directory(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_rel = "out/ops/attestation_contract/not_a_directory_target_mode"
    target = tmp_path / ev_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("x", encoding="utf-8")

    r = _run_cli(["check-evidence-attestation-contract", ev_rel], cwd=tmp_path)
    assert r.returncode == 3, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["mode"] == "target"
    assert out["entries"][0]["status"] == "not_a_directory"


def test_repo_root_not_found_if_applicable(tmp_path: Path) -> None:
    ev_rel = "out/ops/attestation_contract/no_root_target_mode/"
    (tmp_path / ev_rel).mkdir(parents=True, exist_ok=True)

    r = _run_cli(["check-evidence-attestation-contract", ev_rel], cwd=tmp_path)
    assert r.returncode == 2, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["ok"] is False
    assert out["error"] == "input"
    assert out["reason"] == "repo_root_not_found"


def test_no_evidence_slices_is_deterministically_green(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        LevelUpManifestV0(
            slices=(
                SliceContractV0(slice_id="A", title="t", contract_summary="c"),
                SliceContractV0(slice_id="B", title="t", contract_summary="c"),
            )
        ),
    )

    r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip())
    assert out["mode"] == "manifest"
    assert out["checked_count"] == 0
    assert out["entries"] == []


def test_stdout_is_exactly_one_json_object(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_manifest_rel = "out/ops/attestation_contract/stdout_manifest_mode/"
    ev_target_rel = "out/ops/attestation_contract/stdout_target_mode/"
    manifest_dir = tmp_path / ev_manifest_rel
    target_dir = tmp_path / ev_target_rel
    manifest_dir.mkdir(parents=True, exist_ok=True)
    target_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(manifest_dir, {"ok.txt": b"ok"})
    _write_sha256sums(target_dir, {"ok.txt": b"ok"})
    _write_attestation(manifest_dir, slice_id="SO1")
    _write_attestation(target_dir, slice_id="SO2")
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        LevelUpManifestV0(
            slices=(
                SliceContractV0(
                    slice_id="SO1",
                    title="t",
                    contract_summary="c",
                    evidence=EvidenceBundleRefV0(relative_dir=ev_manifest_rel),
                ),
            )
        ),
    )

    manifest_r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    target_r = _run_cli(["check-evidence-attestation-contract", ev_target_rel], cwd=tmp_path)
    for mode, result in (("manifest", manifest_r), ("target", target_r)):
        assert result.returncode == 0, result.stderr
        lines = result.stdout.strip().splitlines()
        assert len(lines) == 1
        out = json.loads(lines[0])
        assert out["ok"] is True
        assert out["command"] == "check-evidence-attestation-contract"
        assert out["mode"] == mode


def test_json_field_stability(tmp_path: Path) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    ev_manifest_rel = "out/ops/attestation_contract/stable_manifest_mode/"
    ev_target_rel = "out/ops/attestation_contract/stable_target_mode/"
    manifest_dir = tmp_path / ev_manifest_rel
    target_dir = tmp_path / ev_target_rel
    manifest_dir.mkdir(parents=True, exist_ok=True)
    target_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(manifest_dir, {"ok.txt": b"ok"})
    _write_sha256sums(target_dir, {"ok.txt": b"ok"})
    _write_attestation(manifest_dir, slice_id="FS1")
    _write_attestation(target_dir, slice_id="FS2")
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        LevelUpManifestV0(
            slices=(
                SliceContractV0(
                    slice_id="FS1",
                    title="t",
                    contract_summary="c",
                    evidence=EvidenceBundleRefV0(relative_dir=ev_manifest_rel),
                ),
            )
        ),
    )

    manifest_result = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    target_result = _run_cli(["check-evidence-attestation-contract", ev_target_rel], cwd=tmp_path)
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
            "attestation_matches",
            "status",
            "missing_requirements",
            "contract_details",
            "repo_root",
            "resolved_path",
        }


def test_regression_manifest_mode_and_target_mode_are_both_explicitly_supported(
    tmp_path: Path,
) -> None:
    _bootstrap_minimal_repo_layout(tmp_path)
    evidence_rel = "out/ops/attestation_contract/regression_manifest_target/"
    evidence_dir = tmp_path / evidence_rel
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _write_sha256sums(evidence_dir, {"ok.txt": b"ok"})
    _write_attestation(evidence_dir, slice_id="RG1")
    manifest = tmp_path / "manifest.json"
    write_manifest(
        manifest,
        LevelUpManifestV0(
            slices=(
                SliceContractV0(
                    slice_id="RG1",
                    title="t",
                    contract_summary="c",
                    evidence=EvidenceBundleRefV0(relative_dir=evidence_rel),
                ),
            )
        ),
    )

    manifest_r = _run_cli(["check-evidence-attestation-contract", str(manifest)])
    target_r = _run_cli(["check-evidence-attestation-contract", evidence_rel], cwd=tmp_path)
    manifest_out = json.loads(manifest_r.stdout.strip())
    target_out = json.loads(target_r.stdout.strip())

    assert manifest_r.returncode == 0
    assert target_r.returncode == 0
    assert manifest_out["mode"] == "manifest"
    assert target_out["mode"] == "target"
    assert manifest_out["entries"][0]["status"] == "ok"
    assert target_out["entries"][0]["status"] == "ok"
