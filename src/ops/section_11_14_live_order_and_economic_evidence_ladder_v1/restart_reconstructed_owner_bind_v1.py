"""Bind that the current §11.14 Live restart-handoff owner is NONE.

Does not mint a storage owner. Does not write productive handoff state.
Does not reuse A1 WAL, DDO ledger, venue GET packs, Testnet durable_state,
Phase 9.2 durable_state, Cap-7.2 SideState, FILEGATE, or venue OKX-EEA as
the Peak_Trade durable pre-restart handoff owner. A future owner may be
bound only by a separate explicit Owner-GO.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
    FORBIDDEN_OWNER_REUSE,
    FUTURE_HANDOFF_OWNER_REQUIRES_SEPARATE_EXPLICIT_OWNER_GO,
    HISTORICAL_HANDOFF_OWNER_BOUND,
    HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
    HISTORICAL_HANDOFF_PRODUCTIVE_BINDING,
    HISTORICAL_HANDOFF_READER_PRESENT,
    HISTORICAL_HANDOFF_WRITER_PRESENT,
)

FORBIDDEN_OWNER_REUSE_REASONS: dict[str, str] = {
    "DDO_DURABLE_EVIDENCE_STORAGE_OWNER": (
        "DDO durable evidence ledger is observation-only evidence storage. "
        "It is not Peak_Trade Live durable pre-restart handoff control-state."
    ),
    "MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER": (
        "A1 WAL / mutation-critical control-state storage is not a Live "
        "identity-bound pre-restart handoff owner."
    ),
    "SECTION_11_14_EVIDENCE_PACKS": (
        "§11.14 evidence packs are forensic ladder artifacts. They are not "
        "a contemporaneous Peak_Trade durable pre-restart handoff owner."
    ),
    "TESTNET_CAMPAIGN_DURABLE_STATE": ("Testnet campaign durable_state is not this Live field."),
    "PHASE_9_2_MD_DURABLE_STATE": ("Phase 9.2 market-data durable_state is not this Live field."),
    "CAP_72_SIDESTATE_PERSIST": (
        "Cap 7.2 SideState persist/restore is strategy lifecycle state, not "
        "a Live submit-identity pre-restart handoff."
    ),
    "FILEGATE_KILL_SWITCH": (
        "FILEGATE kill-switch persistence is safety-gate state, not a Live "
        "pre-restart handoff owner."
    ),
    "VENUE_OKX_EEA": (
        "VENUE_OKX_EEA remains authority over venue state. It is not owner of "
        "the required Peak_Trade durable pre-restart handoff."
    ),
}


def classify_forbidden_owner_reuse_v1(owner: str) -> dict[str, Any]:
    name = str(owner or "").strip()
    forbidden = name in FORBIDDEN_OWNER_REUSE
    return {
        "OWNER": name if name else "NONE",
        "FORBIDDEN_REUSE": forbidden,
        "ALLOWED_AS_SECTION_11_14_LIVE_HANDOFF_OWNER": False,
        "REASON": (
            FORBIDDEN_OWNER_REUSE_REASONS.get(name, "OWNER_IS_NOT_SECTION_11_14_LIVE_HANDOFF")
            if name and name != "NONE"
            else "CURRENT_OWNER_IS_NONE"
        ),
    }


def bind_section_11_14_live_handoff_owner_contract_v1() -> dict[str, Any]:
    forbidden_rows = [classify_forbidden_owner_reuse_v1(name) for name in FORBIDDEN_OWNER_REUSE]
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_OWNER_BIND_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT_OWNER_BIND_CONTRACT",
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_BOUND": HISTORICAL_HANDOFF_OWNER_BOUND,
        "SECTION_11_14_LIVE_HANDOFF_WRITER_PRESENT": HISTORICAL_HANDOFF_WRITER_PRESENT,
        "SECTION_11_14_LIVE_HANDOFF_READER_PRESENT": HISTORICAL_HANDOFF_READER_PRESENT,
        "SECTION_11_14_LIVE_HANDOFF_PRODUCTIVE_BINDING": (HISTORICAL_HANDOFF_PRODUCTIVE_BINDING),
        "FUTURE_HANDOFF_OWNER_REQUIRES_SEPARATE_EXPLICIT_OWNER_GO": (
            FUTURE_HANDOFF_OWNER_REQUIRES_SEPARATE_EXPLICIT_OWNER_GO
        ),
        "A1_WAL_AS_LIVE_HANDOFF_ALLOWED": A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
        "FORBIDDEN_OWNER_REUSE": list(FORBIDDEN_OWNER_REUSE),
        "FORBIDDEN_OWNER_REUSE_ROWS": forbidden_rows,
        "NEW_STORAGE_OWNER_CREATED": False,
        "NEW_HANDOFF_WRITER_CREATED": False,
        "PLACEHOLDER_WRITER_CREATED": False,
        "GENERIC_STORAGE_ABSTRACTION_LAYER_CREATED": False,
        "VENUE_OKX_EEA_IS_VENUE_STATE_AUTHORITY": True,
        "VENUE_OKX_EEA_IS_PEAK_TRADE_PRE_RESTART_HANDOFF_OWNER": False,
        "IMPLICIT_OWNER_REUSE_ALLOWED": False,
    }
