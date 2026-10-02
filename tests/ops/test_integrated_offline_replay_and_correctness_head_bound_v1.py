"""Contract tests for HEAD-bound integrated offline replay correctness v1."""

from __future__ import annotations

from pathlib import Path

from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.adjudication_v1 import (
    evaluate_integrated_paper_shadow_shadow_readiness_head_bound_v1,
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


def test_readiness_producer_consumes_committed_head_bound_evidence() -> None:
    canonical = (
        REPO_ROOT
        / "evidence/ops/integrated_offline_replay_and_correctness_head_bound_v1"
        / resolve_repository_head_sha_v1(repo_root=REPO_ROOT)
    )
    if not (
        canonical / "INTEGRATED_OFFLINE_REPLAY_AND_CORRECTNESS_HEAD_BOUND_PROOF.json"
    ).is_file():
        return
    readiness = produce_paper_shadow_observation_readiness_v1(repo_root=REPO_ROOT)
    assert readiness.PAPER_SHADOW_OBSERVATION_READINESS_PASS is True


def test_shadow_readiness_adjudication_when_committed_evidence_present() -> None:
    head = resolve_repository_head_sha_v1(repo_root=REPO_ROOT)
    canonical = (
        REPO_ROOT / "evidence/ops/integrated_offline_replay_and_correctness_head_bound_v1" / head
    )
    bundle = (
        REPO_ROOT
        / "evidence/ops/integrated_paper_shadow_economic_evidence_bundle_head_bound_v1"
        / head
    )
    if not canonical.is_dir() or not bundle.is_dir():
        return
    result = evaluate_integrated_paper_shadow_shadow_readiness_head_bound_v1(repo_root=REPO_ROOT)
    assert result.SHADOW_READINESS == "READY"
    assert result.INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED is True
