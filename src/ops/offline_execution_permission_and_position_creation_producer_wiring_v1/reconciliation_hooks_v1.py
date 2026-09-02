"""Cap 11.1 / 11.5 reconciliation hooks. No venue GET."""

from __future__ import annotations

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.order_lifecycle_state_machine_v1 import (
    OrderLifecycleStateMachineV1,
    OrderLifecycleTransitionError,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.models_v1 import (
    ReconObligationV1,
    TransportOutcomeKindV1,
)


def _advance_to_submit_attempted(machine: OrderLifecycleStateMachineV1) -> None:
    for state in (
        "ORDER_PLAN_CREATED",
        "RISK_RESERVED",
        "PRE_SUBMIT_VALIDATED",
        "SUBMIT_PENDING",
        "SUBMIT_ATTEMPTED",
    ):
        machine.transition(state)


def advance_lifecycle_for_recording_outcome_v1(
    machine: OrderLifecycleStateMachineV1,
    *,
    outcome: TransportOutcomeKindV1,
) -> tuple[str, ReconObligationV1]:
    """Map recording outcomes onto Cap 11.1. Blind resend remains forbidden."""
    _advance_to_submit_attempted(machine)
    if outcome is TransportOutcomeKindV1.RECORDED:
        machine.transition("ACKNOWLEDGED")
        return machine.current_state, ReconObligationV1.NONE
    if outcome is TransportOutcomeKindV1.REJECTED:
        machine.transition("REJECTED")
        return machine.current_state, ReconObligationV1.NONE
    if outcome is TransportOutcomeKindV1.UNKNOWN:
        machine.transition("UNKNOWN")
        blind_blocked = False
        try:
            machine.transition("ACKNOWLEDGED", exchange_query_completed=False)
        except OrderLifecycleTransitionError as exc:
            blind_blocked = exc.code == "UNKNOWN_REQUIRES_EXCHANGE_QUERY_BEFORE_RETRY"
        if not blind_blocked:
            raise OrderLifecycleTransitionError("BLIND_RETRY_NOT_BLOCKED")
        return machine.current_state, ReconObligationV1.QUERY_BEFORE_RETRY
    raise OrderLifecycleTransitionError("UNSUPPORTED_RECORDING_OUTCOME", outcome.value)
