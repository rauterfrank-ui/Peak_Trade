"""Offline bound send_permitted tests. No live GET. No live POST.

No inner.send. No durable consume. No urllib. Permission is not send.
"""

from __future__ import annotations

import socket
import urllib.request
from pathlib import Path

import pytest

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_ORIGIN_MAIN_SHA,
    FLATTEN_HTTP_ENDPOINT,
    INSTRUMENT_ID,
    PRODUCTIVE_TRANSPORT_BIND_KIND_NO_SEND,
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
    RecordingFakeProductiveSendInnerV1,
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
PERMIT_SRC = PACKAGE / "send_permitted_v1.py"
ADAPTER_SRC = PACKAGE / "productive_flatten_submit_send_adapter_v1.py"


def _boom(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("REAL_NETWORK_MUST_NOT_OCCUR")


def _session_artifact() -> dict:
    return issue_owner_network_session_authority_v1(
        explicit=current_section_11_14_network_session_explicit_v1(issued_at="2026-09-08T06:47:00Z")
    )["artifact"]


def _wire_send_artifact() -> dict:
    payload: dict = {
        "schema_version": PRODUCTIVE_WIRE_SEND_SCHEMA_VERSION,
        "authority_type": AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND,
        "authority_source": AUTHORITY_SOURCE_CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND,
        "issued": True,
        "issued_at": "2026-09-08T06:47:00Z",
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


def test_valid_prerequisites_permit_bound_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    session = _session_artifact()
    wire = _wire_send_artifact()
    inner = RecordingFakeProductiveSendInnerV1(network_session_authorized=False)
    bind = _bind(session=session, wire=wire, inner=inner)
    _authorize(bind=bind, session=session)
    _arm(bind=bind, session=session, wire=wire)
    assert bind.adapter.send_permitted is False
    assert bind.send_permitted is False
    result = permit_productive_send_v1(
        bind=bind,
        network_session=session,
        wire_send=wire,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert result["permitted"] is True
    assert result["SEND_PERMISSION_BIND_VALIDATION"] == "PASS"
    assert result["SEND_PERMITTED_BEFORE"] is False
    assert result["SEND_PERMITTED"] is True
    assert result["SEND_PERMISSION_CHANGED"] is True
    assert bind.adapter.send_permitted is True
    assert bind.send_permitted is False
    assert result["BIND_SEND_PERMITTED"] is False
    assert bind.adapter.session_armed is True
    assert result["SESSION_ARMED"] is True
    assert result["SESSION_ARMED_BEFORE"] is True
    assert inner.network_session_authorized is True
    assert result["NETWORK_SESSION_AUTHORIZED"] is True
    assert result["NETWORK_SESSION_AUTHORIZED_CHANGED"] is False
    assert result["WIRE_SEND_AUTHORITY_ISSUED"] is True
    assert result["WIRE_SEND_AUTHORITY_ACCEPTED"] is True
    assert result["WIRE_SEND_AUTHORITY_CONSUMED"] is False
    assert SESSION_ARMING_STANDING is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert CANARY_AUTHORIZED is False
    assert result["GET_PERFORMED"] is False
    assert result["POST_PERFORMED"] is False
    assert result["REPRICE_EXECUTED"] is False
    assert result["INNER_SEND_EXECUTED"] is False
    assert result["FAKE_INNER_SEND_REACHED"] is False
    assert result["REAL_INNER_SEND_EXECUTED"] is False
    assert result["WIRE_SEND_EXECUTED"] is False
    assert result["REAL_POST_COUNT"] == 0
    assert result["DURABLE_CONSUMED"] is False
    assert result["POSITION_MUTATION"] is False
    assert wire["consumed"] is False
    assert inner.send_calls == []


def test_missing_invalid_consumed_wire_send_does_not_permit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    session = _session_artifact()
    wire = _wire_send_artifact()
    inner = RecordingFakeProductiveSendInnerV1(network_session_authorized=False)
    bind = _bind(session=session, wire=wire, inner=inner)
    _authorize(bind=bind, session=session)
    _arm(bind=bind, session=session, wire=wire)
    missing = permit_productive_send_v1(
        bind=bind,
        network_session=session,
        wire_send=None,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert missing["permitted"] is False
    assert "WIRE_SEND_OWNER_AUTHORITY_MISSING" in missing["reasons"]
    assert bind.adapter.send_permitted is False
    bad_id = dict(wire)
    bad_id["authority_id"] = "0" * 64
    invalid = permit_productive_send_v1(
        bind=bind,
        network_session=session,
        wire_send=bad_id,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert invalid["permitted"] is False
    assert "WIRE_SEND_AUTHORITY_ID_MISMATCH" in invalid["reasons"]
    consumed = dict(wire)
    consumed["consumed"] = True
    reused = permit_productive_send_v1(
        bind=bind,
        network_session=session,
        wire_send=consumed,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert reused["permitted"] is False
    assert "WIRE_SEND_CONSUMED_CANNOT_BE_REUSED" in reused["reasons"]
    assert reused["WIRE_SEND_AUTHORITY_CONSUMED"] is True
    assert bind.adapter.send_permitted is False
    assert wire["consumed"] is False


def test_unauthorized_inner_does_not_permit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    session = _session_artifact()
    wire = _wire_send_artifact()
    inner = RecordingFakeProductiveSendInnerV1(network_session_authorized=False)
    bind = _bind(session=session, wire=wire, inner=inner)
    result = permit_productive_send_v1(
        bind=bind,
        network_session=session,
        wire_send=wire,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert result["permitted"] is False
    assert "PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED" in result["reasons"]
    assert inner.network_session_authorized is False
    assert bind.adapter.send_permitted is False


def test_unarmed_session_does_not_permit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    session = _session_artifact()
    wire = _wire_send_artifact()
    inner = RecordingFakeProductiveSendInnerV1(network_session_authorized=False)
    bind = _bind(session=session, wire=wire, inner=inner)
    _authorize(bind=bind, session=session)
    result = permit_productive_send_v1(
        bind=bind,
        network_session=session,
        wire_send=wire,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert result["permitted"] is False
    assert "SESSION_NOT_ARMED" in result["reasons"]
    assert bind.adapter.session_armed is False
    assert bind.adapter.send_permitted is False
    assert inner.network_session_authorized is True


def test_binding_mismatch_does_not_permit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    session = _session_artifact()
    wire = _wire_send_artifact()
    inner = RecordingFakeProductiveSendInnerV1(network_session_authorized=False)
    bind = _bind(session=session, wire=wire, inner=inner)
    _authorize(bind=bind, session=session)
    _arm(bind=bind, session=session, wire=wire)
    sha = permit_productive_send_v1(
        bind=bind,
        network_session=session,
        wire_send=wire,
        origin_main_sha="deadbeef" * 5,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert sha["permitted"] is False
    assert "NETWORK_SESSION_SHA_MISMATCH" in sha["reasons"]
    assert bind.adapter.send_permitted is False
    envelope = permit_productive_send_v1(
        bind=bind,
        network_session=session,
        wire_send=wire,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id="ffff" * 16,
    )
    assert envelope["permitted"] is False
    assert "NETWORK_SESSION_ENVELOPE_MISMATCH" in envelope["reasons"]
    instrument = permit_productive_send_v1(
        bind=bind,
        network_session=session,
        wire_send=wire,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id="BTC-USD_UM_XPERP-310404",
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert instrument["permitted"] is False
    assert "NETWORK_SESSION_INSTRUMENT_MISMATCH" in instrument["reasons"]
    missing = permit_productive_send_v1(
        bind=None,
        network_session=session,
        wire_send=wire,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert missing["permitted"] is False
    assert "PRODUCTIVE_TRANSPORT_BIND_SEND_CAPABLE_MISSING" in missing["reasons"]
    assert bind.adapter.send_permitted is False
    assert bind.adapter.session_armed is True
    assert inner.network_session_authorized is True


def test_permission_changes_only_adapter_send_permitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    session = _session_artifact()
    wire = _wire_send_artifact()
    inner = RecordingFakeProductiveSendInnerV1(network_session_authorized=False)
    bind = _bind(session=session, wire=wire, inner=inner)
    _authorize(bind=bind, session=session)
    _arm(bind=bind, session=session, wire=wire)
    bind_authorized = bind.network_session_authorized
    permit_productive_send_v1(
        bind=bind,
        network_session=session,
        wire_send=wire,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert bind.adapter.send_permitted is True
    assert bind.send_permitted is False
    assert bind.network_session_authorized is bind_authorized
    assert bind.adapter.session_armed is True
    assert inner.network_session_authorized is True
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert CANARY_AUTHORIZED is False
    assert SESSION_ARMING_STANDING is False
    assert wire["consumed"] is False
    assert inner.send_calls == []
    assert bind.adapter.inner_send_executed is False


def test_orchestrator_after_permission_stops_before_inner_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    session = _session_artifact()
    wire = _wire_send_artifact()
    inner = RecordingFakeProductiveSendInnerV1(network_session_authorized=False)
    bind = _bind(session=session, wire=wire, inner=inner)
    _authorize(bind=bind, session=session)
    _arm(bind=bind, session=session, wire=wire)
    permit = permit_productive_send_v1(
        bind=bind,
        network_session=session,
        wire_send=wire,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert permit["permitted"] is True
    orch = run_productive_wire_send_orchestrator_v1(
        bind=bind,
        wire_send=wire,
        network_session=session,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        session_armed=False,
    )
    assert orch["SESSION_ARMED"] is True
    assert orch["NETWORK_SESSION_AUTHORIZED"] is True
    assert orch["SEND_PERMITTED"] is True
    assert "SEND_PERMITTED_FALSE" not in orch["reasons"]
    assert orch["FIRST_DENY"] == "INNER_SEND_NOT_INVOKED_IN_THIS_IMPLEMENTATION"
    assert orch["SESSION_ARMING_EXECUTED"] is False
    assert orch["INNER_SEND_EXECUTED"] is False
    assert orch["FAKE_INNER_SEND_REACHED"] is False
    assert orch["REAL_INNER_SEND_EXECUTED"] is False
    assert orch["GET_PERFORMED"] is False
    assert orch["REPRICE_EXECUTED"] is False
    assert orch["WIRE_SEND_EXECUTED"] is False
    assert orch["REAL_POST_COUNT"] == 0
    assert orch["DURABLE_CONSUMED"] is False
    assert orch["OPEN_GATE_ORDER_POINTS"] == list(OPEN_GATE_ORDER_POINTS)
    assert inner.send_calls == []
    assert bind.adapter.inner_send_executed is False
    assert bind.adapter.send_permitted is True
    adapter_src = ADAPTER_SRC.read_text(encoding="utf-8")
    assert "self.inner.send" not in adapter_src
    assert "inner.send(" not in adapter_src


def test_historical_no_send_adapter_remains_no_send(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    adapter = construct_productive_flatten_submit_adapter_v1()
    with pytest.raises(FlattenProductiveTransportAdapterError, match="NETWORK_SESSION_NOT"):
        adapter.post(endpoint=FLATTEN_HTTP_ENDPOINT, body={"instId": INSTRUMENT_ID})
    assert adapter.calls == []
    no_send = prepare_productive_flatten_transport_bind_v1()
    assert no_send.kind == PRODUCTIVE_TRANSPORT_BIND_KIND_NO_SEND
    assert no_send.send_permitted is False
    src = NO_SEND_ADAPTER_SRC.read_text(encoding="utf-8")
    assert "inner.send" not in src
    assert "urlopen" not in src


def test_permit_module_has_no_urllib_or_issuer() -> None:
    text = PERMIT_SRC.read_text(encoding="utf-8")
    assert "urlopen" not in text
    assert "httpx" not in text
    assert "requests" not in text
    assert "issue_owner_network_session_authority_v1" not in text
    assert "issue_owner_productive_wire_send" not in text
    assert "open_productive_flatten_urllib_post_v1" not in text
    assert "self.inner.send(" not in text
