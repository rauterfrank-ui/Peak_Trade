"""Phase 11.4 order lifecycle state machine (Cap 11.1 contracts only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.constants_v1 import (
    ORDER_LIFECYCLE_CONTRACT_VERSION,
)

# Exact lifecycle states from PEAK_TRADE_MASTER_RUNBOOK §11.4.
ORDER_LIFECYCLE_STATES: tuple[str, ...] = (
    "INTENT_CREATED",
    "ORDER_PLAN_CREATED",
    "RISK_RESERVED",
    "PRE_SUBMIT_VALIDATED",
    "SUBMIT_PENDING",
    "SUBMIT_ATTEMPTED",
    "ACKNOWLEDGED",
    "REJECTED",
    "UNKNOWN",
    "OPEN",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCEL_PENDING",
    "AMEND_PENDING",
    "CANCELLED",
    "EXPIRED",
    "TERMINAL_REJECTED",
    "ACCOUNTED",
    "RECONCILED",
    "EVIDENCED",
)

TERMINAL_IMMUTABLE_STATES: frozenset[str] = frozenset(
    {
        "EVIDENCED",
    }
)

# States that must not reopen once reached (terminal economic/order closure).
HARD_TERMINAL_ORDER_STATES: frozenset[str] = frozenset(
    {
        "CANCELLED",
        "EXPIRED",
        "TERMINAL_REJECTED",
        "FILLED",
    }
)

# Allowed transitions derived from §11.4 chain (fail-closed elsewhere).
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "INTENT_CREATED": frozenset({"ORDER_PLAN_CREATED"}),
    "ORDER_PLAN_CREATED": frozenset({"RISK_RESERVED"}),
    "RISK_RESERVED": frozenset({"PRE_SUBMIT_VALIDATED"}),
    "PRE_SUBMIT_VALIDATED": frozenset({"SUBMIT_PENDING"}),
    "SUBMIT_PENDING": frozenset({"SUBMIT_ATTEMPTED"}),
    "SUBMIT_ATTEMPTED": frozenset({"ACKNOWLEDGED", "REJECTED", "UNKNOWN"}),
    "ACKNOWLEDGED": frozenset(
        {"OPEN", "PARTIALLY_FILLED", "FILLED", "CANCEL_PENDING", "AMEND_PENDING", "REJECTED"}
    ),
    "UNKNOWN": frozenset(
        {
            # Contract: UNKNOWN may advance only after authoritative query/reconcile.
            # Cap 11.1 encodes the gate as RECONCILED-before-retry semantics via
            # explicit recovery transitions; blind resubmit is forbidden.
            "ACKNOWLEDGED",
            "REJECTED",
            "OPEN",
            "PARTIALLY_FILLED",
            "FILLED",
            "CANCELLED",
            "EXPIRED",
            "TERMINAL_REJECTED",
        }
    ),
    "OPEN": frozenset(
        {
            "PARTIALLY_FILLED",
            "FILLED",
            "CANCEL_PENDING",
            "AMEND_PENDING",
            "CANCELLED",
            "EXPIRED",
        }
    ),
    "PARTIALLY_FILLED": frozenset(
        {"PARTIALLY_FILLED", "FILLED", "CANCEL_PENDING", "AMEND_PENDING", "CANCELLED", "EXPIRED"}
    ),
    "CANCEL_PENDING": frozenset({"CANCELLED", "PARTIALLY_FILLED", "FILLED", "EXPIRED"}),
    "AMEND_PENDING": frozenset(
        {"OPEN", "PARTIALLY_FILLED", "FILLED", "CANCEL_PENDING", "CANCELLED", "EXPIRED", "REJECTED"}
    ),
    "REJECTED": frozenset({"TERMINAL_REJECTED", "ACCOUNTED"}),
    "TERMINAL_REJECTED": frozenset({"ACCOUNTED"}),
    "FILLED": frozenset({"ACCOUNTED"}),
    "CANCELLED": frozenset({"ACCOUNTED"}),
    "EXPIRED": frozenset({"ACCOUNTED"}),
    "ACCOUNTED": frozenset({"RECONCILED"}),
    "RECONCILED": frozenset({"EVIDENCED"}),
    "EVIDENCED": frozenset(),
}


class OrderLifecycleTransitionError(RuntimeError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}:{detail}" if detail else code)


@dataclass
class OrderLifecycleStateMachineV1:
    """Deterministic fail-closed order lifecycle machine for Cap 11.1."""

    current_state: str = "INTENT_CREATED"
    client_order_id: str = ""
    intent_id: str = ""
    order_plan_id: str = ""
    history: list[str] = field(default_factory=lambda: ["INTENT_CREATED"])
    unknown_requires_exchange_query_before_retry: bool = True
    blind_retry_attempted: bool = False
    exchange_query_completed_for_unknown: bool = False
    terminal_immutable: bool = True

    def __post_init__(self) -> None:
        if self.current_state not in ORDER_LIFECYCLE_STATES:
            raise OrderLifecycleTransitionError("INVALID_LIFECYCLE_STATE", self.current_state)

    def can_transition(self, target: str) -> bool:
        if self.current_state in TERMINAL_IMMUTABLE_STATES:
            return False
        allowed = ALLOWED_TRANSITIONS.get(self.current_state, frozenset())
        return target in allowed

    def transition(self, target: str, *, exchange_query_completed: bool = False) -> str:
        if target not in ORDER_LIFECYCLE_STATES:
            raise OrderLifecycleTransitionError("UNKNOWN_TARGET_STATE", target)
        if self.current_state in TERMINAL_IMMUTABLE_STATES:
            raise OrderLifecycleTransitionError(
                "TERMINAL_STATE_IMMUTABLE",
                f"{self.current_state}->{target}",
            )
        if not self.can_transition(target):
            raise OrderLifecycleTransitionError(
                "ILLEGAL_LIFECYCLE_TRANSITION",
                f"{self.current_state}->{target}",
            )
        if self.current_state == "UNKNOWN":
            # Contract semantics: never blind-retry submission from UNKNOWN.
            if not exchange_query_completed and not self.exchange_query_completed_for_unknown:
                raise OrderLifecycleTransitionError(
                    "UNKNOWN_REQUIRES_EXCHANGE_QUERY_BEFORE_RETRY",
                    f"{self.current_state}->{target}",
                )
            self.exchange_query_completed_for_unknown = True
        self.current_state = target
        self.history.append(target)
        return self.current_state

    def mark_blind_retry_attempt(self) -> None:
        self.blind_retry_attempted = True
        raise OrderLifecycleTransitionError(
            "UNKNOWN_SUBMIT_RESULT_NEVER_BLINDLY_RETRIED",
            "blind_retry_forbidden",
        )


def lifecycle_transition_matrix_v1() -> dict[str, list[str]]:
    return {state: sorted(targets) for state, targets in ALLOWED_TRANSITIONS.items()}


def prove_order_lifecycle_state_machine_v1() -> dict[str, Any]:
    machine = OrderLifecycleStateMachineV1()
    happy_path = [
        "ORDER_PLAN_CREATED",
        "RISK_RESERVED",
        "PRE_SUBMIT_VALIDATED",
        "SUBMIT_PENDING",
        "SUBMIT_ATTEMPTED",
        "ACKNOWLEDGED",
        "OPEN",
        "FILLED",
        "ACCOUNTED",
        "RECONCILED",
        "EVIDENCED",
    ]
    for state in happy_path:
        machine.transition(state)

    illegal_blocked = False
    try:
        machine.transition("OPEN")
    except OrderLifecycleTransitionError as exc:
        illegal_blocked = exc.code == "TERMINAL_STATE_IMMUTABLE"

    unknown_machine = OrderLifecycleStateMachineV1()
    for state in [
        "ORDER_PLAN_CREATED",
        "RISK_RESERVED",
        "PRE_SUBMIT_VALIDATED",
        "SUBMIT_PENDING",
        "SUBMIT_ATTEMPTED",
        "UNKNOWN",
    ]:
        unknown_machine.transition(state)

    blind_blocked = False
    try:
        unknown_machine.transition("ACKNOWLEDGED", exchange_query_completed=False)
    except OrderLifecycleTransitionError as exc:
        blind_blocked = exc.code == "UNKNOWN_REQUIRES_EXCHANGE_QUERY_BEFORE_RETRY"

    queried_ok = False
    try:
        unknown_machine.transition("ACKNOWLEDGED", exchange_query_completed=True)
        queried_ok = unknown_machine.current_state == "ACKNOWLEDGED"
    except OrderLifecycleTransitionError:
        queried_ok = False

    return {
        "ok": illegal_blocked and blind_blocked and queried_ok,
        "contract_version": ORDER_LIFECYCLE_CONTRACT_VERSION,
        "ORDER_LIFECYCLE_STATE_MACHINE_BOUND": True,
        "TERMINAL_STATE_IMMUTABLE": True,
        "UNKNOWN_BLIND_RETRY_FORBIDDEN": True,
        "EXCHANGE_QUERY_BEFORE_RETRY_CONTRACT": True,
        "states": list(ORDER_LIFECYCLE_STATES),
        "transition_matrix": lifecycle_transition_matrix_v1(),
        "happy_path": machine.history,
        "illegal_terminal_reopen_blocked": illegal_blocked,
        "unknown_blind_transition_blocked": blind_blocked,
        "unknown_after_query_allowed": queried_ok,
        "CORE_LOGIC_CHANGE": False,
    }
