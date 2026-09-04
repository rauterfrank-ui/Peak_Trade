"""SEND_TIME_PASS_18_19_21_24 offline evaluation tests. Offline only."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    GATE_NAMES,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    GatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.send_time_pass_18_19_21_24_v1 import (
    NAMED_REMAINING_AFTER_SEND_TIME_PASS,
    PASS_OFFLINE_CONTRACT,
    REASON_18_FLATTEN_FLOW_NOT_BOUND,
    REASON_18_OPEN_ORDER_CONFLICT,
    REASON_18_REDUCE_ONLY_REQUIRED,
    REASON_19_INSTRUMENT_MISMATCH,
    REASON_21_DUPLICATE_POST_REQUIRED,
    REASON_21_ONE_SHOT_REQUIRED,
    REASON_24_AUDIT_BOUNDARY_MISSING,
    REASON_24_HTTP_200_IMPLIES_SUCCESS,
    REASON_FLATTEN_EXECUTE,
    REASON_GET,
    REASON_IMPLEMENTATION_GO_AS_EXECUTE,
    REASON_LINEAGE_MISMATCH,
    REASON_LIVE_AUTHORIZED_SUBSTITUTE,
    REASON_MISSING_P25,
    REASON_MISSING_REMAINING,
    REASON_NETWORK_SESSION,
    REASON_P25_NOT_PASS,
    REASON_POST,
    REASON_PROVEN_AT_SEND_CLAIM,
    REASON_REMAINING_MISMATCH,
    REASON_RUNTIME_PERMIT,
    evaluate_send_time_pass_18_19_21_24_v1,
)
from src.ops.section_11_13_5_p25_execution_prerequisite_25_no_additional_owner_decision_v1.contract_v1 import (
    EXECUTION_PREREQUISITE_25_STATUS,
)
from src.ops.section_11_13_5_send_time_pass_18_19_21_24_v1.adjudicate_v1 import (
    SendTimePass182124AdjudicationError,
    adjudicate_send_time_pass_18_19_21_24_v1,
)
from src.ops.section_11_13_5_send_time_pass_18_19_21_24_v1.constants_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    GET_ALLOWED,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P25_CLOSED,
    POST_ALLOWED,
    PRIVATE_AUTH_USED,
    THIS_GO_GET_COUNT,
    THIS_SLICE,
)

TARGET = "SUI-USD_UM_XPERP-310404"


def _eval(**overrides: object) -> tuple[bool, tuple[str, ...]]:
    payload: dict[str, object] = {
        "p25_status": EXECUTION_PREREQUISITE_25_STATUS,
        "reduce_only": True,
        "flatten_flow_bound": True,
        "dedicated_flatten_transport": True,
        "open_order_conflict": False,
        "instrument_id": TARGET,
        "expected_instrument_id": TARGET,
        "duplicate_post_protection": True,
        "one_shot_no_retry": True,
        "audit_boundary_present": True,
        "http_200_implies_flatten_success": False,
        "claimed_remaining_after_send_time_pass": NAMED_REMAINING_AFTER_SEND_TIME_PASS,
        "proven_at_send_18": False,
        "proven_at_send_19": False,
        "proven_at_send_21": False,
        "proven_at_send_24": False,
        "live_authorized_claim": False,
        "runtime_permit_issuance_claim": False,
        "flatten_execute_authorized_claim": False,
        "network_session_authorized_claim": False,
        "post_performed_claim": False,
        "get_performed_claim": False,
        "flatten_execute_owner_go": None,
        "predecessor_lineage_ok": True,
    }
    payload.update(overrides)
    return evaluate_send_time_pass_18_19_21_24_v1(**payload)


def test_owner_go_is_forbidden_flatten_and_does_not_authorize_runtime() -> None:
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert POST_ALLOWED is False
    assert GET_ALLOWED is False
    assert PRIVATE_AUTH_USED is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert THIS_SLICE == "11.13.5.SEND_TIME_PASS"
    assert LAST_CANONICALLY_CLOSED_STEP == "SECTION_11_13_5_SEND_TIME_PASS_18_19_21_24"
    assert P25_CLOSED is True
    assert THIS_GO_GET_COUNT == 0
    assert EARLIEST_UNRESOLVED_DEPENDENCY == "AUTHENTICATED_PRODUCTIVE_TRANSPORT"
    assert NEXT_AUTHORITY_BOUNDARY == "SEPARATE_OWNER_GO_FOR_AUTHENTICATED_PRODUCTIVE_TRANSPORT"
    assert "SEND_TIME_PASS_18_19_21_24" in GATE_NAMES


def test_missing_unproven_mismatch_and_authority_claims_deny() -> None:
    missing_p25_ok, missing_p25 = _eval(p25_status=None)
    assert missing_p25_ok is False
    assert REASON_MISSING_P25 in missing_p25
    unproven_p25_ok, unproven_p25 = _eval(p25_status="UNPROVEN")
    assert unproven_p25_ok is False
    assert REASON_P25_NOT_PASS in unproven_p25
    missing_remaining_ok, missing_remaining = _eval(claimed_remaining_after_send_time_pass=None)
    assert missing_remaining_ok is False
    assert REASON_MISSING_REMAINING in missing_remaining
    mismatch_ok, mismatch = _eval(claimed_remaining_after_send_time_pass=("FLATTEN_EXECUTE",))
    assert mismatch_ok is False
    assert REASON_REMAINING_MISMATCH in mismatch
    flow_ok, flow_reasons = _eval(flatten_flow_bound=False)
    assert flow_ok is False
    assert REASON_18_FLATTEN_FLOW_NOT_BOUND in flow_reasons
    reduce_ok, reduce_reasons = _eval(reduce_only=False)
    assert reduce_ok is False
    assert REASON_18_REDUCE_ONLY_REQUIRED in reduce_reasons
    conflict_ok, conflict_reasons = _eval(open_order_conflict=True)
    assert conflict_ok is False
    assert REASON_18_OPEN_ORDER_CONFLICT in conflict_reasons
    inst_ok, inst_reasons = _eval(instrument_id="BTC-USD_UM_XPERP-000000")
    assert inst_ok is False
    assert REASON_19_INSTRUMENT_MISMATCH in inst_reasons
    dup_ok, dup_reasons = _eval(duplicate_post_protection=False)
    assert dup_ok is False
    assert REASON_21_DUPLICATE_POST_REQUIRED in dup_reasons
    shot_ok, shot_reasons = _eval(one_shot_no_retry=False)
    assert shot_ok is False
    assert REASON_21_ONE_SHOT_REQUIRED in shot_reasons
    audit_ok, audit_reasons = _eval(audit_boundary_present=False)
    assert audit_ok is False
    assert REASON_24_AUDIT_BOUNDARY_MISSING in audit_reasons
    http_ok, http_reasons = _eval(http_200_implies_flatten_success=True)
    assert http_ok is False
    assert REASON_24_HTTP_200_IMPLIES_SUCCESS in http_reasons
    proven_ok, proven_reasons = _eval(proven_at_send_18=True)
    assert proven_ok is False
    assert REASON_PROVEN_AT_SEND_CLAIM in proven_reasons
    live_ok, live_reasons = _eval(live_authorized_claim=True)
    assert live_ok is False
    assert REASON_LIVE_AUTHORIZED_SUBSTITUTE in live_reasons
    permit_ok, permit_reasons = _eval(runtime_permit_issuance_claim=True)
    assert permit_ok is False
    assert REASON_RUNTIME_PERMIT in permit_reasons
    flatten_ok, flatten_reasons = _eval(flatten_execute_authorized_claim=True)
    assert flatten_ok is False
    assert REASON_FLATTEN_EXECUTE in flatten_reasons
    network_ok, network_reasons = _eval(network_session_authorized_claim=True)
    assert network_ok is False
    assert REASON_NETWORK_SESSION in network_reasons
    post_ok, post_reasons = _eval(post_performed_claim=True)
    assert post_ok is False
    assert REASON_POST in post_reasons
    get_ok, get_reasons = _eval(get_performed_claim=True)
    assert get_ok is False
    assert REASON_GET in get_reasons
    go_ok, go_reasons = _eval(flatten_execute_owner_go=OWNER_GO)
    assert go_ok is False
    assert REASON_IMPLEMENTATION_GO_AS_EXECUTE in go_reasons
    lineage_ok, lineage_reasons = _eval(predecessor_lineage_ok=False)
    assert lineage_ok is False
    assert REASON_LINEAGE_MISMATCH in lineage_reasons


def test_matching_contract_passes_without_runtime_authority() -> None:
    ok, reasons = _eval()
    assert ok is True
    assert reasons == ()
    assert EXECUTION_PREREQUISITE_25_STATUS == PASS_OFFLINE_CONTRACT
    transport = GatedProductiveFlattenTransportV1()
    assert transport.network_session_authorized is False


def test_adjudicate_module_has_no_network_side_effect() -> None:
    import src.ops.section_11_13_5_send_time_pass_18_19_21_24_v1.adjudicate_v1 as adj

    text = Path(adj.__file__).read_text(encoding="utf-8")
    assert "urlopen" not in text
    assert "requests" not in text
    gate = Path(
        "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/send_time_pass_18_19_21_24_v1.py"
    ).read_text(encoding="utf-8")
    assert "urlopen" not in gate
    assert "requests" not in gate


def test_live_window_nonzero_advances_to_authenticated_productive_transport() -> None:
    result = adjudicate_prerequisite_08_window_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "1"}]}
    )
    assert result["EXECUTION_PREREQUISITE_12_STATUS"] == "PASS"
    assert result["EARLIEST_UNRESOLVED_DEPENDENCY"] == "BOUNDED_RUNTIME_PERMIT_ISSUANCE"
    assert result["EXECUTION_READY"] is False


def test_origin_main_mismatch_fails_closed() -> None:
    with pytest.raises(SendTimePass182124AdjudicationError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        adjudicate_send_time_pass_18_19_21_24_v1(origin_main_sha="deadbeef")


def test_adjudication_closes_named_send_time_pass_contract_without_runtime() -> None:
    verdict = adjudicate_send_time_pass_18_19_21_24_v1(origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA)
    assert verdict["CASE"] == "CASE_B_OFFLINE_CLOSABLE_CONTRACT"
    assert verdict["SEND_TIME_PASS_18_19_21_24"] == "PASS_OFFLINE_CONTRACT"
    assert verdict["PREREQUISITE_18_PROVEN_AT_SEND"] is False
    assert verdict["PREREQUISITE_19_PROVEN_AT_SEND"] is False
    assert verdict["PREREQUISITE_21_PROVEN_AT_SEND"] is False
    assert verdict["PREREQUISITE_24_PROVEN_AT_SEND"] is False
    assert verdict["STP_FLATTEN_EXECUTE_AUTHORIZED"] is False
    assert verdict["STP_NETWORK_SESSION_AUTHORIZED"] is False
    assert verdict["STRUCTURAL_ALLOW_IS_NOT_WIRE_SEND"] is True
    assert verdict["BOUNDED_RUNTIME_PERMIT_ISSUANCE"] is False
    assert verdict["POST_PERFORMED"] is False
