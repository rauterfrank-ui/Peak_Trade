"""Sole productive Live-execution path identity.

Canary / §11.13.5 / §11.14 remain historical venue-proof and lifecycle evidence.
They are not a second productive Live-execution authority.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY,
    CANARY_SUBMIT_EVIDENCE_IS_NOT_FULL_CORE_SUBMIT_EVIDENCE,
    CANARY_VENUE_PROOF_PATH_IS_FULL_CORE_E2E,
    CANARY_VENUE_PROOF_PATH_KIND,
    CANARY_VENUE_PROOF_PATH_ROLE,
    CURRENT_LIVE_CORE_PATH_PROVEN,
    DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED,
    FULL_CORE_SYSTEM_E2E_PROVEN,
    FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH,
    G12_IS_NOT_FULL_CORE_E2E,
    LIVE_ARMED,
    LIVE_ENABLED,
    PATH_KIND,
    PRODUCTIVE_LIVE_NEXT_POINTER_AUTHORITY,
    SECTION_11_13_5_NEXT_POINTER_DOMAIN,
    SECTION_11_14_ACCOUNTING_IS_NOT_FULL_CORE_E2E,
    SECTION_11_14_NEXT_POINTER_DOMAIN,
    SECTION_11_14_POST_IS_NOT_STEP_29Q,
    STANDING_LIVE_AUTHORIZATION,
    WIRE_SEND_PERMITTED,
)

PRODUCTIVE_LIVE_AUTHORITY_SECTIONS = frozenset({"SECTION_11_2_1", "11.2.1"})
EVIDENCE_ONLY_LIVE_POINTER_SECTIONS = frozenset(
    {
        "SECTION_11_13_5",
        "11.13.5",
        "SECTION_11_14",
        "11.14",
    }
)


def future_productive_live_execution_path_v1() -> str:
    return FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH


def productive_live_next_pointer_authority_v1() -> str:
    return PRODUCTIVE_LIVE_NEXT_POINTER_AUTHORITY


def section_is_productive_live_authority_v1(section: str | None) -> bool:
    token = str(section or "").strip()
    if token in PRODUCTIVE_LIVE_AUTHORITY_SECTIONS:
        return True
    if token.startswith("11.2.1") or token.startswith("SECTION_11_2_1"):
        return True
    return False


def refuse_competing_productive_live_next_pointer_v1(
    claimed_section: str | None,
) -> dict[str, Any]:
    """Refuse §11.13.5 / §11.14 as productive Live-next-pointer authority."""
    token = str(claimed_section or "").strip()
    evidence_only = (
        token in EVIDENCE_ONLY_LIVE_POINTER_SECTIONS
        or token.startswith("11.13.5")
        or token.startswith("11.14")
    )
    productive = section_is_productive_live_authority_v1(token)
    return {
        "claimed_section": token,
        "FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH": FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH,
        "PRODUCTIVE_LIVE_NEXT_POINTER_AUTHORITY": PRODUCTIVE_LIVE_NEXT_POINTER_AUTHORITY,
        "claimed_is_productive_live_authority": bool(productive and not evidence_only),
        "claimed_is_evidence_domain_only": bool(evidence_only),
        "refused_as_productive_live_next_pointer": bool(evidence_only),
        "CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY": (
            CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY
        ),
        "STANDING_LIVE_AUTHORIZATION": STANDING_LIVE_AUTHORIZATION,
    }


def bound_path_identity_v1() -> dict[str, Any]:
    return {
        "PATH_KIND": PATH_KIND,
        "FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH": FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH,
        "CANARY_VENUE_PROOF_PATH_KIND": CANARY_VENUE_PROOF_PATH_KIND,
        "CANARY_VENUE_PROOF_PATH_ROLE": CANARY_VENUE_PROOF_PATH_ROLE,
        "CANARY_VENUE_PROOF_PATH_IS_FULL_CORE_E2E": CANARY_VENUE_PROOF_PATH_IS_FULL_CORE_E2E,
        "CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY": (
            CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY
        ),
        "FULL_CORE_SYSTEM_E2E_PROVEN": FULL_CORE_SYSTEM_E2E_PROVEN,
        "CURRENT_LIVE_CORE_PATH_PROVEN": CURRENT_LIVE_CORE_PATH_PROVEN,
        "STANDING_LIVE_AUTHORIZATION": STANDING_LIVE_AUTHORIZATION,
        "PRODUCTIVE_LIVE_NEXT_POINTER_AUTHORITY": PRODUCTIVE_LIVE_NEXT_POINTER_AUTHORITY,
        "SECTION_11_13_5_NEXT_POINTER_DOMAIN": SECTION_11_13_5_NEXT_POINTER_DOMAIN,
        "SECTION_11_14_NEXT_POINTER_DOMAIN": SECTION_11_14_NEXT_POINTER_DOMAIN,
        "SECTION_11_14_POST_IS_NOT_STEP_29Q": SECTION_11_14_POST_IS_NOT_STEP_29Q,
        "SECTION_11_14_ACCOUNTING_IS_NOT_FULL_CORE_E2E": (
            SECTION_11_14_ACCOUNTING_IS_NOT_FULL_CORE_E2E
        ),
        "G12_IS_NOT_FULL_CORE_E2E": G12_IS_NOT_FULL_CORE_E2E,
        "CANARY_SUBMIT_EVIDENCE_IS_NOT_FULL_CORE_SUBMIT_EVIDENCE": (
            CANARY_SUBMIT_EVIDENCE_IS_NOT_FULL_CORE_SUBMIT_EVIDENCE
        ),
        "LIVE_ENABLED": LIVE_ENABLED,
        "LIVE_ARMED": LIVE_ARMED,
        "WIRE_SEND_PERMITTED": WIRE_SEND_PERMITTED,
        "DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED": DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED,
        "RUNTIME_AUTHORIZATION_EFFECT": "NONE",
    }


def refuse_historical_evidence_as_full_core_e2e_v1(
    claim: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = dict(claim or {})
    return {
        "admissible_as_full_core_e2e": False,
        "FULL_CORE_SYSTEM_E2E_PROVEN": FULL_CORE_SYSTEM_E2E_PROVEN,
        "CURRENT_LIVE_CORE_PATH_PROVEN": CURRENT_LIVE_CORE_PATH_PROVEN,
        "SECTION_11_14_POST_IS_NOT_STEP_29Q": SECTION_11_14_POST_IS_NOT_STEP_29Q,
        "SECTION_11_14_ACCOUNTING_IS_NOT_FULL_CORE_E2E": (
            SECTION_11_14_ACCOUNTING_IS_NOT_FULL_CORE_E2E
        ),
        "G12_IS_NOT_FULL_CORE_E2E": G12_IS_NOT_FULL_CORE_E2E,
        "CANARY_SUBMIT_EVIDENCE_IS_NOT_FULL_CORE_SUBMIT_EVIDENCE": (
            CANARY_SUBMIT_EVIDENCE_IS_NOT_FULL_CORE_SUBMIT_EVIDENCE
        ),
        "CANARY_VENUE_PROOF_PATH_IS_FULL_CORE_E2E": CANARY_VENUE_PROOF_PATH_IS_FULL_CORE_E2E,
        "claimed_keys": tuple(sorted(str(k) for k in payload.keys())),
    }
