# src/trading/master_v2/feedback_learning_boundary_offline_replay_binding_adapter_v0.py
"""
Offline replay adapter: binds Integrated / Scenario / Backtest replay to canonical
Feedback / Learning boundary semantics without duplicating learning-loop logic.

Wiring-only parity slice — observe-only; no strategy, promotion, or runtime mutation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping, Tuple

from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.deploy_inactive_v1 import DEPLOYMENT_CANDIDATE_CONTRACT_NAME
from src.meta.learning_loop.runtime_observation_feedback_v1 import OBSERVATION_CONTRACT_NAME

FEEDBACK_LEARNING_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_LAYER_VERSION = "v0"
FEEDBACK_LEARNING_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.feedback_learning_boundary_offline_replay_binding_adapter_v0"
)
FEEDBACK_LEARNING_CANONICAL_OWNER = "src.meta.learning_loop.runtime_observation_feedback_v1"

FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED = True
FEEDBACK_LEARNING_MODE_OBSERVE_ONLY_NO_MUTATION = "observe_only_no_mutation"

FEEDBACK_LEARNING_BOUNDARY_EFFECT_BOUND_OFFLINE = "BOUND_OFFLINE"
FEEDBACK_LEARNING_BOUNDARY_EFFECT_NONE = "NONE"

RUNTIME_AUTHORITY_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"
CREDENTIAL_EFFECT_NONE = "NONE"


@dataclass(frozen=True)
class FeedbackLearningBoundaryOfflineReplayContextV0:
    """Offline-only Feedback / Learning boundary inputs — no learning effects."""

    feedback_learning_mode: str = FEEDBACK_LEARNING_MODE_OBSERVE_ONLY_NO_MUTATION
    feedback_observation_contract_ref: str = OBSERVATION_CONTRACT_NAME
    learning_deploy_inactive_contract_ref: str = DEPLOYMENT_CANDIDATE_CONTRACT_NAME


@dataclass(frozen=True)
class FeedbackLearningBoundaryOfflineReplayBoundaryV0:
    feedback_learning_boundary_bound: bool
    feedback_learning_boundary_documented: bool
    observe_only_no_mutation: bool
    comparison_authority_invariants_satisfied: bool
    no_strategy_selection_mutation: bool
    no_promotion_mutation: bool
    no_runtime_eligibility_mutation: bool
    no_sizing_mutation: bool
    no_order_intent_mutation: bool
    no_safety_mutation: bool
    no_reconciliation_mutation: bool
    no_economic_results_mutation: bool
    runtime_authority_effect: str
    order_effect: str
    credential_effect: str
    feedback_learning_mode: str
    feedback_observation_contract_ref: str
    learning_deploy_inactive_contract_ref: str
    authority_invariants: Mapping[str, bool]
    input_digest: str
    semantic_digest: str


@dataclass(frozen=True)
class FeedbackLearningBoundaryOfflineReplayBindingResultV0:
    evidence: "CanonicalTradingDecisionEvidenceV1"
    boundary: FeedbackLearningBoundaryOfflineReplayBoundaryV0
    binding_applied: bool
    feedback_learning_boundary_ref: str
    feedback_learning_boundary_effect: str


def _authority_invariants_satisfied() -> bool:
    return all(COMPARISON_AUTHORITY_INVARIANTS.values())


def _compute_input_digest(ctx: FeedbackLearningBoundaryOfflineReplayContextV0) -> str:
    payload = {
        "feedback_learning_mode": ctx.feedback_learning_mode,
        "feedback_observation_contract_ref": ctx.feedback_observation_contract_ref,
        "learning_deploy_inactive_contract_ref": ctx.learning_deploy_inactive_contract_ref,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _serialize_boundary_canonical(
    boundary: FeedbackLearningBoundaryOfflineReplayBoundaryV0,
) -> str:
    payload = {
        "comparison_authority_invariants_satisfied": (
            boundary.comparison_authority_invariants_satisfied
        ),
        "credential_effect": boundary.credential_effect,
        "feedback_learning_boundary_bound": boundary.feedback_learning_boundary_bound,
        "feedback_learning_boundary_documented": boundary.feedback_learning_boundary_documented,
        "feedback_learning_mode": boundary.feedback_learning_mode,
        "no_economic_results_mutation": boundary.no_economic_results_mutation,
        "no_order_intent_mutation": boundary.no_order_intent_mutation,
        "no_promotion_mutation": boundary.no_promotion_mutation,
        "no_reconciliation_mutation": boundary.no_reconciliation_mutation,
        "no_runtime_eligibility_mutation": boundary.no_runtime_eligibility_mutation,
        "no_safety_mutation": boundary.no_safety_mutation,
        "no_sizing_mutation": boundary.no_sizing_mutation,
        "no_strategy_selection_mutation": boundary.no_strategy_selection_mutation,
        "observe_only_no_mutation": boundary.observe_only_no_mutation,
        "order_effect": boundary.order_effect,
        "runtime_authority_effect": boundary.runtime_authority_effect,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def evaluate_offline_feedback_learning_boundary_v0(
    *,
    context: FeedbackLearningBoundaryOfflineReplayContextV0 | None = None,
) -> FeedbackLearningBoundaryOfflineReplayBoundaryV0:
    """Represent Feedback / Learning boundary as observe-only with no authoritative mutation."""
    ctx = context or FeedbackLearningBoundaryOfflineReplayContextV0()
    if ctx.feedback_learning_mode != FEEDBACK_LEARNING_MODE_OBSERVE_ONLY_NO_MUTATION:
        raise ValueError("feedback_learning_mode_invalid")

    invariants_ok = _authority_invariants_satisfied()
    input_digest = _compute_input_digest(ctx)
    boundary = FeedbackLearningBoundaryOfflineReplayBoundaryV0(
        feedback_learning_boundary_bound=True,
        feedback_learning_boundary_documented=FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED,
        observe_only_no_mutation=True,
        comparison_authority_invariants_satisfied=invariants_ok,
        no_strategy_selection_mutation=True,
        no_promotion_mutation=True,
        no_runtime_eligibility_mutation=True,
        no_sizing_mutation=True,
        no_order_intent_mutation=True,
        no_safety_mutation=True,
        no_reconciliation_mutation=True,
        no_economic_results_mutation=True,
        runtime_authority_effect=RUNTIME_AUTHORITY_EFFECT_NONE,
        order_effect=ORDER_EFFECT_NONE,
        credential_effect=CREDENTIAL_EFFECT_NONE,
        feedback_learning_mode=ctx.feedback_learning_mode,
        feedback_observation_contract_ref=ctx.feedback_observation_contract_ref,
        learning_deploy_inactive_contract_ref=ctx.learning_deploy_inactive_contract_ref,
        authority_invariants=dict(COMPARISON_AUTHORITY_INVARIANTS),
        input_digest=input_digest,
        semantic_digest="",
    )
    semantic_digest = hashlib.sha256(
        _serialize_boundary_canonical(boundary).encode("utf-8")
    ).hexdigest()
    return FeedbackLearningBoundaryOfflineReplayBoundaryV0(
        feedback_learning_boundary_bound=boundary.feedback_learning_boundary_bound,
        feedback_learning_boundary_documented=boundary.feedback_learning_boundary_documented,
        observe_only_no_mutation=boundary.observe_only_no_mutation,
        comparison_authority_invariants_satisfied=boundary.comparison_authority_invariants_satisfied,
        no_strategy_selection_mutation=boundary.no_strategy_selection_mutation,
        no_promotion_mutation=boundary.no_promotion_mutation,
        no_runtime_eligibility_mutation=boundary.no_runtime_eligibility_mutation,
        no_sizing_mutation=boundary.no_sizing_mutation,
        no_order_intent_mutation=boundary.no_order_intent_mutation,
        no_safety_mutation=boundary.no_safety_mutation,
        no_reconciliation_mutation=boundary.no_reconciliation_mutation,
        no_economic_results_mutation=boundary.no_economic_results_mutation,
        runtime_authority_effect=boundary.runtime_authority_effect,
        order_effect=boundary.order_effect,
        credential_effect=boundary.credential_effect,
        feedback_learning_mode=boundary.feedback_learning_mode,
        feedback_observation_contract_ref=boundary.feedback_observation_contract_ref,
        learning_deploy_inactive_contract_ref=boundary.learning_deploy_inactive_contract_ref,
        authority_invariants=boundary.authority_invariants,
        input_digest=boundary.input_digest,
        semantic_digest=semantic_digest,
    )


def compute_feedback_learning_boundary_ref_v0(
    boundary: FeedbackLearningBoundaryOfflineReplayBoundaryV0,
) -> str:
    return f"feedback_learning_boundary_v0:{boundary.semantic_digest[:16]}"


def bind_feedback_learning_boundary_offline_replay_evidence_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    context: FeedbackLearningBoundaryOfflineReplayContextV0 | None = None,
) -> FeedbackLearningBoundaryOfflineReplayBindingResultV0:
    """Attach offline Feedback / Learning boundary metadata without mutating decision evidence."""
    boundary = evaluate_offline_feedback_learning_boundary_v0(context=context)
    feedback_ref = compute_feedback_learning_boundary_ref_v0(boundary)
    return FeedbackLearningBoundaryOfflineReplayBindingResultV0(
        evidence=evidence,
        boundary=boundary,
        binding_applied=True,
        feedback_learning_boundary_ref=feedback_ref,
        feedback_learning_boundary_effect=FEEDBACK_LEARNING_BOUNDARY_EFFECT_BOUND_OFFLINE,
    )


def feedback_learning_boundary_binding_non_authority_boundary_ok_v0(
    binding: FeedbackLearningBoundaryOfflineReplayBindingResultV0,
) -> bool:
    boundary = binding.boundary
    if not boundary.feedback_learning_boundary_bound:
        return False
    if not boundary.feedback_learning_boundary_documented:
        return False
    if not boundary.observe_only_no_mutation:
        return False
    if not boundary.comparison_authority_invariants_satisfied:
        return False
    mutation_flags = (
        boundary.no_strategy_selection_mutation,
        boundary.no_promotion_mutation,
        boundary.no_runtime_eligibility_mutation,
        boundary.no_sizing_mutation,
        boundary.no_order_intent_mutation,
        boundary.no_safety_mutation,
        boundary.no_reconciliation_mutation,
        boundary.no_economic_results_mutation,
    )
    if not all(mutation_flags):
        return False
    if boundary.runtime_authority_effect != RUNTIME_AUTHORITY_EFFECT_NONE:
        return False
    if boundary.order_effect != ORDER_EFFECT_NONE:
        return False
    if boundary.credential_effect != CREDENTIAL_EFFECT_NONE:
        return False
    return (
        binding.feedback_learning_boundary_effect == FEEDBACK_LEARNING_BOUNDARY_EFFECT_BOUND_OFFLINE
    )


from trading.master_v2.canonical_trading_decision_evidence_v1 import (  # noqa: E402
    CanonicalTradingDecisionEvidenceV1,
)

__all__ = [
    "FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED",
    "FEEDBACK_LEARNING_BOUNDARY_EFFECT_BOUND_OFFLINE",
    "FEEDBACK_LEARNING_BOUNDARY_EFFECT_NONE",
    "FEEDBACK_LEARNING_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_LAYER_VERSION",
    "FEEDBACK_LEARNING_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER",
    "FEEDBACK_LEARNING_CANONICAL_OWNER",
    "FEEDBACK_LEARNING_MODE_OBSERVE_ONLY_NO_MUTATION",
    "FeedbackLearningBoundaryOfflineReplayBindingResultV0",
    "FeedbackLearningBoundaryOfflineReplayBoundaryV0",
    "FeedbackLearningBoundaryOfflineReplayContextV0",
    "bind_feedback_learning_boundary_offline_replay_evidence_v0",
    "compute_feedback_learning_boundary_ref_v0",
    "evaluate_offline_feedback_learning_boundary_v0",
    "feedback_learning_boundary_binding_non_authority_boundary_ok_v0",
]
