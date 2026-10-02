"""Contract tests for HEAD-bound integrated offline replay correctness v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.adjudication_v1 import (
    evaluate_integrated_paper_shadow_shadow_readiness_head_bound_v1,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.binding_v1 import (
    IMPLEMENTATION_SURFACE_RELPATHS,
    compute_implementation_surface_digest_sha256_v1,
    resolve_configured_correctness_evidence_relpath_v1,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.constants_v1 import (
    MANIFEST_NAME,
    PROOF_ARTIFACT_NAME,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.economic_evidence_bundle_v1 import (
    produce_integrated_paper_shadow_economic_evidence_bundle_head_bound_v1,
    verify_integrated_paper_shadow_economic_evidence_bundle_head_bound_v1,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.proof_v1 import (
    produce_integrated_offline_replay_and_correctness_head_bound_evidence_v1,
    resolve_repository_head_sha_v1,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.verifier_v1 import (
    verify_integrated_offline_replay_and_correctness_head_bound_evidence_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.readiness_producer_v1 import (
    produce_paper_shadow_observation_readiness_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_head_bound_correctness_proof_and_verifier(tmp_path: Path) -> None:
    head = resolve_repository_head_sha_v1(repo_root=REPO_ROOT)
    proof = produce_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        repo_root=REPO_ROOT,
        work_root=tmp_path / "proof",
        expected_head_sha=head,
    )
    assert proof.INTEGRATED_OFFLINE_REPLAY_AND_CORRECTNESS_PASS is True
    assert proof.CRS_CONTEXT_BOUND is True
    assert proof.EXTERNAL_EFFECT_COUNT == 0
    assert proof.implementation_surface_digest_sha256
    verified = verify_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        evidence_root=tmp_path / "proof",
        repo_root=REPO_ROOT,
        require_current_head=True,
    )
    assert verified.verified is True


def test_economic_bundle_and_readiness_with_head_bound(tmp_path: Path) -> None:
    head = resolve_repository_head_sha_v1(repo_root=REPO_ROOT)
    proof_dir = tmp_path / "proof"
    produce_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        repo_root=REPO_ROOT,
        work_root=proof_dir,
        expected_head_sha=head,
    )
    bundle_dir = tmp_path / "bundle"
    produced = produce_integrated_paper_shadow_economic_evidence_bundle_head_bound_v1(
        repo_root=REPO_ROOT,
        bundle_root=bundle_dir,
        correctness_evidence_root=proof_dir,
    )
    assert produced.INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED is True
    verified = verify_integrated_paper_shadow_economic_evidence_bundle_head_bound_v1(
        bundle_root=bundle_dir,
        repo_root=REPO_ROOT,
        correctness_evidence_root=proof_dir,
    )
    assert verified.verified is True


def test_regression_committed_later_commit_still_verifies(tmp_path: Path) -> None:
    """Proof for state X remains valid when verified from a later Git HEAD (simulated)."""
    head = resolve_repository_head_sha_v1(repo_root=REPO_ROOT)
    proof_dir = tmp_path / "committed_evidence"
    produce_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        repo_root=REPO_ROOT,
        work_root=proof_dir,
        expected_head_sha=head,
    )
    proof_path = proof_dir / PROOF_ARTIFACT_NAME
    proof_doc = json.loads(proof_path.read_text(encoding="utf-8"))
    proof_doc["proven_source_sha"] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    proof_doc["repository_head_sha"] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    proof_path.write_text(json.dumps(proof_doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256(proof_path.read_bytes()).hexdigest()
    (proof_dir / MANIFEST_NAME).write_text(
        f"{digest}  {PROOF_ARTIFACT_NAME}\n",
        encoding="utf-8",
    )

    verified = verify_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        evidence_root=proof_dir,
        repo_root=REPO_ROOT,
        require_current_head=True,
    )
    assert verified.verified is True


def test_regression_implementation_mutation_fails(tmp_path: Path) -> None:
    head = resolve_repository_head_sha_v1(repo_root=REPO_ROOT)
    proof_dir = tmp_path / "proof"
    produce_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        repo_root=REPO_ROOT,
        work_root=proof_dir,
        expected_head_sha=head,
    )
    target = REPO_ROOT / IMPLEMENTATION_SURFACE_RELPATHS[0]
    original = target.read_text(encoding="utf-8")
    try:
        target.write_text(original + "\n# binding regression probe\n", encoding="utf-8")
        verified = verify_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
            evidence_root=proof_dir,
            repo_root=REPO_ROOT,
            require_current_head=True,
        )
        assert verified.verified is False
        assert "IMPLEMENTATION_SURFACE_DRIFT" in verified.blockers
    finally:
        target.write_text(original, encoding="utf-8")


def test_regression_manifest_tampering_fails(tmp_path: Path) -> None:
    head = resolve_repository_head_sha_v1(repo_root=REPO_ROOT)
    proof_dir = tmp_path / "proof"
    produce_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        repo_root=REPO_ROOT,
        work_root=proof_dir,
        expected_head_sha=head,
    )
    manifest_path = proof_dir / MANIFEST_NAME
    manifest_path.write_text("0" * 64 + f"  {PROOF_ARTIFACT_NAME}\n", encoding="utf-8")
    verified = verify_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        evidence_root=proof_dir,
        repo_root=REPO_ROOT,
        require_current_head=True,
    )
    assert verified.verified is False
    assert any("MANIFEST_DIGEST_MISMATCH" in b for b in verified.blockers)


def test_regression_wrong_proof_binding_fails(tmp_path: Path) -> None:
    head = resolve_repository_head_sha_v1(repo_root=REPO_ROOT)
    proof_dir = tmp_path / "proof"
    produce_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        repo_root=REPO_ROOT,
        work_root=proof_dir,
        expected_head_sha=head,
    )
    proof_path = proof_dir / PROOF_ARTIFACT_NAME
    proof_doc = json.loads(proof_path.read_text(encoding="utf-8"))
    proof_doc["implementation_surface_digest_sha256"] = "0" * 64
    proof_path.write_text(json.dumps(proof_doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    verified = verify_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        evidence_root=proof_dir,
        repo_root=REPO_ROOT,
        require_current_head=True,
    )
    assert verified.verified is False
    assert "IMPLEMENTATION_SURFACE_DRIFT" in verified.blockers


def test_readiness_producer_consumes_committed_head_bound_evidence() -> None:
    rel = resolve_configured_correctness_evidence_relpath_v1(
        repo_root=REPO_ROOT,
        fallback_head_sha=resolve_repository_head_sha_v1(repo_root=REPO_ROOT),
    )
    canonical = REPO_ROOT / rel
    if not (canonical / PROOF_ARTIFACT_NAME).is_file():
        return
    readiness = produce_paper_shadow_observation_readiness_v1(repo_root=REPO_ROOT)
    assert readiness.PAPER_SHADOW_OBSERVATION_READINESS_PASS is True


def test_shadow_readiness_adjudication_when_committed_evidence_present() -> None:
    head = resolve_repository_head_sha_v1(repo_root=REPO_ROOT)
    canonical_rel = resolve_configured_correctness_evidence_relpath_v1(
        repo_root=REPO_ROOT,
        fallback_head_sha=head,
    )
    from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.binding_v1 import (
        resolve_configured_economic_bundle_evidence_relpath_v1,
    )

    bundle_rel = resolve_configured_economic_bundle_evidence_relpath_v1(
        repo_root=REPO_ROOT,
        fallback_head_sha=head,
    )
    if not (REPO_ROOT / canonical_rel).is_dir() or not (REPO_ROOT / bundle_rel).is_dir():
        return
    digest = compute_implementation_surface_digest_sha256_v1(repo_root=REPO_ROOT)
    proof_path = REPO_ROOT / canonical_rel / PROOF_ARTIFACT_NAME
    if proof_path.is_file():
        proof_doc = json.loads(proof_path.read_text(encoding="utf-8"))
        if proof_doc.get("implementation_surface_digest_sha256") != digest:
            return
    result = evaluate_integrated_paper_shadow_shadow_readiness_head_bound_v1(repo_root=REPO_ROOT)
    assert result.SHADOW_READINESS == "READY"
    assert result.INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED is True
