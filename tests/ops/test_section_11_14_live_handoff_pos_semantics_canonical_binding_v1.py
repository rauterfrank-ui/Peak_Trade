"""Pos-semantics canonical binding tests for §11.14 Live handoff pos."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    OKX_ORDER_DATA_ENTRY_FIELDS_V1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    LIVE_RESTART_RECONSTRUCTED,
    OWNER_GO,
    SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
    THIS_SLICE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_semantics_canonical_binding_execute_v1 import (
    execute_live_handoff_pos_semantics_canonical_binding_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_semantics_canonical_binding_v1 import (
    NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED,
    POS_SEMANTICS,
    POS_SEMANTICS_CAN_BE_BOUND_FROM_EXISTING_AUTHORITY,
    PROPOSED_NEXT_SLICE,
    bind_okx_pos_versus_handoff_pos_v1,
    bind_pos_downstream_effect_v1,
    bind_pos_semantics_canonical_binding_v1,
    bind_required_new_producer_contract_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_existing_authority_does_not_bind_unique_pos_semantics() -> None:
    binding = bind_pos_semantics_canonical_binding_v1()
    assert binding["POS_SEMANTICS"] == "UNPROVEN"
    assert binding["POS_SEMANTICS_STATUS"] == "UNPROVEN"
    assert binding["POS_CANONICAL_MEANING"] == "UNPROVEN"
    assert binding["POS_UNIT"] == "UNPROVEN"
    assert binding["POS_SIGN_SEMANTICS"] == "UNPROVEN"
    assert binding["POS_POS_SIDE_RELATION"] == "UNPROVEN"
    assert binding["POS_INSTRUMENT_BINDING"] == ("MUST_EQUAL_BOUND_INSTID;UNIT_DIMENSION_UNPROVEN")
    assert binding["POS_POSITION_MODE_BINDING"] == "UNPROVEN"
    assert binding["POS_ACCOUNT_MODE_BINDING"] == "UNPROVEN"
    assert binding["POS_SEMANTICS_CAN_BE_BOUND_FROM_EXISTING_AUTHORITY"] is False
    assert binding["NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED"] is True
    assert binding["POS_ACCEPTABLE_PRODUCER_COUNT"] == 0
    assert binding["POS_ACCEPTABLE_PRODUCERS"] == []
    assert binding["POS_UNPROVEN_PRODUCER_COUNT"] == 0
    assert binding["POS_UNPROVEN_PRODUCERS"] == []
    assert binding["POS_REJECTED_PRODUCER_COUNT"] == len(binding["candidates"])
    assert binding["NO_UNIQUE_CANONICAL_MEANING_FROM_AUTHORITY"] is True
    assert binding["TOKEN_NAME_IDENTITY_IS_NOT_SEMANTIC_IDENTITY"] is True
    assert POS_SEMANTICS == "UNPROVEN"
    assert POS_SEMANTICS_CAN_BE_BOUND_FROM_EXISTING_AUTHORITY is False
    assert NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED is True


def test_required_candidates_are_rejected_including_fresh_canary_payload() -> None:
    binding = bind_pos_semantics_canonical_binding_v1()
    ids = {row["CANDIDATE_ID"] for row in binding["candidates"]}
    required = {
        "C01_ORDER_PLAN_QTY",
        "C02_SUBMITTED_ORDER_SZ",
        "C03_ACKNOWLEDGED_SZ",
        "C04_FILL_SZ",
        "C05_ACCUMULATED_FILLS",
        "C06_OKX_POSITION_GET_POS",
        "C07_ACCOUNTING_POSITION",
        "C08_PRODUCTIVE_PORTFOLIO_POSITION",
        "C09_EXECUTION_LEDGER_DDO",
        "C10_LIVE_CANARY_RETURN_PAYLOAD",
        "C11_A1_WAL",
        "C12_FILEGATE",
        "C13_CAP72_SIDESTATE",
        "C14_TESTNET_DURABLE_STATE",
        "C15_EVIDENCE_PACK_VALUES",
        "C16_OFFLINE_CODEC_PLACEHOLDER",
        "C17_P08_HISTORICAL_CAPTURED_POS",
        "C18_EXECUTION_LEDGER_POSITION_MODEL",
        "C19_OWNER_BIND_FILLSZ_PLACEHOLDER",
        "C20_ABSENT_DURABLE_LIVE_WRITER",
        "C21_SIMULATED_EXECUTION_POSITION",
    }
    assert required <= ids
    for row in binding["candidates"]:
        assert row["ACCEPTABLE_FOR_HANDOFF_POS"] == "false"
        assert row["CANONICALLY_BOUND"] is False
        assert row["DISPOSITION"] == "POS_DERIVATION_REJECTED"
    canary = next(
        row
        for row in binding["candidates"]
        if row["CANDIDATE_ID"] == "C10_LIVE_CANARY_RETURN_PAYLOAD"
    )
    assert canary["DISPOSITION"] == "POS_DERIVATION_REJECTED"
    assert binding["LIVE_CANARY_RETURN_PAYLOAD_PRIOR_DISPOSITION"] == ("POS_DERIVATION_UNPROVEN")
    assert binding["PR_6317_REJECTIONS_NOT_BLINDLY_REUSED"] is True
    assert "pos" not in OKX_ORDER_DATA_ENTRY_FIELDS_V1
    assert binding["ACK_OMITS_POS"] is True


def test_okx_pos_is_not_handoff_pos() -> None:
    compared = bind_okx_pos_versus_handoff_pos_v1()
    venue = compared["VENUE_RESPONSE_FIELD"]
    assert venue["schema_field"] == "pos"
    assert venue["get_timing_contemporaneous_pre_restart"] is False
    assert venue["violates_handoff_distinct_from_accounting_venue_get"] is True
    assert venue["HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET"] is True
    assert compared["CONTEMPORANEOUS_PRODUCER_OF_HANDOFF_SEMANTICS"] == "NONE"
    assert compared["TOKEN_NAME_IDENTITY_IS_NOT_SEMANTIC_IDENTITY"] is True


def test_downstream_stays_fail_closed_while_pos_unproven() -> None:
    downstream = bind_pos_downstream_effect_v1()
    assert downstream["COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED"] is False
    assert downstream["OWNER_MINT_CAN_NOW_BE_ADJUDICATED"] is False
    assert downstream["WRITER_BIND_CAN_NOW_BE_ADJUDICATED"] is False
    assert downstream["READER_BIND_CAN_NOW_BE_ADJUDICATED"] is False
    assert downstream["LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED"] is False
    assert downstream["IMPLEMENTATION_AUTHORIZED"] is False
    producer = bind_required_new_producer_contract_v1()
    assert producer["IMPLEMENTATION_AUTHORIZED"] is False
    assert (
        "Emit the required Peak_Trade-owned contemporaneous"
        in (producer["REQUIRED_NEW_PRODUCER_RESPONSIBILITY"])
    )
    assert PROPOSED_NEXT_SLICE == (
        "SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_SEMANTICS_AND_CONTRACT_V1"
    )


def test_execute_is_offline_and_does_not_authorize_implementation() -> None:
    result = execute_live_handoff_pos_semantics_canonical_binding_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        repo_root=REPO_ROOT,
        run_id="20260906T221200Z-test",
    )
    summary = result["summary"]
    assert summary["WIRE_SEND"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["CREDENTIAL_USE"] is False
    assert summary["LIVE_RESTART_RECONSTRUCTED"] is False
    assert summary["POS_SEMANTICS"] == "UNPROVEN"
    assert summary["POS_SEMANTICS_CAN_BE_BOUND_FROM_EXISTING_AUTHORITY"] is False
    assert summary["NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED"] is True
    assert summary["POS_ACCEPTABLE_PRODUCER_COUNT"] == 0
    assert summary["IMPLEMENTATION_AUTHORIZED"] is False
    assert summary["ADMISSION_TRUE"] is False
    assert summary["SUPERVISOR_ACTIVATED"] is False
    assert summary["SEQUENCE_AUTO_EXECUTED"] is False
    assert summary["PROPOSED_NEXT_SLICE"] == PROPOSED_NEXT_SLICE
    assert result["raw_exchanges"] == []
    assert THIS_SLICE.endswith("POS_SEMANTICS_CANONICAL_BINDING")
    assert SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT == "NONE"
    assert LIVE_RESTART_RECONSTRUCTED is False
    adjudication = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={"source_kind": "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS"}
    )
    assert adjudication["LIVE_RESTART_RECONSTRUCTED"] is False
