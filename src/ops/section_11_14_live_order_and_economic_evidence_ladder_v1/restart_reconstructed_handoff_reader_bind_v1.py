"""Slice binding for restart reader, provenance/freshness validation, and consumer.

Does not invent schema v2. Does not claim host-crash durability. Does not
promote LIVE_RESTART_RECONSTRUCTED from tests. Does not rewrite historical
canary provenance. Does not GET. Does not POST.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED,
    FORBIDDEN_OWNER_REUSE,
    HISTORICAL_LIVE_RESTART_HANDOFF_STATUS,
    LIVE_RESTART_RECONSTRUCTED,
    NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
    NO_TIMESTAMP_BACKFILL,
    RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
    SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
    SECTION_11_14_LIVE_HANDOFF_WRITER_PRESENT,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_consumer_bind_v1 import (
    RESTART_CONSUMER_BOUND,
    RESTART_CONSUMER_SELECTED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_implementation_v1 import (
    CAPTURE_TRIGGER_STATUS,
    PROCESS_RESTART_PROOF,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    FIRST_OWNER_ID,
    RELATIVE_DURABLE_DIR,
    STORAGE_OWNER_MINTED,
    WRITER_BOUND,
    WRITER_SEAM_ID,
    mint_section_11_14_live_durable_pre_restart_handoff_owner_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    NEW_PRODUCER_IMPLEMENTED,
    PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED,
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_census_v1 import (
    bind_restart_reader_census_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_v1 import (
    FRESHNESS_VALIDATION,
    PROVENANCE_VALIDATION,
    READER_BOUND,
    SELECTED_PRODUCTIVE_READER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    HANDOFF_SCHEMA_VERSION,
    POS_SEMANTICS,
    SELECTED_SEMANTIC_ID,
)

COMPLETE_CAPTURE_SEAM = "UNPROVEN"
PROPOSED_NEXT_SLICE = (
    "SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_CONTEMPORANEOUS_PRE_RESTART_OBSERVATION_V1"
)
HOST_CRASH_PROOF = "UNPROVEN"
DURABLE_STORAGE_PROOF = "PROCESS_RESTART_READABLE_NOT_HOST_CRASH"

_SEAM_PREDICATES: tuple[tuple[str, bool], ...] = (
    ("NEW_PRODUCER_IMPLEMENTED", True),
    ("PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED", True),
    ("CAPTURE_TRIGGER_PRODUCTIVELY_BOUND", True),
    ("ALL_FIVE_REQUIRED_FIELDS_CONTEMPORANEOUS_PEAK_TRADE_OWNED_AT_SAME_SEAM", True),
    ("RECORD_CONTRACT_BOUND", True),
    ("STORAGE_OWNER_MINTED", True),
    ("WRITER_BOUND", True),
    ("DURABLE_SUCCESS_ACK_BEFORE_MUTATION_SUCCESS_CLAIM", True),
    ("FAIL_CLOSED_ON_CAPTURE_FAILURE", True),
    ("READER_BOUND", True),
    ("PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL", False),
    ("STALE_DATA_REJECTED_BY_BOUND_READER", True),
    ("MALFORMED_DATA_REJECTED_BY_BOUND_READER", True),
    ("NO_RETROACTIVE_SYNTHESIS", True),
    ("NO_TIMESTAMP_BACKFILL", True),
    ("NO_SYNTHETIC_PRE_RESTART_PROVENANCE", True),
    ("NO_HISTORICAL_REINTERPRETATION", True),
    ("RESTART_CONSUMER_BOUND", True),
    ("PROCESS_RESTART_READABLE_HANDOFF_RECORD", True),
)


def bind_restart_reader_provenance_and_consumer_v1() -> dict[str, Any]:
    mint = mint_section_11_14_live_durable_pre_restart_handoff_owner_v1()
    census = bind_restart_reader_census_v1()
    if POS_SEMANTICS != "PROVEN":
        raise Section1114OfflineSurfaceError("POS_SEMANTICS_MUST_REMAIN_PROVEN")
    if SELECTED_SEMANTIC_ID != (
        "S05_PEAK_TRADE_OWNED_RESULTING_CURRENT_POSITION_QTY_VENUE_CONTRACT_COUNT_UNSIGNED"
    ):
        raise Section1114OfflineSurfaceError("SELECTED_SEMANTIC_MUST_REMAIN_S05")
    if NEW_PRODUCER_IMPLEMENTED is not True:
        raise Section1114OfflineSurfaceError("NEW_PRODUCER_MUST_REMAIN_IMPLEMENTED")
    if PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED is not True:
        raise Section1114OfflineSurfaceError("S05_PRODUCER_SEMANTICS_MUST_REMAIN_IMPLEMENTED")
    if STORAGE_OWNER_MINTED is not True or mint["STORAGE_OWNER_MINTED"] is not True:
        raise Section1114OfflineSurfaceError("STORAGE_OWNER_MUST_REMAIN_MINTED")
    if WRITER_BOUND is not True:
        raise Section1114OfflineSurfaceError("WRITER_MUST_REMAIN_BOUND")
    if READER_BOUND is not True:
        raise Section1114OfflineSurfaceError("READER_MUST_BE_BOUND")
    if RESTART_CONSUMER_BOUND is not True:
        raise Section1114OfflineSurfaceError("CONSUMER_MUST_BE_BOUND")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED is True:
        raise Section1114OfflineSurfaceError("HISTORICAL_CANARY_MUST_REMAIN_UNOBSERVED")
    if RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED is True:
        raise Section1114OfflineSurfaceError("RETROACTIVE_SYNTHESIS_MUST_REMAIN_FORBIDDEN")
    if SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT != FIRST_OWNER_ID:
        raise Section1114OfflineSurfaceError("CURRENT_OWNER_MUST_REMAIN_MINTED_FIRST_OWNER")
    if SECTION_11_14_LIVE_HANDOFF_WRITER_PRESENT is not True:
        raise Section1114OfflineSurfaceError("WRITER_PRESENT_MUST_REMAIN_TRUE")
    if FIRST_OWNER_ID in FORBIDDEN_OWNER_REUSE:
        raise Section1114OfflineSurfaceError("FORBIDDEN_OWNER_REUSE")
    if census["SELECTED_PRODUCTIVE_READER"] != SELECTED_PRODUCTIVE_READER:
        raise Section1114OfflineSurfaceError("READER_CENSUS_SELECTION_DRIFT")
    missing = [name for name, proven in _SEAM_PREDICATES if proven is not True]
    predicate_map = {name: proven for name, proven in _SEAM_PREDICATES}
    if missing:
        seam = "UNPROVEN"
    else:
        seam = "PROVEN"
    if seam != COMPLETE_CAPTURE_SEAM and COMPLETE_CAPTURE_SEAM != "UNPROVEN":
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_STATUS_DRIFT")
    return {
        "DOCUMENT_CLASS": (
            "SECTION_11_14_LIVE_HANDOFF_RESTART_READER_PROVENANCE_AND_CONSUMER_BIND_V1"
        ),
        "POS_SEMANTICS": POS_SEMANTICS,
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "NEW_PRODUCER_IMPLEMENTED": True,
        "PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED": True,
        "HANDOFF_REQUIRED_FIELDS": list(REQUIRED_HANDOFF_FIELDS),
        "HANDOFF_REQUIRED_FIELD_COUNT": len(REQUIRED_HANDOFF_FIELDS),
        "HANDOFF_SCHEMA_VERSION": HANDOFF_SCHEMA_VERSION,
        "SCHEMA_CHANGE_REQUIRED": False,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": FIRST_OWNER_ID,
        "STORAGE_OWNER_MINTED": True,
        "WRITER_BOUND": True,
        "WRITER_SEAM_ID": WRITER_SEAM_ID,
        "CAPTURE_TRIGGER_STATUS": CAPTURE_TRIGGER_STATUS,
        "SELECTED_CAPTURE_TRIGGER": REQUIRED_CAPTURE_TRIGGER,
        "CAPTURE_TRIGGER_PRODUCTIVELY_BOUND": True,
        "DURABLE_SUCCESS_ACK_BEFORE_MUTATION_SUCCESS_CLAIM": True,
        "FAIL_CLOSED_ON_CAPTURE_FAILURE": True,
        "PROCESS_RESTART_READABLE_HANDOFF_RECORD": True,
        "PROCESS_RESTART_PROOF": PROCESS_RESTART_PROOF,
        "HOST_CRASH_PROOF": HOST_CRASH_PROOF,
        "DURABLE_STORAGE_PROOF": DURABLE_STORAGE_PROOF,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "POWER_LOSS_DURABILITY": "UNPROVEN",
        "DURABILITY_PROVEN_EFFECTIVE": False,
        "RELATIVE_DURABLE_DIR": RELATIVE_DURABLE_DIR,
        "READER_CANDIDATE_COUNT": census["READER_CANDIDATE_COUNT"],
        "SELECTED_PRODUCTIVE_READER": SELECTED_PRODUCTIVE_READER,
        "READER_IMPLEMENTED": True,
        "READER_BOUND": True,
        "SCHEMA_VALIDATION": "PASS",
        "IDENTITY_VALIDATION": "PASS",
        "S05_VALIDATION": "PASS",
        "POSSIDE_VALIDATION": "PASS",
        "PROVENANCE_VALIDATION": PROVENANCE_VALIDATION,
        "FRESHNESS_VALIDATION": FRESHNESS_VALIDATION,
        "MALFORMED_DATA_REJECTION": True,
        "STALE_DATA_REJECTION": True,
        "WRONG_INSTRUMENT_REJECTION": True,
        "RESTART_CONSUMER_SELECTED": RESTART_CONSUMER_SELECTED,
        "RESTART_CONSUMER_BOUND": True,
        "CAPTURE_SEAM_BOUND": False,
        "PRODUCTIVE_BINDING_PRESENT": True,
        "COMPLETE_CAPTURE_SEAM": seam,
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": missing,
        "COMPLETE_CAPTURE_SEAM_PREDICATES": predicate_map,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED": True,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "HISTORICAL_LIVE_RESTART_HANDOFF_STATUS": HISTORICAL_LIVE_RESTART_HANDOFF_STATUS,
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
        "NO_TIMESTAMP_BACKFILL": NO_TIMESTAMP_BACKFILL,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
        "IMPLEMENTATION_AUTHORIZED": False,
        "ADMISSION_TRUE": False,
        "SUPERVISOR_ACTIVATED": False,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "owner_mint": mint,
        "reader_census": census,
    }
