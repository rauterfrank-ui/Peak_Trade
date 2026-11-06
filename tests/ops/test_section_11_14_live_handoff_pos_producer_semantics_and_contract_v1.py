"""Pos producer-semantics and contract tests for §11.14 Live handoff pos."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    OKX_ORDER_DATA_ENTRY_FIELDS_V1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    HISTORICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_OWNER_GO,
    LIVE_RESTART_RECONSTRUCTED,
    HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_execute_v1 import (
    execute_live_handoff_pos_producer_semantics_and_contract_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    FORBIDDEN_DERIVATIONS,
    NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED,
    POS_SEMANTICS,
    POS_SEMANTICS_CANONICALLY_BOUND,
    POS_UNIT,
    PRODUCER_ID,
    PROPOSED_NEXT_SLICE,
    SELECTED_SEMANTIC_ID,
    bind_handoff_schema_version_v1,
    bind_new_pos_producer_contract_v1,
    bind_pos_downstream_effect_after_producer_contract_v1,
    bind_pos_producer_semantics_and_contract_v1,
    bind_what_restart_reconstructs_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_semantics_canonical_binding_v1 import (
    POS_SEMANTICS as HISTORICAL_POS_SEMANTICS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_required_field_contract_v1 import (
    POS_SEMANTICS as HISTORICAL_REQUIRED_FIELD_POS_SEMANTICS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_unique_semantic_is_proven_with_explicit_unit_and_sign() -> None:
    binding = bind_pos_producer_semantics_and_contract_v1()
    assert binding["POS_SEMANTICS"] == "PROVEN"
    assert binding["POS_SEMANTICS_STATUS"] == "PROVEN"
    assert binding["POS_SEMANTICS_CANONICALLY_BOUND"] is True
    assert binding["SELECTED_SEMANTIC_UNIQUE"] is True
    assert binding["SELECTED_SEMANTIC_ID"] == SELECTED_SEMANTIC_ID
    assert binding["UNPROVEN_SEMANTIC_CANDIDATE_COUNT"] == 0
    assert binding["REJECTED_SEMANTIC_CANDIDATE_COUNT"] == 8
    assert binding["POS_UNIT"] == "VENUE_CONTRACT_COUNT_NUMBER_OF_CONTRACTS"
    assert binding["POS_SIGN_SEMANTICS"] == "UNSIGNED_MAGNITUDE"
    assert "NET_MODE_TOKEN_NOT_DIRECTION" in binding["POS_POS_SIDE_RELATION"]
    assert "net_mode" in binding["POS_POSITION_MODE_BINDING"]
    assert binding["POS_ACCOUNT_MODE_BINDING"].startswith("IRRELEVANT_FOR_HANDOFF_POS_QUANTITY")
    assert POS_SEMANTICS == "PROVEN"
    assert POS_SEMANTICS_CANONICALLY_BOUND is True
    assert POS_UNIT == "VENUE_CONTRACT_COUNT_NUMBER_OF_CONTRACTS"
    selected = [
        row for row in binding["meaning_candidates"] if row["DISPOSITION"] == "POS_MEANING_SELECTED"
    ]
    assert len(selected) == 1
    assert selected[0]["HANDOFF_SUITABLE"] == "true"


def test_prohibited_derivations_remain_rejected() -> None:
    binding = bind_pos_producer_semantics_and_contract_v1()
    rejected_ids = {
        row["SEMANTIC_ID"]
        for row in binding["meaning_candidates"]
        if row["DISPOSITION"] == "POS_MEANING_REJECTED"
    }
    required = {
        "S01_INTENDED_SUBMITTED_POSITION_QUANTITY",
        "S02_ACKNOWLEDGED_QUANTITY",
        "S03_EXECUTION_FILL_QUANTITY",
        "S04_CUMULATIVE_FILLED_QUANTITY",
        "S06_VENUE_RAW_ACCOUNTING_POSITION_QUANTITY",
        "S07_PEAK_TRADE_NORMALIZED_POSITION_QUANTITY",
        "S08_ECONOMIC_EXPOSURE_QUANTITY",
        "S09_RESTART_CONTROL_STATE_QUANTITY_AS_SEPARATE_KIND",
    }
    assert required <= rejected_ids
    producer = bind_new_pos_producer_contract_v1()
    forbidden = set(producer["PRODUCER_FORBIDDEN_DERIVATIONS"])
    assert "E_fresh_venue_GET" in forbidden
    assert "K_fillSz_copy" in forbidden
    assert "A_submitted_sz" in forbidden
    assert "timestamp_backfill" in forbidden
    assert "synthetic_pre_restart_provenance" in forbidden
    assert "pos" not in OKX_ORDER_DATA_ENTRY_FIELDS_V1
    assert HISTORICAL_POS_SEMANTICS == "UNPROVEN"
    assert HISTORICAL_REQUIRED_FIELD_POS_SEMANTICS == "UNPROVEN"
    assert binding["HISTORICAL_POS_SEMANTICS_NOT_REINTERPRETED"] is True
    assert binding["PRIOR_PRODUCER_REJECTIONS_NOT_OVERTURNED"] is True
    assert "E_fresh_venue_GET" in FORBIDDEN_DERIVATIONS


def test_producer_is_contract_only_and_downstream_stays_fail_closed() -> None:
    producer = bind_new_pos_producer_contract_v1()
    assert producer["PRODUCER_ID"] == PRODUCER_ID
    assert producer["PRODUCER_CONTRACT_COMPLETE"] is True
    assert producer["NEW_PRODUCER_IMPLEMENTED"] is False
    assert producer["IMPLEMENTATION_AUTHORIZED"] is False
    assert producer["FAIL_CLOSED"] is True
    assert producer["NON_RETROACTIVE"] is True
    downstream = bind_pos_downstream_effect_after_producer_contract_v1()
    assert downstream["COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED"] is True
    assert downstream["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert downstream["OWNER_MINT_CAN_NOW_BE_ADJUDICATED"] is False
    assert downstream["WRITER_BIND_CAN_NOW_BE_ADJUDICATED"] is False
    assert downstream["READER_BIND_CAN_NOW_BE_ADJUDICATED"] is False
    assert downstream["LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED"] is False
    assert downstream["IMPLEMENTATION_AUTHORIZED"] is False
    assert downstream["NEW_PRODUCER_IMPLEMENTED"] is False
    assert PROPOSED_NEXT_SLICE == ("SECTION_11_14_LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_PROOF_V1")
    schema = bind_handoff_schema_version_v1()
    assert schema["SCHEMA_CHANGE_REQUIRED"] is False
    assert schema["HISTORICAL_DATA_REINTERPRETATION_ALLOWED"] is False
    reconstructed = bind_what_restart_reconstructs_v1()
    assert reconstructed["RECONSTRUCTS_PEAK_TRADE_CONTROL_STATE"] is True
    assert reconstructed["RECONSTRUCTS_EXCHANGE_ACCOUNTING_STATE"] is False
    assert reconstructed["SINGLE_FIELD_POS_OVERLOAD_REQUIRED"] is False


def test_execute_is_offline_and_does_not_authorize_implementation() -> None:
    result = execute_live_handoff_pos_producer_semantics_and_contract_v1(
        owner_go=HISTORICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        repo_root=REPO_ROOT,
        run_id="20260906T224500Z-test",
    )
    summary = result["summary"]
    assert summary["WIRE_SEND"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["CREDENTIAL_USE"] is False
    assert summary["LIVE_RESTART_RECONSTRUCTED"] is False
    assert summary["POS_SEMANTICS"] == "PROVEN"
    assert summary["NEW_PRODUCER_IMPLEMENTED"] is False
    assert summary["IMPLEMENTATION_AUTHORIZED"] is False
    assert summary["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert summary["COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED"] is True
    assert HISTORICAL_HANDOFF_OWNER_CURRENT_NONE == "NONE"
    assert LIVE_RESTART_RECONSTRUCTED is False
    live = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={"source_kind": "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS"}
    )
    assert live["LIVE_RESTART_RECONSTRUCTED"] is False
    assert NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED is True
