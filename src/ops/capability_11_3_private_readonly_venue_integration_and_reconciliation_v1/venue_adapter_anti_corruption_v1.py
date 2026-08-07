"""Venue adapter anti-corruption contract for private read-only Cap 11.3."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.adapter_anti_corruption_v1 import (
    prove_adapter_anti_corruption_v1 as prove_cap_11_1_adapter_anti_corruption_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.constants_v1 import (
    ERROR_TAXONOMY_EXPLICIT,
    MIN_SIZE_AND_NOTIONAL_VALIDATED,
    ORDER_TYPE_SUPPORT_EXPLICIT,
    OWNER,
    RATE_LIMIT_BUDGET_EXPLICIT,
    ROUNDING_AND_PRECISION_EXPLICIT,
    VENUE_ADAPTER_ALLOWED_RESPONSIBILITIES,
    VENUE_ADAPTER_ANTI_CORRUPTION_OWNER,
    VENUE_ADAPTER_DECISION_AUTHORITY,
    VENUE_ADAPTER_FORBIDDEN_AUTHORITIES,
    VENUE_NATIVE_EVENT_NORMALIZED,
)


class VenueAdapterAntiCorruptionError(ValueError):
    """Fail-closed venue adapter anti-corruption violation."""


def refuse_venue_adapter_decision_authority_v1(*, claimed_authority: str) -> dict[str, Any]:
    if claimed_authority in VENUE_ADAPTER_FORBIDDEN_AUTHORITIES:
        raise VenueAdapterAntiCorruptionError(
            f"VENUE_ADAPTER_AUTHORITY_FORBIDDEN:{claimed_authority}"
        )
    raise VenueAdapterAntiCorruptionError(f"VENUE_ADAPTER_AUTHORITY_UNKNOWN:{claimed_authority}")


def prove_venue_adapter_anti_corruption_v1() -> dict[str, Any]:
    predecessor = prove_cap_11_1_adapter_anti_corruption_v1()

    decision_blocked = False
    try:
        refuse_venue_adapter_decision_authority_v1(claimed_authority="decision")
    except VenueAdapterAntiCorruptionError as exc:
        decision_blocked = "VENUE_ADAPTER_AUTHORITY_FORBIDDEN" in str(exc)

    order_mutation_blocked = False
    try:
        refuse_venue_adapter_decision_authority_v1(claimed_authority="order_mutation")
    except VenueAdapterAntiCorruptionError as exc:
        order_mutation_blocked = "VENUE_ADAPTER_AUTHORITY_FORBIDDEN" in str(exc)

    ok = all(
        [
            predecessor.get("ok") is True,
            decision_blocked,
            order_mutation_blocked,
            VENUE_ADAPTER_DECISION_AUTHORITY is False,
            VENUE_NATIVE_EVENT_NORMALIZED is True,
            ROUNDING_AND_PRECISION_EXPLICIT is True,
            MIN_SIZE_AND_NOTIONAL_VALIDATED is True,
            ORDER_TYPE_SUPPORT_EXPLICIT is True,
            RATE_LIMIT_BUDGET_EXPLICIT is True,
            ERROR_TAXONOMY_EXPLICIT is True,
            "private_readonly_account_state_normalization"
            in VENUE_ADAPTER_ALLOWED_RESPONSIBILITIES,
            "order_mutation" in VENUE_ADAPTER_FORBIDDEN_AUTHORITIES,
        ]
    )
    return {
        "ok": ok,
        "VENUE_ADAPTER_DECISION_AUTHORITY": False,
        "VENUE_NATIVE_EVENT_NORMALIZED": True,
        "ROUNDING_AND_PRECISION_EXPLICIT": True,
        "MIN_SIZE_AND_NOTIONAL_VALIDATED": True,
        "ORDER_TYPE_SUPPORT_EXPLICIT": True,
        "RATE_LIMIT_BUDGET_EXPLICIT": True,
        "ERROR_TAXONOMY_EXPLICIT": True,
        "allowed_responsibilities": list(VENUE_ADAPTER_ALLOWED_RESPONSIBILITIES),
        "forbidden_authorities": list(VENUE_ADAPTER_FORBIDDEN_AUTHORITIES),
        "decision_authority_blocked": decision_blocked,
        "order_mutation_blocked": order_mutation_blocked,
        "predecessor_anti_corruption_ok": predecessor.get("ok") is True,
        "OWNER": VENUE_ADAPTER_ANTI_CORRUPTION_OWNER,
        "CAPABILITY_OWNER": OWNER,
    }
