"""Prove or refute contemporaneous pre-restart handoff observability.

Does not synthesize a handoff. Does not backfill timestamps. Does not GET.
Does not POST. Does not execute a restart. Does not write a productive
handoff record. Read-back uses the bound reader only. Consumption uses
the bound restart-reconstruction consumer only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED,
    LIVE_RESTART_RECONSTRUCTED,
    NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
    NO_TIMESTAMP_BACKFILL,
    RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
    SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_consumer_bind_v1 import (
    RESTART_CONSUMER_SELECTED,
    consume_validated_handoff_for_restart_reconstruction_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    FIRST_OWNER_ID,
    HANDOFF_FILENAME,
    RELATIVE_DURABLE_DIR,
    WRITER_SEAM_ID,
    durable_handoff_path_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_bind_v1 import (
    bind_restart_reader_provenance_and_consumer_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_v1 import (
    SELECTED_PRODUCTIVE_READER,
    read_validated_durable_pre_restart_handoff_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    CONTEMPORANEOUS_PROVENANCE_CLASS,
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    PRODUCER_ID,
    SELECTED_SEMANTIC_ID,
)

COMPLETE_CAPTURE_SEAM = "UNPROVEN"
PROPOSED_NEXT_SLICE = (
    "SECTION_11_14_LIVE_HANDOFF_FUTURE_AUTHORIZED_CONTEMPORANEOUS_CAPTURE_WINDOW_V1"
)
OBSERVATION_CASE = (
    "CASE_CONTEMPORANEOUS_PRE_RESTART_HANDOFF_OBSERVABILITY_REFUTED_NO_AUTHORIZED_NON_LIVE_SURFACE"
)
OBSERVATION_STATUS = "CLOSED_REFUTED"
MINIMUM_SAFE_OBSERVATION_CLASS = "READ_BACK_ONLY_NO_WRITE"
RESTART_BOUNDARY_ID = "PROCESS_OR_HOST_RESTART_AFTER_DURABLE_HANDOFF_COMMIT"
PROVENANCE_RECORD_FIELDS: tuple[str, ...] = (
    "owner_id",
    "claimed_owner",
    "provenance_class",
    "attempt_identity",
    "captured_at_utc",
    "written_at_utc",
)


def inventory_productive_pre_restart_capture_trigger_and_producer_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_PRODUCTIVE_PRE_RESTART_CAPTURE_TRIGGER_AND_PRODUCER_V1",
        "SELECTED_CAPTURE_TRIGGER": REQUIRED_CAPTURE_TRIGGER,
        "CAPTURE_TRIGGER_STATUS": "REQUIRED_WINDOW_BOUND_PRODUCTIVE_TRIGGER_BOUND",
        "CAPTURE_TRIGGER_PRODUCTIVELY_BOUND": True,
        "CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME": False,
        "PRODUCER_ID": PRODUCER_ID,
        "PRODUCER_SYMBOL": "emit_s05_handoff_pos_v1",
        "PRODUCER_PATH": (
            "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "restart_reconstructed_handoff_pos_producer_v1.py"
        ),
        "WRITER_SYMBOL": "commit_handoff_after_bound_fill_before_restart_v1",
        "WRITER_PATH": (
            "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "restart_reconstructed_handoff_owner_and_writer_v1.py"
        ),
        "WRITER_SEAM_ID": WRITER_SEAM_ID,
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "PRODUCTIVE_RUNTIME_CALLER_COUNT": 0,
        "TEST_ONLY_CALLER_COUNT": 2,
        "TEST_ONLY_CALLERS": (
            "tests/ops/test_section_11_14_live_handoff_pos_producer_capture_record_owner_and_writer_implementation_v1.py",
            "tests/ops/test_section_11_14_live_handoff_restart_reader_provenance_and_consumer_bind_v1.py",
        ),
        "AUTHORIZED_NON_LIVE_RUNTIME_SURFACE_PRESENT": False,
        "AUTHORIZED_NON_LIVE_RUNTIME_SURFACES": (),
        "CAP72_SIMULATED_MAY_SATISFY_LIVE_FIELD": False,
        "TESTNET_MAY_SATISFY_LIVE_FIELD": False,
        "TEST_TMP_PATH_MAY_SATISFY_LIVE_FIELD": False,
        "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED": (SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED),
    }


def inventory_durable_write_point_and_provenance_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_DURABLE_WRITE_POINT_AND_PROVENANCE_V1",
        "STORAGE_OWNER": FIRST_OWNER_ID,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
        "RELATIVE_DURABLE_DIR": RELATIVE_DURABLE_DIR,
        "HANDOFF_FILENAME": HANDOFF_FILENAME,
        "DURABLE_WRITE_SYMBOL": "commit_handoff_after_bound_fill_before_restart_v1::_atomic_replace_write",
        "REQUIRED_HANDOFF_FIELDS": list(REQUIRED_HANDOFF_FIELDS),
        "PROVENANCE_RECORD_FIELDS": list(PROVENANCE_RECORD_FIELDS),
        "REQUIRED_PROVENANCE_CLASS": CONTEMPORANEOUS_PROVENANCE_CLASS,
        "ENVELOPE_PROVENANCE_IS_CONTRACT_NOT_EMPIRICAL_OBSERVATION": True,
        "PRODUCTIVE_DURABLE_RECORD_PRESENT_IN_REPO": False,
    }


def bind_restart_boundary_for_contemporaneous_classification_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_RESTART_BOUNDARY_FOR_CONTEMPORANEOUS_CLASSIFICATION_V1",
        "RESTART_BOUNDARY_ID": RESTART_BOUNDARY_ID,
        "CAPTURE_WINDOW": REQUIRED_CAPTURE_TRIGGER,
        "REQUIRED_ORDER": (
            "bound fill identity exists "
            "THEN Peak_Trade-owned S05 resulting current position qty available "
            "THEN handoff record construction "
            "THEN durable write "
            "THEN durability success acknowledgement "
            "THEN process/host restart may occur"
        ),
        "RESTART_IS_CONSUMPTION_NOT_CAPTURE": True,
        "CAPTURE_MUST_PRECEDE_RESTART": True,
        "RESTART_ALREADY_OCCURRED_IS_RETROACTIVE_SYNTHESIS": True,
        "HISTORICAL_CANARY_FILL_WINDOW_UNPROVABLE_WITHOUT_CONTEMPORANEOUS_CAPTURE": True,
        "POST_HOC_ASSEMBLY_ACROSS_MOMENTS_IS_RETROACTIVE_SYNTHESIS": True,
    }


def bind_non_synthetic_observation_protocol_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_NON_SYNTHETIC_PRE_RESTART_OBSERVATION_PROTOCOL_V1",
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
        "HISTORICAL_DATA_REINTERPRETATION_ALLOWED": False,
        "TIMESTAMP_BACKFILL_ALLOWED": not NO_TIMESTAMP_BACKFILL,
        "SYNTHETIC_PRE_RESTART_PROVENANCE_ALLOWED": not NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
        "TEST_ROUNDTRIP_IS_NOT_CONTEMPORANEOUS_OBSERVATION": True,
        "VENUE_GET_COPY_FORBIDDEN": True,
        "FILL_SZ_COPY_FORBIDDEN": True,
        "EVIDENCE_PACK_RECLASSIFICATION_FORBIDDEN": True,
        "MINIMUM_SAFE_OBSERVATION_CLASS": MINIMUM_SAFE_OBSERVATION_CLASS,
        "PRODUCTIVE_WRITE_AUTHORIZED": False,
        "READ_BACK_READER": SELECTED_PRODUCTIVE_READER,
        "CONSUMER": RESTART_CONSUMER_SELECTED,
        "LIVE_ORDER_SUBMIT_AUTHORIZED": False,
        "WIRE_SEND_AUTHORIZED": False,
    }


def execute_minimum_safe_read_back_observation_v1(
    *,
    storage_root: Path,
) -> dict[str, Any]:
    trigger = inventory_productive_pre_restart_capture_trigger_and_producer_v1()
    if trigger["AUTHORIZED_NON_LIVE_RUNTIME_SURFACE_PRESENT"] is True:
        raise Section1114OfflineSurfaceError("UNAUTHORIZED_SURFACE_CLAIM")
    if trigger["PRODUCTIVE_RUNTIME_CALLER_COUNT"] != 0:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_RUNTIME_CALLER_MUST_REMAIN_ZERO")
    reader_result = read_validated_durable_pre_restart_handoff_v1(storage_root=storage_root)
    consumed = consume_validated_handoff_for_restart_reconstruction_v1(reader_result=reader_result)
    if reader_result.get("CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED") is True:
        raise Section1114OfflineSurfaceError("READER_MUST_NOT_INVENT_CONTEMPORANEOUS_OBSERVATION")
    if consumed.get("CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED") is True:
        raise Section1114OfflineSurfaceError("CONSUMER_MUST_NOT_INVENT_CONTEMPORANEOUS_OBSERVATION")
    if consumed.get("LIVE_RESTART_RECONSTRUCTED") is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_MINIMUM_SAFE_READ_BACK_OBSERVATION_V1",
        "MINIMUM_SAFE_OBSERVATION_CLASS": MINIMUM_SAFE_OBSERVATION_CLASS,
        "PRODUCTIVE_CAPTURE_WRITE_EXECUTED": False,
        "READ_BACK_EXECUTED": True,
        "STORAGE_ROOT": str(storage_root),
        "DURABLE_PATH": str(durable_handoff_path_v1(storage_root=storage_root)),
        "READER_RESULT": str(reader_result.get("RESULT") or ""),
        "READER_REASON": str(reader_result.get("REASON") or ""),
        "CONSUMER_ACCEPTED": bool(consumed.get("CONSUMER_ACCEPTED") is True),
        "CONSUMER_REASON": str(consumed.get("REASON") or ""),
        "reader_result": dict(reader_result),
        "consumed": dict(consumed),
    }


def bind_contemporaneous_pre_restart_observability_adjudication_v1(
    *,
    read_back: Mapping[str, Any],
) -> dict[str, Any]:
    binding = bind_restart_reader_provenance_and_consumer_v1()
    observed = dict(read_back or {})
    if CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED is True:
        raise Section1114OfflineSurfaceError("HISTORICAL_CANARY_MUST_REMAIN_UNOBSERVED")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED is True:
        raise Section1114OfflineSurfaceError("RETROACTIVE_SYNTHESIS_MUST_REMAIN_FORBIDDEN")
    if observed.get("PRODUCTIVE_CAPTURE_WRITE_EXECUTED") is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_WRITE_MUST_NOT_EXECUTE")
    if str(observed.get("READER_RESULT") or "") not in {"MISSING_HANDOFF", "VALID_HANDOFF"}:
        # Any other typed reader result still cannot promote contemporaneous Live observation.
        pass
    observed_flag = bool(
        observed.get("READER_RESULT") == "VALID_HANDOFF"
        and observed.get("CONSUMER_ACCEPTED") is True
        and CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED is True
    )
    if observed_flag is True:
        raise Section1114OfflineSurfaceError("CONTEMPORANEOUS_OBSERVATION_MUST_REMAIN_UNPROVEN")
    missing = list(binding["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"])
    if "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL" not in missing:
        raise Section1114OfflineSurfaceError("MISSING_CONTEMPORANEOUS_PREDICATE_DRIFT")
    seam = "UNPROVEN" if missing else "PROVEN"
    if seam != COMPLETE_CAPTURE_SEAM:
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    restart_adjudication = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={
            "source_kind": "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS",
            "POST_USED": False,
            "GET_PERFORMED": False,
            "census": {
                "DURABLE_PRE_RESTART_HANDOFF_PRESENT": False,
                "HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH": False,
                "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
                "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
            },
        }
    )
    if restart_adjudication.get("LIVE_RESTART_RECONSTRUCTED") is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    consumer_adjudication = dict(observed.get("consumed") or {}).get("adjudication")
    return {
        "DOCUMENT_CLASS": (
            "SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_CONTEMPORANEOUS_PRE_RESTART_OBSERVATION_V1"
        ),
        "OBSERVATION_STATUS": OBSERVATION_STATUS,
        "CASE_ADJUDICATION": OBSERVATION_CASE,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "COMPLETE_CAPTURE_SEAM": seam,
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": missing,
        "COMPLETE_CAPTURE_SEAM_PREDICATES": dict(binding["COMPLETE_CAPTURE_SEAM_PREDICATES"]),
        "LIVE_RESTART_RECONSTRUCTED": False,
        "LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED": True,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "PROVENANCE_VALIDATION": binding["PROVENANCE_VALIDATION"],
        "FRESHNESS_VALIDATION": binding["FRESHNESS_VALIDATION"],
        "READER_BOUND": True,
        "RESTART_CONSUMER_BOUND": True,
        "WRITER_BOUND": True,
        "NEW_PRODUCER_IMPLEMENTED": True,
        "POS_SEMANTICS": "PROVEN",
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": FIRST_OWNER_ID,
        "IMPLEMENTATION_AUTHORIZED": False,
        "ADMISSION_TRUE": False,
        "SUPERVISOR_ACTIVATED": False,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "reader_binding": binding,
        "restart_adjudication": restart_adjudication,
        "consumer_adjudication": consumer_adjudication,
    }
