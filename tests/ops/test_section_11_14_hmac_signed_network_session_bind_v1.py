"""HMAC-signed productive network-session bind tests.

Hard-network-blocked. No GET. No urllib POST. No wire-send. No lease
consume. No wire-send consume. No session consume. No position mutation.
"""

from __future__ import annotations

import json
from dataclasses import replace
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
    REQUIRED_SECRETREF_URI,
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
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    live_canary_http_request_from_flatten_receipt_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    build_file_secretref_vault_backend_v1,
    release_live_canary_ephemeral_material_v1,
    resolve_and_load_live_canary_secretref_ephemeral_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_ORIGIN_MAIN_SHA,
    INSTRUMENT_ID,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.hmac_generation_v1 import (
    generate_flatten_authenticated_headers_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.hmac_signed_network_session_bind_v1 import (
    CANONICAL_REST_HOST,
    NEXT_GATE_AFTER_BIND,
    PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED,
    bind_hmac_signed_productive_network_session_v1,
    hmac_signed_send_network_session_gate_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.network_session_authority_v1 import (
    current_section_11_14_network_session_explicit_v1,
    issue_owner_network_session_authority_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_wire_send_authority_v1 import (
    productive_wire_send_authority_id_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_wire_send_owner_contract_schema_v1 import (
    AUTHORITY_SOURCE_CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND,
    AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND,
    PRODUCTIVE_WIRE_SEND_ACTION,
    PRODUCTIVE_WIRE_SEND_CONFIRM_TOKEN_EXPECTED,
    PRODUCTIVE_WIRE_SEND_PURPOSE_EXPECTED,
    PRODUCTIVE_WIRE_SEND_SCHEMA_VERSION,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.receipt_missing_v1 import (
    attach_flatten_pre_send_receipt_once_v1,
    mint_flatten_pre_send_attachable_receipt_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = REPO_ROOT / "docs/ops/specs/SECTION_11_14_PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED_V1.md"
BIND_SRC = (
    REPO_ROOT
    / "src/ops/section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1"
    / "hmac_signed_network_session_bind_v1.py"
)
SEND_SRC = (
    REPO_ROOT
    / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1"
    / "authenticated_productive_transport_v1.py"
)
HMAC_ORIGIN_SHA = "e14587a5b03a13963ffb7524f9c25f0cfea0dfc2"
HMAC_ENVELOPE_ID = "0a0133a3b82e4a15bf6986605a9a8e6b47b22665b485ff0f570200803f21cdbe"
TARGET = DEFAULT_INSTRUMENT_ID
QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
FIXTURE_KEY = "ns-bind-fixture-key-not-live"
FIXTURE_SECRET = "ns-bind-fixture-secret-not-live"
FIXTURE_PASS = "ns-bind-fixture-pass-not-live"
URLLIB_PATCH = (
    "src.ops.section_11_13_5_live_canary_minimum_exposure_v1."
    "flatten_productive_transport_v1.open_productive_flatten_urllib_post_v1"
)


def _boom_wire(*_a: Any, **_k: Any) -> Any:
    raise AssertionError("WIRE")


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_NETWORK_SESSION_BIND_TESTS")

    monkeypatch.setattr("urllib.request.urlopen", _blocked)
    monkeypatch.setattr("socket.create_connection", _blocked)
    monkeypatch.setattr(URLLIB_PATCH, _boom_wire)


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


def _valid_gate(*, origin_main_sha: str = HMAC_ORIGIN_SHA) -> FlattenPreSendGateInputV1:
    return FlattenPreSendGateInputV1(
        live_authorized=False,
        live_enabled=True,
        live_armed=True,
        flatten_live_wire_enabled=True,
        allow_productive_wire_send=True,
        flatten_execute_token=FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        flatten_execute_purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        flatten_execute_owner_go=FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        pending_orders_payload=_pending(),
        price_input=_price(),
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha=origin_main_sha,
        flatten_execute_bound_origin_main_sha=origin_main_sha,
        instrument_id=TARGET,
        one_shot_no_retry=True,
        duplicate_post_protection=True,
        flatten_pre_send_decision_id="hmac-ns-bind-pre-send-1",
        position_observation_freshness_evidence=PositionObservationFreshnessEvidenceV1(
            response_received_monotonic_ms=0,
            decision_id="hmac-ns-bind-pre-send-1",
            evidence_kind=PRE_SEND_EVIDENCE_KIND,
        ),
        monotonic_ms_clock=(lambda: 0),
        bounded_activation_permit=offline_contract_proof_bounded_activation_permit_v1(
            origin_main_sha=origin_main_sha,
            instrument_id=TARGET,
        ),
    )


def _wire_send() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": PRODUCTIVE_WIRE_SEND_SCHEMA_VERSION,
        "authority_type": AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND,
        "authority_source": AUTHORITY_SOURCE_CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND,
        "issued": True,
        "issued_at": "2026-09-08T12:00:00Z",
        "section": "11.14",
        "purpose": PRODUCTIVE_WIRE_SEND_PURPOSE_EXPECTED,
        "action": PRODUCTIVE_WIRE_SEND_ACTION,
        "origin_main_sha": HMAC_ORIGIN_SHA,
        "exact_envelope_id": HMAC_ENVELOPE_ID,
        "instrument_id": TARGET,
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


def _handle(tmp_path: Path):
    creds = {
        "api_key": FIXTURE_KEY,
        "api_secret": FIXTURE_SECRET,
        "passphrase": FIXTURE_PASS,
    }
    vault = tmp_path / "ns-bind-fixture-vault.json"
    vault.write_text(json.dumps({REQUIRED_SECRETREF_URI: creds}), encoding="utf-8")
    backend = build_file_secretref_vault_backend_v1(vault_file=vault)
    return resolve_and_load_live_canary_secretref_ephemeral_v1(
        secret_reference=REQUIRED_SECRETREF_URI,
        vault_backend=backend,
    )


def _session_artifact(*, consumed: bool = False) -> dict[str, Any]:
    produced = issue_owner_network_session_authority_v1(
        explicit=current_section_11_14_network_session_explicit_v1(issued_at="2026-09-08T14:00:00Z")
    )
    artifact = produced["artifact"]
    assert artifact is not None
    if consumed:
        artifact = dict(artifact)
        artifact["consumed"] = True
    return artifact


def _mint_hmac(tmp_path: Path):
    handle = _handle(tmp_path)
    receipt = mint_flatten_pre_send_attachable_receipt_v1(
        _valid_gate(),
        expected_origin_main_sha=HMAC_ORIGIN_SHA,
    )
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    attach_flatten_pre_send_receipt_once_v1(transport, receipt)
    request = live_canary_http_request_from_flatten_receipt_v1(receipt)
    wire = _wire_send()
    artifact = generate_flatten_authenticated_headers_v1(
        transport,
        receipt,
        request,
        handle=handle,
        wire_send=wire,
        origin_main_sha=HMAC_ORIGIN_SHA,
        instrument_id=TARGET,
        exact_envelope_id=HMAC_ENVELOPE_ID,
    )
    return handle, transport, receipt, artifact, wire


def test_standing_live_flags_remain_false() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert CANARY_AUTHORIZED is False


def test_valid_authority_binds_session_without_io(tmp_path: Path) -> None:
    handle, transport, receipt, artifact, wire = _mint_hmac(tmp_path)
    try:
        session = _session_artifact()
        result = bind_hmac_signed_productive_network_session_v1(
            transport=transport,
            receipt=receipt,
            artifact=artifact,
            network_session=session,
            origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
            instrument_id=INSTRUMENT_ID,
            exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        )
        assert result["bound"] is True
        assert result["authorized"] is True
        assert result["send_invoked"] is False
        assert result["WIRE_SEND_EXECUTED"] is False
        assert result["HOST"] == "eea.okx.com"
        assert result["HOST"] == CANONICAL_REST_HOST
        assert result["PROXY_FALLBACK"] is False
        assert transport.network_session_authorized is True
        assert receipt.send_lease.consumed is False
        assert wire["consumed"] is False
        assert session["consumed"] is False
        assert transport._sent is False
        assert transport.last_wire_attempted is False
        gate = hmac_signed_send_network_session_gate_v1(transport, receipt, artifact)
        assert gate["bound"] is True
        assert gate["send_invoked"] is False
        assert gate["first_deny"] is None
        assert gate["NEXT_GATE_AFTER_BIND"] == NEXT_GATE_AFTER_BIND
        assert gate["NEXT_GATE_AFTER_BIND"] == "SEND_LEASE_CONSUME"
        assert receipt.send_lease.consumed is False
        assert transport.last_wire_attempted is False
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_missing_authority_denies_hmac_signed_send(tmp_path: Path) -> None:
    handle, transport, receipt, artifact, wire = _mint_hmac(tmp_path)
    try:
        missing = bind_hmac_signed_productive_network_session_v1(
            transport=transport,
            receipt=receipt,
            artifact=artifact,
            network_session=None,
            origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
            instrument_id=INSTRUMENT_ID,
            exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        )
        assert missing["bound"] is False
        assert PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED in missing["reasons"] or (
            "NETWORK_SESSION_OWNER_AUTHORITY_MISSING" in missing["reasons"]
        )
        assert transport.network_session_authorized is False
        gate = hmac_signed_send_network_session_gate_v1(transport, receipt, artifact)
        assert gate["first_deny"] == PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED
        assert receipt.send_lease.consumed is False
        assert wire["consumed"] is False
        assert transport.last_wire_attempted is False
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_sha_instrument_envelope_and_host_mismatch_deny(tmp_path: Path) -> None:
    handle, transport, receipt, artifact, _wire = _mint_hmac(tmp_path)
    try:
        session = _session_artifact()
        sha = bind_hmac_signed_productive_network_session_v1(
            transport=transport,
            receipt=receipt,
            artifact=artifact,
            network_session=session,
            origin_main_sha="deadbeef" * 5,
            instrument_id=INSTRUMENT_ID,
            exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        )
        assert sha["bound"] is False
        assert "NETWORK_SESSION_SHA_MISMATCH" in sha["reasons"]
        inst = bind_hmac_signed_productive_network_session_v1(
            transport=transport,
            receipt=receipt,
            artifact=artifact,
            network_session=session,
            origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
            instrument_id="BTC-USD_UM_XPERP-310404",
            exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        )
        assert inst["bound"] is False
        assert "NETWORK_SESSION_INSTRUMENT_MISMATCH" in inst["reasons"]
        env = bind_hmac_signed_productive_network_session_v1(
            transport=transport,
            receipt=receipt,
            artifact=artifact,
            network_session=session,
            origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
            instrument_id=INSTRUMENT_ID,
            exact_envelope_id="ffff" * 16,
        )
        assert env["bound"] is False
        assert "NETWORK_SESSION_ENVELOPE_MISMATCH" in env["reasons"]
        identity = bind_hmac_signed_productive_network_session_v1(
            transport=transport,
            receipt=receipt,
            artifact=replace(artifact, request_identity="dead" * 16),
            network_session=session,
            origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
            instrument_id=INSTRUMENT_ID,
            exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        )
        assert identity["bound"] is False
        assert "HMAC_NETWORK_SESSION_REQUEST_IDENTITY_MISMATCH" in identity["reasons"]
        assert transport.network_session_authorized is False
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_host_mismatch_denies(tmp_path: Path) -> None:
    handle = _handle(tmp_path)
    try:
        receipt = mint_flatten_pre_send_attachable_receipt_v1(
            _valid_gate(),
            expected_origin_main_sha=HMAC_ORIGIN_SHA,
        )
        bad = replace(receipt, approved_host="www.okx.com")
        transport = AuthenticatedGatedProductiveFlattenTransportV1()
        attach_flatten_pre_send_receipt_once_v1(transport, bad)
        request = live_canary_http_request_from_flatten_receipt_v1(bad)
        artifact = generate_flatten_authenticated_headers_v1(
            transport,
            bad,
            request,
            handle=handle,
            wire_send=_wire_send(),
            origin_main_sha=HMAC_ORIGIN_SHA,
            instrument_id=TARGET,
            exact_envelope_id=HMAC_ENVELOPE_ID,
        )
        result = bind_hmac_signed_productive_network_session_v1(
            transport=transport,
            receipt=bad,
            artifact=artifact,
            network_session=_session_artifact(),
            origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
            instrument_id=INSTRUMENT_ID,
            exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        )
        assert result["bound"] is False
        assert "HMAC_NETWORK_SESSION_HOST_MISMATCH" in result["reasons"]
        assert transport.network_session_authorized is False
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_consumed_and_duplicate_bind_semantics(tmp_path: Path) -> None:
    handle, transport, receipt, artifact, wire = _mint_hmac(tmp_path)
    try:
        consumed = bind_hmac_signed_productive_network_session_v1(
            transport=transport,
            receipt=receipt,
            artifact=artifact,
            network_session=_session_artifact(consumed=True),
            origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
            instrument_id=INSTRUMENT_ID,
            exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        )
        assert consumed["bound"] is False
        assert "NETWORK_SESSION_CONSUMED_MUST_BE_FALSE" in consumed["reasons"]
        session = _session_artifact()
        first = bind_hmac_signed_productive_network_session_v1(
            transport=transport,
            receipt=receipt,
            artifact=artifact,
            network_session=session,
            origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
            instrument_id=INSTRUMENT_ID,
            exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        )
        assert first["bound"] is True
        dup = bind_hmac_signed_productive_network_session_v1(
            transport=transport,
            receipt=receipt,
            artifact=artifact,
            network_session=session,
            origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
            instrument_id=INSTRUMENT_ID,
            exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
        )
        assert dup["bound"] is False
        assert "HMAC_NETWORK_SESSION_ALREADY_BOUND" in dup["reasons"]
        assert session["consumed"] is False
        assert wire["consumed"] is False
        assert receipt.send_lease.consumed is False
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_hmac_present_without_session_authority_still_denies(tmp_path: Path) -> None:
    handle, transport, receipt, artifact, wire = _mint_hmac(tmp_path)
    try:
        assert artifact.headers.get("OK-ACCESS-SIGN")
        assert receipt.allowed is True
        gate = hmac_signed_send_network_session_gate_v1(transport, receipt, artifact)
        assert gate["first_deny"] == PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED
        assert transport.network_session_authorized is False
        assert receipt.send_lease.consumed is False
        assert wire["consumed"] is False
        assert transport.last_wire_attempted is False
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_session_flag_without_matching_authority_denies(tmp_path: Path) -> None:
    handle, transport, receipt, artifact, wire = _mint_hmac(tmp_path)
    try:
        transport.network_session_authorized = True
        gate = hmac_signed_send_network_session_gate_v1(transport, receipt, artifact)
        assert gate["first_deny"] == PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED
        assert gate["send_invoked"] is False
        assert receipt.send_lease.consumed is False
        assert wire["consumed"] is False
        assert transport.last_wire_attempted is False
        assert transport._sent is False
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_deny_entrypoint_and_empty_proxy_remain_canonical() -> None:
    send_src = SEND_SRC.read_text(encoding="utf-8")
    assert "if not self.network_session_authorized:" in send_src
    assert "PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED" in send_src
    opener = (
        REPO_ROOT
        / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1"
        / "flatten_productive_transport_v1.py"
    ).read_text(encoding="utf-8")
    assert "ProxyHandler({})" in opener
    bind_src = BIND_SRC.read_text(encoding="utf-8")
    assert "authorize_network_session_instance_v1" in bind_src
    assert "HTTP_PROXY" not in bind_src
    spec = SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED_V1" in spec
    assert "CURRENT_CANONICAL_BOUNDARY=SEND_LEASE_NOT_CONSUMED" in spec
    assert "NEXT_OWNER_AUTHORITY_REQUIRED=WIRE_SEND" in spec
