"""P25 EXECUTION_PREREQUISITE_25 no-additional-owner-decision tests. Offline only."""

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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.no_additional_owner_decision_required_v1 import (
    NAMED_REMAINING_HIGHER_AUTHORITY_BOUNDARIES,
    PASS_OFFLINE_CONTRACT,
    REASON_ADDITIONAL_PRESENT,
    REASON_FLATTEN_EXECUTE,
    REASON_GET,
    REASON_IMPLEMENTATION_GO_AS_EXECUTE,
    REASON_INSTRUMENT_MISMATCH,
    REASON_LINEAGE_MISMATCH,
    REASON_LIVE_AUTHORIZED_SUBSTITUTE,
    REASON_MISSING_P16,
    REASON_MISSING_P20,
    REASON_MISSING_REMAINING,
    REASON_NETWORK_SESSION,
    REASON_P16_NOT_PASS,
    REASON_P20_NOT_PASS,
    REASON_POST,
    REASON_REMAINING_MISMATCH,
    REASON_RUNTIME_PERMIT,
    evaluate_no_additional_owner_decision_required_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_p16_execution_prerequisite_16_bounded_activation_v1.contract_v1 import (
    EXECUTION_PREREQUISITE_16_STATUS,
)
from src.ops.section_11_13_5_p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1.contract_v1 import (
    EXECUTION_PREREQUISITE_20_STATUS,
)
from src.ops.section_11_13_5_p25_execution_prerequisite_25_no_additional_owner_decision_v1.adjudicate_v1 import (
    P25NoAdditionalOwnerDecisionAdjudicationError,
    adjudicate_execution_prerequisite_25_no_additional_owner_decision_v1,
)
from src.ops.section_11_13_5_p25_execution_prerequisite_25_no_additional_owner_decision_v1.constants_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    GET_ALLOWED,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P20_CLOSED,
    POST_ALLOWED,
    PRIVATE_AUTH_USED,
    THIS_GO_GET_COUNT,
    THIS_SLICE,
)

TARGET = "SUI-USD_UM_XPERP-310404"


def _eval(**overrides: object) -> tuple[bool, tuple[str, ...]]:
    payload: dict[str, object] = {
        "p16_status": EXECUTION_PREREQUISITE_16_STATUS,
        "p20_status": EXECUTION_PREREQUISITE_20_STATUS,
        "additional_owner_decisions": (),
        "claimed_remaining_higher_authority": NAMED_REMAINING_HIGHER_AUTHORITY_BOUNDARIES,
        "live_authorized_claim": False,
        "runtime_permit_issuance_claim": False,
        "flatten_execute_authorized_claim": False,
        "network_session_authorized_claim": False,
        "post_performed_claim": False,
        "get_performed_claim": False,
        "flatten_execute_owner_go": None,
        "instrument_id": TARGET,
        "expected_instrument_id": TARGET,
        "predecessor_lineage_ok": True,
    }
    payload.update(overrides)
    return evaluate_no_additional_owner_decision_required_v1(**payload)


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
    assert THIS_SLICE == "11.13.5.P25"
    assert LAST_CANONICALLY_CLOSED_STEP == "SECTION_11_13_5_P25"
    assert P20_CLOSED is True
    assert THIS_GO_GET_COUNT == 0
    assert EARLIEST_UNRESOLVED_DEPENDENCY == "SEND_TIME_PASS_18_19_21_24"
    assert NEXT_AUTHORITY_BOUNDARY == "SEPARATE_OWNER_GO_FOR_SEND_TIME_PASS_18_19_21_24"
    assert "NO_ADDITIONAL_OWNER_DECISION_REQUIRED" in GATE_NAMES


