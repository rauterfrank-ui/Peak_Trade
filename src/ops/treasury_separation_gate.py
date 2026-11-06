from __future__ import annotations

import os
from dataclasses import dataclass


BOT = "bot"
TREASURY = "treasury"
ALLOWED_ROLES = {BOT, TREASURY}

WITHDRAW = "withdraw"
DEPOSIT_ADDRESS = "deposit_address_request"
INTERNAL_TRANSFER = "internal_transfer"

TREASURY_ONLY_OPERATIONS = {
    WITHDRAW,
    DEPOSIT_ADDRESS,
    INTERNAL_TRANSFER,
}


@dataclass(frozen=True)
class TreasuryPolicyDecision:
    allowed: bool
    role: str
    operation: str
    reason: str
    event_type: str


class TreasurySeparationError(RuntimeError):
    """Raised when a treasury-only operation is attempted in bot mode."""


def get_key_role() -> str:
    role = os.getenv("PT_KEY_ROLE", BOT).strip().lower()
    return role if role in ALLOWED_ROLES else BOT


def is_treasury_only_operation(operation: str) -> bool:
    return operation.strip().lower() in TREASURY_ONLY_OPERATIONS


def evaluate_treasury_policy(operation: str, role: str | None = None) -> TreasuryPolicyDecision:
    normalized_operation = operation.strip().lower()
    normalized_role = (role or get_key_role()).strip().lower()
    if normalized_role not in ALLOWED_ROLES:
        normalized_role = BOT

    if normalized_operation in TREASURY_ONLY_OPERATIONS and normalized_role == BOT:
        return TreasuryPolicyDecision(
            allowed=False,
            role=normalized_role,
            operation=normalized_operation,
            reason=(
                f"treasury_block: operation={normalized_operation} blocked for role={normalized_role}; "
                "set PT_KEY_ROLE=treasury only in dedicated treasury context"
            ),
            event_type="treasury_block",
        )

    return TreasuryPolicyDecision(
        allowed=True,
        role=normalized_role,
        operation=normalized_operation,
        reason=f"allowed: operation={normalized_operation} role={normalized_role}",
        event_type="treasury_allow",
    )


def enforce_treasury_policy(operation: str, role: str | None = None) -> TreasuryPolicyDecision:
    decision = evaluate_treasury_policy(operation=operation, role=role)
    if not decision.allowed:
        raise TreasurySeparationError(decision.reason)
    return decision
