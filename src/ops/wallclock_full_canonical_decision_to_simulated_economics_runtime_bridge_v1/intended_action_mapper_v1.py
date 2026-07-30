"""Map canonical decision + sizing intent → analytical intended_side / quantity."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping, Optional

from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)

_ZERO = Decimal("0")


@dataclass(frozen=True)
class IntendedAnalyticalActionV1:
    intended_side: str  # BUY|SELL|HOLD
    intended_quantity: Decimal
    decision_outcome: str
    selected_side: str
    intent_action: str
    quantity_source: str
    safety_blocked: bool
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "intended_side": self.intended_side,
            "intended_quantity": str(self.intended_quantity),
            "decision_outcome": self.decision_outcome,
            "selected_side": self.selected_side,
            "intent_action": self.intent_action,
            "quantity_source": self.quantity_source,
            "safety_blocked": self.safety_blocked,
            "reason_codes": list(self.reason_codes),
        }


def _portfolio_signed_qty(portfolio_snapshot: Mapping[str, Any], instrument_id: str) -> Decimal:
    state = portfolio_snapshot.get("state") or {}
    positions = state.get("positions") or {}
    pos = positions.get(instrument_id) or {}
    raw = pos.get("quantity", "0")
    try:
        return Decimal(str(raw))
    except Exception:  # noqa: BLE001
        return _ZERO


def map_replay_result_to_intended_analytical_action_v1(
    result: IntegratedOfflineReplayResultV1,
    *,
    instrument_id: str,
    portfolio_snapshot: Mapping[str, Any] | None = None,
) -> IntendedAnalyticalActionV1:
    """Produce analytical BUY/SELL/HOLD from sole decision authority replay result.

    Never implies broker submission. execution_eligible remains false by policy.
    """
    evidence = result.evidence
    outcome = str(evidence.decision_outcome or "").strip().lower()
    selected = str(evidence.selected_side or "").strip().lower()
    reasons = tuple(evidence.reason_codes or ())

    safety_codes = {str(x).lower() for x in reasons}
    safety_blocked = any(
        x.startswith("safety") or "kill" in x or x.endswith("_blocked") for x in safety_codes
    ) or outcome in {"blocked"}

    intent = None
    qty = _ZERO
    intent_action = "NONE"
    if result.intermediate is not None and result.intermediate.canonical_order_intent is not None:
        intent = result.intermediate.canonical_order_intent
        intent_action = str(getattr(intent, "intent_action", "NONE") or "NONE")
        raw_q = getattr(intent, "quantity", None)
        if raw_q is not None:
            qty = Decimal(str(raw_q))
    elif (
        result.intermediate is not None
        and result.intermediate.capital_risk_sizing_decision is not None
    ):
        sz = result.intermediate.capital_risk_sizing_decision
        raw_q = getattr(sz, "final_quantity", None)
        if raw_q is not None:
            qty = Decimal(str(raw_q))
        intent_action = f"SIZING::{outcome}"

    if safety_blocked or not result.replay_pass:
        return IntendedAnalyticalActionV1(
            intended_side="HOLD",
            intended_quantity=_ZERO,
            decision_outcome=outcome or "blocked",
            selected_side=selected or "neutral",
            intent_action=intent_action,
            quantity_source="safety_or_fail_closed",
            safety_blocked=True,
            reason_codes=reasons or ("FAIL_CLOSED_HOLD",),
        )

    if outcome == "enter_long" or intent_action == "ENTER_LONG":
        if qty <= 0:
            return IntendedAnalyticalActionV1(
                intended_side="HOLD",
                intended_quantity=_ZERO,
                decision_outcome=outcome,
                selected_side=selected,
                intent_action=intent_action,
                quantity_source="enter_long_zero_qty",
                safety_blocked=False,
                reason_codes=reasons + ("INTENDED_QUANTITY_REQUIRED",),
            )
        return IntendedAnalyticalActionV1(
            intended_side="BUY",
            intended_quantity=qty,
            decision_outcome=outcome,
            selected_side=selected,
            intent_action=intent_action or "ENTER_LONG",
            quantity_source="canonical_order_intent",
            safety_blocked=False,
            reason_codes=reasons,
        )

    if outcome == "enter_short" or intent_action == "ENTER_SHORT":
        if qty <= 0:
            return IntendedAnalyticalActionV1(
                intended_side="HOLD",
                intended_quantity=_ZERO,
                decision_outcome=outcome,
                selected_side=selected,
                intent_action=intent_action,
                quantity_source="enter_short_zero_qty",
                safety_blocked=False,
                reason_codes=reasons + ("INTENDED_QUANTITY_REQUIRED",),
            )
        return IntendedAnalyticalActionV1(
            intended_side="SELL",
            intended_quantity=qty,
            decision_outcome=outcome,
            selected_side=selected,
            intent_action=intent_action or "ENTER_SHORT",
            quantity_source="canonical_order_intent",
            safety_blocked=False,
            reason_codes=reasons,
        )

    if outcome in {"exit", "reduce"} or intent_action in {"EXIT", "REDUCE"}:
        signed = _portfolio_signed_qty(portfolio_snapshot or {}, instrument_id)
        if signed == 0:
            return IntendedAnalyticalActionV1(
                intended_side="HOLD",
                intended_quantity=_ZERO,
                decision_outcome=outcome,
                selected_side=selected,
                intent_action=intent_action,
                quantity_source="exit_flat",
                safety_blocked=False,
                reason_codes=reasons + ("NO_POSITION_TO_EXIT",),
            )
        close_qty = qty if qty > 0 else signed.copy_abs()
        close_qty = min(close_qty, signed.copy_abs())
        side = "SELL" if signed > 0 else "BUY"
        return IntendedAnalyticalActionV1(
            intended_side=side,
            intended_quantity=close_qty,
            decision_outcome=outcome,
            selected_side=selected,
            intent_action=intent_action or outcome.upper(),
            quantity_source="exit_or_reduce",
            safety_blocked=False,
            reason_codes=reasons,
        )

    return IntendedAnalyticalActionV1(
        intended_side="HOLD",
        intended_quantity=_ZERO,
        decision_outcome=outcome or "hold",
        selected_side=selected or "neutral",
        intent_action=intent_action or "NONE",
        quantity_source="non_actionable",
        safety_blocked=False,
        reason_codes=reasons or ("NON_ACTIONABLE_HOLD",),
    )
