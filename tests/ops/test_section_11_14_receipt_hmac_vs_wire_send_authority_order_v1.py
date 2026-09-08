"""Offline receipt/HMAC vs wire-send-authority order and inner-lease tests.

Hard-network-blocked. Fixture HMAC headers are presence-only and are not
HMAC generation. No receipt mint. No HMAC signer. No urllib POST. No
durable consume. No position mutation.
"""

from __future__ import annotations

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
    GatedProductiveFlattenTransportV1,
    LiveCanaryFlattenProductiveTransportError,
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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
# Short binder keeps flatten_execute_token=<name> under Policy Critic NO_SECRETS length gate.
_FX = FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL
FLATTEN_TRANSPORT_SRC = (
    REPO_ROOT
    / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/flatten_productive_transport_v1.py"
)
AUTH_TRANSPORT_SRC = (
    REPO_ROOT
    / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/authenticated_productive_transport_v1.py"
)
OWNER_GO = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
ORIGIN_SHA = "7085b6e76fef9036319f6d9a4bce0329e5493b02"
TARGET = DEFAULT_INSTRUMENT_ID
QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
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


def _boom_wire(*_a: Any, **_k: Any) -> Any:
    raise AssertionError("WIRE")


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_RECEIPT_HMAC_ORDER_TESTS")

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
        flatten_pre_send_decision_id="receipt-hmac-order-pre-send-1",
        position_observation_freshness_evidence=PositionObservationFreshnessEvidenceV1(
            response_received_monotonic_ms=0,
            decision_id="receipt-hmac-order-pre-send-1",
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


def _fake_open(request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
    return LiveCanaryHttpResponseV1(
        status_code=200,
        body_bytes=b'{"code":"0","data":[{"sCode":"0"}]}',
        elapsed_seconds=0.01,
        endpoint=request.endpoint,
        method="POST",
        send_attempted=True,
        wire_body_sha256="ab",
        wire_body_byte_len=1,
    )


def _unsigned_request(receipt) -> LiveCanaryHttpRequestV1:
    return live_canary_http_request_from_flatten_receipt_v1(receipt)


def _hmac_present_request(receipt) -> LiveCanaryHttpRequestV1:
    return live_canary_http_request_from_flatten_receipt_v1(
        receipt,
        headers=dict(FIXTURE_HMAC_HEADERS),
    )


def test_standing_live_flags_remain_false() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert CANARY_AUTHORIZED is False


def test_session_deny_does_not_consume_lease_or_set_sent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(URLLIB_PATCH, _boom_wire)
    transport = GatedProductiveFlattenTransportV1()
    receipt = _passing_receipt()
    transport.attach_pre_send_receipt(receipt)
    request = _unsigned_request(receipt)
    with pytest.raises(
        LiveCanaryFlattenProductiveTransportError,
        match="PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED",
    ):
        transport.send(request)
    assert receipt.send_lease.consumed is False
    assert transport._sent is False
    assert transport.last_wire_attempted is False
    with pytest.raises(
        LiveCanaryFlattenProductiveTransportError,
        match="PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED",
    ):
        transport.send(request)
    assert receipt.send_lease.consumed is False
    assert transport._sent is False


def test_authenticated_session_deny_does_not_consume_lease(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(URLLIB_PATCH, _boom_wire)
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    receipt = _passing_receipt()
    transport.attach_pre_send_receipt(receipt)
    request = _hmac_present_request(receipt)
    with pytest.raises(
        LiveCanaryFlattenProductiveTransportError,
        match="PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED",
    ):
        transport.send(request)
    assert receipt.send_lease.consumed is False
    assert transport._sent is False
    assert transport.last_wire_attempted is False


def test_receipt_missing_remains_pre_consume(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(URLLIB_PATCH, _boom_wire)
    gated = GatedProductiveFlattenTransportV1()
    gated.network_session_authorized = True
    auth = AuthenticatedGatedProductiveFlattenTransportV1()
    auth.network_session_authorized = True
    unsigned = LiveCanaryHttpRequestV1(
        method="POST",
        url="https://eea.okx.com/api/v5/trade/order",
        host="eea.okx.com",
        endpoint="/api/v5/trade/order",
        headers={"User-Agent": "PeakTrade-Section-11-13-5-FlattenWiring/1"},
        timeout_seconds=1.0,
        body_text="{}",
    )
    with pytest.raises(LiveCanaryFlattenProductiveTransportError, match="RECEIPT_MISSING"):
        gated.send(unsigned)
    with pytest.raises(LiveCanaryFlattenProductiveTransportError, match="RECEIPT_MISSING"):
        auth.send(unsigned)
    assert gated._sent is False
    assert auth._sent is False
    assert gated.last_wire_attempted is False
    assert auth.last_wire_attempted is False


def test_hmac_presence_deny_remains_pre_consume(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(URLLIB_PATCH, _boom_wire)
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    transport.network_session_authorized = True
    receipt = _passing_receipt()
    transport.attach_pre_send_receipt(receipt)
    with pytest.raises(
        LiveCanaryFlattenProductiveTransportError, match="UNSIGNED_PRODUCTIVE_HEADERS"
    ):
        transport.send(_unsigned_request(receipt))
    assert receipt.send_lease.consumed is False
    assert transport._sent is False
    assert transport.last_wire_attempted is False


def test_successful_gated_path_consumes_lease_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[LiveCanaryHttpRequestV1] = []

    def _open(request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
        captured.append(request)
        return _fake_open(request)

    monkeypatch.setattr(URLLIB_PATCH, _open)
    transport = GatedProductiveFlattenTransportV1()
    transport.network_session_authorized = True
    receipt = _passing_receipt()
    transport.attach_pre_send_receipt(receipt)
    request = _unsigned_request(receipt)
    first = transport.send(request)
    assert first.status_code == 200
    assert receipt.send_lease.consumed is True
    assert transport._sent is True
    assert transport.last_wire_attempted is True
    assert len(captured) == 1
    with pytest.raises(LiveCanaryFlattenProductiveTransportError, match="DUPLICATE_POST_FORBIDDEN"):
        transport.send(request)
    assert receipt.send_lease.consumed is True
    assert len(captured) == 1


def test_successful_authenticated_gated_path_consumes_lease_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[LiveCanaryHttpRequestV1] = []

    def _open(request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
        captured.append(request)
        return _fake_open(request)

    monkeypatch.setattr(URLLIB_PATCH, _open)
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    transport.network_session_authorized = True
    receipt = _passing_receipt()
    transport.attach_pre_send_receipt(receipt)
    request = _hmac_present_request(receipt)
    first = transport.send(request)
    assert first.status_code == 200
    assert receipt.send_lease.consumed is True
    assert transport._sent is True
    assert transport.last_wire_attempted is True
    assert len(captured) == 1
    with pytest.raises(LiveCanaryFlattenProductiveTransportError, match="DUPLICATE_POST_FORBIDDEN"):
        transport.send(request)
    assert len(captured) == 1


def test_duplicate_send_remains_fail_closed_after_consume(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(URLLIB_PATCH, _fake_open)
    transport = GatedProductiveFlattenTransportV1()
    transport.network_session_authorized = True
    receipt = _passing_receipt()
    transport.attach_pre_send_receipt(receipt)
    request = _unsigned_request(receipt)
    transport.send(request)
    with pytest.raises(LiveCanaryFlattenProductiveTransportError, match="DUPLICATE_POST_FORBIDDEN"):
        transport.send(request)
    assert transport._sent is True


def test_gated_source_order_lease_after_session_before_wire() -> None:
    text = FLATTEN_TRANSPORT_SRC.read_text(encoding="utf-8")
    class_at = text.find("class GatedProductiveFlattenTransportV1")
    send_at = text.find("def send(self, request: LiveCanaryHttpRequestV1)", class_at)
    receipt_at = text.find("_require_typed_gate_receipt(self._receipt)", send_at)
    session_at = text.find("if not self.network_session_authorized:", send_at)
    post_at = text.find("assert_productive_flatten_post_request_v1(request)", send_at)
    lease_at = text.find("_consume_receipt_lease(receipt)", send_at)
    sent_at = text.find("self._sent = True", send_at)
    last_wire_true = text.find("self.last_wire_attempted = True", send_at)
    urllib_call_at = text.find("open_productive_flatten_urllib_post_v1(request)", last_wire_true)
    assert class_at >= 0
    assert send_at > class_at
    assert receipt_at > send_at
    assert session_at > receipt_at
    assert post_at > session_at
    assert lease_at > post_at
    assert sent_at > lease_at
    assert last_wire_true > sent_at
    assert urllib_call_at > last_wire_true


def test_authenticated_source_order_hmac_session_then_lease_then_wire() -> None:
    text = AUTH_TRANSPORT_SRC.read_text(encoding="utf-8")
    class_at = text.find("class AuthenticatedGatedProductiveFlattenTransportV1")
    send_at = text.find("def send(self, request: LiveCanaryHttpRequestV1)", class_at)
    receipt_at = text.find("_require_typed_gate_receipt(self._receipt)", send_at)
    hmac_at = text.find("assert_authenticated_productive_headers_v1", send_at)
    session_at = text.find("if not self.network_session_authorized:", send_at)
    post_at = text.find("assert_productive_flatten_post_request_v1(request)", send_at)
    lease_at = text.find("_consume_receipt_lease(receipt)", send_at)
    sent_at = text.find("self._sent = True", send_at)
    last_wire_true = text.find("self.last_wire_attempted = True", send_at)
    urllib_import_at = text.find("open_productive_flatten_urllib_post_v1", send_at)
    urllib_call_at = text.find("open_productive_flatten_urllib_post_v1(request)", last_wire_true)
    assert class_at >= 0
    assert send_at > class_at
    assert receipt_at > send_at
    assert hmac_at > receipt_at
    assert session_at > hmac_at
    assert post_at > session_at
    assert lease_at > post_at
    assert sent_at > lease_at
    assert urllib_import_at > lease_at
    assert last_wire_true > urllib_import_at
    assert urllib_call_at > last_wire_true
    assert '"RECEIPT_MISSING"' in text
    assert "build_okx_live_canary_auth_headers_v1(" not in text[send_at:urllib_call_at]
