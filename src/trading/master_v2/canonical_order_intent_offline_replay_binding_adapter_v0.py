# src/trading/master_v2/canonical_order_intent_offline_replay_binding_adapter_v0.py
"""
Offline replay adapter: binds Integrated / Scenario replay to canonical
``canonical_order_intent_v1`` without duplicating intent logic.

Wiring-only parity slice — no runtime authority, no order effects.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
        CanonicalCoreRuntimeCapitalContextV0,
    )

from src.governance.canonical_order_intent_v1 import (
    AUTHORITY_EFFECT_NONE,
    RUNTIME_EFFECT_NONE,
    CanonicalOrderIntentBuildInputV1,
    CanonicalOrderIntentBuildOutcome,
    CanonicalOrderIntentV1,
    IntentAction,
    IntentSide,
    build_canonical_order_intent_v1,
)
from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingDecisionV1,
    CapitalRiskSizingOutcome,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
    finalize_offline_replay_decision_evidence_v1,
)

CANONICAL_ORDER_INTENT_OFFLINE_REPLAY_BINDING_ADAPTER_LAYER_VERSION = "v0"
CANONICAL_ORDER_INTENT_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0"
)
CANONICAL_ORDER_INTENT_OWNER = "src.governance.canonical_order_intent_v1"

ORDER_INTENT_EFFECT_BOUND_OFFLINE = "BOUND_OFFLINE"
ORDER_INTENT_EFFECT_NONE = "NONE"

_DEFAULT_ORDER_TYPE_POLICY = "MARKET_ONLY"
_DEFAULT_PRICE_POLICY = "EXPLICIT_NONE"
_DEFAULT_TIME_IN_FORCE_POLICY = "GTC"
_DEFAULT_MAX_SLIPPAGE_POLICY = "NONE"
_DEFAULT_CANONICAL_TRADING_LOGIC_VERSION = "integrated_offline_trading_logic_replay_v1"


def _expected_position_side(intent_action: str, selected_side: str) -> str:
    if intent_action == IntentAction.ENTER_LONG.value:
        return IntentSide.LONG.value
    if intent_action == IntentAction.ENTER_SHORT.value:
        return IntentSide.SHORT.value
    return selected_side


def compute_order_intent_ref_v0(intent: CanonicalOrderIntentV1) -> str:
    return intent.semantic_digest


@dataclass(frozen=True)
class CanonicalOrderIntentOfflineReplayBindingResultV0:
    evidence: CanonicalTradingDecisionEvidenceV1
    canonical_intent: Optional[CanonicalOrderIntentV1]
    binding_applied: bool
    order_intent_ref: str
    order_intent_effect: str
    intent_outcome: str


def bind_canonical_order_intent_offline_replay_evidence_v0(
    evidence: CanonicalTradingDecisionEvidenceV1,
    *,
    sizing_decision: Optional[CapitalRiskSizingDecisionV1],
    capital_context: "CanonicalCoreRuntimeCapitalContextV0 | None" = None,
) -> CanonicalOrderIntentOfflineReplayBindingResultV0:
    """Derive canonical order intent from bound sizing output for offline replay."""
    from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
        build_capital_risk_sizing_input_from_decision_v0,
        decision_outcome_is_actionable,
        map_decision_outcome_to_intent_action,
        map_selected_side_to_sizing_side,
    )
    from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
        RISK_SIZING_EFFECT_BOUND_OFFLINE,
        default_offline_replay_capital_context_v0,
    )

    if not decision_outcome_is_actionable(evidence.decision_outcome):
        finalized = finalize_offline_replay_decision_evidence_v1(evidence)
        return CanonicalOrderIntentOfflineReplayBindingResultV0(
            evidence=finalized,
            canonical_intent=None,
            binding_applied=False,
            order_intent_ref="",
            order_intent_effect=ORDER_INTENT_EFFECT_NONE,
            intent_outcome="NOT_APPLICABLE",
        )

    if (
        evidence.risk_sizing_effect != RISK_SIZING_EFFECT_BOUND_OFFLINE
        or sizing_decision is None
        or sizing_decision.outcome is not CapitalRiskSizingOutcome.PASS
    ):
        finalized = finalize_offline_replay_decision_evidence_v1(evidence)
        return CanonicalOrderIntentOfflineReplayBindingResultV0(
            evidence=finalized,
            canonical_intent=None,
            binding_applied=False,
            order_intent_ref="",
            order_intent_effect=ORDER_INTENT_EFFECT_NONE,
            intent_outcome="BLOCKED",
        )

    intent_action = map_decision_outcome_to_intent_action(evidence.decision_outcome)
    selected_side = map_selected_side_to_sizing_side(evidence.selected_side)
    if intent_action is None or selected_side is None:
        finalized = finalize_offline_replay_decision_evidence_v1(evidence)
        return CanonicalOrderIntentOfflineReplayBindingResultV0(
            evidence=finalized,
            canonical_intent=None,
            binding_applied=False,
            order_intent_ref="",
            order_intent_effect=ORDER_INTENT_EFFECT_NONE,
            intent_outcome="BLOCKED",
        )

    ctx = capital_context or default_offline_replay_capital_context_v0(
        instrument_id=evidence.instrument_id,
    )
    sizing_input, build_errors = build_capital_risk_sizing_input_from_decision_v0(
        decision=evidence,
        capital_context=ctx,
    )
    if sizing_input is None:
        finalized = finalize_offline_replay_decision_evidence_v1(
            replace(
                evidence,
                reason_codes=tuple(dict.fromkeys((*evidence.reason_codes, *build_errors))),
            )
        )
        return CanonicalOrderIntentOfflineReplayBindingResultV0(
            evidence=finalized,
            canonical_intent=None,
            binding_applied=False,
            order_intent_ref="",
            order_intent_effect=ORDER_INTENT_EFFECT_NONE,
            intent_outcome="BLOCKED",
        )

    intent_build = build_canonical_order_intent_v1(
        CanonicalOrderIntentBuildInputV1(
            sizing_input=sizing_input,
            sizing_decision=sizing_decision,
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
    intent_outcome = intent_build.outcome.value
    if (
        intent_build.outcome is not CanonicalOrderIntentBuildOutcome.PASS
        or intent_build.intent is None
    ):
        finalized = finalize_offline_replay_decision_evidence_v1(
            replace(
                evidence,
                reason_codes=tuple(
                    dict.fromkeys((*evidence.reason_codes, *intent_build.reason_codes))
                ),
            )
        )
        return CanonicalOrderIntentOfflineReplayBindingResultV0(
            evidence=finalized,
            canonical_intent=None,
            binding_applied=False,
            order_intent_ref="",
            order_intent_effect=ORDER_INTENT_EFFECT_NONE,
            intent_outcome=intent_outcome,
        )

    intent = intent_build.intent
    order_intent_ref = compute_order_intent_ref_v0(intent)
    bound_evidence = replace(
        evidence,
        order_intent_ref=order_intent_ref,
        order_intent_effect=ORDER_INTENT_EFFECT_BOUND_OFFLINE,
    )
    finalized = finalize_offline_replay_decision_evidence_v1(bound_evidence)
    return CanonicalOrderIntentOfflineReplayBindingResultV0(
        evidence=finalized,
        canonical_intent=intent,
        binding_applied=True,
        order_intent_ref=order_intent_ref,
        order_intent_effect=ORDER_INTENT_EFFECT_BOUND_OFFLINE,
        intent_outcome=intent_outcome,
    )


def evaluate_scenario_canonical_order_intent_v0(
    evidence: CanonicalTradingDecisionEvidenceV1,
    *,
    sizing_decision: Optional[CapitalRiskSizingDecisionV1],
    reference_price=None,
) -> CanonicalOrderIntentOfflineReplayBindingResultV0:
    from decimal import Decimal

    from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
        default_offline_replay_capital_context_v0,
    )

    ctx = default_offline_replay_capital_context_v0(
        instrument_id=evidence.instrument_id,
        reference_price=reference_price if reference_price is not None else Decimal("3500"),
    )
    return bind_canonical_order_intent_offline_replay_evidence_v0(
        evidence,
        sizing_decision=sizing_decision,
        capital_context=ctx,
    )


def canonical_order_intent_binding_non_authority_boundary_ok_v0(
    binding: CanonicalOrderIntentOfflineReplayBindingResultV0,
) -> bool:
    ev = binding.evidence
    intent = binding.canonical_intent
    if not ev.execution_eligible and ev.adapter_compatible:
        return False
    if ev.authority_effect != AUTHORITY_EFFECT_NONE:
        return False
    if ev.runtime_effect != RUNTIME_EFFECT_NONE:
        return False
    if ev.order_effect != "NONE":
        return False
    if binding.binding_applied and binding.order_intent_effect != ORDER_INTENT_EFFECT_BOUND_OFFLINE:
        return False
    if intent is not None:
        if intent.execution_eligible or intent.adapter_compatible or intent.submission_authorized:
            return False
        if intent.authority_effect != AUTHORITY_EFFECT_NONE:
            return False
        if intent.runtime_effect != RUNTIME_EFFECT_NONE:
            return False
    return True


def system_economic_evidence_admissible_v0(
    binding: CanonicalOrderIntentOfflineReplayBindingResultV0,
) -> bool:
    """Offline replay must not admit system-economic evidence without full chain proof."""
    ev = binding.evidence
    if not binding.binding_applied:
        return False
    if not binding.order_intent_ref:
        return False
    if ev.execution_eligible or ev.adapter_compatible:
        return False
    if ev.order_intent_effect != ORDER_INTENT_EFFECT_BOUND_OFFLINE:
        return False
    return False
