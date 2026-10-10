"""Offline productive replay → simulated portfolio economics (GHV-aligned consumer).

Uses the same intended-action mapping as the wallclock full canonical
decision→simulated economics bridge. Never treats evidence.execution_eligible
as simulated-fill admission.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    SimulatedFillV1,
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.simulated_economics_round_trip_ledger_v1 import (
    SimulatedEconomicsObservabilityContextV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.intended_action_mapper_v1 import (
    IntendedAnalyticalActionV1,
    map_replay_result_to_intended_analytical_action_v1,
)
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    ORDER_INTENT_EFFECT_BOUND_OFFLINE,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)

_BRIDGE_OWNER = "ops.integrated_offline_economic_evidence_v1.replay_simulated_economics_bridge_v1"


@dataclass(frozen=True)
class ReplaySimulatedEconomicsAdmissionV1:
    """One epoch admission outcome (observation only)."""

    admitted: bool
    intended_side: str
    intended_quantity: Decimal
    quantity_source: str
    canonical_order_intent_present: bool
    order_intent_effect: str
    execution_eligible: bool
    external_submission_authorized: bool
    fill: Optional[SimulatedFillV1]

    def to_dict(self) -> dict[str, Any]:
        return {
            "admitted": self.admitted,
            "intended_side": self.intended_side,
            "intended_quantity": str(self.intended_quantity),
            "quantity_source": self.quantity_source,
            "canonical_order_intent_present": self.canonical_order_intent_present,
            "order_intent_effect": self.order_intent_effect,
            "execution_eligible": self.execution_eligible,
            "external_submission_authorized": self.external_submission_authorized,
            "fill_applied": self.fill is not None,
            "bridge_owner": _BRIDGE_OWNER,
        }


def _external_submission_authorized_v1(result: IntegratedOfflineReplayResultV1) -> bool:
    intent = result.intermediate.canonical_order_intent if result.intermediate is not None else None
    if intent is not None and bool(getattr(intent, "submission_authorized", False)):
        return True
    return bool(result.evidence.execution_eligible)


def apply_replay_result_to_simulated_portfolio_v1(
    portfolio: SimulatedPortfolioEconomicsModelV1,
    *,
    result: IntegratedOfflineReplayResultV1,
    instrument_id: str,
    mark_price: Decimal,
    observability_context: SimulatedEconomicsObservabilityContextV1 | None = None,
) -> ReplaySimulatedEconomicsAdmissionV1:
    """Map replay → analytical action → portfolio; preserve offline non-authority."""
    if result.evidence.execution_eligible:
        raise ValueError("OFFLINE_REPLAY_EXECUTION_ELIGIBLE_MUST_REMAIN_FALSE")

    intended: IntendedAnalyticalActionV1 = map_replay_result_to_intended_analytical_action_v1(
        result,
        instrument_id=instrument_id,
        portfolio_snapshot=portfolio.snapshot(),
    )
    inter = result.intermediate
    coi_present = bool(inter is not None and inter.canonical_order_intent is not None)
    order_intent_effect = str(result.evidence.order_intent_effect or "NONE")

    side = intended.intended_side
    qty = intended.intended_quantity
    fill: Optional[SimulatedFillV1] = None
    if side in {"BUY", "SELL"} and qty > 0:
        fill = portfolio.apply_intended_action(
            instrument_id=instrument_id,
            side=side,
            quantity=qty,
            mark_price=mark_price,
            observability_context=observability_context,
        )
    else:
        portfolio.apply_intended_action(
            instrument_id=instrument_id,
            side="HOLD",
            quantity=Decimal("0"),
            mark_price=mark_price,
            observability_context=observability_context,
        )

    admitted = side in {"BUY", "SELL"} and qty > 0 and fill is not None
    if admitted and order_intent_effect != ORDER_INTENT_EFFECT_BOUND_OFFLINE and coi_present:
        # Fail-closed: admitted fill requires BOUND_OFFLINE intent effect when COI present.
        raise ValueError("ADMITTED_FILL_REQUIRES_ORDER_INTENT_EFFECT_BOUND_OFFLINE")

    return ReplaySimulatedEconomicsAdmissionV1(
        admitted=admitted,
        intended_side=side,
        intended_quantity=qty,
        quantity_source=intended.quantity_source,
        canonical_order_intent_present=coi_present,
        order_intent_effect=order_intent_effect,
        execution_eligible=bool(result.evidence.execution_eligible),
        external_submission_authorized=_external_submission_authorized_v1(result),
        fill=fill,
    )


def bridge_owner_v1() -> str:
    return _BRIDGE_OWNER
