# src/trading/master_v2/capital_risk_sizing_safety_intent_restore_v1.py
"""Thin composition adapter: A01–A05 evidence → STEP-29P → Safety → STEP-29Q.

Not a compute, risk, sizing, safety, intent, or SideState owner.
Does not wrap the A06 adapter. Does not reorder integrated replay.
Does not restore EV, execution, live, testnet, canary, enabled, or armed authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from src.governance.canonical_order_intent_v1 import (
    CanonicalOrderIntentBuildInputV1,
    CanonicalOrderIntentBuildOutcome,
    CanonicalOrderIntentBuildResultV1,
    CanonicalOrderIntentV1,
    IntentAction,
    build_canonical_order_intent_v1,
)
from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingChainResultV1,
    CapitalRiskSizingContextV1,
    CapitalRiskSizingDecisionV1,
    CapitalRiskSizingInputV1,
    CapitalRiskSizingOutcome,
    CapitalRiskSizingPolicyV1,
    evaluate_quantity_chain_v1,
)
from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
    CanonicalCoreRuntimeCapitalContextV0,
    decision_outcome_is_actionable,
    map_decision_outcome_to_intent_action,
    map_selected_side_to_sizing_side,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    default_offline_replay_capital_context_v0,
)
from trading.master_v2.decision_packet_from_integrated_replay_v1 import (
    DECISION_PACKET_ROLE_HANDOFF_EVIDENCE_ONLY,
)
from trading.master_v2.double_play_core_wiring_v1 import (
    MasterV2DoublePlayCoreWiringResultV1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import SafetyMode
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
)
from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
    SafetyKernelOfflineReplayBindingResultV0,
    SafetyKernelOfflineReplayContextV0,
    bind_safety_kernel_offline_replay_evidence_v0,
)

QUANTITY_CHAIN_OWNER = "src.governance.capital_risk_sizing_v1"
SAFETY_OWNER = "trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0"
INTENT_OWNER = "src.governance.canonical_order_intent_v1"
ADAPTER_ROLE = "COMPOSITION_ONLY"
ADAPTER_IS_COMPUTE_OWNER = False
ADAPTER_IS_RISK_OWNER = False
ADAPTER_IS_SIZING_OWNER = False
ADAPTER_IS_SAFETY_OWNER = False
ADAPTER_IS_INTENT_OWNER = False
SAFETY_OWNER_CHANGED = False
SAFETY_AUTHORITY_CHANGED = False
SAFETY_WIRING_CHANGED = True
EXECUTION_MODE_PLAN_ONLY = "PLAN_ONLY"
SUBMISSION_AUTHORIZED = False
_DEFAULT_POLICY_VERSION = "capital_risk_sizing_policy_v1"
_DEFAULT_CANONICAL_TRADING_LOGIC_VERSION = "integrated_offline_trading_logic_replay_v1"
_DEFAULT_ORDER_TYPE_POLICY = "MARKET_ONLY"
_DEFAULT_PRICE_POLICY = "EXPLICIT_NONE"
_DEFAULT_TIME_IN_FORCE_POLICY = "GTC"
_DEFAULT_MAX_SLIPPAGE_POLICY = "NONE"


@dataclass(frozen=True)
class MasterV2CapitalRiskSizingSafetyIntentCompositionV1:
    """Owner-composition result. Adapter is not a semantic stage owner."""

    core: MasterV2DoublePlayCoreWiringResultV1
    chain: CapitalRiskSizingChainResultV1
    safety_binding: SafetyKernelOfflineReplayBindingResultV0
    intent: Optional[CanonicalOrderIntentV1]
    intent_build: Optional[CanonicalOrderIntentBuildResultV1]
    compute_owner: str
    decision_packet_role: str
    side_state_writer: str
    quantity_chain_owner: str = QUANTITY_CHAIN_OWNER
    safety_owner: str = SAFETY_OWNER
    intent_owner: str = INTENT_OWNER
    adapter_role: str = ADAPTER_ROLE
    adapter_is_compute_owner: bool = ADAPTER_IS_COMPUTE_OWNER
    adapter_is_risk_owner: bool = ADAPTER_IS_RISK_OWNER
    adapter_is_sizing_owner: bool = ADAPTER_IS_SIZING_OWNER
    adapter_is_safety_owner: bool = ADAPTER_IS_SAFETY_OWNER
    adapter_is_intent_owner: bool = ADAPTER_IS_INTENT_OWNER
    safety_owner_changed: bool = SAFETY_OWNER_CHANGED
    safety_authority_changed: bool = SAFETY_AUTHORITY_CHANGED
    safety_wiring_changed: bool = SAFETY_WIRING_CHANGED
    execution_mode: str = EXECUTION_MODE_PLAN_ONLY
    submission_authorized: bool = SUBMISSION_AUTHORIZED


def safety_context_from_integrated_replay_input_v1(
    inp: IntegratedOfflineReplayInputV1,
) -> SafetyKernelOfflineReplayContextV0:
    """Map attested A01–A05 / IntegratedOfflineReplayInputV1 Safety fields.

    Field mapping matches the existing compute-owner Safety caller. Not a second
    Safety engine. Missing input has no implicit NORMAL / allowed default.
    """

    if inp is None:
        raise TypeError("IntegratedOfflineReplayInputV1 is required; no implicit Safety default")
    return SafetyKernelOfflineReplayContextV0(
        safety_mode=inp.safety_mode,
        safety_exit_signal=inp.safety_exit_signal,
        reconciliation_state=inp.reconciliation_state,
        position_state=inp.position_state,
        trading_gate=inp.trading_gate,
        killswitch_blocked=(
            inp.safety_mode is SafetyMode.BLOCKED
            or inp.safety_exit_signal.triggered
            or inp.side_state is SideState.KILL_ALL
        ),
        safety_decision_allowed=inp.safety_mode is not SafetyMode.BLOCKED,
    )


def capital_context_to_quantity_chain_inputs_v1(
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


def _sizing_input_for_29q(
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


def _decision_from_chain(
    chain: CapitalRiskSizingChainResultV1,
    *,
    selected_side: str,
) -> CapitalRiskSizingDecisionV1:
    return CapitalRiskSizingDecisionV1(
        outcome=chain.outcome,
        final_quantity=chain.final_quantity,
        selected_side=selected_side,
        scope_capital_envelope=chain.scope_capital_envelope,
        pre_sizing_risk=chain.pre_sizing_risk,
        canonical_position_sizing=chain.canonical_position_sizing,
        post_sizing_risk=chain.post_sizing_risk,
        quantity_provenance=chain.quantity_provenance,
        reason_codes=chain.reason_codes,
        authority_effect=chain.authority_effect,
        runtime_effect=chain.runtime_effect,
        adapter_compatible=chain.adapter_compatible,
    )


def _expected_position_side(intent_action: str, selected_side: str) -> str:
    if intent_action == IntentAction.ENTER_LONG.value:
        return "LONG"
    if intent_action == IntentAction.ENTER_SHORT.value:
        return "SHORT"
    return selected_side


def compose_capital_risk_sizing_safety_intent_from_core_evidence_v1(
    core: MasterV2DoublePlayCoreWiringResultV1,
    *,
    safety_context: SafetyKernelOfflineReplayContextV0,
    capital_context: Optional[CanonicalCoreRuntimeCapitalContextV0] = None,
) -> MasterV2CapitalRiskSizingSafetyIntentCompositionV1:
    """Compose STEP-29P, then existing Safety, then STEP-29Q PLAN_ONLY.

    29Q is not called before Safety. 29Q is invoked at most once. A Safety
    hard-block skips 29Q. The adapter does not invent Safety policy.
    """

    if safety_context is None:
        raise TypeError(
            "SafetyKernelOfflineReplayContextV0 is required; no implicit Safety default"
        )
    evidence = core.replay.evidence
    ctx = capital_context or default_offline_replay_capital_context_v0(
        instrument_id=evidence.instrument_id,
    )
    context, policy = capital_context_to_quantity_chain_inputs_v1(ctx)
    chain = evaluate_quantity_chain_v1(evidence, context, policy)
    safety_binding = bind_safety_kernel_offline_replay_evidence_v0(
        evidence,
        context=safety_context,
    )
    intent: Optional[CanonicalOrderIntentV1] = None
    intent_build: Optional[CanonicalOrderIntentBuildResultV1] = None
    selected_side = map_selected_side_to_sizing_side(evidence.selected_side) or str(
        evidence.selected_side
    )
    safety_hard_blocks = safety_binding.boundary.hard_block_reasons
    if (
        chain.outcome is CapitalRiskSizingOutcome.PASS
        and chain.quantity_provenance is not None
        and decision_outcome_is_actionable(evidence.decision_outcome)
        and not safety_hard_blocks
    ):
        intent_action = map_decision_outcome_to_intent_action(evidence.decision_outcome)
        if intent_action is not None:
            decision = _decision_from_chain(chain, selected_side=selected_side)
            sizing_input = _sizing_input_for_29q(evidence, ctx, context, policy)
            intent_build = build_canonical_order_intent_v1(
                CanonicalOrderIntentBuildInputV1(
                    sizing_input=sizing_input,
                    sizing_decision=decision,
                    intent_id=f"intent-{evidence.decision_id}",
                    trading_epoch=str(evidence.trading_epoch),
                    canonical_trading_logic_version=_DEFAULT_CANONICAL_TRADING_LOGIC_VERSION,
                    intent_action=intent_action,
                    policy_digest=ctx.policy_digest,
                    order_type_policy=_DEFAULT_ORDER_TYPE_POLICY,
                    price_policy=_DEFAULT_PRICE_POLICY,
                    time_in_force_policy=_DEFAULT_TIME_IN_FORCE_POLICY,
                    max_slippage_policy=_DEFAULT_MAX_SLIPPAGE_POLICY,
                    expected_position_side=_expected_position_side(intent_action, selected_side),
                    current_reconciled_exposure=ctx.current_reconciled_exposure,
                    current_open_side=ctx.current_open_side,
                )
            )
            if (
                intent_build.outcome is CanonicalOrderIntentBuildOutcome.PASS
                and intent_build.intent is not None
            ):
                intent = intent_build.intent
    return MasterV2CapitalRiskSizingSafetyIntentCompositionV1(
        core=core,
        chain=chain,
        safety_binding=safety_binding,
        intent=intent,
        intent_build=intent_build,
        compute_owner=core.compute_owner,
        decision_packet_role=core.decision_packet_role
        or DECISION_PACKET_ROLE_HANDOFF_EVIDENCE_ONLY,
        side_state_writer=core.side_state_writer,
        submission_authorized=(False if intent is None else bool(intent.submission_authorized)),
    )
