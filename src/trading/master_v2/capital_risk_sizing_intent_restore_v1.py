# src/trading/master_v2/capital_risk_sizing_intent_restore_v1.py
"""Current-system A06 restore: Capital Envelope → Risk → Sizing → Position Intent.

Consumes authoritative Integrated Replay decision evidence from A01–A05 core
wiring. Does not treat a Decision Packet as compute owner. Does not split the
existing capital_risk_sizing_v1 module; semantic stages remain independently
observable. No live, order-submit, or execution authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping, Optional

from src.execution_pipeline.plan_only_boundary_v0 import PLAN_ONLY_BOUNDARY_OWNER
from src.governance.canonical_order_intent_v1 import (
    CanonicalOrderIntentBuildInputV1,
    CanonicalOrderIntentBuildOutcome,
    CanonicalOrderIntentV1,
    IntentAction,
    build_canonical_order_intent_v1,
)
from src.governance.capital_risk_sizing_v1 import (
    CanonicalPositionSizingV1,
    CapitalRiskSizingChainResultV1,
    CapitalRiskSizingContextV1,
    CapitalRiskSizingDecisionV1,
    CapitalRiskSizingInputV1,
    CapitalRiskSizingOutcome,
    CapitalRiskSizingPolicyV1,
    EnvelopeStatus,
    PreSizingRiskAssessmentV1,
    PreSizingRiskStatus,
    QuantityStatus,
    ScopeCapitalEnvelopeV1,
    chain_result_to_decision_v1,
    compute_capital_risk_sizing_policy_digest_v1,
    evaluate_quantity_chain_v1,
    evaluate_scope_capital_envelope_v1,
)
from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
    CanonicalCoreRuntimeCapitalContextV0,
    INTEGRATION_STATUS_BOUND_NOT_ACTIVATED,
    decision_outcome_is_actionable,
    map_decision_outcome_to_intent_action,
    map_selected_side_to_sizing_side,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    default_offline_replay_capital_context_v0,
)
from trading.master_v2.decision_packet_from_integrated_replay_v1 import (
    DECISION_PACKET_ROLE_HANDOFF_EVIDENCE_ONLY,
    SOURCE_ROLE_DERIVED_FROM_INTEGRATED_REPLAY,
)
from trading.master_v2.decision_packet_v1 import MasterV2DecisionPacketV1
from trading.master_v2.double_play_core_wiring_v1 import (
    MasterV2DoublePlayCoreWiringResultV1,
    assert_core_wiring_authority_invariants_v1,
)
from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    CANONICAL_BULL_BEAR_STATE_OWNER,
    CANONICAL_OFFLINE_ORCHESTRATOR,
    LIVE_AUTHORIZED,
    ORDERS_ENABLED,
    REASON_COMPETING_SIDE_STATE_WRITER,
    assert_path_cannot_write_side_state_v1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
)
from trading.master_v2.registry_suitability_snapshot_v1 import (
    RegistryDerivedSuitabilitySnapshotV1,
)
from trading.master_v2.strategy_identity_binding_v1 import (
    REASON_AMBIGUOUS_STRATEGY_BINDING,
    REASON_UNKNOWN_STRATEGY_ID,
    StrategyIdentityBindingError,
    bind_strategy_identity_v1,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
)

CAPITAL_RISK_SIZING_INTENT_RESTORE_LAYER_VERSION = "v1"
CAPITAL_RISK_SIZING_INTENT_RESTORE_OWNER = "trading.master_v2.capital_risk_sizing_intent_restore_v1"
CAPITAL_RISK_SIZING_MODULE_OWNER = "src.governance.capital_risk_sizing_v1"
POSITION_INTENT_MODULE_OWNER = "src.governance.canonical_order_intent_v1"

SEMANTIC_STAGE_OWNERSHIP_SEPARATE = True
IMPLEMENTATION_MODULE_OWNERSHIP_MAY_BE_COMBINED = True
AUTH_014_POLICY_CHOICE_REQUIRED = False
AUTH_014_STATUS = "CONSERVATIVE_SEMANTIC_STAGES_SEPARATE_MODULE_MAY_COMBINE"

EXECUTION_MODE_PLAN_ONLY = "PLAN_ONLY"
ORDER_SUBMIT_AUTHORIZED = False
A06_LIVE_AUTHORIZED = False
RUNTIME_BRIDGE_STATUS = INTEGRATION_STATUS_BOUND_NOT_ACTIVATED

STAGE_CAPITAL_ENVELOPE = "CAPITAL_ENVELOPE"
STAGE_RISK = "RISK"
STAGE_SIZING = "SIZING"
STAGE_POSITION_INTENT = "POSITION_INTENT"
CANONICAL_STAGE_ORDER = (
    STAGE_CAPITAL_ENVELOPE,
    STAGE_RISK,
    STAGE_SIZING,
    STAGE_POSITION_INTENT,
)

REASON_MISSING_DECISION_EVIDENCE = "missing_decision_evidence"
REASON_MISSING_STRATEGY_IDENTITY = "missing_strategy_identity"
REASON_EVIDENCE_STRATEGY_MISMATCH = "evidence_strategy_mismatch"
REASON_MISSING_CAPITAL_ENVELOPE = "missing_capital_envelope"
REASON_CAPITAL_RISK_PROVENANCE_MISMATCH = "capital_risk_provenance_mismatch"
REASON_RISK_REJECTION = "risk_rejection"
REASON_SIZING_WITHOUT_RISK_APPROVAL = "sizing_without_valid_risk_approval"
REASON_INTENT_WITHOUT_SIZING = "position_intent_without_valid_sizing"
REASON_LEGACY_PACKET_COMPUTE_AUTHORITY = "legacy_decision_packet_independent_compute_authority"
REASON_DOWNSTREAM_SIDESTATE_OVERRIDE = "downstream_sidestate_or_double_play_override"
REASON_DUPLICATE_PROVENANCE = "duplicate_inconsistent_provenance_identifier"
REASON_ACCIDENTAL_EXECUTION_AUTHORIZATION = "accidental_execution_live_or_order_submit"
REASON_NON_AUTHORITATIVE_UPSTREAM = "non_authoritative_upstream_evidence"

_DEFAULT_CANONICAL_TRADING_LOGIC_VERSION = "integrated_offline_trading_logic_replay_v1"
_DEFAULT_ORDER_TYPE_POLICY = "MARKET_ONLY"
_DEFAULT_PRICE_POLICY = "EXPLICIT_NONE"
_DEFAULT_TIME_IN_FORCE_POLICY = "GTC"
_DEFAULT_MAX_SLIPPAGE_POLICY = "NONE"
_DEFAULT_POLICY_VERSION = "capital_risk_sizing_policy_v1"


class A06RestoreError(ValueError):
    """Fail-closed A06 contract error. Does not grant trading authority."""


class FunctionalStageId(str, Enum):
    CAPITAL_ENVELOPE = STAGE_CAPITAL_ENVELOPE
    RISK = STAGE_RISK
    SIZING = STAGE_SIZING
    POSITION_INTENT = STAGE_POSITION_INTENT


def _sha256_hex(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _stage_digest(*, stage_id: str, **fields: Any) -> str:
    return _sha256_hex({"stage_id": stage_id, **fields})


@dataclass(frozen=True)
class CapitalEnvelopeStageResultV1:
    stage_id: str
    envelope: ScopeCapitalEnvelopeV1
    decision_evidence_id: str
    replay_id: str
    strategy_identity: str
    double_play_selected_side: str
    next_direction_state: str
    input_digest: str
    stage_digest: str
    module_owner: str = CAPITAL_RISK_SIZING_MODULE_OWNER


@dataclass(frozen=True)
class RiskStageResultV1:
    stage_id: str
    assessment: PreSizingRiskAssessmentV1
    consumed_capital_envelope_digest: str
    decision_evidence_id: str
    input_digest: str
    stage_digest: str
    approved: bool
    module_owner: str = CAPITAL_RISK_SIZING_MODULE_OWNER


@dataclass(frozen=True)
class SizingStageResultV1:
    stage_id: str
    sizing: CanonicalPositionSizingV1
    consumed_risk_digest: str
    decision_evidence_id: str
    input_digest: str
    stage_digest: str
    module_owner: str = CAPITAL_RISK_SIZING_MODULE_OWNER


@dataclass(frozen=True)
class PositionIntentStageResultV1:
    stage_id: str
    intent: CanonicalOrderIntentV1
    consumed_sizing_digest: str
    decision_evidence_id: str
    input_digest: str
    stage_digest: str
    execution_mode: str = EXECUTION_MODE_PLAN_ONLY
    order_submit_authorized: bool = ORDER_SUBMIT_AUTHORIZED
    live_authorized: bool = A06_LIVE_AUTHORIZED
    runtime_bridge_status: str = RUNTIME_BRIDGE_STATUS
    plan_only_boundary_owner: str = PLAN_ONLY_BOUNDARY_OWNER
    module_owner: str = POSITION_INTENT_MODULE_OWNER


@dataclass(frozen=True)
class MasterV2A06CapitalRiskSizingIntentResultV1:
    core: MasterV2DoublePlayCoreWiringResultV1
    capital: CapitalEnvelopeStageResultV1
    risk: RiskStageResultV1
    sizing: Optional[SizingStageResultV1]
    position_intent: Optional[PositionIntentStageResultV1]
    chain: CapitalRiskSizingChainResultV1
    observed_stage_order: tuple[str, ...]
    compute_owner: str
    decision_packet_role: str
    execution_mode: str
    order_submit_authorized: bool
    live_authorized: bool
    semantic_payload: Mapping[str, Any]
    semantic_digest: str
    auth_014_status: str = AUTH_014_STATUS
    semantic_stage_ownership_separate: bool = SEMANTIC_STAGE_OWNERSHIP_SEPARATE
    implementation_module_ownership_may_be_combined: bool = (
        IMPLEMENTATION_MODULE_OWNERSHIP_MAY_BE_COMBINED
    )
    auth_014_policy_choice_required: bool = AUTH_014_POLICY_CHOICE_REQUIRED


def _require_authoritative_evidence(
    evidence: Optional[CanonicalTradingDecisionEvidenceV1],
    *,
    compute_owner: str,
) -> CanonicalTradingDecisionEvidenceV1:
    if evidence is None or not evidence.decision_id or not evidence.replay_id:
        raise A06RestoreError(REASON_MISSING_DECISION_EVIDENCE)
    if not evidence.input_digest:
        raise A06RestoreError(REASON_MISSING_DECISION_EVIDENCE)
    if compute_owner != INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER:
        raise A06RestoreError(REASON_NON_AUTHORITATIVE_UPSTREAM)
    if compute_owner != CANONICAL_OFFLINE_ORCHESTRATOR:
        raise A06RestoreError(REASON_NON_AUTHORITATIVE_UPSTREAM)
    return evidence


def _bind_strategy_identity_from_evidence(
    evidence: CanonicalTradingDecisionEvidenceV1,
    snapshot: RegistryDerivedSuitabilitySnapshotV1,
    *,
    require_identity: bool,
) -> str:
    strategy_ref = str(evidence.selected_strategy_ref or "").strip()
    if not strategy_ref:
        if require_identity:
            raise A06RestoreError(REASON_MISSING_STRATEGY_IDENTITY)
        return ""
    try:
        binding = bind_strategy_identity_v1(strategy_ref)
    except StrategyIdentityBindingError as exc:
        raise A06RestoreError(str(exc)) from exc
    if binding.canonical_strategy_id not in snapshot.strategy_ids_sorted:
        raise A06RestoreError(REASON_EVIDENCE_STRATEGY_MISMATCH)
    return binding.canonical_strategy_id


def assert_legacy_decision_packet_is_not_compute_authority_v1(
    packet: Optional[MasterV2DecisionPacketV1],
    *,
    treat_as_compute_owner: bool = False,
) -> None:
    """Fail closed if a Decision Packet is offered as independent compute authority."""

    if treat_as_compute_owner:
        raise A06RestoreError(REASON_LEGACY_PACKET_COMPUTE_AUTHORITY)
    if packet is None:
        return
    handoff = packet.doubleplay
    if handoff is None:
        raise A06RestoreError(REASON_LEGACY_PACKET_COMPUTE_AUTHORITY)
    if handoff.source_role != SOURCE_ROLE_DERIVED_FROM_INTEGRATED_REPLAY:
        raise A06RestoreError(REASON_LEGACY_PACKET_COMPUTE_AUTHORITY)
    if handoff.compute_owner != INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER:
        raise A06RestoreError(REASON_LEGACY_PACKET_COMPUTE_AUTHORITY)


def assert_no_downstream_sidestate_override_v1(
    evidence: CanonicalTradingDecisionEvidenceV1,
    *,
    claimed_side_state_writer: str = CANONICAL_BULL_BEAR_STATE_OWNER,
    override_selected_side: Optional[str] = None,
    override_next_direction_state: Optional[str] = None,
) -> None:
    if claimed_side_state_writer != CANONICAL_BULL_BEAR_STATE_OWNER:
        raise A06RestoreError(REASON_DOWNSTREAM_SIDESTATE_OVERRIDE)
    assert_path_cannot_write_side_state_v1(
        path_id=CAPITAL_RISK_SIZING_INTENT_RESTORE_OWNER,
        claimed_may_write_side_state=False,
    )
    if override_selected_side is not None and str(override_selected_side) != str(
        evidence.selected_side
    ):
        raise A06RestoreError(REASON_DOWNSTREAM_SIDESTATE_OVERRIDE)
    if override_next_direction_state is not None and str(override_next_direction_state) != str(
        evidence.next_direction_state
    ):
        raise A06RestoreError(REASON_DOWNSTREAM_SIDESTATE_OVERRIDE)


def assert_no_accidental_execution_authorization_v1(
    *,
    execution_eligible: bool = False,
    adapter_compatible: bool = False,
    submission_authorized: bool = False,
    live_authorized: bool = False,
    order_submit_authorized: bool = False,
    orders_enabled: str = ORDERS_ENABLED,
    live_authorized_token: str = LIVE_AUTHORIZED,
) -> None:
    if any(
        (
            execution_eligible,
            adapter_compatible,
            submission_authorized,
            live_authorized,
            order_submit_authorized,
            str(orders_enabled).lower() == "true",
            str(live_authorized_token).lower() == "true",
        )
    ):
        raise A06RestoreError(REASON_ACCIDENTAL_EXECUTION_AUTHORIZATION)


def capital_context_to_crs_inputs_v1(
    ctx: CanonicalCoreRuntimeCapitalContextV0,
) -> tuple[CapitalRiskSizingContextV1, CapitalRiskSizingPolicyV1]:
    policy = CapitalRiskSizingPolicyV1(
        policy_version=_DEFAULT_POLICY_VERSION,
        total_capital_limit_usd=ctx.total_capital_limit,
        order_limit_usd=ctx.per_trade_risk_limit,
        daily_loss_limit_usd=ctx.daily_loss_remaining_budget,
        max_positions=ctx.maximum_positions,
    )
    context = CapitalRiskSizingContextV1(
        reference_price=ctx.reference_price,
        protective_stop_price=ctx.protective_stop_price,
        stop_distance=None,
        account_equity=ctx.account_equity,
        already_committed_capital=Decimal("0"),
        daily_loss_consumed=Decimal("0"),
        current_reconciled_exposure=ctx.current_reconciled_exposure,
        reconciled_open_position_quantity=Decimal("0"),
        current_open_positions_count=ctx.current_open_positions_count,
        current_open_side=ctx.current_open_side,
        reconciliation_status=ctx.reconciliation_status,
        configured_quantity_cap=ctx.configured_quantity_cap,
        leverage_ceiling=ctx.leverage_ceiling,
        instrument=ctx.instrument,
        config_digest=ctx.config_digest,
        order_notional_cap=ctx.scope_capital_limit,
        per_trade_risk_cap=ctx.per_trade_risk_limit,
    )
    return context, policy


def _handoff_sizing_input_v1(
    evidence: CanonicalTradingDecisionEvidenceV1,
    ctx: CanonicalCoreRuntimeCapitalContextV0,
    context: CapitalRiskSizingContextV1,
    policy: CapitalRiskSizingPolicyV1,
) -> CapitalRiskSizingInputV1:
    selected_side = map_selected_side_to_sizing_side(evidence.selected_side) or str(
        evidence.selected_side
    )
    return CapitalRiskSizingInputV1(
        decision_id=evidence.decision_id,
        instrument_id=evidence.instrument_id,
        selected_side=selected_side,
        reference_price=context.reference_price,
        protective_stop_price=context.protective_stop_price,
        stop_distance=context.stop_distance,
        account_equity=context.account_equity,
        scope_capital_limit=ctx.scope_capital_limit,
        per_trade_risk_limit=ctx.per_trade_risk_limit,
        total_capital_limit=policy.total_capital_limit_usd,
        daily_loss_remaining_budget=policy.daily_loss_limit_usd,
        current_reconciled_exposure=context.current_reconciled_exposure,
        maximum_positions=policy.max_positions,
        current_open_positions_count=context.current_open_positions_count,
        current_open_side=context.current_open_side,
        configured_quantity_cap=context.configured_quantity_cap,
        leverage_ceiling=context.leverage_ceiling,
        reconciliation_status=context.reconciliation_status,
        policy_version=policy.policy_version,
        config_digest=context.config_digest,
        input_digest=evidence.input_digest,
        instrument=context.instrument,
        decision_outcome=str(evidence.decision_outcome),
        already_committed_capital=context.already_committed_capital,
        reconciled_open_position_quantity=context.reconciled_open_position_quantity,
        daily_loss_consumed=context.daily_loss_consumed,
    )


def evaluate_capital_envelope_stage_v1(
    evidence: CanonicalTradingDecisionEvidenceV1,
    context: CapitalRiskSizingContextV1,
    policy: CapitalRiskSizingPolicyV1,
    *,
    strategy_identity: str,
) -> CapitalEnvelopeStageResultV1:
    envelope = evaluate_scope_capital_envelope_v1(evidence, context, policy)
    if envelope.decision_id != evidence.decision_id:
        raise A06RestoreError(REASON_DUPLICATE_PROVENANCE)
    if envelope.input_digest != evidence.input_digest:
        raise A06RestoreError(REASON_DUPLICATE_PROVENANCE)
    stage_digest = _stage_digest(
        stage_id=STAGE_CAPITAL_ENVELOPE,
        decision_id=envelope.decision_id,
        replay_id=evidence.replay_id,
        strategy_identity=strategy_identity,
        selected_side=evidence.selected_side,
        next_direction_state=evidence.next_direction_state,
        input_digest=envelope.input_digest,
        status=envelope.status.value,
    )
    return CapitalEnvelopeStageResultV1(
        stage_id=STAGE_CAPITAL_ENVELOPE,
        envelope=envelope,
        decision_evidence_id=evidence.decision_id,
        replay_id=evidence.replay_id,
        strategy_identity=strategy_identity,
        double_play_selected_side=str(evidence.selected_side),
        next_direction_state=str(evidence.next_direction_state),
        input_digest=evidence.input_digest,
        stage_digest=stage_digest,
    )


def evaluate_risk_stage_v1(
    *,
    envelope: Optional[CapitalEnvelopeStageResultV1],
    evidence: CanonicalTradingDecisionEvidenceV1,
    chain: CapitalRiskSizingChainResultV1,
) -> RiskStageResultV1:
    if envelope is None:
        raise A06RestoreError(REASON_MISSING_CAPITAL_ENVELOPE)
    chain_envelope = chain.scope_capital_envelope
    if (
        chain_envelope.decision_id != envelope.envelope.decision_id
        or chain_envelope.input_digest != envelope.envelope.input_digest
        or envelope.decision_evidence_id != evidence.decision_id
        or envelope.input_digest != evidence.input_digest
    ):
        raise A06RestoreError(REASON_CAPITAL_RISK_PROVENANCE_MISMATCH)
    assessment = chain.pre_sizing_risk
    if assessment.input_digest != evidence.input_digest:
        raise A06RestoreError(REASON_CAPITAL_RISK_PROVENANCE_MISMATCH)
    approved = assessment.status is not PreSizingRiskStatus.BLOCK
    if envelope.envelope.status is EnvelopeStatus.BLOCK:
        approved = False
    stage_digest = _stage_digest(
        stage_id=STAGE_RISK,
        decision_id=assessment.decision_id,
        capital_digest=envelope.stage_digest,
        status=assessment.status.value,
        input_digest=assessment.input_digest,
        approved=approved,
    )
    return RiskStageResultV1(
        stage_id=STAGE_RISK,
        assessment=assessment,
        consumed_capital_envelope_digest=envelope.stage_digest,
        decision_evidence_id=evidence.decision_id,
        input_digest=evidence.input_digest,
        stage_digest=stage_digest,
        approved=approved,
    )


def evaluate_sizing_stage_v1(
    *,
    risk: Optional[RiskStageResultV1],
    chain: CapitalRiskSizingChainResultV1,
    evidence: CanonicalTradingDecisionEvidenceV1,
) -> SizingStageResultV1:
    if risk is None or not risk.approved:
        raise A06RestoreError(REASON_SIZING_WITHOUT_RISK_APPROVAL)
    sizing = chain.canonical_position_sizing
    if sizing is None:
        raise A06RestoreError(REASON_SIZING_WITHOUT_RISK_APPROVAL)
    if sizing.input_digest != evidence.input_digest:
        raise A06RestoreError(REASON_DUPLICATE_PROVENANCE)
    if chain.outcome is CapitalRiskSizingOutcome.BLOCKED:
        raise A06RestoreError(REASON_RISK_REJECTION)
    stage_digest = _stage_digest(
        stage_id=STAGE_SIZING,
        decision_id=sizing.decision_id,
        risk_digest=risk.stage_digest,
        rounded_quantity=str(sizing.rounded_quantity),
        quantity_status=sizing.quantity_status.value,
        input_digest=sizing.input_digest,
    )
    return SizingStageResultV1(
        stage_id=STAGE_SIZING,
        sizing=sizing,
        consumed_risk_digest=risk.stage_digest,
        decision_evidence_id=evidence.decision_id,
        input_digest=evidence.input_digest,
        stage_digest=stage_digest,
    )


def evaluate_position_intent_stage_v1(
    *,
    sizing: Optional[SizingStageResultV1],
    decision: CapitalRiskSizingDecisionV1,
    sizing_input: CapitalRiskSizingInputV1,
    evidence: CanonicalTradingDecisionEvidenceV1,
    policy: CapitalRiskSizingPolicyV1,
    ctx: CanonicalCoreRuntimeCapitalContextV0,
) -> PositionIntentStageResultV1:
    if sizing is None:
        raise A06RestoreError(REASON_INTENT_WITHOUT_SIZING)
    if decision.outcome is not CapitalRiskSizingOutcome.PASS:
        raise A06RestoreError(REASON_INTENT_WITHOUT_SIZING)
    if decision.quantity_provenance is None:
        raise A06RestoreError(REASON_INTENT_WITHOUT_SIZING)
    intent_action = map_decision_outcome_to_intent_action(evidence.decision_outcome)
    selected_side = map_selected_side_to_sizing_side(evidence.selected_side)
    if intent_action is None or selected_side is None:
        raise A06RestoreError(REASON_INTENT_WITHOUT_SIZING)
    expected_side = "LONG" if intent_action == IntentAction.ENTER_LONG.value else selected_side
    if intent_action == IntentAction.ENTER_SHORT.value:
        expected_side = "SHORT"
    build = build_canonical_order_intent_v1(
        CanonicalOrderIntentBuildInputV1(
            sizing_input=sizing_input,
            sizing_decision=decision,
            intent_id=f"a06-intent::{evidence.decision_id}",
            trading_epoch=str(evidence.trading_epoch),
            canonical_trading_logic_version=_DEFAULT_CANONICAL_TRADING_LOGIC_VERSION,
            intent_action=intent_action,
            policy_digest=compute_capital_risk_sizing_policy_digest_v1(policy),
            order_type_policy=_DEFAULT_ORDER_TYPE_POLICY,
            price_policy=_DEFAULT_PRICE_POLICY,
            time_in_force_policy=_DEFAULT_TIME_IN_FORCE_POLICY,
            max_slippage_policy=_DEFAULT_MAX_SLIPPAGE_POLICY,
            expected_position_side=expected_side,
            current_reconciled_exposure=ctx.current_reconciled_exposure,
            current_open_side=ctx.current_open_side,
        )
    )
    if build.outcome is not CanonicalOrderIntentBuildOutcome.PASS or build.intent is None:
        raise A06RestoreError(REASON_INTENT_WITHOUT_SIZING)
    intent = build.intent
    assert_no_accidental_execution_authorization_v1(
        execution_eligible=intent.execution_eligible,
        adapter_compatible=intent.adapter_compatible,
        submission_authorized=intent.submission_authorized,
        live_authorized=False,
        order_submit_authorized=False,
    )
    stage_digest = _stage_digest(
        stage_id=STAGE_POSITION_INTENT,
        decision_id=intent.decision_id,
        sizing_digest=sizing.stage_digest,
        semantic_digest=intent.semantic_digest,
        execution_mode=EXECUTION_MODE_PLAN_ONLY,
        submission_authorized=intent.submission_authorized,
    )
    return PositionIntentStageResultV1(
        stage_id=STAGE_POSITION_INTENT,
        intent=intent,
        consumed_sizing_digest=sizing.stage_digest,
        decision_evidence_id=evidence.decision_id,
        input_digest=evidence.input_digest,
        stage_digest=stage_digest,
    )


def _semantic_payload_v1(
    *,
    core: MasterV2DoublePlayCoreWiringResultV1,
    capital: CapitalEnvelopeStageResultV1,
    risk: RiskStageResultV1,
    sizing: Optional[SizingStageResultV1],
    position_intent: Optional[PositionIntentStageResultV1],
    observed_stage_order: tuple[str, ...],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "layer_version": CAPITAL_RISK_SIZING_INTENT_RESTORE_LAYER_VERSION,
        "compute_owner": core.compute_owner,
        "decision_packet_role": core.decision_packet_role,
        "registry_snapshot_digest": core.snapshot.snapshot_digest,
        "replay_id": core.replay.evidence.replay_id,
        "decision_id": core.replay.evidence.decision_id,
        "evidence_input_digest": core.replay.evidence.input_digest,
        "evidence_semantic_digest": core.replay.evidence.semantic_digest,
        "selected_side": core.replay.evidence.selected_side,
        "selected_strategy_ref": capital.strategy_identity,
        "decision_outcome": core.replay.evidence.decision_outcome,
        "observed_stage_order": list(observed_stage_order),
        "capital_stage_id": capital.stage_id,
        "capital_stage_digest": capital.stage_digest,
        "capital_status": capital.envelope.status.value,
        "risk_stage_id": risk.stage_id,
        "risk_stage_digest": risk.stage_digest,
        "risk_approved": risk.approved,
        "risk_status": risk.assessment.status.value,
        "sizing_stage_id": sizing.stage_id if sizing is not None else None,
        "sizing_stage_digest": sizing.stage_digest if sizing is not None else None,
        "sizing_quantity": str(sizing.sizing.rounded_quantity) if sizing is not None else None,
        "intent_stage_id": position_intent.stage_id if position_intent is not None else None,
        "intent_stage_digest": (
            position_intent.stage_digest if position_intent is not None else None
        ),
        "intent_semantic_digest": (
            position_intent.intent.semantic_digest if position_intent is not None else None
        ),
        "execution_mode": EXECUTION_MODE_PLAN_ONLY,
        "order_submit_authorized": ORDER_SUBMIT_AUTHORIZED,
        "live_authorized": A06_LIVE_AUTHORIZED,
        "auth_014_status": AUTH_014_STATUS,
    }
    return payload


def run_master_v2_a06_capital_risk_sizing_intent_v1(
    core: MasterV2DoublePlayCoreWiringResultV1,
    *,
    capital_context: Optional[CanonicalCoreRuntimeCapitalContextV0] = None,
    claimed_side_state_writer: str = CANONICAL_BULL_BEAR_STATE_OWNER,
    override_selected_side: Optional[str] = None,
    override_next_direction_state: Optional[str] = None,
    treat_packet_as_compute_owner: bool = False,
) -> MasterV2A06CapitalRiskSizingIntentResultV1:
    """Restore Capital → Risk → Sizing → Intent from A01–A05 core wiring evidence."""

    assert_core_wiring_authority_invariants_v1(core)
    assert_legacy_decision_packet_is_not_compute_authority_v1(
        core.packet,
        treat_as_compute_owner=treat_packet_as_compute_owner,
    )
    evidence = _require_authoritative_evidence(
        core.replay.evidence,
        compute_owner=core.compute_owner,
    )
    if core.decision_packet_role != DECISION_PACKET_ROLE_HANDOFF_EVIDENCE_ONLY:
        raise A06RestoreError(REASON_LEGACY_PACKET_COMPUTE_AUTHORITY)
    assert_no_downstream_sidestate_override_v1(
        evidence,
        claimed_side_state_writer=claimed_side_state_writer,
        override_selected_side=override_selected_side,
        override_next_direction_state=override_next_direction_state,
    )
    assert_no_accidental_execution_authorization_v1(
        execution_eligible=evidence.execution_eligible,
        adapter_compatible=evidence.adapter_compatible,
        live_authorized=core.snapshot.live_authorized,
        order_submit_authorized=core.snapshot.orders_allowed,
    )
    require_identity = decision_outcome_is_actionable(evidence.decision_outcome)
    strategy_identity = _bind_strategy_identity_from_evidence(
        evidence,
        core.snapshot,
        require_identity=require_identity,
    )
    ctx = capital_context or default_offline_replay_capital_context_v0(
        instrument_id=evidence.instrument_id,
    )
    context, policy = capital_context_to_crs_inputs_v1(ctx)
    capital = evaluate_capital_envelope_stage_v1(
        evidence,
        context,
        policy,
        strategy_identity=strategy_identity,
    )
    chain = evaluate_quantity_chain_v1(evidence, context, policy)
    risk = evaluate_risk_stage_v1(envelope=capital, evidence=evidence, chain=chain)
    observed: list[str] = [STAGE_CAPITAL_ENVELOPE, STAGE_RISK]
    sizing: Optional[SizingStageResultV1] = None
    position_intent: Optional[PositionIntentStageResultV1] = None
    if (
        risk.approved
        and chain.outcome is CapitalRiskSizingOutcome.PASS
        and chain.canonical_position_sizing is not None
        and chain.canonical_position_sizing.quantity_status is not QuantityStatus.BLOCK
    ):
        sizing = evaluate_sizing_stage_v1(risk=risk, chain=chain, evidence=evidence)
        observed.append(STAGE_SIZING)
        decision = chain_result_to_decision_v1(chain, selected_side=str(evidence.selected_side))
        sizing_input = _handoff_sizing_input_v1(evidence, ctx, context, policy)
        if decision_outcome_is_actionable(evidence.decision_outcome):
            position_intent = evaluate_position_intent_stage_v1(
                sizing=sizing,
                decision=decision,
                sizing_input=sizing_input,
                evidence=evidence,
                policy=policy,
                ctx=ctx,
            )
            observed.append(STAGE_POSITION_INTENT)
    if require_identity and position_intent is None:
        if not risk.approved:
            raise A06RestoreError(REASON_RISK_REJECTION)
        raise A06RestoreError(REASON_SIZING_WITHOUT_RISK_APPROVAL)
    payload = _semantic_payload_v1(
        core=core,
        capital=capital,
        risk=risk,
        sizing=sizing,
        position_intent=position_intent,
        observed_stage_order=tuple(observed),
    )
    return MasterV2A06CapitalRiskSizingIntentResultV1(
        core=core,
        capital=capital,
        risk=risk,
        sizing=sizing,
        position_intent=position_intent,
        chain=chain,
        observed_stage_order=tuple(observed),
        compute_owner=core.compute_owner,
        decision_packet_role=core.decision_packet_role,
        execution_mode=EXECUTION_MODE_PLAN_ONLY,
        order_submit_authorized=ORDER_SUBMIT_AUTHORIZED,
        live_authorized=A06_LIVE_AUTHORIZED,
        semantic_payload=payload,
        semantic_digest=_sha256_hex(payload),
    )


def run_a06_from_legacy_decision_packet_v1(
    packet: MasterV2DecisionPacketV1,
) -> MasterV2A06CapitalRiskSizingIntentResultV1:
    """Negative contract: a packet cannot become the A06 compute owner."""

    raise A06RestoreError(REASON_LEGACY_PACKET_COMPUTE_AUTHORITY)


# Re-export identity reasons so tests can match fail-closed tokens without a second owner.
A06_REASON_UNKNOWN_STRATEGY_ID = REASON_UNKNOWN_STRATEGY_ID
A06_REASON_AMBIGUOUS_STRATEGY_BINDING = REASON_AMBIGUOUS_STRATEGY_BINDING
A06_REASON_COMPETING_SIDE_STATE_WRITER = REASON_COMPETING_SIDE_STATE_WRITER
