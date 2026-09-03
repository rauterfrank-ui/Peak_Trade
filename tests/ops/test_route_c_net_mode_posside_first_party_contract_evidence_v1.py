"""Route-C net-mode posSide first-party contract evidence census and adjudication tests."""

from __future__ import annotations

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_net_mode_posside_first_party_adjudicate_v1 import (
    adjudicate_route_c_net_mode_posside_first_party_contract_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_net_mode_posside_first_party_census_v1 import (
    FIRST_PARTY_EVIDENCE_RECORDS_V1,
    census_summary_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_net_mode_posside_first_party_contract_evidence_constants_v1 import (
    CANARY_SEMANTICS_TRANSFER_USED,
    EVIDENCE_EXHAUSTION_PROVEN,
    FIRST_PARTY_CONTRACT_EVIDENCE_SUFFICIENT,
    FIRST_PARTY_ROUTE_C_NET_MODE_POSSIDE_CONTRACT_FOUND,
    MISSING_EVIDENCE_EDGE,
    OWNER_GO,
    POSITION_MODE_FAIL_CLOSED,
    POSITION_MODE_SEMANTICS_UNPROVEN,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_constants_v1 import (
    POSITION_MODE_SUBMIT_BODY_SEMANTICS,
)


def test_census_has_fourteen_frozen_records() -> None:
    assert len(FIRST_PARTY_EVIDENCE_RECORDS_V1) == 14
    summary = census_summary_v1()
    assert summary["FIRST_PARTY_CANDIDATE_COUNT"] == 14
    assert summary["FIRST_PARTY_RELEVANT_EVIDENCE_COUNT"] == 13
    assert summary["UNADJUDICATED_RELEVANT_HIT_COUNT"] == 0
    assert summary["PROVEN_SUBMIT_BODY_SEMANTICS_COUNT"] == 0


def test_no_record_proves_route_c_submit_body_semantics() -> None:
    for record in FIRST_PARTY_EVIDENCE_RECORDS_V1:
        assert record.proves_submit_body_semantics is False
        assert record.transfer_to_route_c_proven is False


def test_leverage_info_pos_side_is_not_submit_body_proof() -> None:
    record = next(
        r for r in FIRST_PARTY_EVIDENCE_RECORDS_V1 if r.record_id == "LEVERAGE_INFO_POSSIDE_NET"
    )
    assert record.pos_side_value_if_present == "net"
    assert record.request_body_constructed is False
    assert record.path_kind == "LEVERAGE_GET"
    assert "not submit-body" in record.adjudication.lower()


def test_canary_omit_is_not_route_c_transfer() -> None:
    record = next(
        r for r in FIRST_PARTY_EVIDENCE_RECORDS_V1 if r.record_id == "CANARY_ENTRY_SUBMIT_OMIT"
    )
    assert record.omission_asserted is True
    assert record.path_kind == "CANARY_CREATE"
    assert (
        "not transfer" in record.adjudication.lower()
        or "separate path" in record.adjudication.lower()
    )


def test_adjudication_is_insufficient_fail_closed() -> None:
    result = adjudicate_route_c_net_mode_posside_first_party_contract_v1()
    assert result["OWNER_GO"] == OWNER_GO
    assert result["WORKPACKAGE_ID"] == WORKPACKAGE_ID
    assert result["THIS_SLICE"] == THIS_SLICE
    assert result["RESULT_CLASS"] == "FIRST_PARTY_CONTRACT_EVIDENCE_INSUFFICIENT_FAIL_CLOSED"
    assert (
        result["G_POSMODE_ADJUDICATION"] == "FIRST_PARTY_CONTRACT_EVIDENCE_INSUFFICIENT_FAIL_CLOSED"
    )
    assert result["FIRST_PARTY_CONTRACT_EVIDENCE_SUFFICIENT"] is False
    assert result["EVIDENCE_EXHAUSTION_PROVEN"] is True
    assert result["FIRST_PARTY_ROUTE_C_NET_MODE_POSSIDE_CONTRACT_FOUND"] is False
    assert result["POSITION_MODE_SUBMIT_BODY_SEMANTICS"] == POSITION_MODE_SEMANTICS_UNPROVEN
    assert result["POSITION_MODE_FAIL_CLOSED"] is POSITION_MODE_FAIL_CLOSED
    assert result["CANARY_SEMANTICS_TRANSFER_USED"] is CANARY_SEMANTICS_TRANSFER_USED
    assert result["MISSING_EVIDENCE_EDGE"] == MISSING_EVIDENCE_EDGE
    assert result["PROVEN_POSSIDE_RULE"] is None
    assert result["OPEN_CONTRADICTIONS"] == []


def test_standing_constants_remain_unproven() -> None:
    assert POSITION_MODE_SUBMIT_BODY_SEMANTICS == "UNPROVEN"
    assert EVIDENCE_EXHAUSTION_PROVEN is True
    assert FIRST_PARTY_CONTRACT_EVIDENCE_SUFFICIENT is False
    assert FIRST_PARTY_ROUTE_C_NET_MODE_POSSIDE_CONTRACT_FOUND is False