def test_missing_unproven_additional_mismatch_and_authority_claims_deny() -> None:
    missing_p16_ok, missing_p16 = _eval(p16_status=None)
    assert missing_p16_ok is False
    assert REASON_MISSING_P16 in missing_p16
    unproven_p16_ok, unproven_p16 = _eval(p16_status="UNPROVEN")
    assert unproven_p16_ok is False
    assert REASON_P16_NOT_PASS in unproven_p16
    missing_p20_ok, missing_p20 = _eval(p20_status=None)
    assert missing_p20_ok is False
    assert REASON_MISSING_P20 in missing_p20
    unproven_p20_ok, unproven_p20 = _eval(p20_status="UNPROVEN")
    assert unproven_p20_ok is False
    assert REASON_P20_NOT_PASS in unproven_p20
    missing_remaining_ok, missing_remaining = _eval(claimed_remaining_higher_authority=None)
    assert missing_remaining_ok is False
    assert REASON_MISSING_REMAINING in missing_remaining
    additional_ok, additional = _eval(additional_owner_decisions=("INVENTED_OWNER_DECISION",))
    assert additional_ok is False
    assert REASON_ADDITIONAL_PRESENT in additional
    mismatch_ok, mismatch = _eval(claimed_remaining_higher_authority=("FLATTEN_EXECUTE",))
    assert mismatch_ok is False
    assert REASON_REMAINING_MISMATCH in mismatch
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
    inst_ok, inst_reasons = _eval(instrument_id="BTC-USD_UM_XPERP-000000")
    assert inst_ok is False
    assert REASON_INSTRUMENT_MISMATCH in inst_reasons
    lineage_ok, lineage_reasons = _eval(predecessor_lineage_ok=False)
    assert lineage_ok is False
    assert REASON_LINEAGE_MISMATCH in lineage_reasons


def test_matching_contract_passes_without_runtime_authority() -> None:
    ok, reasons = _eval()
    assert ok is True
    assert reasons == ()
    assert EXECUTION_PREREQUISITE_16_STATUS == PASS_OFFLINE_CONTRACT
    assert EXECUTION_PREREQUISITE_20_STATUS == PASS_OFFLINE_CONTRACT
    transport = GatedProductiveFlattenTransportV1()
    assert transport.network_session_authorized is False


def test_adjudicate_module_has_no_network_side_effect() -> None:
    import src.ops.section_11_13_5_p25_execution_prerequisite_25_no_additional_owner_decision_v1.adjudicate_v1 as adj

    text = Path(adj.__file__).read_text(encoding="utf-8")
    assert "urlopen" not in text
    assert "requests" not in text
    gate = Path(
        "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
        "no_additional_owner_decision_required_v1.py"
    ).read_text(encoding="utf-8")
    assert "urlopen" not in gate
    assert "requests" not in gate


def test_live_window_nonzero_advances_to_send_time_pass() -> None:
    result = adjudicate_prerequisite_08_window_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "1"}]}
    )
    assert result["EXECUTION_PREREQUISITE_12_STATUS"] == "PASS"
    assert result["EARLIEST_UNRESOLVED_DEPENDENCY"] == "BOUNDED_RUNTIME_PERMIT_ISSUANCE"
    assert result["EXECUTION_READY"] is False


def test_origin_main_mismatch_fails_closed() -> None:
    with pytest.raises(
        P25NoAdditionalOwnerDecisionAdjudicationError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        adjudicate_execution_prerequisite_25_no_additional_owner_decision_v1(
            origin_main_sha="deadbeef"
        )


def test_adjudication_closes_named_p25_contract_without_runtime() -> None:
    verdict = adjudicate_execution_prerequisite_25_no_additional_owner_decision_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA
    )
    assert verdict["CASE"] == "CASE_B_OFFLINE_CLOSABLE_CONTRACT"
    assert verdict["EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED"] == (
        "PASS_OFFLINE_CONTRACT"
    )
    assert verdict["PREREQUISITE_25_FLATTEN_EXECUTE_AUTHORIZED"] is False
    assert verdict["PREREQUISITE_25_NETWORK_SESSION_AUTHORIZED"] is False
    assert verdict["STRUCTURAL_ALLOW_IS_NOT_WIRE_SEND"] is True
    assert verdict["POST_PERFORMED"] is False
    assert verdict["BOUNDED_RUNTIME_PERMIT_ISSUANCE"] is False
    assert verdict["LIVE_EXECUTION"] is False
    assert verdict["ADDITIONAL_OWNER_DECISION_DENIES"] is True
    assert verdict["RUNTIME_PERMIT_CLAIM_DENIES"] is True
    assert verdict["EARLIEST_UNRESOLVED_DEPENDENCY"] == EARLIEST_UNRESOLVED_DEPENDENCY
    assert verdict["P25_DOES_NOT_ISSUE_RUNTIME_PERMIT"] is True
