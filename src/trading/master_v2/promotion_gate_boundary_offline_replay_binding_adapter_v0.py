# src/trading/master_v2/promotion_gate_boundary_offline_replay_binding_adapter_v0.py
"""
Offline replay adapter: binds Integrated / Scenario / Backtest replay to canonical
Promotion Gate boundary semantics via promotion_economic_gate_v1 without duplicating
gate logic.

Wiring-only parity slice — no runtime authority, no order effects, no promotion authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Tuple

from src.backtest.economic_validity_policy_v1 import canonical_economic_validity_policy_v1
from src.governance.promotion_loop.promotion_economic_gate_v1 import (
    AUTHORITY_EFFECT_NONE,
    PROMOTION_ECONOMIC_GATE_POLICY_OWNER,
    PROMOTION_ECONOMIC_GATE_POLICY_VERSION,
    REASON_CONFIDENCE_SCORE_ONLY,
    REASON_MANIFEST_BINDING_FAILED,
    REASON_ZERO_COST_EVIDENCE,
    PromotionEconomicGateInputV1,
    PromotionEconomicGateResultV1,
    canonical_promotion_economic_gate_policy_v1,
    evaluate_promotion_economic_gate_v1,
)

PROMOTION_GATE_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_LAYER_VERSION = "v0"
PROMOTION_GATE_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.promotion_gate_boundary_offline_replay_binding_adapter_v0"
)
PROMOTION_GATE_CANONICAL_OWNER = PROMOTION_ECONOMIC_GATE_POLICY_OWNER

PROMOTION_GATE_BOUNDARY_EFFECT_BOUND_OFFLINE = "BOUND_OFFLINE"
PROMOTION_GATE_BOUNDARY_EFFECT_NONE = "NONE"

RUNTIME_AUTHORITY_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"
CREDENTIAL_EFFECT_NONE = "NONE"

_OFFLINE_EVALUATION_TIMESTAMP = "2026-07-02T22:30:00Z"


@dataclass(frozen=True)
class PromotionGateBoundaryOfflineReplayContextV0:
    """Offline-only Promotion Gate boundary inputs — no runtime authority."""

    strategy_id: str
    strategy_version: str
    candidate_id: str
    economic_viability_evidence_ref: str
    economic_validity_status: str
    robustness_status: str
    data_admissibility_status: str
    evidence_admissibility_status: str
    policy_threshold_status: str
    walk_forward_status: str
    out_of_sample_status: str
    monte_carlo_status: str
    stress_status: str
    parameter_sensitivity_status: str
    reproducibility_status: str
    digest_binding_status: str
    manifest_binding_status: str
    safety_policy_status: str
    futures_only: bool
    bitcoin_direction_allowed: bool
    config_digest: str
    implementation_digest: str
    policy_digest: str
    evidence_manifest_digest: str
    economic_validity_proven: bool = False
    profitability_claim_allowed: bool = False
    promotion_basis_confidence_only: bool = False
    promotion_basis_in_sample_profit_only: bool = False
    zero_cost_evidence: bool = False
    raw_signal_evidence: bool = False
    manifest_verify_only: bool = False


@dataclass(frozen=True)
class PromotionGateBoundaryOfflineReplayBoundaryV0:
    promotion_gate_boundary_bound: bool
    runtime_authority_effect: str
    order_effect: str
    credential_effect: str
    promotion_eligible: bool
    economic_validity_pass: bool
    robustness_pass: bool
    evidence_admissible: bool
    safety_policy_pass: bool
    promotion_gate_semantics_represented: bool
    economic_validity_required_for_promotion_represented: bool
    robustness_required_for_promotion_represented: bool
    evidence_admissibility_required_for_promotion_represented: bool
    safety_policy_required_for_promotion_represented: bool
    no_promotion_from_confidence_only_represented: bool
    no_runtime_authority_from_promotion_represented: bool
    no_economic_claim_from_manifest_verify_alone_represented: bool
    raw_signal_evidence_not_promotion_admissible_represented: bool
    hard_block_reasons: Tuple[str, ...]
    reason_codes: Tuple[str, ...]
    promotion_gate_owner_ref: str
    promotion_gate_policy_version_ref: str
    gate_result_id: str
    evaluation_digest: str
    input_digest: str
    semantic_digest: str


@dataclass(frozen=True)
class PromotionGateBoundaryOfflineReplayBindingResultV0:
    evidence: "CanonicalTradingDecisionEvidenceV1"
    boundary: PromotionGateBoundaryOfflineReplayBoundaryV0
    binding_applied: bool
    promotion_gate_boundary_ref: str
    promotion_gate_boundary_effect: str
    gate_result: PromotionEconomicGateResultV1


def _compute_input_digest(ctx: PromotionGateBoundaryOfflineReplayContextV0) -> str:
    payload = {
        "bitcoin_direction_allowed": ctx.bitcoin_direction_allowed,
        "candidate_id": ctx.candidate_id,
        "config_digest": ctx.config_digest,
        "data_admissibility_status": ctx.data_admissibility_status,
        "digest_binding_status": ctx.digest_binding_status,
        "economic_validity_proven": ctx.economic_validity_proven,
        "economic_validity_status": ctx.economic_validity_status,
        "economic_viability_evidence_ref": ctx.economic_viability_evidence_ref,
        "evidence_admissibility_status": ctx.evidence_admissibility_status,
        "evidence_manifest_digest": ctx.evidence_manifest_digest,
        "futures_only": ctx.futures_only,
        "implementation_digest": ctx.implementation_digest,
        "manifest_binding_status": ctx.manifest_binding_status,
        "manifest_verify_only": ctx.manifest_verify_only,
        "monte_carlo_status": ctx.monte_carlo_status,
        "out_of_sample_status": ctx.out_of_sample_status,
        "parameter_sensitivity_status": ctx.parameter_sensitivity_status,
        "policy_digest": ctx.policy_digest,
        "policy_threshold_status": ctx.policy_threshold_status,
        "profitability_claim_allowed": ctx.profitability_claim_allowed,
        "promotion_basis_confidence_only": ctx.promotion_basis_confidence_only,
        "promotion_basis_in_sample_profit_only": ctx.promotion_basis_in_sample_profit_only,
        "raw_signal_evidence": ctx.raw_signal_evidence,
        "reproducibility_status": ctx.reproducibility_status,
        "robustness_status": ctx.robustness_status,
        "safety_policy_status": ctx.safety_policy_status,
        "strategy_id": ctx.strategy_id,
        "strategy_version": ctx.strategy_version,
        "stress_status": ctx.stress_status,
        "walk_forward_status": ctx.walk_forward_status,
        "zero_cost_evidence": ctx.zero_cost_evidence,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _serialize_boundary_canonical(boundary: PromotionGateBoundaryOfflineReplayBoundaryV0) -> str:
    payload = {
        "credential_effect": boundary.credential_effect,
        "economic_validity_pass": boundary.economic_validity_pass,
        "economic_validity_required_for_promotion_represented": (
            boundary.economic_validity_required_for_promotion_represented
        ),
        "evidence_admissibility_required_for_promotion_represented": (
            boundary.evidence_admissibility_required_for_promotion_represented
        ),
        "evidence_admissible": boundary.evidence_admissible,
        "gate_result_id": boundary.gate_result_id,
        "hard_block_reasons": list(boundary.hard_block_reasons),
        "no_economic_claim_from_manifest_verify_alone_represented": (
            boundary.no_economic_claim_from_manifest_verify_alone_represented
        ),
        "no_promotion_from_confidence_only_represented": (
            boundary.no_promotion_from_confidence_only_represented
        ),
        "no_runtime_authority_from_promotion_represented": (
            boundary.no_runtime_authority_from_promotion_represented
        ),
        "order_effect": boundary.order_effect,
        "promotion_eligible": boundary.promotion_eligible,
        "promotion_gate_boundary_bound": boundary.promotion_gate_boundary_bound,
        "promotion_gate_owner_ref": boundary.promotion_gate_owner_ref,
        "promotion_gate_policy_version_ref": boundary.promotion_gate_policy_version_ref,
        "promotion_gate_semantics_represented": boundary.promotion_gate_semantics_represented,
        "raw_signal_evidence_not_promotion_admissible_represented": (
            boundary.raw_signal_evidence_not_promotion_admissible_represented
        ),
        "reason_codes": list(boundary.reason_codes),
        "robustness_pass": boundary.robustness_pass,
        "robustness_required_for_promotion_represented": (
            boundary.robustness_required_for_promotion_represented
        ),
        "runtime_authority_effect": boundary.runtime_authority_effect,
        "safety_policy_pass": boundary.safety_policy_pass,
        "safety_policy_required_for_promotion_represented": (
            boundary.safety_policy_required_for_promotion_represented
        ),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def build_promotion_gate_input_v0(
    ctx: PromotionGateBoundaryOfflineReplayContextV0,
) -> PromotionEconomicGateInputV1:
    economic_policy = canonical_economic_validity_policy_v1()
    policy_digest = ctx.policy_digest.strip() or economic_policy.policy_digest()
    return PromotionEconomicGateInputV1(
        strategy_id=ctx.strategy_id,
        strategy_version=ctx.strategy_version,
        candidate_id=ctx.candidate_id,
        economic_viability_evidence_ref=ctx.economic_viability_evidence_ref,
        economic_validity_status=ctx.economic_validity_status,
        robustness_status=ctx.robustness_status,
        data_admissibility_status=ctx.data_admissibility_status,
        evidence_admissibility_status=ctx.evidence_admissibility_status,
        policy_threshold_status=ctx.policy_threshold_status,
        walk_forward_status=ctx.walk_forward_status,
        out_of_sample_status=ctx.out_of_sample_status,
        monte_carlo_status=ctx.monte_carlo_status,
        stress_status=ctx.stress_status,
        parameter_sensitivity_status=ctx.parameter_sensitivity_status,
        reproducibility_status=ctx.reproducibility_status,
        digest_binding_status=ctx.digest_binding_status,
        manifest_binding_status=ctx.manifest_binding_status,
        safety_policy_status=ctx.safety_policy_status,
        futures_only=ctx.futures_only,
        bitcoin_direction_allowed=ctx.bitcoin_direction_allowed,
        config_digest=ctx.config_digest,
        implementation_digest=ctx.implementation_digest,
        policy_digest=policy_digest,
        evidence_manifest_digest=ctx.evidence_manifest_digest,
        economic_validity_proven=ctx.economic_validity_proven,
        profitability_claim_allowed=ctx.profitability_claim_allowed,
        promotion_basis_confidence_only=ctx.promotion_basis_confidence_only,
        promotion_basis_in_sample_profit_only=ctx.promotion_basis_in_sample_profit_only,
        zero_cost_evidence=ctx.zero_cost_evidence,
    )


def evaluate_offline_promotion_gate_boundary_v0(
    ctx: PromotionGateBoundaryOfflineReplayContextV0,
) -> tuple[PromotionEconomicGateResultV1, PromotionGateBoundaryOfflineReplayBoundaryV0]:
    gate_policy = canonical_promotion_economic_gate_policy_v1()
    input_data = build_promotion_gate_input_v0(ctx)
    gate_result = evaluate_promotion_economic_gate_v1(
        policy=gate_policy,
        input_data=input_data,
        evaluation_timestamp=_OFFLINE_EVALUATION_TIMESTAMP,
        expected_policy_digest=input_data.policy_digest,
    )

    hard_blocks: list[str] = []
    if ctx.promotion_basis_confidence_only:
        hard_blocks.append("promotion_confidence_only_blocked")
    if ctx.zero_cost_evidence or ctx.raw_signal_evidence:
        hard_blocks.append("raw_signal_evidence_not_promotion_admissible")
    if ctx.manifest_verify_only and not gate_result.economic_validity_pass:
        hard_blocks.append("manifest_verify_alone_no_economic_claim")
    if not gate_result.promotion_eligible:
        hard_blocks.append("promotion_candidate_ineligible")

    reason_codes = tuple(dict.fromkeys((*gate_result.reason_codes, *hard_blocks)))
    semantics_represented = True
    no_confidence_only = (
        not ctx.promotion_basis_confidence_only
        or REASON_CONFIDENCE_SCORE_ONLY in gate_result.reason_codes
    )
    no_manifest_alone = (
        not ctx.manifest_verify_only
        or not gate_result.economic_validity_pass
        or REASON_MANIFEST_BINDING_FAILED in gate_result.reason_codes
        or any(code.startswith(REASON_MANIFEST_BINDING_FAILED) for code in gate_result.reason_codes)
    )
    raw_signal_blocked = (
        not (ctx.raw_signal_evidence or ctx.zero_cost_evidence)
        or REASON_ZERO_COST_EVIDENCE in gate_result.reason_codes
        or not gate_result.promotion_eligible
    )

    input_digest = _compute_input_digest(ctx)
    boundary = PromotionGateBoundaryOfflineReplayBoundaryV0(
        promotion_gate_boundary_bound=True,
        runtime_authority_effect=RUNTIME_AUTHORITY_EFFECT_NONE,
        order_effect=ORDER_EFFECT_NONE,
        credential_effect=CREDENTIAL_EFFECT_NONE,
        promotion_eligible=gate_result.promotion_eligible,
        economic_validity_pass=gate_result.economic_validity_pass,
        robustness_pass=gate_result.robustness_pass,
        evidence_admissible=gate_result.evidence_admissible,
        safety_policy_pass=gate_result.safety_policy_pass,
        promotion_gate_semantics_represented=semantics_represented,
        economic_validity_required_for_promotion_represented=True,
        robustness_required_for_promotion_represented=True,
        evidence_admissibility_required_for_promotion_represented=True,
        safety_policy_required_for_promotion_represented=True,
        no_promotion_from_confidence_only_represented=no_confidence_only,
        no_runtime_authority_from_promotion_represented=(
            gate_result.authority_effect == AUTHORITY_EFFECT_NONE
            and gate_result.runtime_effect == RUNTIME_AUTHORITY_EFFECT_NONE
            and not gate_result.runtime_eligible
            and not gate_result.execution_allowed
        ),
        no_economic_claim_from_manifest_verify_alone_represented=no_manifest_alone,
        raw_signal_evidence_not_promotion_admissible_represented=raw_signal_blocked,
        hard_block_reasons=tuple(dict.fromkeys(hard_blocks)),
        reason_codes=reason_codes,
        promotion_gate_owner_ref=PROMOTION_GATE_CANONICAL_OWNER,
        promotion_gate_policy_version_ref=PROMOTION_ECONOMIC_GATE_POLICY_VERSION,
        gate_result_id=gate_result.gate_result_id,
        evaluation_digest=gate_result.evaluation_digest,
        input_digest=input_digest,
        semantic_digest="",
    )
    semantic_digest = hashlib.sha256(
        _serialize_boundary_canonical(boundary).encode("utf-8")
    ).hexdigest()
    return gate_result, replace(boundary, semantic_digest=semantic_digest)


def compute_promotion_gate_boundary_ref_v0(
    boundary: PromotionGateBoundaryOfflineReplayBoundaryV0,
) -> str:
    return f"promotion_gate_boundary_v0:{boundary.semantic_digest[:16]}"


def bind_promotion_gate_boundary_offline_replay_evidence_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    context: PromotionGateBoundaryOfflineReplayContextV0,
) -> PromotionGateBoundaryOfflineReplayBindingResultV0:
    from trading.master_v2.canonical_trading_decision_evidence_v1 import (
        finalize_offline_replay_decision_evidence_v1,
    )

    gate_result, boundary = evaluate_offline_promotion_gate_boundary_v0(context)
    promotion_ref = compute_promotion_gate_boundary_ref_v0(boundary)
    merged_reason_codes = tuple(dict.fromkeys((*evidence.reason_codes, *boundary.reason_codes)))
    bound_evidence = replace(
        evidence,
        reason_codes=merged_reason_codes,
    )
    finalized = finalize_offline_replay_decision_evidence_v1(bound_evidence)
    return PromotionGateBoundaryOfflineReplayBindingResultV0(
        evidence=finalized,
        boundary=boundary,
        binding_applied=True,
        promotion_gate_boundary_ref=promotion_ref,
        promotion_gate_boundary_effect=PROMOTION_GATE_BOUNDARY_EFFECT_BOUND_OFFLINE,
        gate_result=gate_result,
    )


def promotion_gate_boundary_binding_non_authority_boundary_ok_v0(
    binding: PromotionGateBoundaryOfflineReplayBindingResultV0,
) -> bool:
    boundary = binding.boundary
    ev = binding.evidence
    if not boundary.promotion_gate_boundary_bound:
        return False
    if boundary.runtime_authority_effect != RUNTIME_AUTHORITY_EFFECT_NONE:
        return False
    if boundary.order_effect != ORDER_EFFECT_NONE:
        return False
    if boundary.credential_effect != CREDENTIAL_EFFECT_NONE:
        return False
    if not boundary.no_runtime_authority_from_promotion_represented:
        return False
    if ev.execution_eligible or ev.adapter_compatible:
        return False
    if ev.authority_effect != "NONE":
        return False
    if ev.runtime_effect != "NONE":
        return False
    if ev.order_effect != "NONE":
        return False
    if binding.gate_result.runtime_eligible or binding.gate_result.execution_allowed:
        return False
    if (
        binding.binding_applied
        and binding.promotion_gate_boundary_effect != PROMOTION_GATE_BOUNDARY_EFFECT_BOUND_OFFLINE
    ):
        return False
    return True


from trading.master_v2.canonical_trading_decision_evidence_v1 import (  # noqa: E402
    CanonicalTradingDecisionEvidenceV1,
)
