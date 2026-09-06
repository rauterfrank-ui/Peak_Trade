"""Explicit refusal of every candidate derivation of handoff `pos`.

Authority does not equate submitted quantity with filled position, venue GET
with contemporaneous handoff, or accounting with restart handoff.
Does not write. Does not GET. Does not POST.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    ACCOUNTING_ONLY_IS_NOT_RESTART,
    A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
    NO_RECLASSIFICATION_OF_EVIDENCE_PACK_AS_CONTROL_HANDOFF,
    NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
    NO_TIMESTAMP_BACKFILL,
    RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
    VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_required_field_contract_v1 import (
    POS_SEMANTICS,
)

POS_DERIVATION_ALLOWED = "POS_DERIVATION_ALLOWED"
POS_DERIVATION_REJECTED = "POS_DERIVATION_REJECTED"
POS_DERIVATION_UNPROVEN = "POS_DERIVATION_UNPROVEN"

_DERIVATIONS: tuple[dict[str, Any], ...] = (
    {
        "ID": "A",
        "CLAIM": "pos = submitted order size",
        "DISPOSITION": POS_DERIVATION_REJECTED,
        "AUTHORITY": "submitted quantity != filled position; FILL_IS_NOT_POSITION_PROOF",
    },
    {
        "ID": "B",
        "CLAIM": "pos = signed submitted order size",
        "DISPOSITION": POS_DERIVATION_REJECTED,
        "AUTHORITY": "Signed sz is still submitted quantity. Authority does not equate them.",
    },
    {
        "ID": "C",
        "CLAIM": "pos = acknowledged order size",
        "DISPOSITION": POS_DERIVATION_REJECTED,
        "AUTHORITY": "ACK allowlist omits sz and pos. Acknowledged size is absent.",
    },
    {
        "ID": "D",
        "CLAIM": "pos = cumulative fill quantity",
        "DISPOSITION": POS_DERIVATION_REJECTED,
        "AUTHORITY": "FILL_IS_NOT_POSITION_PROOF; fill/fee observation is insufficient for restart.",
    },
    {
        "ID": "E",
        "CLAIM": "pos = fresh venue GET position",
        "DISPOSITION": POS_DERIVATION_REJECTED,
        "AUTHORITY": "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF",
    },
    {
        "ID": "F",
        "CLAIM": "pos = Peak_Trade accounting position",
        "DISPOSITION": POS_DERIVATION_REJECTED,
        "AUTHORITY": "ACCOUNTING_ONLY_IS_NOT_RESTART",
    },
    {
        "ID": "G",
        "CLAIM": "pos = reconciliation result",
        "DISPOSITION": POS_DERIVATION_REJECTED,
        "AUTHORITY": "POSITION_IS_NOT_RESTART_PROOF; LIVE_POSITION_RECONCILED is not this field.",
    },
    {
        "ID": "H",
        "CLAIM": "pos = order lifecycle state",
        "DISPOSITION": POS_DERIVATION_REJECTED,
        "AUTHORITY": "ORDER_STATE_IS_NOT_POSITION_PROOF",
    },
    {
        "ID": "I",
        "CLAIM": "pos = pre-existing position + fills",
        "DISPOSITION": POS_DERIVATION_REJECTED,
        "AUTHORITY": "Post-hoc arithmetic is POST_HOC_DERIVATION. Retroactive synthesis forbidden.",
    },
    {
        "ID": "J",
        "CLAIM": "pos = canary ACK return payload field",
        "DISPOSITION": POS_DERIVATION_UNPROVEN,
        "AUTHORITY": (
            "ACK return is partial identity only. pos is omitted. "
            "POS_SEMANTICS remains UNPROVEN rather than invented."
        ),
    },
)


def refuse_pos_derivation_v1(*, derivation_id: str) -> dict[str, Any]:
    match = next((row for row in _DERIVATIONS if row["ID"] == str(derivation_id).strip()), None)
    if match is None:
        raise Section1114OfflineSurfaceError("UNKNOWN_POS_DERIVATION_ID")
    if match["DISPOSITION"] == POS_DERIVATION_ALLOWED:
        raise Section1114OfflineSurfaceError("POS_DERIVATION_MUST_NOT_BE_ALLOWED")
    return {
        "DERIVATION_ID": match["ID"],
        "CLAIM": match["CLAIM"],
        "DISPOSITION": match["DISPOSITION"],
        "ALLOWED": False,
        "AUTHORITY": match["AUTHORITY"],
        "POS_SEMANTICS": POS_SEMANTICS,
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
        "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF": (
            VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF
        ),
        "ACCOUNTING_ONLY_IS_NOT_RESTART": ACCOUNTING_ONLY_IS_NOT_RESTART,
        "A1_WAL_AS_LIVE_HANDOFF_ALLOWED": A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
        "NO_RECLASSIFICATION_OF_EVIDENCE_PACK_AS_CONTROL_HANDOFF": (
            NO_RECLASSIFICATION_OF_EVIDENCE_PACK_AS_CONTROL_HANDOFF
        ),
        "NO_TIMESTAMP_BACKFILL": NO_TIMESTAMP_BACKFILL,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
    }


def refuse_ambiguous_pos_semantics_v1(*, claimed_semantics: str) -> dict[str, Any]:
    claimed = str(claimed_semantics or "").strip()
    if claimed and claimed != POS_SEMANTICS:
        raise Section1114OfflineSurfaceError("AMBIGUOUS_POS_SEMANTICS_NORMALIZATION_FORBIDDEN")
    return {
        "POS_SEMANTICS": POS_SEMANTICS,
        "CLAIMED_SEMANTICS": claimed or POS_SEMANTICS,
        "NORMALIZATION_FORBIDDEN": True,
        "ALLOWED": False,
    }


def bind_pos_derivation_adjudication_v1() -> dict[str, Any]:
    rows = [refuse_pos_derivation_v1(derivation_id=str(row["ID"])) for row in _DERIVATIONS]
    allowed = [row for row in rows if row["DISPOSITION"] == POS_DERIVATION_ALLOWED]
    if allowed:
        raise Section1114OfflineSurfaceError("POS_DERIVATION_MUST_NOT_BE_ALLOWED")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_POS_DERIVATION_ADJUDICATION_V1",
        "POS_SEMANTICS": POS_SEMANTICS,
        "ALLOWED_COUNT": 0,
        "REJECTED_COUNT": len(
            [row for row in rows if row["DISPOSITION"] == POS_DERIVATION_REJECTED]
        ),
        "UNPROVEN_COUNT": len(
            [row for row in rows if row["DISPOSITION"] == POS_DERIVATION_UNPROVEN]
        ),
        "rows": rows,
        "SUBMITTED_QUANTITY_IS_NOT_FILLED_POSITION": True,
        "VENUE_GET_IS_NOT_CONTEMPORANEOUS_HANDOFF": True,
        "ACCOUNTING_IS_NOT_RESTART_HANDOFF": True,
    }
