"""Venue adapter anti-corruption contract for Testnet Cap 11.4 (§11.11)."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.adapter_anti_corruption_v1 import (
    prove_adapter_anti_corruption_v1 as prove_cap_11_1_adapter_anti_corruption_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.constants_v1 import (
    ERROR_TAXONOMY_EXPLICIT,
    MIN_SIZE_AND_NOTIONAL_VALIDATED,
    NATIVE_ORDER_SERIALIZATION_EXPLICIT,
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

    kill_switch_blocked = False
    try:
        refuse_venue_adapter_decision_authority_v1(claimed_authority="kill_switch_authority")
    except VenueAdapterAntiCorruptionError as exc:
        kill_switch_blocked = "VENUE_ADAPTER_AUTHORITY_FORBIDDEN" in str(exc)

    restart_blocked = False
    try:
        refuse_venue_adapter_decision_authority_v1(claimed_authority="restart_recovery_authority")
    except VenueAdapterAntiCorruptionError as exc:
        restart_blocked = "VENUE_ADAPTER_AUTHORITY_FORBIDDEN" in str(exc)

    ok = all(
        [
            predecessor.get("ok") is True,
            decision_blocked,
            kill_switch_blocked,
            restart_blocked,
            VENUE_ADAPTER_DECISION_AUTHORITY is False,
            VENUE_NATIVE_EVENT_NORMALIZED is True,
            ROUNDING_AND_PRECISION_EXPLICIT is True,
            MIN_SIZE_AND_NOTIONAL_VALIDATED is True,
            ORDER_TYPE_SUPPORT_EXPLICIT is True,
            RATE_LIMIT_BUDGET_EXPLICIT is True,
            ERROR_TAXONOMY_EXPLICIT is True,
            NATIVE_ORDER_SERIALIZATION_EXPLICIT is True,
            "native_order_serialization" in VENUE_ADAPTER_ALLOWED_RESPONSIBILITIES,
            "decision" in VENUE_ADAPTER_FORBIDDEN_AUTHORITIES,
            "kill_switch_authority" in VENUE_ADAPTER_FORBIDDEN_AUTHORITIES,
            "restart_recovery_authority" in VENUE_ADAPTER_FORBIDDEN_AUTHORITIES,
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
        "NATIVE_ORDER_SERIALIZATION_EXPLICIT": True,
        "allowed_responsibilities": list(VENUE_ADAPTER_ALLOWED_RESPONSIBILITIES),
        "forbidden_authorities": list(VENUE_ADAPTER_FORBIDDEN_AUTHORITIES),
        "decision_authority_blocked": decision_blocked,
        "kill_switch_authority_blocked": kill_switch_blocked,
        "restart_recovery_authority_blocked": restart_blocked,
        "predecessor_anti_corruption_ok": predecessor.get("ok") is True,
        "OWNER": VENUE_ADAPTER_ANTI_CORRUPTION_OWNER,
        "CAPABILITY_OWNER": OWNER,
    }
