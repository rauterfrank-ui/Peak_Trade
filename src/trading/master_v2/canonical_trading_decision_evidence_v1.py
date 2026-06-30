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
from dataclasses import dataclass
from typing import Mapping, Tuple

CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION = "v1"
EVIDENCE_SCHEMA_VERSION = "canonical_trading_decision_evidence_v1"

_AUTHORITY_EFFECT_NONE = "NONE"
_RUNTIME_EFFECT_NONE = "NONE"
_ORDER_EFFECT_NONE = "NONE"
_RISK_EFFECT_NONE = "NONE"
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
    authority_effect: str = _AUTHORITY_EFFECT_NONE
    runtime_effect: str = _RUNTIME_EFFECT_NONE
    order_effect: str = _ORDER_EFFECT_NONE
    risk_sizing_effect: str = _RISK_EFFECT_NONE

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
    payload = {
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
        "policy_versions": _sorted_mapping(evidence.policy_versions),
        "previous_direction_state": evidence.previous_direction_state,
        "quantity_status": evidence.quantity_status,
        "reason_codes": sorted(evidence.reason_codes),
        "replay_id": evidence.replay_id,
        "risk_sizing_effect": evidence.risk_sizing_effect,
        "runtime_effect": evidence.runtime_effect,
        "scope_event_ref": evidence.scope_event_ref,
        "scope_initialization_ref": evidence.scope_initialization_ref,
        "selected_side": evidence.selected_side,
        "selected_strategy_ref": evidence.selected_strategy_ref,
        "state_switch_ref": evidence.state_switch_ref,
        "trading_epoch": evidence.trading_epoch,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_canonical_trading_decision_evidence_semantic_digest(
    evidence: CanonicalTradingDecisionEvidenceV1,
) -> str:
    canonical = serialize_canonical_trading_decision_evidence_canonical(evidence)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def with_computed_evidence_semantic_digest(
    evidence: CanonicalTradingDecisionEvidenceV1,
) -> CanonicalTradingDecisionEvidenceV1:
    digest = compute_canonical_trading_decision_evidence_semantic_digest(evidence)
    return CanonicalTradingDecisionEvidenceV1(
        decision_id=evidence.decision_id,
        replay_id=evidence.replay_id,
        instrument_id=evidence.instrument_id,
        trading_epoch=evidence.trading_epoch,
        market_context_ref=evidence.market_context_ref,
        scope_initialization_ref=evidence.scope_initialization_ref,
        scope_event_ref=evidence.scope_event_ref,
        bull_assessment_ref=evidence.bull_assessment_ref,
        bear_assessment_ref=evidence.bear_assessment_ref,
        state_switch_ref=evidence.state_switch_ref,
        bull_survival_ref=evidence.bull_survival_ref,
        bear_survival_ref=evidence.bear_survival_ref,
        bull_suitability_ref=evidence.bull_suitability_ref,
        bear_suitability_ref=evidence.bear_suitability_ref,
        composition_result_ref=evidence.composition_result_ref,
        entry_exit_policy_ref=evidence.entry_exit_policy_ref,
        current_scope_ref=evidence.current_scope_ref,
        next_scope_ref=evidence.next_scope_ref,
        previous_direction_state=evidence.previous_direction_state,
        next_direction_state=evidence.next_direction_state,
        selected_side=evidence.selected_side,
        selected_strategy_ref=evidence.selected_strategy_ref,
        decision_outcome=evidence.decision_outcome,
        entry_or_exit_policy_ref=evidence.entry_or_exit_policy_ref,
        reason_codes=evidence.reason_codes,
        decision_precedence_trace=evidence.decision_precedence_trace,
        component_versions=evidence.component_versions,
        policy_versions=evidence.policy_versions,
        config_digest=evidence.config_digest,
        implementation_digest=evidence.implementation_digest,
        input_digest=evidence.input_digest,
        semantic_digest=digest,
        evidence_schema_version=evidence.evidence_schema_version,
        execution_eligible=False,
        adapter_compatible=False,
        quantity_status=_QUANTITY_STATUS_NOT_BOUND,
        authority_effect=_AUTHORITY_EFFECT_NONE,
        runtime_effect=_RUNTIME_EFFECT_NONE,
        order_effect=_ORDER_EFFECT_NONE,
        risk_sizing_effect=_RISK_EFFECT_NONE,
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
