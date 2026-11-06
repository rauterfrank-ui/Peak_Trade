"""Execute complete-capture-seam proof persist. No GET. No POST. No writer."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    LIVE_RESTART_RECONSTRUCTED,
    HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_OWNER_GO,
    HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_capture_seam_proof_v1 import (
    bind_capture_trigger_adjudication_v1,
    bind_complete_capture_seam_predicate_v1,
    bind_complete_capture_seam_proof_v1,
    bind_crash_boundary_v1,
    bind_failure_matrix_v1,
    bind_handoff_record_field_matrix_v1,
    bind_implementation_workpackage_v1,
    bind_s05_producer_recensus_v1,
    bind_storage_owner_census_v1,
    bind_test_plan_v1,
    bind_writer_reader_dataflow_v1,
)


def execute_live_handoff_complete_capture_seam_proof_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    if str(owner_go or "").strip() not in {HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_OWNER_GO}:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_contract_invariants_v1()
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or CANONICAL_EVIDENCE_RUN_ID)
    proof = bind_complete_capture_seam_proof_v1()
    predicate = bind_complete_capture_seam_predicate_v1()
    producer = bind_s05_producer_recensus_v1()
    trigger = bind_capture_trigger_adjudication_v1()
    record = bind_handoff_record_field_matrix_v1()
    storage = bind_storage_owner_census_v1()
    dataflow = bind_writer_reader_dataflow_v1()
    failures = bind_failure_matrix_v1()
    crash = bind_crash_boundary_v1()
    tests = bind_test_plan_v1()
    implementation = bind_implementation_workpackage_v1()
    adjudication = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={"source_kind": "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS"}
    )
    if adjudication.get("LIVE_RESTART_RECONSTRUCTED") is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if proof["COMPLETE_CAPTURE_SEAM"] != "UNPROVEN":
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    if proof["NEW_PRODUCER_IMPLEMENTED"] is True:
        raise Section1114OfflineSurfaceError("NEW_PRODUCER_MUST_REMAIN_UNIMPLEMENTED")
    if proof["STORAGE_OWNER_MINTED"] is True:
        raise Section1114OfflineSurfaceError("STORAGE_OWNER_MUST_REMAIN_UNMINTED")
    if proof["WRITER_BOUND"] is True or proof["READER_BOUND"] is True:
        raise Section1114OfflineSurfaceError("WRITER_READER_MUST_REMAIN_UNBOUND")
    if proof["IMPLEMENTATION_AUTHORIZED"] is True:
        raise Section1114OfflineSurfaceError("IMPLEMENTATION_MUST_REMAIN_UNAUTHORIZED")
    ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary = {
        "OWNER_GO": HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_OWNER_GO,
        "CANONICAL_EVIDENCE_RUN_ID": pack_run_id,
        "ORIGIN_MAIN_SHA": origin_main_sha,
        "STARTED_AT_UTC": started,
        "ENDED_AT_UTC": ended,
        "LIVE_ACCOUNTING_RECONSTRUCTED": True,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "LIVE_AUTONOMOUS_RECOVERY_OBSERVED": False,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
        "FIRST_OWNER_PRODUCTIVELY_BOUND": False,
        "POS_SEMANTICS": proof["POS_SEMANTICS"],
        "SELECTED_SEMANTIC_ID": proof["SELECTED_SEMANTIC_ID"],
        "PRODUCER_CANDIDATE_COUNT": proof["PRODUCER_CANDIDATE_COUNT"],
        "SELECTED_PRODUCTIVE_PRODUCER": proof["SELECTED_PRODUCTIVE_PRODUCER"],
        "NEW_PRODUCER_CONTRACT_DEFINED": True,
        "NEW_PRODUCER_IMPLEMENTED": False,
        "CAPTURE_TRIGGER_STATUS": proof["CAPTURE_TRIGGER_STATUS"],
        "SELECTED_CAPTURE_TRIGGER": proof["SELECTED_CAPTURE_TRIGGER"],
        "HANDOFF_RECORD_CONTRACT_STATUS": proof["HANDOFF_RECORD_CONTRACT_STATUS"],
        "HANDOFF_REQUIRED_FIELD_COUNT": proof["HANDOFF_REQUIRED_FIELD_COUNT"],
        "HANDOFF_CURRENTLY_PRODUCIBLE_FIELD_COUNT": proof[
            "HANDOFF_CURRENTLY_PRODUCIBLE_FIELD_COUNT"
        ],
        "STORAGE_OWNER_CANDIDATE_COUNT": proof["STORAGE_OWNER_CANDIDATE_COUNT"],
        "SELECTED_STORAGE_OWNER": proof["SELECTED_STORAGE_OWNER"],
        "STORAGE_OWNER_MINTED": False,
        "WRITER_BOUND": False,
        "READER_BOUND": False,
        "CAPTURE_SEAM_BOUND": False,
        "PRODUCTIVE_BINDING_PRESENT": False,
        "PROCESS_RESTART_PROOF": proof["PROCESS_RESTART_PROOF"],
        "HOST_CRASH_PROOF": proof["HOST_CRASH_PROOF"],
        "DURABLE_STORAGE_PROOF": proof["DURABLE_STORAGE_PROOF"],
        "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
        "COMPLETE_CAPTURE_SEAM_PROOF_STATUS": proof["COMPLETE_CAPTURE_SEAM_PROOF_STATUS"],
        "COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED": True,
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": proof[
            "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"
        ],
        "OWNER_MINT_CAN_NOW_BE_ADJUDICATED": False,
        "WRITER_BIND_CAN_NOW_BE_ADJUDICATED": False,
        "READER_BIND_CAN_NOW_BE_ADJUDICATED": False,
        "LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED": False,
        "HISTORICAL_DATA_REINTERPRETATION_ALLOWED": False,
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": False,
        "NO_TIMESTAMP_BACKFILL": True,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": True,
        "FAILURE_MATRIX_STATUS": proof["FAILURE_MATRIX_STATUS"],
        "TEST_PLAN_STATUS": proof["TEST_PLAN_STATUS"],
        "DEPENDENT_MUTATION_ALLOWED": False,
        "PRODUCTIVE_HOST_BINDING": False,
        "ADMISSION_TRUE": False,
        "SUPERVISOR_ACTIVATED": False,
        "IMPLEMENTATION_AUTHORIZED": False,
        "PROPOSED_NEXT_SLICE": proof["PROPOSED_NEXT_SLICE"],
        "PROPOSED_NEXT_IMPLEMENTATION_WORKPACKAGE": proof[
            "PROPOSED_NEXT_IMPLEMENTATION_WORKPACKAGE"
        ],
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
        "proof": proof,
        "predicate": predicate,
        "producer_recensus": producer,
        "capture_trigger": trigger,
        "handoff_record": record,
        "storage_owner": storage,
        "writer_reader_dataflow": dataflow,
        "failure_matrix": failures,
        "crash_boundary": crash,
        "test_plan": tests,
        "implementation_workpackage": implementation,
        "claims": dict(CLAIMS),
        "adjudication": adjudication,
        "raw_exchanges": [],
    }
