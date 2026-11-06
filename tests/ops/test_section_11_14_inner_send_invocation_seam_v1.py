"""Offline inner.send invocation-seam tests. Fake transport only.

FAKE_INNER_SEND_REACHED is not REAL_INNER_SEND_EXECUTED. No urllib. No POST.
No GET. No consume. No position mutation.
"""

from __future__ import annotations

import socket
import urllib.request
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    AuthenticatedGatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpRequestV1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_ORIGIN_MAIN_SHA,
    FLATTEN_HTTP_ENDPOINT,
    INSTRUMENT_ID,
    PRODUCTIVE_TRANSPORT_BIND_KIND_NO_SEND,
    REST_SCHEME_HOST,
    SESSION_ARMING_STANDING,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.network_session_authority_v1 import (
    current_section_11_14_network_session_explicit_v1,
    issue_owner_network_session_authority_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.network_session_instance_authorization_v1 import (
    authorize_network_session_instance_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_flatten_submit_send_adapter_v1 import (
    FlattenProductiveSendAdapterError,
    RecordingFakeProductiveSendInnerV1,
    construct_productive_flatten_submit_send_adapter_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_transport_adapter_v1 import (
    FlattenProductiveTransportAdapterError,
    construct_productive_flatten_submit_adapter_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_transport_bind_send_capable_v1 import (
    prepare_productive_transport_bind_send_capable_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_transport_bind_v1 import (
    prepare_productive_flatten_transport_bind_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_wire_send_authority_v1 import (
    productive_wire_send_authority_id_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_wire_send_orchestrator_v1 import (
    OPEN_GATE_ORDER_POINTS,
    run_productive_wire_send_orchestrator_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_wire_send_owner_contract_schema_v1 import (
    AUTHORITY_SOURCE_CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND,
    AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND,
    PRODUCTIVE_WIRE_SEND_ACTION,
    PRODUCTIVE_WIRE_SEND_CONFIRM_TOKEN_EXPECTED,
    PRODUCTIVE_WIRE_SEND_PURPOSE_EXPECTED,
    PRODUCTIVE_WIRE_SEND_SCHEMA_VERSION,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.send_permitted_v1 import (
    permit_productive_send_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.session_arming_v1 import (
    arm_productive_session_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE = (
    REPO_ROOT
    / "src/ops/section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1"
)
NO_SEND_ADAPTER_SRC = PACKAGE / "productive_transport_adapter_v1.py"
ADAPTER_SRC = PACKAGE / "productive_flatten_submit_send_adapter_v1.py"
REAL_TRANSPORT_SRC = (
    REPO_ROOT
    / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/authenticated_productive_transport_v1.py"
)
BODY = {"instId": INSTRUMENT_ID}


def _boom(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("REAL_NETWORK_MUST_NOT_OCCUR")


def _session_artifact() -> dict:
    return issue_owner_network_session_authority_v1(
        explicit=current_section_11_14_network_session_explicit_v1(issued_at="2026-09-08T06:58:00Z")
    )["artifact"]


def _wire_send_artifact() -> dict:
    payload: dict = {
        "schema_version": PRODUCTIVE_WIRE_SEND_SCHEMA_VERSION,
        "authority_type": AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND,
        "authority_source": AUTHORITY_SOURCE_CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND,
        "issued": True,
        "issued_at": "2026-09-08T06:58:00Z",
        "section": "11.14",
        "purpose": PRODUCTIVE_WIRE_SEND_PURPOSE_EXPECTED,
        "action": PRODUCTIVE_WIRE_SEND_ACTION,
        "origin_main_sha": BOUND_ORIGIN_MAIN_SHA,
        "exact_envelope_id": BOUND_FROZEN_ENVELOPE_ID,
        "instrument_id": INSTRUMENT_ID,
        "confirm_token": PRODUCTIVE_WIRE_SEND_CONFIRM_TOKEN_EXPECTED,
        "single_use": True,
        "consumed": False,
        "retry_allowed": False,
        "second_submit_allowed": False,
        "network_session_grant_cannot_authorize_this": True,
        "flatten_grant_cannot_authorize_this": True,
        "live_flags_cannot_authorize_this": True,
        "session_arming_cannot_authorize_this": True,
    }
    payload["authority_id"] = productive_wire_send_authority_id_v1(payload)
    return payload


def _bind(*, session: dict, wire: dict, inner: RecordingFakeProductiveSendInnerV1 | None = None):
    return prepare_productive_transport_bind_send_capable_v1(
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        wire_send=wire,
        network_session=session,
        session_armed=False,
        inner=inner,
    )


def _authorize(*, bind, session: dict) -> None:
    result = authorize_network_session_instance_v1(
        bind=bind,
        network_session=session,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert result["authorized"] is True


def _arm(*, bind, session: dict, wire: dict) -> None:
    result = arm_productive_session_v1(
        bind=bind,
        network_session=session,
        wire_send=wire,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert result["armed"] is True


def _permit(*, bind, session: dict, wire: dict) -> None:
    result = permit_productive_send_v1(
        bind=bind,
        network_session=session,
        wire_send=wire,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert result["permitted"] is True


def _ready_fake_bind():
    session = _session_artifact()
    wire = _wire_send_artifact()
    inner = RecordingFakeProductiveSendInnerV1(network_session_authorized=False)
    bind = _bind(session=session, wire=wire, inner=inner)
    _authorize(bind=bind, session=session)
    _arm(bind=bind, session=session, wire=wire)
    _permit(bind=bind, session=session, wire=wire)
    return session, wire, inner, bind


def test_all_gates_true_recording_fake_reaches_send_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    session, wire, inner, bind = _ready_fake_bind()
    orch = run_productive_wire_send_orchestrator_v1(
        bind=bind,
        wire_send=wire,
        network_session=session,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        session_armed=False,
        body=BODY,
    )
    assert orch["FAKE_INNER_SEND_REACHED"] is True
    assert orch["FAKE_INNER_SEND_CALL_COUNT"] == 1
    assert len(inner.send_calls) == 1
    request = inner.send_calls[0]
    assert isinstance(request, LiveCanaryHttpRequestV1)
    assert request.method == "POST"
    assert request.host == "eea.okx.com"
    assert request.endpoint == FLATTEN_HTTP_ENDPOINT
    assert request.url == f"{REST_SCHEME_HOST}{FLATTEN_HTTP_ENDPOINT}"
    assert request.headers == {}
    assert "instId" in request.body_text
    assert orch["REAL_INNER_SEND_EXECUTED"] is False
    assert orch["REAL_PRODUCTIVE_TRANSPORT_INVOKED"] is False
    assert orch["WIRE_SEND_EXECUTED"] is False
    assert orch["REAL_POST_COUNT"] == 0
    assert orch["GET_PERFORMED"] is False
    assert orch["REPRICE_EXECUTED"] is False
    assert orch["DURABLE_CONSUMED"] is False
    assert orch["FIRST_DENY"] == "PRODUCTIVE_INNER_SEND_EXECUTION_NOT_AUTHORIZED"
    assert orch["OPEN_GATE_ORDER_POINTS"] == list(OPEN_GATE_ORDER_POINTS)
    assert wire["consumed"] is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert CANARY_AUTHORIZED is False
    assert SESSION_ARMING_STANDING is False
    assert bind.adapter.inner_send_executed is False


def test_invalid_wire_send_does_not_reach_fake_send(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    session, wire, inner, bind = _ready_fake_bind()
    bad = dict(wire)
    bad["authority_id"] = "0" * 64
    orch = run_productive_wire_send_orchestrator_v1(
        bind=bind,
        wire_send=bad,
        network_session=session,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        session_armed=False,
        body=BODY,
    )
    assert orch["FAKE_INNER_SEND_REACHED"] is False
    assert inner.send_calls == []
    assert bind.adapter.fake_inner_send_reached is False


def test_consumed_authority_does_not_reach_fake_send(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    session, wire, inner, bind = _ready_fake_bind()
    consumed = dict(wire)
    consumed["consumed"] = True
    orch = run_productive_wire_send_orchestrator_v1(
        bind=bind,
        wire_send=consumed,
        network_session=session,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        session_armed=False,
        body=BODY,
    )
    assert orch["FAKE_INNER_SEND_REACHED"] is False
    assert orch["WIRE_SEND_AUTHORITY_CONSUMED"] is True
    assert inner.send_calls == []
    assert wire["consumed"] is False


def test_unauthorized_inner_does_not_reach_fake_send(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    inner = RecordingFakeProductiveSendInnerV1(network_session_authorized=False)
    adapter = construct_productive_flatten_submit_send_adapter_v1(
        inner=inner,
        session_armed=True,
        send_permitted=True,
        wire_send_accepted=True,
        session_accepted=True,
    )
    with pytest.raises(
        FlattenProductiveSendAdapterError, match="PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED"
    ):
        adapter.post(endpoint=FLATTEN_HTTP_ENDPOINT, body=BODY)
    assert inner.send_calls == []
    assert adapter.fake_inner_send_reached is False


def test_unarmed_session_does_not_reach_fake_send(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    inner = RecordingFakeProductiveSendInnerV1(network_session_authorized=True)
    adapter = construct_productive_flatten_submit_send_adapter_v1(
        inner=inner,
        session_armed=False,
        send_permitted=True,
        wire_send_accepted=True,
        session_accepted=True,
    )
    with pytest.raises(FlattenProductiveSendAdapterError, match="SESSION_NOT_ARMED"):
        adapter.post(endpoint=FLATTEN_HTTP_ENDPOINT, body=BODY)
    assert inner.send_calls == []
    assert adapter.fake_inner_send_reached is False


def test_send_permitted_false_does_not_reach_fake_send(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    inner = RecordingFakeProductiveSendInnerV1(network_session_authorized=True)
    adapter = construct_productive_flatten_submit_send_adapter_v1(
        inner=inner,
        session_armed=True,
        send_permitted=False,
        wire_send_accepted=True,
        session_accepted=True,
    )
    with pytest.raises(FlattenProductiveSendAdapterError, match="SEND_PERMITTED_FALSE"):
        adapter.post(endpoint=FLATTEN_HTTP_ENDPOINT, body=BODY)
    assert inner.send_calls == []
    assert adapter.fake_inner_send_reached is False


def test_bind_mismatch_does_not_reach_fake_send(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    session, wire, inner, bind = _ready_fake_bind()
    orch = run_productive_wire_send_orchestrator_v1(
        bind=bind,
        wire_send=wire,
        network_session=session,
        origin_main_sha="deadbeef" * 5,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        session_armed=False,
        body=BODY,
    )
    assert orch["FAKE_INNER_SEND_REACHED"] is False
    assert inner.send_calls == []


def test_malformed_request_provenance_does_not_reach_fake_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    inner = RecordingFakeProductiveSendInnerV1(network_session_authorized=True)
    adapter = construct_productive_flatten_submit_send_adapter_v1(
        inner=inner,
        session_armed=True,
        send_permitted=True,
        wire_send_accepted=True,
        session_accepted=True,
    )
    with pytest.raises(FlattenProductiveSendAdapterError, match="REQUEST_BODY_MISSING"):
        adapter.post(endpoint=FLATTEN_HTTP_ENDPOINT, body={})
    assert inner.send_calls == []
    assert adapter.fake_inner_send_reached is False
    with pytest.raises(
        FlattenProductiveSendAdapterError, match="REQUEST_BODY_NOT_JSON_SERIALIZABLE"
    ):
        adapter.post(endpoint=FLATTEN_HTTP_ENDPOINT, body={"instId": object()})
    assert inner.send_calls == []
    assert adapter.fake_inner_send_reached is False


def test_real_productive_transport_send_stops_at_receipt_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    session = _session_artifact()
    wire = _wire_send_artifact()
    bind = _bind(session=session, wire=wire, inner=None)
    assert isinstance(bind.adapter.inner, AuthenticatedGatedProductiveFlattenTransportV1)
    _authorize(bind=bind, session=session)
    _arm(bind=bind, session=session, wire=wire)
    _permit(bind=bind, session=session, wire=wire)
    real = bind.adapter.inner
    assert real.network_session_authorized is True
    assert real._receipt is None
    orch = run_productive_wire_send_orchestrator_v1(
        bind=bind,
        wire_send=wire,
        network_session=session,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        session_armed=False,
        body=BODY,
    )
    assert orch["FAKE_INNER_SEND_REACHED"] is False
    assert orch["PRODUCTIVE_INNER_SEND_INVOKED"] is True
    assert orch["PRODUCTIVE_INNER_SEND_CALL_COUNT"] == 1
    assert orch["REAL_PRODUCTIVE_TRANSPORT_INVOKED"] is True
    assert orch["REAL_INNER_SEND_EXECUTED"] is False
    assert orch["FIRST_DENY"] == "RECEIPT_MISSING"
    assert orch["RECEIPT_PRESENT"] is False
    assert orch["HMAC_VALIDATION_REACHED"] is False
    assert orch["LEASE_VALIDATION_REACHED"] is False
    assert orch["LEASE_CONSUMED"] is False
    assert real.last_wire_attempted is False
    assert real._sent is False
    assert real._receipt is None
    assert orch["REAL_POST_COUNT"] == 0
    assert orch["WIRE_SEND_EXECUTED"] is False
    assert orch["GET_PERFORMED"] is False
    assert orch["REPRICE_EXECUTED"] is False
    assert orch["DURABLE_CONSUMED"] is False
    assert orch["WIRE_SEND_AUTHORITY_CONSUMED"] is False
    assert wire["consumed"] is False


def test_historical_no_send_adapter_remains_no_send(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    adapter = construct_productive_flatten_submit_adapter_v1()
    with pytest.raises(FlattenProductiveTransportAdapterError, match="NETWORK_SESSION_NOT"):
        adapter.post(endpoint=FLATTEN_HTTP_ENDPOINT, body=BODY)
    assert adapter.calls == []
    no_send = prepare_productive_flatten_transport_bind_v1()
    assert no_send.kind == PRODUCTIVE_TRANSPORT_BIND_KIND_NO_SEND
    src = NO_SEND_ADAPTER_SRC.read_text(encoding="utf-8")
    assert "inner.send" not in src
    assert "urlopen" not in src


def test_productive_send_first_deny_is_receipt_missing_before_urllib() -> None:
    text = REAL_TRANSPORT_SRC.read_text(encoding="utf-8")
    class_at = text.find("class AuthenticatedGatedProductiveFlattenTransportV1")
    send_at = text.find("def send(self, request: LiveCanaryHttpRequestV1)", class_at)
    receipt_at = text.find("_require_typed_gate_receipt(self._receipt)", send_at)
    hmac_at = text.find("assert_authenticated_productive_headers_v1", send_at)
    urllib_at = text.find("open_productive_flatten_urllib_post_v1", send_at)
    assert class_at >= 0
    assert send_at > class_at
    assert receipt_at > send_at
    assert hmac_at > receipt_at
    assert urllib_at > hmac_at
    assert '"RECEIPT_MISSING"' in text


def test_adapter_calls_real_send_then_maps_receipt_missing() -> None:
    text = ADAPTER_SRC.read_text(encoding="utf-8")
    real_gate = text.find("isinstance(self.inner, AuthenticatedGatedProductiveFlattenTransportV1)")
    send_at = text.find("self.inner.send(request)", real_gate)
    refuse_unknown = text.find(
        "PRODUCTIVE_INNER_SEND_EXECUTION_NOT_AUTHORIZED",
        send_at,
    )
    assert real_gate >= 0
    assert send_at > real_gate
    assert refuse_unknown > send_at
    assert "LiveCanaryFlattenProductiveTransportError" in text
    assert "urlopen" not in text
    assert "httpx" not in text
    assert "requests" not in text
    assert "open_productive_flatten_urllib_post_v1" not in text
