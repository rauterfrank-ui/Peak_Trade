"""Execute productive capture-hook caller binding and offline call-path persist.

No GET. No POST. No restart execution. No productive hook execution as Live.
No productive handoff write during this persist. COMPLETE_CAPTURE_SEAM remains
UNPROVEN. LIVE_RESTART_RECONSTRUCTED remains false.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    LIVE_RESTART_RECONSTRUCTED,
    OWNER_GO,
    SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
    STRUCTURAL_RUNTIME_BINDING_PROVEN,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    FIRST_OWNER_ID,
    WRITER_SEAM_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    HANDOFF_SCHEMA_VERSION,
    SELECTED_SEMANTIC_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_productive_capture_hook_caller_binding_and_offline_call_path_proof_v1 import (
    CASE_ADJUDICATION,
    PRODUCTIVE_CALL_PATH_OFFLINE_PROOF,
    PRODUCTIVE_HOOK_CALLER,
    PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN,
    PRODUCTIVE_LIFECYCLE_EVENT,
    PROPOSED_NEXT_SLICE,
    PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL,
    bind_productive_capture_hook_caller_and_offline_call_path_v1,
)


def execute_live_handoff_productive_capture_hook_caller_binding_and_offline_call_path_proof_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    if str(owner_go or "").strip() != OWNER_GO:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_contract_invariants_v1()
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or CANONICAL_EVIDENCE_RUN_ID)
    adjudication = bind_productive_capture_hook_caller_and_offline_call_path_v1(repo_root=repo_root)
    if adjudication["COMPLETE_CAPTURE_SEAM"] != "UNPROVEN":
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    if adjudication["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_CAPTURE_MUST_NOT_BE_CLAIMED")
    if adjudication["LIVE_RESTART_RECONSTRUCTED"] is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if adjudication["PRODUCTIVE_HOOK_CALLER"] != PRODUCTIVE_HOOK_CALLER:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_HOOK_CALLER_DRIFT")
    if adjudication["PRODUCTIVE_CALL_PATH_OFFLINE_PROOF"] is not True:
        raise Section1114OfflineSurfaceError("OFFLINE_CALL_PATH_PROOF_MISSING")
    ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary = {
        "OWNER_GO": OWNER_GO,
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
        "NEW_PRODUCER_IMPLEMENTED": True,
        "STORAGE_OWNER_MINTED": True,
        "SELECTED_STORAGE_OWNER": FIRST_OWNER_ID,
        "WRITER_BOUND": True,
        "WRITER_SEAM_ID": WRITER_SEAM_ID,
        "READER_BOUND": True,
        "RESTART_CONSUMER_BOUND": True,
        "SELECTED_CAPTURE_TRIGGER": REQUIRED_CAPTURE_TRIGGER,
        "HANDOFF_REQUIRED_FIELD_COUNT": len(REQUIRED_HANDOFF_FIELDS),
        "HANDOFF_SCHEMA_VERSION": HANDOFF_SCHEMA_VERSION,
        "SCHEMA_CHANGE_REQUIRED": False,
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "PRODUCTIVE_HOOK_CALLER": PRODUCTIVE_HOOK_CALLER,
        "PRODUCTIVE_HOOK_CALLER_SYMBOL": PRODUCTIVE_HOOK_CALLER,
        "PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN": PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN,
        "PRODUCTIVE_LIFECYCLE_EVENT": PRODUCTIVE_LIFECYCLE_EVENT,
        "PRODUCTIVE_CALL_PATH_OFFLINE_PROOF": PRODUCTIVE_CALL_PATH_OFFLINE_PROOF,
        "STRUCTURAL_RUNTIME_BINDING_PROVEN": STRUCTURAL_RUNTIME_BINDING_PROVEN,
        "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
        "AUTHORIZED_RUNTIME_SURFACE": "NONE",
        "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
        "COMPLETE_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND": True,
        "REQUIRED_FIELD_PROVENANCE_MATRIX_BOUND": True,
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": list(
            adjudication["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"]
        ),
        "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": (
            PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL
        ),
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "PROVEN_COMPLETE_FIELD_COUNT": adjudication["PROVEN_COMPLETE_FIELD_COUNT"],
        "PROVEN_FAIL_CLOSED_FIELD_COUNT": adjudication["PROVEN_FAIL_CLOSED_FIELD_COUNT"],
        "PARTIAL_CAPTURE_ALLOWED": False,
        "RETROACTIVE_SYNTHESIS_ALLOWED": False,
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "OBSERVATION_STATUS": "PRODUCTIVE_HOOK_CALLER_BOUND_OFFLINE_NOT_LIVE_OBSERVED",
        "AUTHORIZED_NON_LIVE_RUNTIME_SURFACE_PRESENT": False,
        "PRODUCTIVE_CAPTURE_WRITE_EXECUTED": False,
        "HANDOFF_WRITTEN": False,
        "HISTORICAL_DATA_REINTERPRETATION_ALLOWED": False,
        "NO_TIMESTAMP_BACKFILL": True,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": True,
        "IMPLEMENTATION_AUTHORIZED": True,
        "ADMISSION_TRUE": False,
        "SUPERVISOR_ACTIVATED": False,
        "DEPENDENT_MUTATION_ALLOWED": False,
        "PRODUCTIVE_HOST_BINDING": False,
        "POST_USED": False,
        "GET_PERFORMED": False,
        "PRIVATE_GET_USED": False,
        "CREDENTIAL_USE": False,
        "SECRET_VALUES_INCLUDED": False,
        "RESTART_EXECUTION": False,
        "WIRE_SEND": False,
        "LIVE_ACTION": "NONE",
        "RAW_EVIDENCE_MODIFIED": False,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "repo_root": str(repo_root),
    }
    pack = (
        repo_root
        / "evidence"
        / "ops"
        / "section_11_14_live_order_and_economic_evidence_ladder_v1"
        / pack_run_id
    )
    return {
        "summary": summary,
        "caller_census": dict(adjudication["caller_census"]),
        "host_graph": dict(adjudication["host_graph"]),
        "dataflow": dict(adjudication["dataflow"]),
        "required_field_provenance_matrix": dict(adjudication["required_field_provenance_matrix"]),
        "seam_predicate": {
            "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
            "MISSING_PREDICATES": list(adjudication["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"]),
            "COMPLETE_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND": True,
            "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": False,
        },
        "baseline": {
            "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
            "ORIGIN_MAIN_SHA": origin_main_sha,
            "EXPECTED_ORIGIN_MAIN_MATCH": origin_main_sha == EXPECTED_ORIGIN_MAIN_SHA,
            "OWNER_GO": OWNER_GO,
            "CANONICAL_EVIDENCE_RUN_ID": pack_run_id,
        },
        "changed_path_census": {
            "SCOPE": (
                "SECTION_11_14_LIVE_HANDOFF_PRODUCTIVE_CAPTURE_HOOK_CALLER_BINDING_"
                "AND_OFFLINE_CALL_PATH_PROOF_V1"
            ),
            "UNTRACKED_FOREIGN_EVIDENCE_UNTOUCHED": True,
        },
        "safety": {
            "LIVE_ENABLED": False,
            "LIVE_ARMED": False,
            "CANARY_AUTHORIZED": False,
            "GET_PERFORMED": False,
            "POST_USED": False,
            "WIRE_SEND": False,
            "LIVE_ACTION": "NONE",
            "CREDENTIAL_USE": False,
            "IMPLEMENTATION_AUTHORIZED": True,
            "NEXT_SLICE_AUTHORIZED": False,
            "PRODUCTIVE_CAPTURE_WRITE_EXECUTED": False,
            "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
            "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
            "STRUCTURAL_RUNTIME_BINDING_PROVEN": True,
            "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
            "PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN": True,
            "PRODUCTIVE_CALL_PATH_OFFLINE_PROOF": True,
        },
        "claims": dict(CLAIMS),
        "adjudication": dict(adjudication),
        "pack": str(pack),
        "raw_exchanges": [],
    }
