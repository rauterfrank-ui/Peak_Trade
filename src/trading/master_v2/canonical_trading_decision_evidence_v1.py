# src/trading/master_v2/canonical_trading_decision_evidence_v1.py
"""
Pure Canonical Trading Decision Evidence v1: aggregated offline replay output.

Binds provenance from STEP 29B–29H component evidence. No runtime, order,
adapter, quantity, or authority effects.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from typing import Any, Mapping, Optional, Tuple

CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION = "v1"
EVIDENCE_SCHEMA_VERSION = "canonical_trading_decision_evidence_v1"

_AUTHORITY_EFFECT_NONE = "NONE"
_RUNTIME_EFFECT_NONE = "NONE"
_ORDER_EFFECT_NONE = "NONE"
_RISK_EFFECT_NONE = "NONE"
_ORDER_INTENT_EFFECT_NONE = "NONE"
_SAFETY_BOUNDARY_EFFECT_NONE = "NONE"
_RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_NONE = "NONE"
_KILLSWITCH_BOUNDARY_EFFECT_NONE = "NONE"
_QUANTITY_STATUS_NOT_BOUND = "NOT_BOUND"


def _valid_sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


@dataclass(frozen=True)
class ComponentRefV1:
    component_id: str
    layer_version: str
    semantic_digest: str

    def __post_init__(self) -> None:
        if self.semantic_digest and not _valid_sha256_hex(self.semantic_digest):
            msg = "semantic_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)


@dataclass(frozen=True)
class CanonicalVolatilityDecisionEvidenceProvenanceV1:
    """Versioned volatility estimate identity for decision evidence (O10)."""

    volatility_contract_version: str
    value: float
    unit: str
    horizon: str
    annualized: bool
    estimator: str
    observation_count: int
    as_of_event_time: str
    fallback_used: bool
    source_digest: str
    typed_estimate_digest: str
    legacy_adaptation_digest: str
    stale_status: str
    validation_result: str
    volatility_input_binding_digest: str
    legacy_float_value: float

    def __post_init__(self) -> None:
        for digest_name in (
            "source_digest",
            "typed_estimate_digest",
            "legacy_adaptation_digest",
            "volatility_input_binding_digest",
        ):
            digest = getattr(self, digest_name)
            if digest and not _valid_sha256_hex(digest):
                msg = f"{digest_name} must be empty or a 64-char lowercase sha256 hex"
                raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        return {
            "annualized": bool(self.annualized),
            "as_of_event_time": str(self.as_of_event_time),
            "estimator": str(self.estimator),
            "fallback_used": bool(self.fallback_used),
            "horizon": str(self.horizon),
            "legacy_adaptation_digest": str(self.legacy_adaptation_digest),
            "legacy_float_value": float(self.legacy_float_value),
            "observation_count": int(self.observation_count),
            "source_digest": str(self.source_digest),
            "stale_status": str(self.stale_status),
            "typed_estimate_digest": str(self.typed_estimate_digest),
            "unit": str(self.unit),
            "validation_result": str(self.validation_result),
            "value": float(self.value),
            "volatility_contract_version": str(self.volatility_contract_version),
            "volatility_input_binding_digest": str(self.volatility_input_binding_digest),
        }


@dataclass(frozen=True)
class CanonicalTradingDecisionEvidenceV1:
    decision_id: str
    replay_id: str
    instrument_id: str
    trading_epoch: int
    market_context_ref: str
    scope_initialization_ref: str
    scope_event_ref: str
    bull_assessment_ref: str
    bear_assessment_ref: str
    state_switch_ref: str
    bull_survival_ref: str
    bear_survival_ref: str
    bull_suitability_ref: str
    bear_suitability_ref: str
    composition_result_ref: str
    entry_exit_policy_ref: str
    current_scope_ref: str
    next_scope_ref: str
    previous_direction_state: str
    next_direction_state: str
    selected_side: str
    selected_strategy_ref: str
    decision_outcome: str
    entry_or_exit_policy_ref: str
    reason_codes: Tuple[str, ...]
    decision_precedence_trace: Tuple[str, ...]
    component_versions: Mapping[str, str]
    policy_versions: Mapping[str, str]
    config_digest: str
    implementation_digest: str
    input_digest: str
    semantic_digest: str
    evidence_schema_version: str = EVIDENCE_SCHEMA_VERSION
    execution_eligible: bool = False
    adapter_compatible: bool = False
    quantity_status: str = _QUANTITY_STATUS_NOT_BOUND
    quantity_provenance_ref: str = ""
    risk_sizing_ref: str = ""
    order_intent_ref: str = ""
    authority_effect: str = _AUTHORITY_EFFECT_NONE
    runtime_effect: str = _RUNTIME_EFFECT_NONE
    order_effect: str = _ORDER_EFFECT_NONE
    risk_sizing_effect: str = _RISK_EFFECT_NONE
    order_intent_effect: str = _ORDER_INTENT_EFFECT_NONE
    safety_boundary_ref: str = ""
    safety_boundary_effect: str = _SAFETY_BOUNDARY_EFFECT_NONE
    reconciliation_unknown_outcome_ref: str = ""
    reconciliation_unknown_outcome_effect: str = _RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_NONE
    killswitch_boundary_ref: str = ""
    killswitch_boundary_effect: str = _KILLSWITCH_BOUNDARY_EFFECT_NONE
    volatility_provenance: Optional[CanonicalVolatilityDecisionEvidenceProvenanceV1] = None

    def __post_init__(self) -> None:
        if self.semantic_digest and not _valid_sha256_hex(self.semantic_digest):
            msg = "semantic_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)
        if self.input_digest and not _valid_sha256_hex(self.input_digest):
            msg = "input_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)


def _sorted_mapping(mapping: Mapping[str, str]) -> dict[str, str]:
    return {str(k): str(v) for k, v in sorted(mapping.items())}


def serialize_canonical_trading_decision_evidence_canonical(
    evidence: CanonicalTradingDecisionEvidenceV1,
) -> str:
    """Deterministic JSON serialization for semantic digest (excludes semantic_digest)."""
    payload: dict[str, Any] = {
        "adapter_compatible": evidence.adapter_compatible,
        "authority_effect": evidence.authority_effect,
        "bear_assessment_ref": evidence.bear_assessment_ref,
        "bear_survival_ref": evidence.bear_survival_ref,
        "bear_suitability_ref": evidence.bear_suitability_ref,
        "bull_assessment_ref": evidence.bull_assessment_ref,
        "bull_survival_ref": evidence.bull_survival_ref,
        "bull_suitability_ref": evidence.bull_suitability_ref,
        "component_versions": _sorted_mapping(evidence.component_versions),
        "composition_result_ref": evidence.composition_result_ref,
        "config_digest": evidence.config_digest,
        "current_scope_ref": evidence.current_scope_ref,
        "decision_id": evidence.decision_id,
        "decision_outcome": evidence.decision_outcome,
        "decision_precedence_trace": list(evidence.decision_precedence_trace),
        "entry_exit_policy_ref": evidence.entry_exit_policy_ref,
        "entry_or_exit_policy_ref": evidence.entry_or_exit_policy_ref,
        "evidence_schema_version": evidence.evidence_schema_version,
        "execution_eligible": evidence.execution_eligible,
        "implementation_digest": evidence.implementation_digest,
        "instrument_id": evidence.instrument_id,
        "layer_version": CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION,
        "market_context_ref": evidence.market_context_ref,
        "next_direction_state": evidence.next_direction_state,
        "next_scope_ref": evidence.next_scope_ref,
        "order_effect": evidence.order_effect,
        "order_intent_effect": evidence.order_intent_effect,
        "order_intent_ref": evidence.order_intent_ref,
        "policy_versions": _sorted_mapping(evidence.policy_versions),
        "previous_direction_state": evidence.previous_direction_state,
        "quantity_provenance_ref": evidence.quantity_provenance_ref,
        "quantity_status": evidence.quantity_status,
        "reason_codes": sorted(evidence.reason_codes),
        "replay_id": evidence.replay_id,
        "risk_sizing_effect": evidence.risk_sizing_effect,
        "risk_sizing_ref": evidence.risk_sizing_ref,
        "runtime_effect": evidence.runtime_effect,
        "killswitch_boundary_effect": evidence.killswitch_boundary_effect,
        "killswitch_boundary_ref": evidence.killswitch_boundary_ref,
        "reconciliation_unknown_outcome_effect": evidence.reconciliation_unknown_outcome_effect,
        "reconciliation_unknown_outcome_ref": evidence.reconciliation_unknown_outcome_ref,
        "safety_boundary_effect": evidence.safety_boundary_effect,
        "safety_boundary_ref": evidence.safety_boundary_ref,
        "scope_event_ref": evidence.scope_event_ref,
        "scope_initialization_ref": evidence.scope_initialization_ref,
        "selected_side": evidence.selected_side,
        "selected_strategy_ref": evidence.selected_strategy_ref,
        "state_switch_ref": evidence.state_switch_ref,
        "trading_epoch": evidence.trading_epoch,
    }
    # Omit None so legacy evidence digests remain unchanged.
    if evidence.volatility_provenance is not None:
        payload["volatility_provenance"] = evidence.volatility_provenance.to_dict()
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_canonical_trading_decision_evidence_semantic_digest(
    evidence: CanonicalTradingDecisionEvidenceV1,
) -> str:
    canonical = serialize_canonical_trading_decision_evidence_canonical(evidence)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def finalize_offline_replay_decision_evidence_v1(
    evidence: CanonicalTradingDecisionEvidenceV1,
) -> CanonicalTradingDecisionEvidenceV1:
    """Compute semantic digest while preserving offline capital/risk/sizing binding fields."""
    digest = compute_canonical_trading_decision_evidence_semantic_digest(evidence)
    return replace(
        evidence,
        semantic_digest=digest,
        execution_eligible=False,
        adapter_compatible=False,
        authority_effect=_AUTHORITY_EFFECT_NONE,
        runtime_effect=_RUNTIME_EFFECT_NONE,
        order_effect=_ORDER_EFFECT_NONE,
    )


def with_computed_evidence_semantic_digest(
    evidence: CanonicalTradingDecisionEvidenceV1,
) -> CanonicalTradingDecisionEvidenceV1:
    return finalize_offline_replay_decision_evidence_v1(
        replace(
            evidence,
            semantic_digest="",
            execution_eligible=False,
            adapter_compatible=False,
            quantity_status=_QUANTITY_STATUS_NOT_BOUND,
            quantity_provenance_ref="",
            risk_sizing_ref="",
            order_intent_ref="",
            authority_effect=_AUTHORITY_EFFECT_NONE,
            runtime_effect=_RUNTIME_EFFECT_NONE,
            order_effect=_ORDER_EFFECT_NONE,
            risk_sizing_effect=_RISK_EFFECT_NONE,
            order_intent_effect=_ORDER_INTENT_EFFECT_NONE,
            safety_boundary_ref="",
            safety_boundary_effect=_SAFETY_BOUNDARY_EFFECT_NONE,
            reconciliation_unknown_outcome_ref="",
            reconciliation_unknown_outcome_effect=_RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_NONE,
            killswitch_boundary_ref="",
            killswitch_boundary_effect=_KILLSWITCH_BOUNDARY_EFFECT_NONE,
            # Preserve volatility_provenance when present (identity must survive digesting).
            volatility_provenance=evidence.volatility_provenance,
        )
    )


def derive_decision_id(
    *,
    replay_id: str,
    instrument_id: str,
    trading_epoch: int,
    input_digest: str,
) -> str:
    material = f"{replay_id}|{instrument_id}|{trading_epoch}|{input_digest}"
    return f"decision-{hashlib.sha256(material.encode('utf-8')).hexdigest()[:32]}"
