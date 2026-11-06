"""Complete-capture-seam proof tests for §11.14 Live handoff."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    OKX_ORDER_DATA_ENTRY_FIELDS_V1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    LIVE_RESTART_RECONSTRUCTED,
    HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_OWNER_GO,
    HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_capture_seam_proof_execute_v1 import (
    execute_live_handoff_complete_capture_seam_proof_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_capture_seam_proof_v1 import (
    COMPLETE_CAPTURE_SEAM,
    PROPOSED_NEXT_SLICE,
    SELECTED_CAPTURE_TRIGGER,
    bind_complete_capture_seam_predicate_v1,
    bind_complete_capture_seam_proof_v1,
    bind_failure_matrix_v1,
    bind_handoff_record_field_matrix_v1,
    bind_implementation_workpackage_v1,
    bind_s05_producer_recensus_v1,
    bind_storage_owner_census_v1,
    bind_writer_reader_dataflow_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    POS_SEMANTICS,
    SELECTED_SEMANTIC_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_required_field_contract_v1 import (
    POS_SEMANTICS as HISTORICAL_REQUIRED_FIELD_POS_SEMANTICS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_s05_is_proven_and_no_productive_producer_exists() -> None:
    recensus = bind_s05_producer_recensus_v1()
    assert POS_SEMANTICS == "PROVEN"
    assert recensus["SELECTED_SEMANTIC_ID"] == SELECTED_SEMANTIC_ID
    assert recensus["PRODUCER_CANDIDATE_COUNT"] == 18
    assert recensus["POS_ACCEPTABLE_PRODUCER_COUNT"] == 0
    assert recensus["POS_UNPROVEN_PRODUCER_COUNT"] == 0
    assert recensus["SELECTED_PRODUCTIVE_PRODUCER"] == "NONE"
    assert recensus["NEW_PRODUCER_IMPLEMENTED"] is False
    assert recensus["HISTORICAL_UNPROVEN_ACK_RETURN_NOW_REJECTED_AGAINST_S05"] is True
    assert "pos" not in OKX_ORDER_DATA_ENTRY_FIELDS_V1
    assert HISTORICAL_REQUIRED_FIELD_POS_SEMANTICS == "UNPROVEN"


def test_complete_capture_seam_remains_unproven_without_invention() -> None:
    proof = bind_complete_capture_seam_proof_v1()
    predicate = bind_complete_capture_seam_predicate_v1()
    assert proof["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert COMPLETE_CAPTURE_SEAM == "UNPROVEN"
    assert predicate["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert proof["CAPTURE_SEAM_BOUND"] is False
    assert proof["NEW_PRODUCER_IMPLEMENTED"] is False
    assert proof["STORAGE_OWNER_MINTED"] is False
    assert proof["WRITER_BOUND"] is False
    assert proof["READER_BOUND"] is False
    assert proof["PRODUCTIVE_BINDING_PRESENT"] is False
    assert proof["IMPLEMENTATION_AUTHORIZED"] is False
    missing = set(predicate["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"])
    assert "NEW_PRODUCER_IMPLEMENTED" in missing
    assert "WRITER_BOUND" in missing
    assert "STORAGE_OWNER_MINTED" in missing
    assert "READER_BOUND" in missing
    assert "POS_SEMANTICS_PROVEN" not in missing
    assert "RECORD_CONTRACT_BOUND" not in missing
    assert "NO_RETROACTIVE_SYNTHESIS" not in missing


def test_capture_trigger_and_record_and_storage_remain_unbound() -> None:
    proof = bind_complete_capture_seam_proof_v1()
    record = bind_handoff_record_field_matrix_v1()
    storage = bind_storage_owner_census_v1()
    dataflow = bind_writer_reader_dataflow_v1()
    assert proof["SELECTED_CAPTURE_TRIGGER"] == SELECTED_CAPTURE_TRIGGER
    assert proof["CAPTURE_TRIGGER_STATUS"] == ("REQUIRED_WINDOW_BOUND_PRODUCTIVE_TRIGGER_UNBOUND")
    assert record["HANDOFF_REQUIRED_FIELD_COUNT"] == 5
    assert record["HANDOFF_CURRENTLY_PRODUCIBLE_FIELD_COUNT"] == 3
    assert record["SCHEMA_CHANGE_REQUIRED"] is False
    assert storage["SELECTED_STORAGE_OWNER"] == "NONE"
    assert storage["EXISTING_COMPATIBLE_OWNER_COUNT"] == 0
    assert storage["PR_6317_6318_6319_DID_NOT_MINT_STORAGE_OWNER"] is True
    assert dataflow["PRODUCTIVE_PATH_PRODUCER_TO_RECORD_TO_STORAGE"] is False
    assert dataflow["CAPTURE_FAILURE_MUST_FAIL_CLOSED"] is True


def test_failure_matrix_and_implementation_remain_fail_closed() -> None:
    failures = bind_failure_matrix_v1()
    implementation = bind_implementation_workpackage_v1()
    assert failures["CASE_COUNT"] == 22
    case_ids = {row["CASE_ID"] for row in failures["rows"]}
    assert "restart_between_mutation_and_capture" in case_ids
    assert "missing_record" in case_ids
    missing = next(row for row in failures["rows"] if row["CASE_ID"] == "missing_record")
    assert missing["PROVEN_OR_UNPROVEN"] == "PROVEN"
    assert missing["FAIL_OPEN_OR_FAIL_CLOSED"] == "FAIL_CLOSED"
    assert implementation["IMPLEMENTATION_AUTHORIZED"] is False
    assert implementation["PROPOSED_NEXT_SLICE"] == PROPOSED_NEXT_SLICE
    assert "A_producer_implementation_S05" in implementation["PROPOSED_IMPLEMENTATION_SCOPE"]
    assert "H_reconstruction_consumer_LIVE_RESTART_RECONSTRUCTED" in implementation["OUT_OF_SCOPE"]


def test_execute_is_offline_and_does_not_authorize_implementation() -> None:
    result = execute_live_handoff_complete_capture_seam_proof_v1(
        owner_go=HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        repo_root=REPO_ROOT,
        run_id="20260907T001700Z-test",
    )
    summary = result["summary"]
    assert summary["WIRE_SEND"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["CREDENTIAL_USE"] is False
    assert summary["LIVE_RESTART_RECONSTRUCTED"] is False
    assert summary["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert summary["NEW_PRODUCER_IMPLEMENTED"] is False
    assert summary["STORAGE_OWNER_MINTED"] is False
    assert summary["WRITER_BOUND"] is False
    assert summary["READER_BOUND"] is False
    assert summary["IMPLEMENTATION_AUTHORIZED"] is False
    assert HISTORICAL_HANDOFF_OWNER_CURRENT_NONE == "NONE"
    assert LIVE_RESTART_RECONSTRUCTED is False
    live = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={"source_kind": "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS"}
    )
    assert live["LIVE_RESTART_RECONSTRUCTED"] is False
    assert result["raw_exchanges"] == []
