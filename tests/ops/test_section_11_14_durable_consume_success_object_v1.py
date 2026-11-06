"""Offline durable-consume success-object contract tests.

Hard-network-blocked. Mocked inner.send only. No real POST. No HMAC
generation. No receipt mint. No Owner Flatten-GO consume. No position
mutation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    AuthenticatedGatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.bounded_activation_permit_v1 import (
    offline_contract_proof_bounded_activation_permit_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
    FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
    FLATTEN_EXECUTE_PURPOSE_CANONICAL,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateInputV1,
    evaluate_flatten_pre_send_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    live_canary_http_request_from_flatten_receipt_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpRequestV1,
    LiveCanaryHttpResponseV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.durable_consume_success_object_v1 import (
    CLASSIFICATION_VENUE_SUCCESS,
    FlattenProductiveSendSuccessObjectError,
    FlattenProductiveSendSuccessObjectV1,
    consume_flatten_durable_on_success_object_v1,
    mint_flatten_productive_send_success_object_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.durable_consume_v1 import (
    FlattenDurableConsumeError,
    load_flatten_durable_consume_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_FX = FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL
OWNER_GO = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
ORIGIN_SHA = "287ed348d000bdda2ced929b1940284729b5c66e"
TARGET = DEFAULT_INSTRUMENT_ID
QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
ENVELOPE_ID = "0a0133a3b82e4a15bf6986605a9a8e6b47b22665b485ff0f570200803f21cdbe"
AUTHORITY_ID = "fixture-authority-durable-consume-success-object"
FIXTURE_HMAC_HEADERS = {
    "OK-ACCESS-KEY": "fixture-key",
    "OK-ACCESS-SIGN": "fixture-sign",
    "OK-ACCESS-TIMESTAMP": "2026-09-08T12:00:00.000Z",
    "OK-ACCESS-PASSPHRASE": "fixture-pass",
    "User-Agent": "PeakTrade-Section-11-13-5-LiveCanary/1",
}
URLLIB_PATCH = (
    "src.ops.section_11_13_5_live_canary_minimum_exposure_v1."
    "flatten_productive_transport_v1.open_productive_flatten_urllib_post_v1"
)
HMAC_SPEC = (
    REPO_ROOT / "docs/ops/specs/SECTION_11_14_RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER_V1.md"
)
SUCCESS_SPEC = REPO_ROOT / "docs/ops/specs/SECTION_11_14_DURABLE_CONSUME_SUCCESS_OBJECT_V1.md"
REAL_POST_COUNT = 0
WIRE_SEND_EXECUTED = False
POSITION_MUTATION = False


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_DURABLE_CONSUME_SUCCESS_OBJECT_TESTS")

    monkeypatch.setattr("urllib.request.urlopen", _blocked)
    monkeypatch.setattr("socket.create_connection", _blocked)


def _positions(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _pending(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _price() -> FlattenPriceInputV1:
    return FlattenPriceInputV1(
        flatten_side="SELL",
        observed_signed_pos="1",
        bid="64805.6",
        ask="64805.7",
        quote_timestamp_ms=QUOTE_TS,
        evaluation_timestamp_ms=EVAL_TS,
        tick_sz="0.1",
        freshness_threshold_ms=str(FRESHNESS_THRESHOLD_MS),
    )


def _valid_gate() -> FlattenPreSendGateInputV1:
    return FlattenPreSendGateInputV1(
        live_authorized=False,
        live_enabled=True,
        live_armed=True,
        flatten_live_wire_enabled=True,
        allow_productive_wire_send=True,
        flatten_execute_token=_FX,
        flatten_execute_purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        flatten_execute_owner_go=FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        pending_orders_payload=_pending(),
        price_input=_price(),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
        flatten_execute_bound_origin_main_sha=ORIGIN_SHA,
        instrument_id=TARGET,
        one_shot_no_retry=True,
        duplicate_post_protection=True,
        flatten_pre_send_decision_id="durable-consume-success-object-pre-send-1",
        position_observation_freshness_evidence=PositionObservationFreshnessEvidenceV1(
            response_received_monotonic_ms=0,
            decision_id="durable-consume-success-object-pre-send-1",
            evidence_kind=PRE_SEND_EVIDENCE_KIND,
        ),
        monotonic_ms_clock=(lambda: 0),
        bounded_activation_permit=offline_contract_proof_bounded_activation_permit_v1(
            origin_main_sha=ORIGIN_SHA,
            instrument_id=TARGET,
        ),
    )


def _passing_receipt():
    receipt = evaluate_flatten_pre_send_gate_v1(_valid_gate())
    assert receipt.allowed is True
    assert receipt.send_lease.consumed is False
    return receipt


def _success_body(receipt: Any, *, ord_id: str = "synthetic-flatten") -> bytes:
    sent_cl = str((receipt.request_body or {}).get("clOrdId") or "").strip()
    row: dict[str, str] = {"sCode": "0", "ordId": ord_id}
    if sent_cl:
        row["clOrdId"] = sent_cl
    return json.dumps({"code": "0", "data": [row]}, separators=(",", ":")).encode("utf-8")


def _response(
    request: LiveCanaryHttpRequestV1,
    *,
    status_code: int = 200,
    body: bytes | None = None,
    redirect_followed: bool = False,
) -> LiveCanaryHttpResponseV1:
    payload = (
        body
        if body is not None
        else (b'{"code":"0","data":[{"sCode":"0","ordId":"synthetic-flatten"}]}')
    )
    return LiveCanaryHttpResponseV1(
        status_code=status_code,
        body_bytes=payload,
        elapsed_seconds=0.01,
        endpoint=request.endpoint,
        method="POST",
        send_attempted=True,
        wire_body_sha256="ab",
        wire_body_byte_len=1,
        redirect_followed=redirect_followed,
    )


def _hmac_present_request(receipt) -> LiveCanaryHttpRequestV1:
    return live_canary_http_request_from_flatten_receipt_v1(
        receipt,
        headers=dict(FIXTURE_HMAC_HEADERS),
    )


def _mint(
    *,
    receipt=None,
    response=None,
    envelope_id: str = ENVELOPE_ID,
    origin_main_sha: str = ORIGIN_SHA,
    authority_id: str = AUTHORITY_ID,
    expected_envelope_id: str = ENVELOPE_ID,
    expected_origin_main_sha: str = ORIGIN_SHA,
    expected_authority_id: str = AUTHORITY_ID,
    expected_request_identity: str = "",
    transport_error: str | None = None,
) -> FlattenProductiveSendSuccessObjectV1:
    bound_receipt = receipt if receipt is not None else _passing_receipt()
    request = _hmac_present_request(bound_receipt)
    bound_response = (
        response if response is not None else _response(request, body=_success_body(bound_receipt))
    )
    expected_req = expected_request_identity or bound_receipt.approved_request_identity
    return mint_flatten_productive_send_success_object_v1(
        receipt=bound_receipt,
        response=bound_response,
        envelope_id=envelope_id,
        origin_main_sha=origin_main_sha,
        authority_id=authority_id,
        expected_envelope_id=expected_envelope_id,
        expected_origin_main_sha=expected_origin_main_sha,
        expected_authority_id=expected_authority_id,
        expected_request_identity=expected_req,
        transport_error=transport_error,
    )


def test_standing_live_flags_remain_false() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert CANARY_AUTHORIZED is False
    assert REAL_POST_COUNT == 0
    assert WIRE_SEND_EXECUTED is False
    assert POSITION_MUTATION is False


def test_valid_success_object_consume_exactly_once(tmp_path: Path) -> None:
    success = _mint()
    assert success.classification == CLASSIFICATION_VENUE_SUCCESS
    assert success.ord_id == "synthetic-flatten"
    record = consume_flatten_durable_on_success_object_v1(
        store_root=tmp_path,
        success=success,
        expected_envelope_id=ENVELOPE_ID,
        expected_origin_main_sha=ORIGIN_SHA,
        expected_authority_id=AUTHORITY_ID,
    )
    assert record["consumed"] is True
    assert record["durable_state"] == "COMPLETED"
    assert record["outcome"] == "VENUE_SUCCESS"
    loaded = load_flatten_durable_consume_v1(store_root=tmp_path)
    assert loaded["durable_consumed"] is True
    with pytest.raises(
        FlattenDurableConsumeError, match="DURABLE_CONSUME_ALREADY_PRESENT_NO_REWRITE"
    ):
        consume_flatten_durable_on_success_object_v1(
            store_root=tmp_path,
            success=success,
            expected_envelope_id=ENVELOPE_ID,
            expected_origin_main_sha=ORIGIN_SHA,
            expected_authority_id=AUTHORITY_ID,
        )
    assert REAL_POST_COUNT == 0
    assert WIRE_SEND_EXECUTED is False
    assert POSITION_MUTATION is False


def test_missing_receipt_does_not_consume(tmp_path: Path) -> None:
    receipt = _passing_receipt()
    request = _hmac_present_request(receipt)
    with pytest.raises(FlattenProductiveSendSuccessObjectError, match="RECEIPT_MISSING"):
        mint_flatten_productive_send_success_object_v1(
            receipt=None,
            response=_response(request),
            envelope_id=ENVELOPE_ID,
            origin_main_sha=ORIGIN_SHA,
            authority_id=AUTHORITY_ID,
        )
    assert load_flatten_durable_consume_v1(store_root=tmp_path)["durable_consumed"] is False


def test_transport_failure_does_not_consume(tmp_path: Path) -> None:
    receipt = _passing_receipt()
    request = _hmac_present_request(receipt)
    with pytest.raises(FlattenProductiveSendSuccessObjectError, match="TRANSPORT_FAILURE"):
        mint_flatten_productive_send_success_object_v1(
            receipt=receipt,
            response=_response(request),
            envelope_id=ENVELOPE_ID,
            origin_main_sha=ORIGIN_SHA,
            authority_id=AUTHORITY_ID,
            transport_error="PRODUCTIVE_FLATTEN_WIRE_ERROR:URLError",
        )
    assert load_flatten_durable_consume_v1(store_root=tmp_path)["durable_consumed"] is False


def test_venue_reject_does_not_consume(tmp_path: Path) -> None:
    receipt = _passing_receipt()
    request = _hmac_present_request(receipt)
    with pytest.raises(FlattenProductiveSendSuccessObjectError, match="VENUE_REJECT"):
        _mint(
            receipt=receipt,
            response=_response(
                request,
                body=b'{"code":"1","data":[{"sCode":"0","ordId":"x"}]}',
            ),
        )
    with pytest.raises(FlattenProductiveSendSuccessObjectError, match="VENUE_REJECT"):
        _mint(
            receipt=receipt,
            response=_response(
                request,
                body=b'{"code":"0","data":[{"sCode":"51000","ordId":"x"}]}',
            ),
        )
    assert load_flatten_durable_consume_v1(store_root=tmp_path)["durable_consumed"] is False


def test_malformed_success_payload_does_not_consume(tmp_path: Path) -> None:
    receipt = _passing_receipt()
    request = _hmac_present_request(receipt)
    with pytest.raises(FlattenProductiveSendSuccessObjectError, match="MALFORMED_SUCCESS_PAYLOAD"):
        _mint(receipt=receipt, response=_response(request, body=b"not-json"))
    with pytest.raises(FlattenProductiveSendSuccessObjectError, match="MALFORMED_SUCCESS_PAYLOAD"):
        _mint(receipt=receipt, response=_response(request, body=b'{"code":"0","data":[]}'))
    with pytest.raises(FlattenProductiveSendSuccessObjectError, match="HTTP_STATUS_NOT_200"):
        _mint(receipt=receipt, response=_response(request, status_code=500))
    with pytest.raises(FlattenProductiveSendSuccessObjectError, match="ORD_ID_MISSING"):
        _mint(
            receipt=receipt,
            response=_response(
                request,
                body=b'{"code":"0","data":[{"sCode":"0"}]}',
            ),
        )
    assert load_flatten_durable_consume_v1(store_root=tmp_path)["durable_consumed"] is False


def test_identity_mismatch_does_not_consume(tmp_path: Path) -> None:
    receipt = _passing_receipt()
    with pytest.raises(FlattenProductiveSendSuccessObjectError, match="ENVELOPE_IDENTITY_MISMATCH"):
        _mint(receipt=receipt, expected_envelope_id="deadbeef" * 8)
    with pytest.raises(FlattenProductiveSendSuccessObjectError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        _mint(receipt=receipt, expected_origin_main_sha="aa" * 20)
    with pytest.raises(
        FlattenProductiveSendSuccessObjectError, match="AUTHORITY_IDENTITY_MISMATCH"
    ):
        _mint(receipt=receipt, expected_authority_id="other-authority")
    with pytest.raises(FlattenProductiveSendSuccessObjectError, match="REQUEST_IDENTITY_MISMATCH"):
        _mint(receipt=receipt, expected_request_identity="0" * 64)
    request = _hmac_present_request(receipt)
    with pytest.raises(FlattenProductiveSendSuccessObjectError, match="CLORDID_IDENTITY_MISMATCH"):
        _mint(
            receipt=receipt,
            response=_response(
                request,
                body=b'{"code":"0","data":[{"sCode":"0","ordId":"x","clOrdId":"FOREIGN"}]}',
            ),
        )
    forged = FlattenProductiveSendSuccessObjectV1(
        envelope_id="foreign-envelope",
        origin_main_sha=ORIGIN_SHA,
        authority_id=AUTHORITY_ID,
        approved_request_identity=receipt.approved_request_identity,
        http_status=200,
        venue_code="0",
        venue_s_code="0",
        ord_id="synthetic-flatten",
        returned_cl_ord_id="",
        sent_cl_ord_id="",
    )
    with pytest.raises(FlattenProductiveSendSuccessObjectError, match="ENVELOPE_IDENTITY_MISMATCH"):
        consume_flatten_durable_on_success_object_v1(
            store_root=tmp_path,
            success=forged,
            expected_envelope_id=ENVELOPE_ID,
        )
    assert load_flatten_durable_consume_v1(store_root=tmp_path)["durable_consumed"] is False


def test_already_consumed_authority_fail_closed(tmp_path: Path) -> None:
    first = _mint()
    consume_flatten_durable_on_success_object_v1(
        store_root=tmp_path,
        success=first,
        expected_envelope_id=ENVELOPE_ID,
        expected_origin_main_sha=ORIGIN_SHA,
        expected_authority_id=AUTHORITY_ID,
    )
    replay = _mint()
    with pytest.raises(
        FlattenDurableConsumeError, match="DURABLE_CONSUME_ALREADY_PRESENT_NO_REWRITE"
    ):
        consume_flatten_durable_on_success_object_v1(
            store_root=tmp_path,
            success=replay,
            expected_envelope_id=ENVELOPE_ID,
            expected_origin_main_sha=ORIGIN_SHA,
            expected_authority_id=AUTHORITY_ID,
        )
    loaded = load_flatten_durable_consume_v1(store_root=tmp_path)
    assert loaded["reconstruction"]["resubmit_allowed"] is False


def test_mocked_inner_send_success_then_consume(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls = {"count": 0}

    def _fake_open(request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
        calls["count"] += 1
        return _response(request, body=_success_body(receipt))

    monkeypatch.setattr(URLLIB_PATCH, _fake_open)
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    transport.network_session_authorized = True
    receipt = _passing_receipt()
    transport.attach_pre_send_receipt(receipt)
    request = _hmac_present_request(receipt)
    response = transport.send(request)
    success = mint_flatten_productive_send_success_object_v1(
        receipt=receipt,
        response=response,
        envelope_id=ENVELOPE_ID,
        origin_main_sha=ORIGIN_SHA,
        authority_id=AUTHORITY_ID,
        expected_envelope_id=ENVELOPE_ID,
        expected_origin_main_sha=ORIGIN_SHA,
        expected_authority_id=AUTHORITY_ID,
        expected_request_identity=receipt.approved_request_identity,
    )
    consume_flatten_durable_on_success_object_v1(
        store_root=tmp_path,
        success=success,
        expected_envelope_id=ENVELOPE_ID,
        expected_origin_main_sha=ORIGIN_SHA,
        expected_authority_id=AUTHORITY_ID,
    )
    assert calls["count"] == 1
    assert load_flatten_durable_consume_v1(store_root=tmp_path)["durable_consumed"] is True
    assert REAL_POST_COUNT == 0
    assert WIRE_SEND_EXECUTED is False
    assert POSITION_MUTATION is False


def test_previous_receipt_hmac_gate_contract_unchanged() -> None:
    text = HMAC_SPEC.read_text(encoding="utf-8")
    assert "Q1_CANONICAL=YES" in text
    assert "Q2_CANONICAL=NO" in text
    assert "Q3_CANONICAL=INNER_REPAIR_REQUIRED" in text
    assert "INNER_REPAIR_IMPLEMENTED=true" in text
    assert "LEASE_CONSUME_AFTER_LOCAL_PREWIRE_GATES=true" in text
    assert "HMAC_GENERATION_WIRED=false" in text
    assert "RUNTIME_RECEIPT_MINT_EXECUTED=false" in text
    assert "POST_PERFORMED=false" in text
    assert "WIRE_SEND_EXECUTED=false" in text


def test_success_object_spec_non_execution() -> None:
    text = SUCCESS_SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_DURABLE_CONSUME_SUCCESS_OBJECT_V1" in text
    assert "DURABLE_CONSUME_SUCCESS_OBJECT=PROVEN" in text
    assert "POST_PERFORMED=false" in text
    assert "WIRE_SEND_EXECUTED=false" in text
    assert "REAL_POST_COUNT=0" in text
    assert "NEXT_OWNER_AUTHORITY_REQUIRED=RECEIPT_MISSING" in text
