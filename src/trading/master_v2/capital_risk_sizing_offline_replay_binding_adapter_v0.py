# src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py
"""
Offline replay adapter: binds Integrated / Scenario replay to canonical
``capital_risk_sizing_v1`` without duplicating sizing logic.

Wiring-only parity slice — no runtime authority, no order effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
        CanonicalCoreRuntimeCapitalContextV0,
    )

from src.governance.canonical_order_intent_v1 import compute_quantity_provenance_ref
from src.governance.capital_risk_sizing_v1 import (
    AUTHORITY_EFFECT_NONE,
    CapitalRiskSizingDecisionV1,
    CapitalRiskSizingOutcome,
    InstrumentQuantityConstraintsV1,
    RUNTIME_EFFECT_NONE,
    evaluate_capital_risk_sizing_v1,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
    finalize_offline_replay_decision_evidence_v1,
)

CAPITAL_RISK_SIZING_OFFLINE_REPLAY_BINDING_ADAPTER_LAYER_VERSION = "v0"
CAPITAL_RISK_SIZING_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0"
)
CANONICAL_CAPITAL_RISK_SIZING_OWNER = "src.governance.capital_risk_sizing_v1"

RISK_SIZING_EFFECT_BOUND_OFFLINE = "BOUND_OFFLINE"
RISK_SIZING_EFFECT_NONE = "NONE"
_QUANTITY_STATUS_NOT_BOUND = "NOT_BOUND"

_OFFLINE_BINDING_CONFIG_DIGEST = hashlib.sha256(
    b"capital-risk-sizing-offline-replay-binding-adapter-v0-config"
).hexdigest()
DEFAULT_OFFLINE_BINDING_CONFIG_DIGEST = _OFFLINE_BINDING_CONFIG_DIGEST

_DEFAULT_REFERENCE_PRICE = Decimal("3500")
_DEFAULT_PROTECTIVE_STOP = Decimal("3400")
_DEFAULT_ACCOUNT_EQUITY = Decimal("10000")
_DEFAULT_SCOPE_CAPITAL = Decimal("500")
_DEFAULT_PER_TRADE_RISK = Decimal("25")
_DEFAULT_TOTAL_CAPITAL = Decimal("500")
_DEFAULT_DAILY_LOSS_BUDGET = Decimal("25")


def default_offline_replay_instrument_v0(
    instrument_id: str,
) -> InstrumentQuantityConstraintsV1:
    return InstrumentQuantityConstraintsV1(
        instrument_id=instrument_id,
        market_type="futures",
        contract_kind="LINEAR",
        contract_multiplier=Decimal("1"),
        lot_size=Decimal("0.01"),
        minimum_quantity=Decimal("0.01"),
        maximum_quantity=Decimal("100"),
        minimum_notional=Decimal("5"),
        tick_size=Decimal("0.01"),
        instrument_metadata_version="offline_replay_futures_metadata_v0",
    )


def default_offline_replay_capital_context_v0(
    *,
    instrument_id: str,
    reference_price: Decimal | None = None,
) -> "CanonicalCoreRuntimeCapitalContextV0":
    from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
        CanonicalCoreRuntimeCapitalContextV0,
    )

    price = reference_price if reference_price is not None else _DEFAULT_REFERENCE_PRICE
    return CanonicalCoreRuntimeCapitalContextV0(
        reference_price=price,
        protective_stop_price=_DEFAULT_PROTECTIVE_STOP,
        account_equity=_DEFAULT_ACCOUNT_EQUITY,
        scope_capital_limit=_DEFAULT_SCOPE_CAPITAL,
        per_trade_risk_limit=_DEFAULT_PER_TRADE_RISK,
        total_capital_limit=_DEFAULT_TOTAL_CAPITAL,
        daily_loss_remaining_budget=_DEFAULT_DAILY_LOSS_BUDGET,
        current_reconciled_exposure=Decimal("0"),
        instrument=default_offline_replay_instrument_v0(instrument_id),
        config_digest=_OFFLINE_BINDING_CONFIG_DIGEST,
    )


def compute_risk_sizing_decision_ref_v0(
    decision: CapitalRiskSizingDecisionV1,
) -> str:
    provenance = decision.quantity_provenance
    if provenance is not None:
        return compute_quantity_provenance_ref(provenance)
    payload = {
        "outcome": decision.outcome.value,
        "final_quantity": str(decision.final_quantity),
        "reason_codes": sorted(decision.reason_codes),
        "selected_side": decision.selected_side,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"risk_sizing::{digest}"


def _quantity_status_from_sizing_v0(
    decision: CapitalRiskSizingDecisionV1,
) -> str:
    provenance = decision.quantity_provenance
    if provenance is not None:
        return provenance.final_quantity_status.value
    if decision.outcome is CapitalRiskSizingOutcome.BLOCKED:
        return "BLOCK"
    return _QUANTITY_STATUS_NOT_BOUND


@dataclass(frozen=True)
class CapitalRiskSizingOfflineReplayBindingResultV0:
    evidence: CanonicalTradingDecisionEvidenceV1
    sizing_decision: Optional[CapitalRiskSizingDecisionV1]
    binding_applied: bool
    quantity_provenance_ref: str
    risk_sizing_ref: str
    quantity_status: str
    risk_sizing_effect: str


def bind_capital_risk_sizing_offline_replay_evidence_v0(
    evidence: CanonicalTradingDecisionEvidenceV1,
    *,
    capital_context: "CanonicalCoreRuntimeCapitalContextV0 | None" = None,
) -> CapitalRiskSizingOfflineReplayBindingResultV0:
    """Evaluate canonical sizing owner and attach offline replay evidence fields."""
    from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
        build_capital_risk_sizing_input_from_decision_v0,
        decision_outcome_is_actionable,
    )

    ctx = capital_context or default_offline_replay_capital_context_v0(
        instrument_id=evidence.instrument_id,
    )
    if not decision_outcome_is_actionable(evidence.decision_outcome):
        finalized = finalize_offline_replay_decision_evidence_v1(evidence)
        return CapitalRiskSizingOfflineReplayBindingResultV0(
            evidence=finalized,
            sizing_decision=None,
            binding_applied=False,
            quantity_provenance_ref="",
            risk_sizing_ref="",
            quantity_status=_QUANTITY_STATUS_NOT_BOUND,
            risk_sizing_effect=RISK_SIZING_EFFECT_NONE,
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
        return CapitalRiskSizingOfflineReplayBindingResultV0(
            evidence=finalized,
            sizing_decision=None,
            binding_applied=False,
            quantity_provenance_ref="",
            risk_sizing_ref="",
            quantity_status=_QUANTITY_STATUS_NOT_BOUND,
            risk_sizing_effect=RISK_SIZING_EFFECT_NONE,
        )

    sizing_decision = evaluate_capital_risk_sizing_v1(sizing_input)
    quantity_provenance_ref = ""
    provenance = sizing_decision.quantity_provenance
    if provenance is not None:
        quantity_provenance_ref = compute_quantity_provenance_ref(provenance)
    risk_sizing_ref = compute_risk_sizing_decision_ref_v0(sizing_decision)
    quantity_status = _quantity_status_from_sizing_v0(sizing_decision)

    bound_evidence = replace(
        evidence,
        quantity_status=quantity_status,
        quantity_provenance_ref=quantity_provenance_ref,
        risk_sizing_ref=risk_sizing_ref,
        risk_sizing_effect=RISK_SIZING_EFFECT_BOUND_OFFLINE,
    )
    finalized = finalize_offline_replay_decision_evidence_v1(bound_evidence)
    return CapitalRiskSizingOfflineReplayBindingResultV0(
        evidence=finalized,
        sizing_decision=sizing_decision,
        binding_applied=True,
        quantity_provenance_ref=quantity_provenance_ref,
        risk_sizing_ref=risk_sizing_ref,
        quantity_status=quantity_status,
        risk_sizing_effect=RISK_SIZING_EFFECT_BOUND_OFFLINE,
    )


def build_scenario_tick_decision_evidence_v0(
    *,
    decision_id: str,
    replay_id: str,
    instrument_id: str,
    trading_epoch: int,
    composition_result_id: str,
    entry_exit_policy_ref: str,
    selected_side: str,
    decision_outcome: str,
    reason_codes: tuple[str, ...],
    decision_precedence_trace: tuple[str, ...],
    config_digest: str,
    implementation_digest: str,
) -> CanonicalTradingDecisionEvidenceV1:
    input_material = json.dumps(
        {
            "decision_id": decision_id,
            "instrument_id": instrument_id,
            "trading_epoch": trading_epoch,
            "composition_result_id": composition_result_id,
        },
        sort_keys=True,
    )
    input_digest = hashlib.sha256(input_material.encode("utf-8")).hexdigest()
    return CanonicalTradingDecisionEvidenceV1(
        decision_id=decision_id,
        replay_id=replay_id,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        market_context_ref=f"scenario-market-context::{decision_id}",
        scope_initialization_ref=f"scenario-scope-init::{decision_id}",
        scope_event_ref=f"scenario-scope-event::{decision_id}",
        bull_assessment_ref=f"scenario-bull::{decision_id}",
        bear_assessment_ref=f"scenario-bear::{decision_id}",
        state_switch_ref=f"scenario-state-switch::{decision_id}",
        bull_survival_ref=f"scenario-bull-survival::{decision_id}",
        bear_survival_ref=f"scenario-bear-survival::{decision_id}",
        bull_suitability_ref=f"scenario-bull-suitability::{decision_id}",
        bear_suitability_ref=f"scenario-bear-suitability::{decision_id}",
        composition_result_ref=composition_result_id,
        entry_exit_policy_ref=entry_exit_policy_ref,
        current_scope_ref=f"scenario-current-scope::{decision_id}",
        next_scope_ref=f"scenario-next-scope::{decision_id}",
        previous_direction_state="neutral",
        next_direction_state=selected_side,
        selected_side=selected_side,
        selected_strategy_ref="",
        decision_outcome=decision_outcome,
        entry_or_exit_policy_ref=entry_exit_policy_ref,
        reason_codes=reason_codes,
        decision_precedence_trace=decision_precedence_trace,
        component_versions={},
        policy_versions={},
        config_digest=config_digest,
        implementation_digest=implementation_digest,
        input_digest=input_digest,
        semantic_digest="",
    )


def evaluate_scenario_capital_risk_sizing_v0(
    evidence: CanonicalTradingDecisionEvidenceV1,
    *,
    reference_price: Decimal | None = None,
) -> CapitalRiskSizingOfflineReplayBindingResultV0:
    ctx = default_offline_replay_capital_context_v0(
        instrument_id=evidence.instrument_id,
        reference_price=reference_price,
    )
    return bind_capital_risk_sizing_offline_replay_evidence_v0(
        evidence,
        capital_context=ctx,
    )


def capital_risk_sizing_binding_non_authority_boundary_ok_v0(
    binding: CapitalRiskSizingOfflineReplayBindingResultV0,
) -> bool:
    ev = binding.evidence
    decision = binding.sizing_decision
    if not ev.execution_eligible and ev.adapter_compatible:
        return False
    if ev.authority_effect != AUTHORITY_EFFECT_NONE:
        return False
    if ev.runtime_effect != RUNTIME_EFFECT_NONE:
        return False
    if ev.order_effect != "NONE":
        return False
    if binding.binding_applied and binding.risk_sizing_effect != RISK_SIZING_EFFECT_BOUND_OFFLINE:
        return False
    if decision is not None:
        if decision.adapter_compatible or decision.authority_effect != AUTHORITY_EFFECT_NONE:
            return False
        if decision.runtime_effect != RUNTIME_EFFECT_NONE:
            return False
    return True


def system_economic_evidence_admissible_v0(
    binding: CapitalRiskSizingOfflineReplayBindingResultV0,
) -> bool:
    """Offline replay must not admit system-economic evidence without full chain proof."""
    ev = binding.evidence
    if not binding.binding_applied:
        return False
    if not binding.quantity_provenance_ref:
        return False
    if ev.execution_eligible or ev.adapter_compatible:
        return False
    if ev.risk_sizing_effect != RISK_SIZING_EFFECT_BOUND_OFFLINE:
        return False
    return False
