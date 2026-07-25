"""Focused tests: Step 29U audit / provenance completeness v0."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from src.ops.step_29u_audit_provenance_v0 import (
    EXPECTED_SOAK_TESTED_HEAD_SHA,
    STATUS_ABSENT,
    STATUS_COMPLETE,
    STATUS_CONTRADICTORY,
    STATUS_INVALID,
    STATUS_STALE,
    STATUS_UNVERIFIED,
    AuditProvenanceOverridesV0,
    Step29UAuditProvenanceError,
    evaluate_step_29u_audit_provenance_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_SOAK = REPO_ROOT / "evidence/ops/step_29u_post_merge_shadow_soak/20260725T222915Z"
CANONICAL_OFFLINE = (
    REPO_ROOT / "evidence/ops/step_29u_offline_capability/2026-07-25_capability_hold_cycle"
)


def _copy_tree(src: Path, dest: Path) -> Path:
    shutil.copytree(src, dest)
    return dest


def _refresh_manifest_entry(evidence_dir: Path, rel: str) -> None:
    manifest = evidence_dir / "evidence_manifest.sha256"
    digest = hashlib.sha256((evidence_dir / rel).read_bytes()).hexdigest()
    lines = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        _d, name = line.split(None, 1)
        if name.strip() == rel:
            lines.append(f"{digest}  {rel}")
        else:
            lines.append(line)
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_complete_valid_chain() -> None:
    result = evaluate_step_29u_audit_provenance_v0(repo_root=REPO_ROOT)
    assert result.status == STATUS_COMPLETE
    assert result.audit_provenance_complete is True
    assert result.traversal_order[0] == "binding_runbook"
    assert not result.blockers
    assert result.safety_facts["STEP_29U_ACTIVATED"] is False


def test_missing_manifest(tmp_path: Path) -> None:
    soak = _copy_tree(CANONICAL_SOAK, tmp_path / "soak")
    (soak / "evidence_manifest.sha256").unlink()
    result = evaluate_step_29u_audit_provenance_v0(
        repo_root=REPO_ROOT,
        overrides=AuditProvenanceOverridesV0(soak_dir=soak),
    )
    assert result.status == STATUS_ABSENT
    assert result.audit_provenance_complete is False
    assert any("MANIFEST_MISSING" in b or "ABSENT" in b for b in result.blockers)


def test_missing_manifest_member(tmp_path: Path) -> None:
    soak = _copy_tree(CANONICAL_SOAK, tmp_path / "soak")
    (soak / "soak_summary.json").unlink()
    result = evaluate_step_29u_audit_provenance_v0(
        repo_root=REPO_ROOT,
        overrides=AuditProvenanceOverridesV0(soak_dir=soak),
    )
    assert result.status in {STATUS_ABSENT, STATUS_INVALID}
    assert result.audit_provenance_complete is False


def test_digest_mismatch(tmp_path: Path) -> None:
    soak = _copy_tree(CANONICAL_SOAK, tmp_path / "soak")
    summary = soak / "soak_summary.json"
    payload = json.loads(summary.read_text(encoding="utf-8"))
    payload["VERDICT"] = "TAMPERED"
    summary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = evaluate_step_29u_audit_provenance_v0(
        repo_root=REPO_ROOT,
        overrides=AuditProvenanceOverridesV0(soak_dir=soak),
    )
    assert result.status == STATUS_INVALID
    soak_link = next(link for link in result.links if link.link_id == "post_merge_soak_evidence")
    assert "DIGEST_MISMATCH" in soak_link.reason_code


def test_stale_evidence_wrong_git_sha(tmp_path: Path) -> None:
    soak = _copy_tree(CANONICAL_SOAK, tmp_path / "soak")
    summary = soak / "soak_summary.json"
    payload = json.loads(summary.read_text(encoding="utf-8"))
    payload["TESTED_HEAD_SHA"] = "0" * 40
    summary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _refresh_manifest_entry(soak, "soak_summary.json")
    (soak / "exact_head.txt").write_text("0" * 40 + "\n", encoding="utf-8")
    _refresh_manifest_entry(soak, "exact_head.txt")
    result = evaluate_step_29u_audit_provenance_v0(
        repo_root=REPO_ROOT,
        overrides=AuditProvenanceOverridesV0(soak_dir=soak),
    )
    assert result.status == STATUS_STALE
    assert result.audit_provenance_complete is False


def test_contradictory_pass_result(tmp_path: Path) -> None:
    soak = _copy_tree(CANONICAL_SOAK, tmp_path / "soak")
    summary = soak / "soak_summary.json"
    payload = json.loads(summary.read_text(encoding="utf-8"))
    payload["STATUS"] = "PASS"
    payload["ORDERS_CREATED"] = True
    summary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _refresh_manifest_entry(soak, "soak_summary.json")
    result = evaluate_step_29u_audit_provenance_v0(
        repo_root=REPO_ROOT,
        overrides=AuditProvenanceOverridesV0(soak_dir=soak),
    )
    assert result.status == STATUS_CONTRADICTORY


def test_wrong_git_sha_expected_override(tmp_path: Path) -> None:
    result = evaluate_step_29u_audit_provenance_v0(
        repo_root=REPO_ROOT,
        overrides=AuditProvenanceOverridesV0(expected_soak_head="deadbeef" * 5),
    )
    assert result.status == STATUS_STALE
    assert EXPECTED_SOAK_TESTED_HEAD_SHA  # canonical constant remains defined


def test_local_only_tracked_contradiction() -> None:
    result = evaluate_step_29u_audit_provenance_v0(
        repo_root=REPO_ROOT,
        overrides=AuditProvenanceOverridesV0(treat_as_local_only=True),
    )
    assert result.status == STATUS_INVALID
    assert any("LOCAL_ONLY" in link.reason_code for link in result.links)


def test_deterministic_traversal() -> None:
    a = evaluate_step_29u_audit_provenance_v0(
        repo_root=REPO_ROOT,
        overrides=AuditProvenanceOverridesV0(evaluated_main_sha="abc"),
    )
    b = evaluate_step_29u_audit_provenance_v0(
        repo_root=REPO_ROOT,
        overrides=AuditProvenanceOverridesV0(evaluated_main_sha="abc"),
    )
    assert a.traversal_order == b.traversal_order
    assert [link.link_id for link in a.links] == [link.link_id for link in b.links]
    assert [link.status for link in a.links] == [link.status for link in b.links]


def test_fail_closed_unknown_status() -> None:
    with pytest.raises(Step29UAuditProvenanceError) as exc:
        evaluate_step_29u_audit_provenance_v0(
            repo_root=REPO_ROOT,
            overrides=AuditProvenanceOverridesV0(force_unknown_status=True),
        )
    assert "UNKNOWN_AUDIT_STATUS" in str(exc.value)


def test_unverified_when_offline_verify_fails(tmp_path: Path) -> None:
    offline = _copy_tree(CANONICAL_OFFLINE, tmp_path / "offline")
    # Drop a required artifact referenced by manifest without updating → INVALID digest path.
    # Prefer corrupting capability_result content while refreshing digest so verify fails.
    result_path = offline / "capability_result.json"
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["capability_result"] = "STEP_29U_OFFLINE_CAPABILITY_ERROR"
    payload["step_29u_verified_offline"] = False
    result_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _refresh_manifest_entry(offline, "capability_result.json")
    result = evaluate_step_29u_audit_provenance_v0(
        repo_root=REPO_ROOT,
        overrides=AuditProvenanceOverridesV0(offline_dir=offline),
    )
    assert result.audit_provenance_complete is False
    assert result.status in {STATUS_UNVERIFIED, STATUS_INVALID, STATUS_CONTRADICTORY}
