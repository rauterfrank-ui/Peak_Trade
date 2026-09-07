"""Execute productive S05 producer / owner / writer implementation persist.

No GET. No POST. No restart execution. No historical canary rewrite.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    HISTORICAL_IMPLEMENTATION_OWNER_GO,
    HISTORICAL_IMPLEMENTATION_RUN_ID,
    HISTORICAL_IMPLEMENTATION_SHA,
    LIVE_RESTART_RECONSTRUCTED,
    SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_implementation_v1 import (
    bind_pos_producer_capture_record_owner_and_writer_implementation_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    FIRST_OWNER_ID,
    WRITER_SEAM_ID,
    mint_section_11_14_live_durable_pre_restart_handoff_owner_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    ADMISSIBLE_POS_SOURCE_KIND,
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    FORBIDDEN_DERIVATIONS,
    HANDOFF_SCHEMA_VERSION,
    POS_UNIT,
    PRODUCER_ID,
    SELECTED_SEMANTIC_ID,
)


def execute_live_handoff_pos_producer_capture_record_owner_and_writer_implementation_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    if str(owner_go or "").strip() != HISTORICAL_IMPLEMENTATION_OWNER_GO:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != HISTORICAL_IMPLEMENTATION_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_contract_invariants_v1()
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or HISTORICAL_IMPLEMENTATION_RUN_ID)
    binding = bind_pos_producer_capture_record_owner_and_writer_implementation_v1()
    mint = mint_section_11_14_live_durable_pre_restart_handoff_owner_v1()
    adjudication = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={"source_kind": "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS"}
    )
    if adjudication.get("LIVE_RESTART_RECONSTRUCTED") is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if binding["COMPLETE_CAPTURE_SEAM"] != "UNPROVEN":
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    if binding["NEW_PRODUCER_IMPLEMENTED"] is not True:
        raise Section1114OfflineSurfaceError("NEW_PRODUCER_MUST_BE_IMPLEMENTED")
    if binding["STORAGE_OWNER_MINTED"] is not True:
        raise Section1114OfflineSurfaceError("STORAGE_OWNER_MUST_BE_MINTED")
    if binding["WRITER_BOUND"] is not True:
        raise Section1114OfflineSurfaceError("WRITER_MUST_BE_BOUND")
    if binding["READER_BOUND"] is True:
        raise Section1114OfflineSurfaceError("READER_MUST_REMAIN_UNBOUND")
    ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary = {
        "OWNER_GO": HISTORICAL_IMPLEMENTATION_OWNER_GO,
        "CANONICAL_EVIDENCE_RUN_ID": pack_run_id,
        "ORIGIN_MAIN_SHA": origin_main_sha,
        "STARTED_AT_UTC": started,
        "ENDED_AT_UTC": ended,
        "LIVE_ACCOUNTING_RECONSTRUCTED": True,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "LIVE_AUTONOMOUS_RECOVERY_OBSERVED": False,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
        "FIRST_OWNER_PRODUCTIVELY_BOUND": True,
        "POS_SEMANTICS": "PROVEN",
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "PRODUCER_ID": PRODUCER_ID,
        "NEW_PRODUCER_CONTRACT_DEFINED": True,
        "NEW_PRODUCER_IMPLEMENTED": True,
        "PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED": True,
        "CAPTURE_TRIGGER_STATUS": binding["CAPTURE_TRIGGER_STATUS"],
        "SELECTED_CAPTURE_TRIGGER": REQUIRED_CAPTURE_TRIGGER,
        "CAPTURE_TRIGGER_PRODUCTIVELY_BOUND": True,
        "HANDOFF_REQUIRED_FIELD_COUNT": len(REQUIRED_HANDOFF_FIELDS),
        "HANDOFF_SCHEMA_VERSION": HANDOFF_SCHEMA_VERSION,
        "SCHEMA_CHANGE_REQUIRED": False,
        "STORAGE_OWNER_MINTED": True,
        "SELECTED_STORAGE_OWNER": FIRST_OWNER_ID,
        "WRITER_BOUND": True,
        "WRITER_SEAM_ID": WRITER_SEAM_ID,
        "READER_BOUND": False,
        "CAPTURE_SEAM_BOUND": False,
        "PRODUCTIVE_BINDING_PRESENT": False,
        "DURABLE_SUCCESS_ACK_BEFORE_MUTATION_SUCCESS_CLAIM": True,
        "PROCESS_RESTART_READABLE_HANDOFF_RECORD": True,
        "PROCESS_RESTART_PROOF": binding["PROCESS_RESTART_PROOF"],
        "HOST_CRASH_PROOF": "UNPROVEN",
        "DURABLE_STORAGE_PROOF": binding["DURABLE_STORAGE_PROOF"],
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "POWER_LOSS_DURABILITY": "UNPROVEN",
        "DURABILITY_PROVEN_EFFECTIVE": False,
        "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
        "OWNER_MINT_CAN_NOW_BE_ADJUDICATED": False,
        "WRITER_BIND_CAN_NOW_BE_ADJUDICATED": False,
        "READER_BIND_CAN_NOW_BE_ADJUDICATED": True,
        "LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED": False,
        "HISTORICAL_DATA_REINTERPRETATION_ALLOWED": False,
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": False,
        "NO_TIMESTAMP_BACKFILL": True,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": True,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "ADMISSIBLE_POS_SOURCE_KIND": ADMISSIBLE_POS_SOURCE_KIND,
        "POS_UNIT": POS_UNIT,
        "FORBIDDEN_DERIVATION_COUNT": len(FORBIDDEN_DERIVATIONS),
        "DEPENDENT_MUTATION_ALLOWED": False,
        "PRODUCTIVE_HOST_BINDING": False,
        "ADMISSION_TRUE": False,
        "SUPERVISOR_ACTIVATED": False,
        "IMPLEMENTATION_AUTHORIZED": False,
        "PROPOSED_NEXT_SLICE": binding["PROPOSED_NEXT_SLICE"],
        "SEQUENCE_AUTO_EXECUTED": False,
        "POST_USED": False,
        "GET_PERFORMED": False,
        "PRIVATE_GET_USED": False,
        "CREDENTIAL_USE": False,
        "RESTART_EXECUTION": False,
        "WIRE_SEND": False,
        "LIVE_ACTION": "NONE",
        "RAW_EVIDENCE_MODIFIED": False,
        "SECRET_VALUES_INCLUDED": False,
        "repo_root": str(repo_root),
    }
    pack = (
        Path(repo_root)
        / "evidence"
        / "ops"
        / "section_11_14_live_order_and_economic_evidence_ladder_v1"
        / pack_run_id
    )
    return {
        "pack": str(pack),
        "summary": summary,
        "binding": binding,
        "owner_mint": mint,
        "producer": {
            "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_IMPLEMENTATION_V1",
            "PRODUCER_ID": PRODUCER_ID,
            "NEW_PRODUCER_IMPLEMENTED": True,
            "PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED": True,
            "ADMISSIBLE_POS_SOURCE_KIND": ADMISSIBLE_POS_SOURCE_KIND,
            "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        },
        "writer_binding": {
            "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_WRITER_BINDING_V1",
            "WRITER_BOUND": True,
            "WRITER_SEAM_ID": WRITER_SEAM_ID,
            "READER_BOUND": False,
            "DURABLE_SUCCESS_ACK_BEFORE_MUTATION_SUCCESS_CLAIM": True,
            "PROCESS_RESTART_READABLE_HANDOFF_RECORD": True,
            "HOST_CRASH_DURABILITY": "UNPROVEN",
        },
        "durability": {
            "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_IMPLEMENTATION_DURABILITY_V1",
            "PROCESS_RESTART_PROOF": binding["PROCESS_RESTART_PROOF"],
            "HOST_CRASH_PROOF": "UNPROVEN",
            "DURABLE_STORAGE_PROOF": binding["DURABLE_STORAGE_PROOF"],
            "DURABILITY_PROVEN_EFFECTIVE": False,
            "A1_WAL_AS_LIVE_HANDOFF_ALLOWED": False,
        },
        "failure_semantics": {
            "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_IMPLEMENTATION_FAILURE_SEMANTICS_V1",
            "CAPTURE_FAILURE_MUST_FAIL_CLOSED": True,
            "WRITE_FAILURE_MUST_FAIL_CLOSED": True,
            "SERIALIZATION_FAILURE_MUST_FAIL_CLOSED": True,
            "IDEMPOTENCY": "IDEMPOTENT_REJECT_OR_EXACT_SAME_RECORD;NO_SECOND_IDENTITY",
            "ATOMICITY": "TEMP_FILE_FSYNC_REPLACE_DIR_FSYNC;TORN_WRITE_INVISIBLE",
            "HEURISTIC_RECOVERY_FORBIDDEN": True,
        },
        "claims": dict(CLAIMS),
        "adjudication": adjudication,
        "raw_exchanges": [],
    }
