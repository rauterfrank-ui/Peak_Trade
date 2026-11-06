"""Offline flatten pre-send receipt authority adjudication tests.

Hard-network-blocked. Schema is defined. Attachable mint is blocked by
open gate-order. No GET. No POST. No HMAC. No urllib.
"""

from __future__ import annotations

import socket
import urllib.request
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1 import (
    flatten_productive_transport_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    AuthenticatedGatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateReceiptV1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_ORIGIN_MAIN_SHA,
    INSTRUMENT_ID,
    PRE_SUBMIT_FRESH_GET_REQUIRED,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.flatten_pre_send_receipt_authority_adjudication_v1 import (
    CURRENT_CANONICAL_BOUNDARY,
    EARLIEST_UNRESOLVED_RUNTIME_GATE,
    EXPECTED_ORIGIN_MAIN_SHA,
    FIRST_DENY_AFTER_RECEIPT,
    OPEN_GATE_ORDER_BLOCKER,
    RECEIPT_AUTHORITY_SCHEMA_STATUS,
    RECEIPT_CONSUMER,
    RECEIPT_MINTED,
    RECEIPT_PRODUCER,
    RECEIPT_WORK_BLOCKED_BY_OPEN_GATE_ORDER,
    adjudicate_flatten_pre_send_receipt_authority_v1,
    census_denied_producer_receipt_v1,
    persist_flatten_pre_send_receipt_authority_evidence_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.network_session_authority_v1 import (
    current_section_11_14_network_session_explicit_v1,
    issue_owner_network_session_authority_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.network_session_instance_authorization_v1 import (
    authorize_network_session_instance_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_transport_bind_send_capable_v1 import (
    prepare_productive_transport_bind_send_capable_v1,
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

BODY = {"instId": INSTRUMENT_ID}
REPO_ROOT = Path(__file__).resolve().parents[2]
COMMITTED_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops/section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1"
    / "20260908T054500Z_flatten_pre_send_receipt_authority_and_binding_v1"
)


def _install_network_hard_fail(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    attempts: list[str] = []

    def _hard_fail(name: str):
        def _boom(*_args: object, **_kwargs: object) -> None:
            attempts.append(name)
            raise AssertionError("NETWORK_CALL_ATTEMPTED")

        return _boom

    monkeypatch.setattr(urllib.request, "urlopen", _hard_fail("urlopen"))
    monkeypatch.setattr(socket, "create_connection", _hard_fail("create_connection"))
    monkeypatch.setattr(
        flatten_productive_transport_v1,
        "open_productive_flatten_urllib_post_v1",
        _hard_fail("open_productive_flatten_urllib_post_v1"),
    )
    return attempts


def _session_artifact() -> dict:
    return issue_owner_network_session_authority_v1(
        explicit=current_section_11_14_network_session_explicit_v1(issued_at="2026-09-08T05:45:00Z")
    )["artifact"]


def _wire_send_artifact() -> dict:
    payload: dict = {
        "schema_version": PRODUCTIVE_WIRE_SEND_SCHEMA_VERSION,
        "authority_type": AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND,
        "authority_source": AUTHORITY_SOURCE_CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND,
        "issued": True,
        "issued_at": "2026-09-08T05:45:00Z",
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


def _ready_real_bind():
    session = _session_artifact()
    wire = _wire_send_artifact()
    bind = prepare_productive_transport_bind_send_capable_v1(
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        wire_send=wire,
        network_session=session,
        session_armed=False,
        inner=None,
    )
    assert (
        authorize_network_session_instance_v1(
            bind=bind,
            network_session=session,
            origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
            instrument_id=INSTRUMENT_ID,
            exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        )["authorized"]
        is True
    )
    assert (
        arm_productive_session_v1(
            bind=bind,
            network_session=session,
            wire_send=wire,
            origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
            instrument_id=INSTRUMENT_ID,
            exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        )["armed"]
        is True
    )
    assert (
        permit_productive_send_v1(
            bind=bind,
            network_session=session,
            wire_send=wire,
            origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
            instrument_id=INSTRUMENT_ID,
            exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        )["permitted"]
        is True
    )
    return session, wire, bind


def test_schema_defined_producer_consumer_match_mint_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _install_network_hard_fail(monkeypatch)
    verdict = adjudicate_flatten_pre_send_receipt_authority_v1()
    assert verdict["RECEIPT_AUTHORITY_SCHEMA_STATUS"] == RECEIPT_AUTHORITY_SCHEMA_STATUS
    assert verdict["RECEIPT_AUTHORITY_SCHEMA_STATUS"] == "DEFINED"
    assert verdict["RECEIPT_PRODUCER"] == RECEIPT_PRODUCER
    assert verdict["RECEIPT_CONSUMER"] == RECEIPT_CONSUMER
    assert verdict["RECEIPT_PRODUCER_ADJUDICATED"] is True
    assert verdict["RECEIPT_CONSUMER_ADJUDICATED"] is True
    assert verdict["PRODUCER_CONSUMER_SCHEMA_MATCH"] is True
    assert verdict["RECEIPT_OWNER_ISSUANCE_SCHEMA_INVENTED"] is False
    assert verdict["RECEIPT_MINTED"] is False
    assert verdict["RECEIPT_BOUND"] is False
    assert verdict["RECEIPT_ATTACHED"] is False
    assert verdict["RECEIPT_WORK_BLOCKED_BY_OPEN_GATE_ORDER"] is True
    assert verdict["OPEN_GATE_ORDER_BLOCKER"] == OPEN_GATE_ORDER_BLOCKER
    assert verdict["OPEN_GATE_ORDER_BLOCKER"] == "FRESH_PRE_SUBMIT_GET"
    assert verdict["OPEN_GATE_ORDER_POINTS"] == list(OPEN_GATE_ORDER_POINTS)
    assert verdict["CURRENT_CANONICAL_BOUNDARY"] == CURRENT_CANONICAL_BOUNDARY
    assert verdict["EARLIEST_UNRESOLVED_RUNTIME_GATE"] == EARLIEST_UNRESOLVED_RUNTIME_GATE
    assert verdict["FIRST_DENY_AFTER_RECEIPT"] == FIRST_DENY_AFTER_RECEIPT
    assert verdict["PRODUCER_CENSUS_ALLOWED"] is False
    assert verdict["DENIED_ATTACH_FIRST_DENY"] == "RECEIPT_NOT_ALLOWED"
    assert verdict["PRE_SUBMIT_FRESH_GET_REQUIRED"] is True
    assert PRE_SUBMIT_FRESH_GET_REQUIRED is True
    assert verdict["GET_PERFORMED"] is False
    assert verdict["HMAC_EXECUTED"] is False
    assert verdict["REPRICE_EXECUTED"] is False
    assert verdict["POST_PERFORMED"] is False
    assert verdict["WIRE_SEND_EXECUTED"] is False
    assert verdict["DURABLE_CONSUMED"] is False
    assert verdict["POSITION_MUTATION_EXECUTED"] is False
    assert attempts == []
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert CANARY_AUTHORIZED is False
    assert RECEIPT_MINTED is False
    assert EXPECTED_ORIGIN_MAIN_SHA == "376fe84088dae800fdc1ac25436162fe25e1620a"


def test_denied_producer_census_is_typed_and_not_attachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _install_network_hard_fail(monkeypatch)
    receipt = census_denied_producer_receipt_v1()
    assert isinstance(receipt, FlattenPreSendGateReceiptV1)
    assert receipt.allowed is False
    assert receipt.approved_request_identity == ""
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    with pytest.raises(Exception, match="RECEIPT_NOT_ALLOWED"):
        transport.attach_pre_send_receipt(receipt)
    assert transport._receipt is None
    assert attempts == []


def test_orchestrator_first_deny_remains_receipt_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _install_network_hard_fail(monkeypatch)
    session, wire, bind = _ready_real_bind()
    real = bind.adapter.inner
    assert isinstance(real, AuthenticatedGatedProductiveFlattenTransportV1)
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
    assert orch["FIRST_DENY"] == "RECEIPT_MISSING"
    assert orch["RECEIPT_PRESENT"] is False
    assert orch["PRODUCTIVE_INNER_SEND_INVOKED"] is True
    assert orch["REAL_INNER_SEND_EXECUTED"] is False
    assert orch["HMAC_VALIDATION_REACHED"] is False
    assert orch["LEASE_CONSUMED"] is False
    assert orch["GET_PERFORMED"] is False
    assert orch["REPRICE_EXECUTED"] is False
    assert orch["WIRE_SEND_EXECUTED"] is False
    assert orch["OPEN_GATE_ORDER_POINTS"] == list(OPEN_GATE_ORDER_POINTS)
    assert real.last_wire_attempted is False
    assert attempts == []


def test_persist_receipt_authority_evidence_offline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    attempts = _install_network_hard_fail(monkeypatch)
    verdict = adjudicate_flatten_pre_send_receipt_authority_v1()
    result = persist_flatten_pre_send_receipt_authority_evidence_v1(
        persist_root=tmp_path,
        adjudication=verdict,
    )
    assert int(result["MANIFEST_VERIFY_RC"]) == 0
    verified = verify_manifest_v1(tmp_path)
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    summary = (tmp_path / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"RECEIPT_MINTED": false' in summary
    assert '"RECEIPT_WORK_BLOCKED_BY_OPEN_GATE_ORDER": true' in summary
    assert '"GET_PERFORMED": false' in summary
    assert '"POST_PERFORMED": false' in summary
    assert attempts == []


def test_committed_evidence_manifest_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = _install_network_hard_fail(monkeypatch)
    assert COMMITTED_EVIDENCE.is_dir()
    verified = verify_manifest_v1(COMMITTED_EVIDENCE)
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    summary = (COMMITTED_EVIDENCE / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"RECEIPT_MINTED": false' in summary
    assert '"RECEIPT_WORK_BLOCKED_BY_OPEN_GATE_ORDER": true' in summary
    assert '"GET_PERFORMED": false' in summary
    assert '"POST_PERFORMED": false' in summary
    assert attempts == []
