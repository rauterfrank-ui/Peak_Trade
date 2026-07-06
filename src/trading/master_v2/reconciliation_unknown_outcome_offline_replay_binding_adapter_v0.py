# src/trading/master_v2/reconciliation_unknown_outcome_offline_replay_binding_adapter_v0.py
"""
Offline replay adapter: binds Integrated / Scenario replay to canonical
reconciliation and unknown-outcome boundary semantics without duplicating
live reconciliation logic.

Wiring-only parity slice — no runtime authority, no order effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Tuple

from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    ExistingPositionSide,
    PositionState,
    ReconciliationState,
)

RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_ADAPTER_LAYER_VERSION = "v0"
RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0"
)
RUNTIME_STATE_RECONCILIATION_OWNER = "src.meta.learning_loop.runtime_state_reconciliation_v1"
ENTRY_EXIT_POLICY_OWNER = "trading.master_v2.double_play_entry_exit_policy_v0"

RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE = "BOUND_OFFLINE"
RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_NONE = "NONE"

RUNTIME_AUTHORITY_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"
CREDENTIAL_EFFECT_NONE = "NONE"

_ENTER_OUTCOMES = frozenset(
    {
        DecisionOutcome.ENTER_LONG.value,
        DecisionOutcome.ENTER_SHORT.value,
    }
)
_OPPOSITE_ENTRY_BLOCKED_POSITIONS = frozenset(
    {
        PositionState.REDUCING_PARTIAL,
        PositionState.EXIT_PENDING,
        PositionState.SUBMISSION_UNKNOWN,
        PositionState.RECONCILIATION_REQUIRED,
    }
)


@dataclass(frozen=True)
class ReconciliationUnknownOutcomeOfflineReplayContextV0:
    """Offline-only reconciliation / unknown-outcome boundary inputs."""

    position_state: PositionState = PositionState.FLAT_RECONCILED
    reconciliation_state: ReconciliationState = ReconciliationState.RECONCILED
    venue_flat: bool = True
    existing_position_side: ExistingPositionSide = ExistingPositionSide.NONE
    intent_snapshot_unresolved: bool = False
    order_snapshot_unresolved: bool = False
    fill_snapshot_unresolved: bool = False


@dataclass(frozen=True)
class ReconciliationUnknownOutcomeOfflineReplayBoundaryV0:
    reconciliation_unknown_outcome_bound: bool
    runtime_authority_effect: str
    order_effect: str
    credential_effect: str
    submission_unknown_blocks_new_exposure: bool
    unresolved_reduce_blocks_opposite_side: bool
    reconciliation_required_maps_to_reconcile_only: bool
    reconciled_flat_required_before_opposite_side: bool
    unknown_outcome_never_auto_resubmits: bool
    venue_flat_alone_insufficient: bool
    no_auto_resubmit: bool
    hard_block_reasons: Tuple[str, ...]
    reason_codes: Tuple[str, ...]
    entry_exit_policy_owner_ref: str
    runtime_state_reconciliation_owner_ref: str
    input_digest: str
    semantic_digest: str


@dataclass(frozen=True)
class ReconciliationUnknownOutcomeOfflineReplayBindingResultV0:
    evidence: "CanonicalTradingDecisionEvidenceV1"
    boundary: ReconciliationUnknownOutcomeOfflineReplayBoundaryV0
    binding_applied: bool
    reconciliation_unknown_outcome_ref: str
    reconciliation_unknown_outcome_effect: str


def _compute_input_digest(ctx: ReconciliationUnknownOutcomeOfflineReplayContextV0) -> str:
    payload = {
        "existing_position_side": ctx.existing_position_side.value,
        "fill_snapshot_unresolved": ctx.fill_snapshot_unresolved,
        "intent_snapshot_unresolved": ctx.intent_snapshot_unresolved,
        "order_snapshot_unresolved": ctx.order_snapshot_unresolved,
        "position_state": ctx.position_state.value,
        "reconciliation_state": ctx.reconciliation_state.value,
        "venue_flat": ctx.venue_flat,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _serialize_boundary_canonical(
    boundary: ReconciliationUnknownOutcomeOfflineReplayBoundaryV0,
) -> str:
    payload = {
        "credential_effect": boundary.credential_effect,
        "entry_exit_policy_owner_ref": boundary.entry_exit_policy_owner_ref,
        "hard_block_reasons": list(boundary.hard_block_reasons),
        "no_auto_resubmit": boundary.no_auto_resubmit,
        "order_effect": boundary.order_effect,
        "reason_codes": list(boundary.reason_codes),
        "reconciled_flat_required_before_opposite_side": (
            boundary.reconciled_flat_required_before_opposite_side
        ),
        "reconciliation_required_maps_to_reconcile_only": (
            boundary.reconciliation_required_maps_to_reconcile_only
        ),
        "reconciliation_unknown_outcome_bound": boundary.reconciliation_unknown_outcome_bound,
        "runtime_authority_effect": boundary.runtime_authority_effect,
        "runtime_state_reconciliation_owner_ref": (boundary.runtime_state_reconciliation_owner_ref),
        "submission_unknown_blocks_new_exposure": boundary.submission_unknown_blocks_new_exposure,
        "unknown_outcome_never_auto_resubmits": boundary.unknown_outcome_never_auto_resubmits,
        "unresolved_reduce_blocks_opposite_side": boundary.unresolved_reduce_blocks_opposite_side,
        "venue_flat_alone_insufficient": boundary.venue_flat_alone_insufficient,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_reconciliation_unknown_outcome_ref_v0(
    boundary: ReconciliationUnknownOutcomeOfflineReplayBoundaryV0,
) -> str:
    return boundary.semantic_digest


def _snapshots_unresolved(ctx: ReconciliationUnknownOutcomeOfflineReplayContextV0) -> bool:
    return (
        ctx.intent_snapshot_unresolved
        or ctx.order_snapshot_unresolved
        or ctx.fill_snapshot_unresolved
    )


def evaluate_offline_reconciliation_unknown_outcome_boundary_v0(
    ctx: ReconciliationUnknownOutcomeOfflineReplayContextV0,
    *,
    decision_outcome: str = "",
) -> ReconciliationUnknownOutcomeOfflineReplayBoundaryV0:
    """Derive offline reconciliation / unknown-outcome boundary from replay context."""
    hard_blocks: list[str] = []
    reason_codes: list[str] = []

    submission_unknown_blocks = False
    unresolved_reduce_blocks = False
    reconciliation_reconcile_only = False
    reconciled_flat_required = False
    unknown_never_resubmits = False
    venue_flat_insufficient = False
    no_auto_resubmit = True

    if ctx.position_state is PositionState.SUBMISSION_UNKNOWN:
        submission_unknown_blocks = True
        unknown_never_resubmits = True
        no_auto_resubmit = True
        hard_blocks.append("submission_unknown_blocks_new_exposure")
        hard_blocks.append("unknown_outcome_no_auto_resubmit")
        reason_codes.append("submission_unknown")

    if ctx.position_state is PositionState.RECONCILIATION_REQUIRED:
        reconciliation_reconcile_only = True
        hard_blocks.append("reconciliation_required_blocks_new_exposure")
        reason_codes.append("position_reconciliation_required")

    if ctx.reconciliation_state is not ReconciliationState.RECONCILED:
        reconciliation_reconcile_only = True
        hard_blocks.append("reconciliation_required_blocks_new_exposure")
        reason_codes.append("reconciliation_required")

    if ctx.position_state in _OPPOSITE_ENTRY_BLOCKED_POSITIONS:
        unresolved_reduce_blocks = True
        reconciled_flat_required = True
        hard_blocks.append("unresolved_reduce_blocks_opposite_side_entry")
        reason_codes.append("unresolved_position_state")

    if ctx.position_state is not PositionState.FLAT_RECONCILED:
        reconciled_flat_required = True
        if ctx.venue_flat:
            venue_flat_insufficient = True
            hard_blocks.append("venue_flat_alone_insufficient")
            reason_codes.append("venue_flat_not_reconciled_flat")

    if ctx.venue_flat and _snapshots_unresolved(ctx):
        venue_flat_insufficient = True
        hard_blocks.append("venue_flat_alone_insufficient_unresolved_snapshots")
        reason_codes.append("intent_order_fill_snapshots_unresolved")

    if decision_outcome in _ENTER_OUTCOMES and hard_blocks:
        reason_codes.append("entry_blocked_by_reconciliation_unknown_outcome_boundary")

    input_digest = _compute_input_digest(ctx)
    boundary = ReconciliationUnknownOutcomeOfflineReplayBoundaryV0(
        reconciliation_unknown_outcome_bound=True,
        runtime_authority_effect=RUNTIME_AUTHORITY_EFFECT_NONE,
        order_effect=ORDER_EFFECT_NONE,
        credential_effect=CREDENTIAL_EFFECT_NONE,
        submission_unknown_blocks_new_exposure=submission_unknown_blocks,
        unresolved_reduce_blocks_opposite_side=unresolved_reduce_blocks,
        reconciliation_required_maps_to_reconcile_only=reconciliation_reconcile_only,
        reconciled_flat_required_before_opposite_side=reconciled_flat_required,
        unknown_outcome_never_auto_resubmits=unknown_never_resubmits,
        venue_flat_alone_insufficient=venue_flat_insufficient,
        no_auto_resubmit=no_auto_resubmit,
        hard_block_reasons=tuple(dict.fromkeys(hard_blocks)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        entry_exit_policy_owner_ref=ENTRY_EXIT_POLICY_OWNER,
        runtime_state_reconciliation_owner_ref=RUNTIME_STATE_RECONCILIATION_OWNER,
        input_digest=input_digest,
        semantic_digest="",
    )
    semantic_digest = hashlib.sha256(
        _serialize_boundary_canonical(boundary).encode("utf-8")
    ).hexdigest()
    return replace(boundary, semantic_digest=semantic_digest)


def bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    context: ReconciliationUnknownOutcomeOfflineReplayContextV0,
) -> ReconciliationUnknownOutcomeOfflineReplayBindingResultV0:
    from trading.master_v2.canonical_trading_decision_evidence_v1 import (
        CanonicalTradingDecisionEvidenceV1,
        finalize_offline_replay_decision_evidence_v1,
    )

    boundary = evaluate_offline_reconciliation_unknown_outcome_boundary_v0(
        context,
        decision_outcome=evidence.decision_outcome,
    )
    reconciliation_ref = compute_reconciliation_unknown_outcome_ref_v0(boundary)
    merged_reason_codes = tuple(dict.fromkeys((*evidence.reason_codes, *boundary.reason_codes)))
    bound_evidence = replace(
        evidence,
        reason_codes=merged_reason_codes,
        reconciliation_unknown_outcome_ref=reconciliation_ref,
        reconciliation_unknown_outcome_effect=RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE,
    )
    finalized = finalize_offline_replay_decision_evidence_v1(bound_evidence)
    return ReconciliationUnknownOutcomeOfflineReplayBindingResultV0(
        evidence=finalized,
        boundary=boundary,
        binding_applied=True,
        reconciliation_unknown_outcome_ref=reconciliation_ref,
        reconciliation_unknown_outcome_effect=RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE,
    )


def evaluate_scenario_reconciliation_unknown_outcome_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    context: ReconciliationUnknownOutcomeOfflineReplayContextV0,
) -> ReconciliationUnknownOutcomeOfflineReplayBindingResultV0:
    return bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(
        evidence,
        context=context,
    )


def reconciliation_unknown_outcome_binding_non_authority_boundary_ok_v0(
    binding: ReconciliationUnknownOutcomeOfflineReplayBindingResultV0,
) -> bool:
    boundary = binding.boundary
    ev = binding.evidence
    if not boundary.reconciliation_unknown_outcome_bound:
        return False
    if boundary.runtime_authority_effect != RUNTIME_AUTHORITY_EFFECT_NONE:
        return False
    if boundary.order_effect != ORDER_EFFECT_NONE:
        return False
    if boundary.credential_effect != CREDENTIAL_EFFECT_NONE:
        return False
    if not boundary.no_auto_resubmit:
        return False
    if ev.execution_eligible or ev.adapter_compatible:
        return False
    if ev.authority_effect != "NONE":
        return False
    if ev.runtime_effect != "NONE":
        return False
    if ev.order_effect != "NONE":
        return False
    if (
        binding.binding_applied
        and binding.reconciliation_unknown_outcome_effect
        != RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE
    ):
        return False
    return True


def system_economic_evidence_admissible_v0(
    binding: ReconciliationUnknownOutcomeOfflineReplayBindingResultV0,
) -> bool:
    return False


# Avoid circular import at module level for type hints only.
from trading.master_v2.canonical_trading_decision_evidence_v1 import (  # noqa: E402
    CanonicalTradingDecisionEvidenceV1,
)
