"""Offline fail-closed tests for §11.14 send orchestrator / send-capable bind.

No live GET. No live POST. No session arming as standing mutation. No durable
consume. No inner.send. No urllib write I/O.
"""

from __future__ import annotations

import json
import socket
import urllib.request
from pathlib import Path

import pytest

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_FROZEN_EVIDENCE_RELATIVE,
    BOUND_ORIGIN_MAIN_SHA,
    FLATTEN_ACTION,
    FLATTEN_CONFIRM_TOKEN_EXPECTED,
    FLATTEN_HTTP_ENDPOINT,
    FLATTEN_PURPOSE_EXPECTED,
    FLATTEN_SECTION,
    INSTRUMENT_ID,
    PRODUCTIVE_TRANSPORT_BIND_KIND_NO_SEND,
    PRODUCTIVE_TRANSPORT_BIND_KIND_SEND_CAPABLE,
    SESSION_ARMING_STANDING,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.execution_harness_v1 import (
    run_flatten_execution_harness_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.issuance_v1 import (
    current_section_11_14_issuance_explicit_v1,
    issue_owner_flatten_authority_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.network_session_authority_v1 import (
    current_section_11_14_network_session_explicit_v1,
    issue_owner_network_session_authority_v1,
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
    verify_owner_productive_wire_send_authority_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_wire_send_orchestrator_v1 import (
    OPEN_GATE_ORDER_POINTS,
    ProductiveWireSendOrchestratorV1,
    run_productive_wire_send_orchestrator_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_wire_send_owner_contract_schema_v1 import (
    AUTHORITY_SOURCE_CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND,
    AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND,
    EVALUATOR_IMPLEMENTED,
    ORCHESTRATOR_IMPLEMENTED,
    PRODUCER_IMPLEMENTED,
    PRODUCTIVE_WIRE_SEND_ACTION,
    PRODUCTIVE_WIRE_SEND_CONFIRM_TOKEN_EXPECTED,
    PRODUCTIVE_WIRE_SEND_PURPOSE_EXPECTED,
    PRODUCTIVE_WIRE_SEND_SCHEMA_VERSION,
    SEND_ADAPTER_IMPLEMENTED,
    SEND_CAPABLE_BIND_IMPLEMENTED,
    productive_wire_send_owner_contract_schema_v1,
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
FROZEN_ROOT = Path(BOUND_FROZEN_EVIDENCE_RELATIVE)
MINT_ARTIFACT = (
    REPO_ROOT
    / "evidence/ops/section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1"
    / "20260908T040816Z_owner_productive_wire_send_authority_v1"
    / "OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY.json"
)
NO_SEND_ADAPTER_SRC = PACKAGE / "productive_transport_adapter_v1.py"
INNER_TRANSPORT_SRC = (
    REPO_ROOT
    / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1"
    / "authenticated_productive_transport_v1.py"
)


def _boom(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("REAL_NETWORK_MUST_NOT_OCCUR")


def _frozen_envelope() -> dict:
    return json.loads((FROZEN_ROOT / "FLATTEN_ENVELOPE.json").read_text(encoding="utf-8"))


def _candidate(*, envelope: dict) -> dict:
    return {
        "action": FLATTEN_ACTION,
        "section": FLATTEN_SECTION,
        "purpose": FLATTEN_PURPOSE_EXPECTED,
        "confirm_token": FLATTEN_CONFIRM_TOKEN_EXPECTED,
        "origin_main_sha": BOUND_ORIGIN_MAIN_SHA,
        "instrument_id": INSTRUMENT_ID,
        "expected_signed_position": "1",
        "pos_side": "net",
        "margin_mode": "cross",
        "order_side": "SELL",
        "order_qty": "1",
        "order_qty_unit": "CONTRACTS_SZ",
        "reduce_only": True,
        "order_type": "LIMIT",
        "exact_envelope_id": envelope["FLATTEN_ENVELOPE_ID"],
        "single_use": True,
        "retry_allowed": False,
        "second_submit_allowed": False,
        "pre_submit_fresh_get_required": True,
        "post_submit_position_recon_required": True,
        "capture_required": True,
        "consumed": False,
        "venue_reduce_only_no_flip_acknowledgement": "UNPROVEN",
    }


def _session_artifact() -> dict:
    return issue_owner_network_session_authority_v1(
        explicit=current_section_11_14_network_session_explicit_v1(issued_at="2026-09-08T06:00:00Z")
    )["artifact"]


def _flatten_artifact() -> dict:
    return issue_owner_flatten_authority_v1(
        explicit=current_section_11_14_issuance_explicit_v1(issued_at="2026-09-08T06:00:00Z")
    )["artifact"]


def _wire_send_artifact(**overrides: object) -> dict:
    payload: dict = {
        "schema_version": PRODUCTIVE_WIRE_SEND_SCHEMA_VERSION,
        "authority_type": AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND,
        "authority_source": AUTHORITY_SOURCE_CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND,
        "issued": True,
        "issued_at": "2026-09-08T06:00:00Z",
        "section": FLATTEN_SECTION,
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
    payload.update(overrides)
    if "authority_id" not in overrides:
        payload["authority_id"] = productive_wire_send_authority_id_v1(payload)
    return payload


def test_schema_flags_implemented_but_unbound_not_accepted() -> None:
    schema = productive_wire_send_owner_contract_schema_v1()
    assert EVALUATOR_IMPLEMENTED is True
    assert ORCHESTRATOR_IMPLEMENTED is True
    assert SEND_CAPABLE_BIND_IMPLEMENTED is True
    assert SEND_ADAPTER_IMPLEMENTED is True
    assert PRODUCER_IMPLEMENTED is False
    assert schema["ISSUED"] is False
    assert schema["ACCEPTED"] is False
    assert schema["CONSUMED"] is False
    assert schema["EVALUATOR_IMPLEMENTED"] is True
    assert schema["ORCHESTRATOR_IMPLEMENTED"] is True
    assert schema["SEND_CAPABLE_BIND_IMPLEMENTED"] is True
    assert schema["SEND_ADAPTER_IMPLEMENTED"] is True
    assert schema["PRODUCER_IMPLEMENTED"] is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert CANARY_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert SESSION_ARMING_STANDING is False


def test_valid_issued_artifact_evaluator_accepted() -> None:
    artifact = _wire_send_artifact()
    verdict = verify_owner_productive_wire_send_authority_v1(
        issuance=artifact,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert verdict["accepted"] is True
    assert verdict["issued"] is True
    assert verdict["consumed"] is False
    assert verdict["reasons"] == []
    assert verdict["SESSION_ARMING_EXECUTED"] is False
    assert verdict["NETWORK_SESSION_AUTHORIZED_CHANGED"] is False
    assert verdict["INNER_SEND_EXECUTED"] is False
    assert verdict["WIRE_SEND_EXECUTED"] is False


def test_invalid_authority_id_rejected() -> None:
    artifact = _wire_send_artifact(authority_id="0" * 64)
    verdict = verify_owner_productive_wire_send_authority_v1(
        issuance=artifact,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert verdict["accepted"] is False
    assert "WIRE_SEND_AUTHORITY_ID_MISMATCH" in verdict["reasons"]


def test_wrong_origin_envelope_instrument_rejected() -> None:
    artifact = _wire_send_artifact()
    sha = verify_owner_productive_wire_send_authority_v1(
        issuance=artifact,
        origin_main_sha="deadbeef" * 5,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert sha["accepted"] is False
    assert "WIRE_SEND_SHA_MISMATCH" in sha["reasons"]
    envelope = verify_owner_productive_wire_send_authority_v1(
        issuance=artifact,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id="ffff" * 16,
    )
    assert envelope["accepted"] is False
    assert "WIRE_SEND_ENVELOPE_MISMATCH" in envelope["reasons"]
    instrument = verify_owner_productive_wire_send_authority_v1(
        issuance=artifact,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id="BTC-USD_UM_XPERP-310404",
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert instrument["accepted"] is False
    assert "WIRE_SEND_INSTRUMENT_MISMATCH" in instrument["reasons"]


def test_consumed_authority_rejected() -> None:
    artifact = _wire_send_artifact(consumed=True)
    verdict = verify_owner_productive_wire_send_authority_v1(
        issuance=artifact,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert verdict["accepted"] is False
    assert "WIRE_SEND_CONSUMED_CANNOT_BE_REUSED" in verdict["reasons"]


def test_missing_authority_rejected() -> None:
    verdict = verify_owner_productive_wire_send_authority_v1(
        issuance=None,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert verdict["accepted"] is False
    assert verdict["reasons"] == ["WIRE_SEND_OWNER_AUTHORITY_MISSING"]
    malformed = verify_owner_productive_wire_send_authority_v1(
        issuance={},
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert malformed["accepted"] is False
    assert any(str(item).startswith("WIRE_SEND_FIELDS_MISSING") for item in malformed["reasons"])


def test_issued_but_unevaluated_is_not_accepted() -> None:
    artifact = _wire_send_artifact()
    assert artifact["issued"] is True
    schema = productive_wire_send_owner_contract_schema_v1()
    assert schema["ACCEPTED"] is False
    assert schema["ISSUED"] is False
    assert artifact.get("accepted") is not True


def test_accepted_authority_alone_does_not_send_or_arm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    artifact = _wire_send_artifact()
    session = _session_artifact()
    bind = prepare_productive_transport_bind_send_capable_v1(
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        wire_send=artifact,
        network_session=session,
        session_armed=False,
    )
    assert bind.wire_send_verdict["accepted"] is True
    assert bind.send_permitted is False
    assert bind.network_session_authorized is False
    assert bind.adapter.inner.network_session_authorized is False
    orch = run_productive_wire_send_orchestrator_v1(
        bind=bind,
        wire_send=artifact,
        network_session=session,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        session_armed=False,
    )
    assert orch["WIRE_SEND_AUTHORITY_ACCEPTED"] is True
    assert orch["SESSION_ARMING_EXECUTED"] is False
    assert orch["NETWORK_SESSION_AUTHORIZED"] is False
    assert orch["INNER_SEND_EXECUTED"] is False
    assert orch["WIRE_SEND_EXECUTED"] is False
    assert orch["REAL_POST_COUNT"] == 0
    assert orch["DURABLE_CONSUMED"] is False
    assert "SESSION_NOT_ARMED" in orch["reasons"]
    assert ProductiveWireSendOrchestratorV1 is not None


def test_send_capable_bind_construction_performs_no_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    bind = prepare_productive_transport_bind_send_capable_v1(
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        wire_send=_wire_send_artifact(),
        network_session=_session_artifact(),
    )
    assert bind.kind == PRODUCTIVE_TRANSPORT_BIND_KIND_SEND_CAPABLE
    assert bind.send_permitted is False
    assert bind.adapter.inner_send_executed is False
    assert bind.adapter.inner.network_session_authorized is False


def test_constructive_adapter_remains_no_send(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_new_adapter_session_armed_false_stops_before_inner_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    inner = RecordingFakeProductiveSendInnerV1(network_session_authorized=False)
    adapter = construct_productive_flatten_submit_send_adapter_v1(
        inner=inner,
        session_armed=False,
        send_permitted=False,
        wire_send_accepted=True,
        session_accepted=True,
    )
    with pytest.raises(FlattenProductiveSendAdapterError, match="SESSION_NOT_ARMED"):
        adapter.post(endpoint=FLATTEN_HTTP_ENDPOINT, body={"instId": INSTRUMENT_ID})
    assert inner.send_calls == []
    assert adapter.inner_send_executed is False
    assert adapter.prepared is not None
    assert adapter.prepared["inner_send_invoked"] is False


def test_new_adapter_network_session_authorized_false_stops_before_inner_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
        adapter.post(endpoint=FLATTEN_HTTP_ENDPOINT, body={"instId": INSTRUMENT_ID})
    assert inner.send_calls == []
    assert adapter.inner_send_executed is False


def test_new_adapter_synthetic_authorized_fake_inner_still_does_not_send(
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
    with pytest.raises(
        FlattenProductiveSendAdapterError, match="INNER_SEND_NOT_INVOKED_IN_THIS_IMPLEMENTATION"
    ):
        adapter.post(endpoint=FLATTEN_HTTP_ENDPOINT, body={"instId": INSTRUMENT_ID})
    assert inner.send_calls == []
    assert adapter.inner_send_executed is False
    assert adapter.prepared is not None


def test_no_send_harness_path_keeps_not_implemented_deny(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    envelope = _frozen_envelope()
    result = run_flatten_execution_harness_v1(
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        candidate=_candidate(envelope=envelope),
        envelope=envelope,
        mode="execute",
        session_armed=True,
        issuance=_flatten_artifact(),
        productive_bind=prepare_productive_flatten_transport_bind_v1(),
        network_session=_session_artifact(),
        transport=None,
    )
    assert "PRODUCTIVE_WIRE_SEND_NOT_IMPLEMENTED_IN_THIS_REPAIR" in result["reasons"]
    assert result["REAL_POST_COUNT"] == 0
    assert result["WIRE_SEND"] is False
    assert result["NETWORK_SESSION_AUTHORIZED"] is False
    assert result["OWNER_TOKEN_CONSUMED"] is False


def test_send_capable_harness_path_stops_before_inner_send(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    envelope = _frozen_envelope()
    artifact = _wire_send_artifact()
    session = _session_artifact()
    bind = prepare_productive_transport_bind_send_capable_v1(
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        wire_send=artifact,
        network_session=session,
        session_armed=True,
    )
    result = run_flatten_execution_harness_v1(
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        candidate=_candidate(envelope=envelope),
        envelope=envelope,
        mode="execute",
        session_armed=True,
        issuance=_flatten_artifact(),
        send_capable_bind=bind,
        network_session=session,
        wire_send=artifact,
        transport=None,
        durable_store=tmp_path,
    )
    assert result["WIRE_SEND_AUTHORITY_ACCEPTED"] is True
    assert result["NETWORK_SESSION_AUTHORIZED"] is False
    assert result["INNER_SEND_EXECUTED"] is False
    assert result["REAL_POST_COUNT"] == 0
    assert result["WIRE_SEND"] is False
    assert result["OWNER_TOKEN_CONSUMED"] is False
    assert result["FIRST_DENY"] == "PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED"
    assert "PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED" in result["reasons"]
    assert result["OPEN_GATE_ORDER_POINTS"] == list(OPEN_GATE_ORDER_POINTS)


def test_mint_artifact_accepts_when_present() -> None:
    if not MINT_ARTIFACT.is_file():
        pytest.skip("mint artifact is local-only and not required for CI")
    artifact = json.loads(MINT_ARTIFACT.read_text(encoding="utf-8"))
    verdict = verify_owner_productive_wire_send_authority_v1(
        issuance=artifact,
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert verdict["accepted"] is True
    assert artifact["consumed"] is False
    assert artifact["authority_id"] == (
        "5ae31e1f63ae07eb3abea0989fa549a95d9dcba1cd0dda04aa04ce454b32355f"
    )


def test_new_modules_have_no_urllib_write() -> None:
    for name in (
        "productive_wire_send_authority_v1.py",
        "productive_transport_bind_send_capable_v1.py",
        "productive_flatten_submit_send_adapter_v1.py",
        "productive_wire_send_orchestrator_v1.py",
        "network_session_instance_authorization_v1.py",
    ):
        text = (PACKAGE / name).read_text(encoding="utf-8")
        assert "urlopen" not in text
        assert "httpx" not in text
        assert "requests" not in text
        assert "def issue_owner_productive_wire_send" not in text
    inner = INNER_TRANSPORT_SRC.read_text(encoding="utf-8")
    assert "open_productive_flatten_urllib_post_v1" in inner
    assert "if not self.network_session_authorized:" in inner
