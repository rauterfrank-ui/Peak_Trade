"""AUTHENTICATED_PRODUCTIVE_TRANSPORT offline evaluation tests. Offline only."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_authenticated_productive_transport_v1.adjudicate_v1 import (
    AuthenticatedProductiveTransportAdjudicationError,
    adjudicate_authenticated_productive_transport_v1,
)
from src.ops.section_11_13_5_authenticated_productive_transport_v1.constants_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    GET_ALLOWED,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    POST_ALLOWED,
    PRIVATE_AUTH_USED,
    STP_CLOSED,
    THIS_GO_GET_COUNT,
    THIS_SLICE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    NAMED_REMAINING_AFTER_AUTHENTICATED_PRODUCTIVE_TRANSPORT,
    PRODUCTIVE_SIGNING_COMPONENT,
    REASON_CREDENTIAL_USE_CLAIM,
    REASON_DEDICATED_AUTH_TRANSPORT_REQUIRED,
    REASON_FLATTEN_EXECUTE,
    REASON_GET,
    REASON_HMAC_REORDERED_BEFORE_08,
    REASON_IMPLEMENTATION_GO_AS_EXECUTE,
    REASON_LINEAGE_MISMATCH,
    REASON_LIVE_AUTHORIZED_SUBSTITUTE,
    REASON_MISSING_REMAINING,
    REASON_MISSING_STP,
    REASON_NETWORK_PROVEN_CLAIM,
    REASON_NETWORK_SESSION,
    REASON_POST,
    REASON_POST_PROVEN_CLAIM,
    REASON_PRIVATE_GET_CLAIM,
    REASON_REMAINING_MISMATCH,
    REASON_RUNTIME_AUTH_CLAIM,
    REASON_RUNTIME_PERMIT,
    REASON_SIGNING_COMPONENT_MISMATCH,
    REASON_SIGNING_ONTOLOGY_INVENTED,
    REASON_STP_NOT_PASS,
    REASON_UNSIGNED_ACCEPTED,
    AuthenticatedGatedProductiveFlattenTransportV1,
    RecordingAuthenticatedProductiveFlattenTransportV1,
    assert_authenticated_productive_headers_v1,
    construct_okx_signing_input_v1,
    evaluate_authenticated_productive_transport_v1,
    sign_okx_signing_input_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_SUBMIT,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    REUSED_BINDING_REST_HOST,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    GATE_NAMES,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpRequestV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_send_time_pass_18_19_21_24_v1.contract_v1 import (
    SEND_TIME_PASS_18_19_21_24_STATUS,
)

TARGET = "SUI-USD_UM_XPERP-310404"
FIXTURE_TIMESTAMP = "2026-09-04T03:17:00.000Z"
FIXTURE_SECRET = "apt-offline-fixture-secret-not-a-credential"


def _eval(**overrides: object) -> tuple[bool, tuple[str, ...]]:
    payload: dict[str, object] = {
        "stp_status": SEND_TIME_PASS_18_19_21_24_STATUS,
        "dedicated_authenticated_transport": True,
        "signing_component": PRODUCTIVE_SIGNING_COMPONENT,
        "signing_ontology_invented": False,
        "hmac_handle_reordered_before_08": False,
        "unsigned_headers_accepted_as_authenticated": False,
        "claimed_remaining_after_authenticated_productive_transport": (
            NAMED_REMAINING_AFTER_AUTHENTICATED_PRODUCTIVE_TRANSPORT
        ),
        "runtime_authentication_proven_claim": False,
        "network_proven_claim": False,
        "credential_use_proven_claim": False,
        "private_get_proven_claim": False,
        "post_proven_claim": False,
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
    return evaluate_authenticated_productive_transport_v1(**payload)


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
    assert THIS_SLICE == "11.13.5.AUTHENTICATED_PRODUCTIVE_TRANSPORT"
    assert LAST_CANONICALLY_CLOSED_STEP == "SECTION_11_13_5_AUTHENTICATED_PRODUCTIVE_TRANSPORT"
    assert STP_CLOSED is True
    assert THIS_GO_GET_COUNT == 0
    assert EARLIEST_UNRESOLVED_DEPENDENCY == "SEND_TIME_POSITION_REOBSERVATION"
    assert NEXT_AUTHORITY_BOUNDARY == "SEPARATE_OWNER_GO_FOR_SEND_TIME_POSITION_REOBSERVATION"
    assert "AUTHENTICATED_PRODUCTIVE_TRANSPORT" in GATE_NAMES
    assert "SEND_TIME_PASS_18_19_21_24" in GATE_NAMES


def test_missing_unproven_mismatch_and_authority_claims_deny() -> None:
    missing_stp_ok, missing_stp = _eval(stp_status=None)
    assert missing_stp_ok is False
    assert REASON_MISSING_STP in missing_stp
    unproven_stp_ok, unproven_stp = _eval(stp_status="UNPROVEN")
    assert unproven_stp_ok is False
    assert REASON_STP_NOT_PASS in unproven_stp
    missing_remaining_ok, missing_remaining = _eval(
        claimed_remaining_after_authenticated_productive_transport=None
    )
    assert missing_remaining_ok is False
    assert REASON_MISSING_REMAINING in missing_remaining
    mismatch_ok, mismatch = _eval(
        claimed_remaining_after_authenticated_productive_transport=("FLATTEN_EXECUTE",)
    )
    assert mismatch_ok is False
    assert REASON_REMAINING_MISMATCH in mismatch
    transport_ok, transport_reasons = _eval(dedicated_authenticated_transport=False)
    assert transport_ok is False
    assert REASON_DEDICATED_AUTH_TRANSPORT_REQUIRED in transport_reasons
    signer_ok, signer_reasons = _eval(signing_component="invented-signer")
    assert signer_ok is False
    assert REASON_SIGNING_COMPONENT_MISMATCH in signer_reasons
    ontology_ok, ontology_reasons = _eval(signing_ontology_invented=True)
    assert ontology_ok is False
    assert REASON_SIGNING_ONTOLOGY_INVENTED in ontology_reasons
    reorder_ok, reorder_reasons = _eval(hmac_handle_reordered_before_08=True)
    assert reorder_ok is False
    assert REASON_HMAC_REORDERED_BEFORE_08 in reorder_reasons
    unsigned_ok, unsigned_reasons = _eval(unsigned_headers_accepted_as_authenticated=True)
    assert unsigned_ok is False
    assert REASON_UNSIGNED_ACCEPTED in unsigned_reasons
    runtime_ok, runtime_reasons = _eval(runtime_authentication_proven_claim=True)
    assert runtime_ok is False
    assert REASON_RUNTIME_AUTH_CLAIM in runtime_reasons
    network_proven_ok, network_proven_reasons = _eval(network_proven_claim=True)
    assert network_proven_ok is False
    assert REASON_NETWORK_PROVEN_CLAIM in network_proven_reasons
    cred_ok, cred_reasons = _eval(credential_use_proven_claim=True)
    assert cred_ok is False
    assert REASON_CREDENTIAL_USE_CLAIM in cred_reasons
    get_proven_ok, get_proven_reasons = _eval(private_get_proven_claim=True)
    assert get_proven_ok is False
    assert REASON_PRIVATE_GET_CLAIM in get_proven_reasons
    post_proven_ok, post_proven_reasons = _eval(post_proven_claim=True)
    assert post_proven_ok is False
    assert REASON_POST_PROVEN_CLAIM in post_proven_reasons
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
    assert SEND_TIME_PASS_18_19_21_24_STATUS == "PASS_OFFLINE_CONTRACT"
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    assert transport.network_session_authorized is False
    assert transport.signing_component == PRODUCTIVE_SIGNING_COMPONENT


def test_signing_input_is_deterministic_and_contains_no_secret() -> None:
    url = f"https://{REUSED_BINDING_REST_HOST}{ENDPOINT_SUBMIT}"
    body = '{"instId":"SUI-USD_UM_XPERP-310404","sz":"1"}'
    first = construct_okx_signing_input_v1(
        timestamp=FIXTURE_TIMESTAMP, method="POST", url=url, body=body
    )
    second = construct_okx_signing_input_v1(
        timestamp=FIXTURE_TIMESTAMP, method="POST", url=url, body=body
    )
    assert first.prehash == second.prehash
    assert FIXTURE_SECRET not in first.prehash
    assert first.body == body
    assert first.method == "POST"
    assert first.request_path == ENDPOINT_SUBMIT
    first_sign = sign_okx_signing_input_v1(secret=FIXTURE_SECRET, signing_input=first)
    second_sign = sign_okx_signing_input_v1(secret=FIXTURE_SECRET, signing_input=second)
    assert first_sign == second_sign
    assert FIXTURE_SECRET not in first_sign


def test_unsigned_headers_fail_closed_and_recording_transport_requires_hmac() -> None:
    with pytest.raises(Exception, match="UNSIGNED_PRODUCTIVE_HEADERS"):
        assert_authenticated_productive_headers_v1(
            {"User-Agent": "PeakTrade-Section-11-13-5-FlattenWiring/1"}
        )
    with pytest.raises(Exception, match="DEMO_SIMULATION_HEADER_FORBIDDEN"):
        assert_authenticated_productive_headers_v1(
            {
                "OK-ACCESS-KEY": "k",
                "OK-ACCESS-SIGN": "s",
                "OK-ACCESS-TIMESTAMP": FIXTURE_TIMESTAMP,
                "OK-ACCESS-PASSPHRASE": "p",
                "User-Agent": "PeakTrade-Section-11-13-5-LiveCanary/1",
                "x-simulated-trading": "1",
            }
        )
    headers = {
        "OK-ACCESS-KEY": "fixture-key",
        "OK-ACCESS-SIGN": "fixture-sign",
        "OK-ACCESS-TIMESTAMP": FIXTURE_TIMESTAMP,
        "OK-ACCESS-PASSPHRASE": "fixture-pass",
        "User-Agent": "PeakTrade-Section-11-13-5-LiveCanary/1",
    }
    assert_authenticated_productive_headers_v1(headers)
    recording = RecordingAuthenticatedProductiveFlattenTransportV1()
    assert recording.network_session_authorized is False
    unsigned = LiveCanaryHttpRequestV1(
        method="POST",
        url=f"https://{REUSED_BINDING_REST_HOST}{ENDPOINT_SUBMIT}",
        host=REUSED_BINDING_REST_HOST,
        endpoint=ENDPOINT_SUBMIT,
        headers={"User-Agent": "PeakTrade-Section-11-13-5-FlattenWiring/1"},
        timeout_seconds=1.0,
        body_text="{}",
    )
    with pytest.raises(Exception, match="RECEIPT_MISSING"):
        recording.send(unsigned)


def test_adjudicate_module_has_no_network_side_effect() -> None:
    import src.ops.section_11_13_5_authenticated_productive_transport_v1.adjudicate_v1 as adj

    text = Path(adj.__file__).read_text(encoding="utf-8")
    assert "urlopen" not in text
    assert "requests" not in text
    gate = Path(
        "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
        "authenticated_productive_transport_v1.py"
    ).read_text(encoding="utf-8")
    assert "urlopen" not in gate
    assert "requests" not in gate


def test_live_window_nonzero_advances_to_send_time_position_reobservation() -> None:
    result = adjudicate_prerequisite_08_window_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "1"}]}
    )
    assert result["EXECUTION_PREREQUISITE_12_STATUS"] == "PASS"
    assert result["EARLIEST_UNRESOLVED_DEPENDENCY"] == "AUTHENTICATED_PRIVATE_RUNTIME_READ"
    assert result["EXECUTION_READY"] is False


def test_origin_main_mismatch_fails_closed() -> None:
    with pytest.raises(
        AuthenticatedProductiveTransportAdjudicationError, match="ORIGIN_MAIN_SHA_MISMATCH"
    ):
        adjudicate_authenticated_productive_transport_v1(origin_main_sha="deadbeef")


def test_adjudication_closes_named_authenticated_transport_contract_without_runtime() -> None:
    verdict = adjudicate_authenticated_productive_transport_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA
    )
    assert verdict["CASE"] == "CASE_B_OFFLINE_CLOSABLE_CONTRACT"
    assert verdict["AUTHENTICATED_PRODUCTIVE_TRANSPORT"] == "PASS_OFFLINE_CONTRACT"
    assert verdict["AUTHENTICATED_PRODUCTIVE_TRANSPORT_RUNTIME_PROVEN"] is False
    assert verdict["AUTHENTICATION_PROVEN"] is False
    assert verdict["NETWORK_PROVEN"] is False
    assert verdict["CREDENTIAL_USE_PROVEN"] is False
    assert verdict["PRIVATE_GET_PROVEN"] is False
    assert verdict["POST_PROVEN"] is False
    assert verdict["APT_FLATTEN_EXECUTE_AUTHORIZED"] is False
    assert verdict["APT_NETWORK_SESSION_AUTHORIZED"] is False
    assert verdict["STRUCTURAL_ALLOW_IS_NOT_WIRE_SEND"] is True
    assert verdict["BOUNDED_RUNTIME_PERMIT_ISSUANCE"] is False
    assert verdict["POST_PERFORMED"] is False
