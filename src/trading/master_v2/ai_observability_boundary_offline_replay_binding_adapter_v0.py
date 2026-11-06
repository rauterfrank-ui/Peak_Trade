# src/trading/master_v2/ai_observability_boundary_offline_replay_binding_adapter_v0.py
"""
Offline replay adapter: binds Integrated / Scenario / Backtest replay to canonical
AI / Observability / Explainability boundary semantics via canonical decision evidence.

Wiring-only parity slice — read-only evidence-only; no runtime authority, no order effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Tuple

from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION,
    EVIDENCE_SCHEMA_VERSION,
)
from trading.master_v2.decision_packet_v1 import MASTER_V2_DECISION_PACKET_LAYER_VERSION

AI_OBSERVABILITY_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_LAYER_VERSION = "v0"
AI_OBSERVABILITY_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.ai_observability_boundary_offline_replay_binding_adapter_v0"
)
AI_OBSERVABILITY_CANONICAL_OWNER = "trading.master_v2.canonical_trading_decision_evidence_v1"

AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED = True
EXPLAINABILITY_MODE_READ_ONLY_EVIDENCE_ONLY = "read_only_evidence_only"

AI_OBSERVABILITY_BOUNDARY_EFFECT_BOUND_OFFLINE = "BOUND_OFFLINE"
AI_OBSERVABILITY_BOUNDARY_EFFECT_NONE = "NONE"

RUNTIME_AUTHORITY_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"
CREDENTIAL_EFFECT_NONE = "NONE"


@dataclass(frozen=True)
class AiObservabilityBoundaryOfflineReplayContextV0:
    """Offline-only AI / Observability boundary inputs — no runtime authority."""

    explainability_envelope_mode: str = EXPLAINABILITY_MODE_READ_ONLY_EVIDENCE_ONLY
    ai_layer_owner_digest_ref: str = EVIDENCE_SCHEMA_VERSION
    decision_packet_owner_digest_ref: str = MASTER_V2_DECISION_PACKET_LAYER_VERSION


@dataclass(frozen=True)
class AiObservabilityBoundaryOfflineReplayBoundaryV0:
    ai_observability_boundary_bound: bool
    ai_layer_observability_boundary_documented: bool
    read_only_evidence_only: bool
    explainability_envelope_represented: bool
    reason_codes_observable: bool
    decision_precedence_trace_observable: bool
    no_ai_trade_authority: bool
    runtime_authority_effect: str
    order_effect: str
    credential_effect: str
    explainability_envelope_mode: str
    ai_layer_owner_digest_ref: str
    decision_packet_owner_digest_ref: str
    input_digest: str
    semantic_digest: str


@dataclass(frozen=True)
class AiObservabilityBoundaryOfflineReplayBindingResultV0:
    evidence: "CanonicalTradingDecisionEvidenceV1"
    boundary: AiObservabilityBoundaryOfflineReplayBoundaryV0
    binding_applied: bool
    ai_observability_boundary_ref: str
    ai_observability_boundary_effect: str


def _compute_input_digest(ctx: AiObservabilityBoundaryOfflineReplayContextV0) -> str:
    payload = {
        "ai_layer_owner_digest_ref": ctx.ai_layer_owner_digest_ref,
        "decision_packet_owner_digest_ref": ctx.decision_packet_owner_digest_ref,
        "explainability_envelope_mode": ctx.explainability_envelope_mode,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _serialize_boundary_canonical(
    boundary: AiObservabilityBoundaryOfflineReplayBoundaryV0,
) -> str:
    payload = {
        "ai_layer_observability_boundary_documented": (
            boundary.ai_layer_observability_boundary_documented
        ),
        "ai_observability_boundary_bound": boundary.ai_observability_boundary_bound,
        "credential_effect": boundary.credential_effect,
        "decision_packet_owner_digest_ref": boundary.decision_packet_owner_digest_ref,
        "decision_precedence_trace_observable": boundary.decision_precedence_trace_observable,
        "explainability_envelope_mode": boundary.explainability_envelope_mode,
        "explainability_envelope_represented": boundary.explainability_envelope_represented,
        "no_ai_trade_authority": boundary.no_ai_trade_authority,
        "order_effect": boundary.order_effect,
        "read_only_evidence_only": boundary.read_only_evidence_only,
        "reason_codes_observable": boundary.reason_codes_observable,
        "runtime_authority_effect": boundary.runtime_authority_effect,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def evaluate_offline_ai_observability_boundary_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    context: AiObservabilityBoundaryOfflineReplayContextV0 | None = None,
) -> AiObservabilityBoundaryOfflineReplayBoundaryV0:
    """Represent AI / Observability / Explainability boundary from decision evidence only."""
    ctx = context or AiObservabilityBoundaryOfflineReplayContextV0()
    if ctx.explainability_envelope_mode != EXPLAINABILITY_MODE_READ_ONLY_EVIDENCE_ONLY:
        raise ValueError("ai_observability_explainability_mode_invalid")

    reason_codes_observable = bool(evidence.reason_codes)
    trace_observable = bool(evidence.decision_precedence_trace)
    explainability_represented = (
        ctx.explainability_envelope_mode == EXPLAINABILITY_MODE_READ_ONLY_EVIDENCE_ONLY
        and evidence.evidence_schema_version == EVIDENCE_SCHEMA_VERSION
    )
    no_ai_trade_authority = (
        evidence.authority_effect == RUNTIME_AUTHORITY_EFFECT_NONE
        and evidence.runtime_effect == RUNTIME_AUTHORITY_EFFECT_NONE
        and evidence.order_effect == ORDER_EFFECT_NONE
        and not evidence.execution_eligible
    )

    input_digest = _compute_input_digest(ctx)
    boundary = AiObservabilityBoundaryOfflineReplayBoundaryV0(
        ai_observability_boundary_bound=True,
        ai_layer_observability_boundary_documented=AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED,
        read_only_evidence_only=True,
        explainability_envelope_represented=explainability_represented,
        reason_codes_observable=reason_codes_observable,
        decision_precedence_trace_observable=trace_observable,
        no_ai_trade_authority=no_ai_trade_authority,
        runtime_authority_effect=RUNTIME_AUTHORITY_EFFECT_NONE,
        order_effect=ORDER_EFFECT_NONE,
        credential_effect=CREDENTIAL_EFFECT_NONE,
        explainability_envelope_mode=ctx.explainability_envelope_mode,
        ai_layer_owner_digest_ref=ctx.ai_layer_owner_digest_ref,
        decision_packet_owner_digest_ref=ctx.decision_packet_owner_digest_ref,
        input_digest=input_digest,
        semantic_digest="",
    )
    semantic_digest = hashlib.sha256(
        _serialize_boundary_canonical(boundary).encode("utf-8")
    ).hexdigest()
    return AiObservabilityBoundaryOfflineReplayBoundaryV0(
        ai_observability_boundary_bound=boundary.ai_observability_boundary_bound,
        ai_layer_observability_boundary_documented=boundary.ai_layer_observability_boundary_documented,
        read_only_evidence_only=boundary.read_only_evidence_only,
        explainability_envelope_represented=boundary.explainability_envelope_represented,
        reason_codes_observable=boundary.reason_codes_observable,
        decision_precedence_trace_observable=boundary.decision_precedence_trace_observable,
        no_ai_trade_authority=boundary.no_ai_trade_authority,
        runtime_authority_effect=boundary.runtime_authority_effect,
        order_effect=boundary.order_effect,
        credential_effect=boundary.credential_effect,
        explainability_envelope_mode=boundary.explainability_envelope_mode,
        ai_layer_owner_digest_ref=boundary.ai_layer_owner_digest_ref,
        decision_packet_owner_digest_ref=boundary.decision_packet_owner_digest_ref,
        input_digest=boundary.input_digest,
        semantic_digest=semantic_digest,
    )


def compute_ai_observability_boundary_ref_v0(
    boundary: AiObservabilityBoundaryOfflineReplayBoundaryV0,
) -> str:
    return f"ai_observability_boundary_v0:{boundary.semantic_digest[:16]}"


def bind_ai_observability_boundary_offline_replay_evidence_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    context: AiObservabilityBoundaryOfflineReplayContextV0 | None = None,
) -> AiObservabilityBoundaryOfflineReplayBindingResultV0:
    """Attach offline AI / Observability boundary metadata without mutating decision evidence."""
    boundary = evaluate_offline_ai_observability_boundary_v0(evidence, context=context)
    ai_ref = compute_ai_observability_boundary_ref_v0(boundary)
    return AiObservabilityBoundaryOfflineReplayBindingResultV0(
        evidence=evidence,
        boundary=boundary,
        binding_applied=True,
        ai_observability_boundary_ref=ai_ref,
        ai_observability_boundary_effect=AI_OBSERVABILITY_BOUNDARY_EFFECT_BOUND_OFFLINE,
    )


def ai_observability_boundary_binding_non_authority_boundary_ok_v0(
    binding: AiObservabilityBoundaryOfflineReplayBindingResultV0,
) -> bool:
    boundary = binding.boundary
    if not boundary.ai_observability_boundary_bound:
        return False
    if not boundary.ai_layer_observability_boundary_documented:
        return False
    if not boundary.read_only_evidence_only:
        return False
    if boundary.runtime_authority_effect != RUNTIME_AUTHORITY_EFFECT_NONE:
        return False
    if boundary.order_effect != ORDER_EFFECT_NONE:
        return False
    if boundary.credential_effect != CREDENTIAL_EFFECT_NONE:
        return False
    if not boundary.no_ai_trade_authority:
        return False
    return (
        binding.ai_observability_boundary_effect == AI_OBSERVABILITY_BOUNDARY_EFFECT_BOUND_OFFLINE
    )


from trading.master_v2.canonical_trading_decision_evidence_v1 import (  # noqa: E402
    CanonicalTradingDecisionEvidenceV1,
)

__all__ = [
    "AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED",
    "AI_OBSERVABILITY_BOUNDARY_EFFECT_BOUND_OFFLINE",
    "AI_OBSERVABILITY_BOUNDARY_EFFECT_NONE",
    "AI_OBSERVABILITY_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_LAYER_VERSION",
    "AI_OBSERVABILITY_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER",
    "AI_OBSERVABILITY_CANONICAL_OWNER",
    "AiObservabilityBoundaryOfflineReplayBindingResultV0",
    "AiObservabilityBoundaryOfflineReplayBoundaryV0",
    "AiObservabilityBoundaryOfflineReplayContextV0",
    "CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION",
    "EXPLAINABILITY_MODE_READ_ONLY_EVIDENCE_ONLY",
    "ai_observability_boundary_binding_non_authority_boundary_ok_v0",
    "bind_ai_observability_boundary_offline_replay_evidence_v0",
    "compute_ai_observability_boundary_ref_v0",
    "evaluate_offline_ai_observability_boundary_v0",
]
