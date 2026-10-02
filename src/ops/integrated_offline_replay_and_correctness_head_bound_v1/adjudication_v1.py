"""Adjudicate integrated Paper-Shadow shadow readiness at CURRENT HEAD v1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.discovery_v1 import (
    discover_verified_head_bound_correctness_at_current_head_v1,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.economic_evidence_bundle_v1 import (
    verify_integrated_paper_shadow_economic_evidence_bundle_head_bound_v1,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.proof_v1 import (
    default_canonical_evidence_dir_for_head_v1,
    resolve_repository_head_sha_v1,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.verifier_v1 import (
    verify_integrated_offline_replay_and_correctness_head_bound_evidence_v1,
)
from src.ops.integrated_paper_shadow_economic_validity_pipeline_v1 import (
    IntegratedPaperShadowEconomicValidityEvidenceInputV1,
    evaluate_integrated_paper_shadow_economic_validity_pipeline_v1,
    evaluate_paper_shadow_observation_readiness_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.readiness_producer_v1 import (
    produce_paper_shadow_observation_readiness_v1,
)
from src.ops.step_29u_canonical_shadow_binding_v0 import observe_canonical_step_29u_bound_v0


@dataclass
class ShadowReadinessAdjudicationResultV1:
    SHADOW_READINESS: str
    TESTNET_READINESS: str
    INTEGRATED_OFFLINE_REPLAY_AND_CORRECTNESS_PASS: bool
    PAPER_SHADOW_OBSERVATION_READINESS_PASS: bool
    INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE: bool
    INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED: bool
    repository_head_sha: str
    blockers: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_integrated_paper_shadow_shadow_readiness_head_bound_v1(
    *,
    repo_root: Path,
    bundle_evidence_relpath: str | None = None,
) -> ShadowReadinessAdjudicationResultV1:
    root = repo_root.resolve()
    head = resolve_repository_head_sha_v1(repo_root=root)
    correctness_dir = root / default_canonical_evidence_dir_for_head_v1(head_sha=head)
    correctness = verify_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        evidence_root=correctness_dir,
        repo_root=root,
        require_current_head=True,
    )
    bundle_rel = bundle_evidence_relpath or (
        f"evidence/ops/integrated_paper_shadow_economic_evidence_bundle_head_bound_v1/{head}"
    )
    bundle_dir = root / bundle_rel
    bundle = verify_integrated_paper_shadow_economic_evidence_bundle_head_bound_v1(
        bundle_root=bundle_dir,
        repo_root=root,
        correctness_evidence_root=correctness_dir,
    )

    readiness = produce_paper_shadow_observation_readiness_v1(repo_root=root)
    step29u_bound, _ = observe_canonical_step_29u_bound_v0(repo_root=root)
    offline_pass, correctness_pass, chain_proxy, _ = (
        discover_verified_head_bound_correctness_at_current_head_v1(repo_root=root)
    )

    evidence = IntegratedPaperShadowEconomicValidityEvidenceInputV1(
        full_canonical_system_parity=chain_proxy and step29u_bound,
        system_correctness_pass=correctness_pass and step29u_bound,
        integrated_offline_replay_pass=offline_pass,
        backtest_runtime_decision_parity_pass=offline_pass,
        canonical_decision_chain_bound=step29u_bound,
        master_v2_double_play_sole_decision_authority=True,
        ai_layer_non_authority=True,
        safety_kernel_killstate_fail_closed=True,
        broker_write_path_unreachable=True,
        order_authority_absent=True,
        simulated_portfolio_fill_fee_slippage_pnl_model_defined=True,
        evidence_directory_manifest_schema_config_digests_verifier_defined=True,
        session_preregistration_and_operator_go_contract_present=True,
        integrated_paper_shadow_evidence_complete=bundle.INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE,
        offline_economic_evidence_complete=bundle.INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE,
        integrated_economic_evidence_bundle_verified=bundle.INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED,
        economic_validity_offline_gate_pass=False,
    )
    pipeline_ready, pipeline_blockers = evaluate_paper_shadow_observation_readiness_v1(evidence)
    evaluate_integrated_paper_shadow_economic_validity_pipeline_v1(evidence=evidence)

    blockers: list[str] = []
    if not correctness.verified:
        blockers.extend(correctness.blockers)
    if not bundle.verified:
        blockers.extend(bundle.blockers)
    if not readiness.PAPER_SHADOW_OBSERVATION_READINESS_PASS:
        blockers.extend(readiness.readiness_blockers)
    if not pipeline_ready:
        blockers.extend(list(pipeline_blockers))

    correctness_pass_flag = correctness.verified and bool(
        correctness.proof
        and correctness.proof.get("INTEGRATED_OFFLINE_REPLAY_AND_CORRECTNESS_PASS")
    )
    shadow_ready = (
        correctness_pass_flag
        and readiness.PAPER_SHADOW_OBSERVATION_READINESS_PASS
        and bundle.INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED
        and not blockers
    )
    return ShadowReadinessAdjudicationResultV1(
        SHADOW_READINESS="READY" if shadow_ready else "NOT_READY",
        TESTNET_READINESS="NOT_READY",
        INTEGRATED_OFFLINE_REPLAY_AND_CORRECTNESS_PASS=correctness_pass_flag,
        PAPER_SHADOW_OBSERVATION_READINESS_PASS=readiness.PAPER_SHADOW_OBSERVATION_READINESS_PASS,
        INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE=bundle.INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE,
        INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED=bundle.INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED,
        repository_head_sha=head,
        blockers=sorted(set(blockers)),
    )
