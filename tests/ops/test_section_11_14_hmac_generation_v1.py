"""Offline HMAC_GENERATION contract tests.

Hard-network-blocked. Fixture HMAC only. No GET. No urllib POST. No
wire-send. No lease consume. No wire-send consume. No position mutation.
No standing Live flag mutation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    PRODUCTIVE_SIGNING_COMPONENT,
    AuthenticatedGatedProductiveFlattenTransportV1,
    construct_okx_signing_input_v1,
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
    FlattenPreSendGateReceiptV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    live_canary_http_request_from_flatten_receipt_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpRequestV1,
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
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.hmac_generation_v1 import (
    FIRST_DENY_AFTER_HMAC_SIGNED_SEND,
    AuthenticatedProductiveFlattenHeadersV1,
    FlattenHmacGenerationError,
    first_deny_after_hmac_signed_send_v1,
    generate_flatten_authenticated_headers_v1,
    hmac_signed_request_from_artifact_v1,
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
SPEC = REPO_ROOT / "docs/ops/specs/SECTION_11_14_HMAC_GENERATION_V1.md"
_FX = FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL
OWNER_GO = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
ORIGIN_SHA = "e14587a5b03a13963ffb7524f9c25f0cfea0dfc2"
STALE_SHA = "a738004fda83f9b7df477400b8664949589bb52e"
ENVELOPE_ID = "0a0133a3b82e4a15bf6986605a9a8e6b47b22665b485ff0f570200803f21cdbe"
TARGET = DEFAULT_INSTRUMENT_ID
QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
FIXTURE_KEY = "hmac-gen-fixture-key-not-live"
FIXTURE_SECRET = "hmac-gen-fixture-secret-not-live"
FIXTURE_PASS = "hmac-gen-fixture-pass-not-live"
URLLIB_PATCH = (
    "src.ops.section_11_13_5_live_canary_minimum_exposure_v1."
    "flatten_productive_transport_v1.open_productive_flatten_urllib_post_v1"
)
SEND_SRC = (
    REPO_ROOT
    / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1"
    / "authenticated_productive_transport_v1.py"
)


def _boom_wire(*_a: Any, **_k: Any) -> Any:
    raise AssertionError("WIRE")


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_HMAC_GENERATION_TESTS")

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


def _valid_gate(*, origin_main_sha: str = ORIGIN_SHA) -> FlattenPreSendGateInputV1:
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
        origin_main_sha=origin_main_sha,
        flatten_execute_bound_origin_main_sha=origin_main_sha,
        instrument_id=TARGET,
        one_shot_no_retry=True,
        duplicate_post_protection=True,
        flatten_pre_send_decision_id="hmac-generation-pre-send-1",
        position_observation_freshness_evidence=PositionObservationFreshnessEvidenceV1(
            response_received_monotonic_ms=0,
            decision_id="hmac-generation-pre-send-1",
            evidence_kind=PRE_SEND_EVIDENCE_KIND,
        ),
        monotonic_ms_clock=(lambda: 0),
        bounded_activation_permit=offline_contract_proof_bounded_activation_permit_v1(
            origin_main_sha=origin_main_sha,
            instrument_id=TARGET,
        ),
    )


def _wire_send(
    *,
    origin_main_sha: str = ORIGIN_SHA,
    exact_envelope_id: str = ENVELOPE_ID,
    instrument_id: str = TARGET,
    consumed: bool = False,
    issued: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": PRODUCTIVE_WIRE_SEND_SCHEMA_VERSION,
        "authority_type": AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND,
        "authority_source": AUTHORITY_SOURCE_CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND,
        "issued": issued,
        "issued_at": "2026-09-08T12:00:00Z",
        "section": "11.14",
        "purpose": PRODUCTIVE_WIRE_SEND_PURPOSE_EXPECTED,
        "action": PRODUCTIVE_WIRE_SEND_ACTION,
        "origin_main_sha": origin_main_sha,
        "exact_envelope_id": exact_envelope_id,
        "instrument_id": instrument_id,
        "confirm_token": PRODUCTIVE_WIRE_SEND_CONFIRM_TOKEN_EXPECTED,
        "single_use": True,
        "consumed": consumed,
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
    vault = tmp_path / "hmac-fixture-vault.json"
    vault.write_text(json.dumps({REQUIRED_SECRETREF_URI: creds}), encoding="utf-8")
    backend = build_file_secretref_vault_backend_v1(vault_file=vault)
    return resolve_and_load_live_canary_secretref_ephemeral_v1(
        secret_reference=REQUIRED_SECRETREF_URI,
        vault_backend=backend,
    )


def _mint_attached():
    receipt = mint_flatten_pre_send_attachable_receipt_v1(
        _valid_gate(),
        expected_origin_main_sha=ORIGIN_SHA,
    )
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    attach_flatten_pre_send_receipt_once_v1(transport, receipt)
    request = live_canary_http_request_from_flatten_receipt_v1(receipt)
    return transport, receipt, request


def test_standing_live_flags_remain_false() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert CANARY_AUTHORIZED is False


def test_valid_receipt_and_inputs_produce_hmac_artifact(tmp_path: Path) -> None:
    handle = _handle(tmp_path)
    try:
        transport, receipt, request = _mint_attached()
        wire = _wire_send()
        artifact = generate_flatten_authenticated_headers_v1(
            transport,
            receipt,
            request,
            handle=handle,
            wire_send=wire,
            origin_main_sha=ORIGIN_SHA,
            instrument_id=TARGET,
            exact_envelope_id=ENVELOPE_ID,
        )
        assert isinstance(artifact, AuthenticatedProductiveFlattenHeadersV1)
        assert artifact.request_identity == receipt.approved_request_identity
        assert artifact.method == "POST"
        assert artifact.body_text == receipt.approved_body_text
        assert artifact.body_text == request.body_text
        assert artifact.signing_component == PRODUCTIVE_SIGNING_COMPONENT
        assert artifact.wire_send_accepted is True
        assert artifact.lease_consumed is False
        audit = artifact.to_dict()
        assert audit["OK-ACCESS-KEY_PRESENT"] is True
        assert audit["OK-ACCESS-SIGN_PRESENT"] is True
        assert audit["OK-ACCESS-TIMESTAMP_PRESENT"] is True
        assert audit["OK-ACCESS-PASSPHRASE_PRESENT"] is True
        assert audit["SECRET_VALUES_INCLUDED"] is False
        assert "OK-ACCESS-KEY" in artifact.headers
        signed = hmac_signed_request_from_artifact_v1(receipt, artifact)
        assert signed.body_text == receipt.approved_body_text
        assert signed.body_text == request.body_text
        deny = first_deny_after_hmac_signed_send_v1(transport, receipt, artifact)
        assert deny == FIRST_DENY_AFTER_HMAC_SIGNED_SEND
        assert deny == "PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED"
        assert receipt.send_lease.consumed is False
        assert wire["consumed"] is False
        assert transport._sent is False
        assert transport.last_wire_attempted is False
        assert transport.network_session_authorized is False
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_missing_receipt_denies(tmp_path: Path) -> None:
    handle = _handle(tmp_path)
    try:
        transport = AuthenticatedGatedProductiveFlattenTransportV1()
        request = LiveCanaryHttpRequestV1(
            method="POST",
            url="https://eea.okx.com/api/v5/trade/order",
            host="eea.okx.com",
            endpoint="/api/v5/trade/order",
            headers={},
            timeout_seconds=1.0,
            body_text="{}",
        )
        with pytest.raises(FlattenHmacGenerationError, match="RECEIPT_MISSING"):
            generate_flatten_authenticated_headers_v1(
                transport,
                None,
                request,
                handle=handle,
                wire_send=_wire_send(),
                origin_main_sha=ORIGIN_SHA,
                instrument_id=TARGET,
                exact_envelope_id=ENVELOPE_ID,
            )
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_unattached_receipt_denies(tmp_path: Path) -> None:
    handle = _handle(tmp_path)
    try:
        receipt = mint_flatten_pre_send_attachable_receipt_v1(
            _valid_gate(),
            expected_origin_main_sha=ORIGIN_SHA,
        )
        transport = AuthenticatedGatedProductiveFlattenTransportV1()
        request = live_canary_http_request_from_flatten_receipt_v1(receipt)
        with pytest.raises(FlattenHmacGenerationError, match="RECEIPT_NOT_ATTACHED"):
            generate_flatten_authenticated_headers_v1(
                transport,
                receipt,
                request,
                handle=handle,
                wire_send=_wire_send(),
                origin_main_sha=ORIGIN_SHA,
                instrument_id=TARGET,
                exact_envelope_id=ENVELOPE_ID,
            )
        assert receipt.send_lease.consumed is False
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_request_identity_mismatch_denies(tmp_path: Path) -> None:
    handle = _handle(tmp_path)
    try:
        transport, receipt, request = _mint_attached()
        mismatched = LiveCanaryHttpRequestV1(
            method=request.method,
            url=request.url,
            host=request.host,
            endpoint=request.endpoint,
            headers=dict(request.headers),
            timeout_seconds=request.timeout_seconds,
            body_text='{"instId":"BTC-USD_UM_XPERP","sz":"1"}',
        )
        with pytest.raises(
            FlattenHmacGenerationError,
            match="REQUEST_IDENTITY_MISMATCH|BODY_CHANGED|INSTRUMENT_CHANGED",
        ):
            generate_flatten_authenticated_headers_v1(
                transport,
                receipt,
                mismatched,
                handle=handle,
                wire_send=_wire_send(),
                origin_main_sha=ORIGIN_SHA,
                instrument_id=TARGET,
                exact_envelope_id=ENVELOPE_ID,
            )
        assert receipt.send_lease.consumed is False
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_method_path_body_mismatch_denies(tmp_path: Path) -> None:
    handle = _handle(tmp_path)
    try:
        transport, receipt, request = _mint_attached()
        get_req = LiveCanaryHttpRequestV1(
            method="GET",
            url=request.url,
            host=request.host,
            endpoint=request.endpoint,
            headers=dict(request.headers),
            timeout_seconds=request.timeout_seconds,
            body_text=request.body_text,
        )
        with pytest.raises(FlattenHmacGenerationError, match="REQUEST_IDENTITY_MISMATCH"):
            generate_flatten_authenticated_headers_v1(
                transport,
                receipt,
                get_req,
                handle=handle,
                wire_send=_wire_send(),
                origin_main_sha=ORIGIN_SHA,
                instrument_id=TARGET,
                exact_envelope_id=ENVELOPE_ID,
            )
        path_req = LiveCanaryHttpRequestV1(
            method=request.method,
            url="https://eea.okx.com/api/v5/trade/close-position",
            host=request.host,
            endpoint="/api/v5/trade/close-position",
            headers=dict(request.headers),
            timeout_seconds=request.timeout_seconds,
            body_text=request.body_text,
        )
        with pytest.raises(FlattenHmacGenerationError, match="REQUEST_IDENTITY_MISMATCH"):
            generate_flatten_authenticated_headers_v1(
                transport,
                receipt,
                path_req,
                handle=handle,
                wire_send=_wire_send(),
                origin_main_sha=ORIGIN_SHA,
                instrument_id=TARGET,
                exact_envelope_id=ENVELOPE_ID,
            )
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_malformed_signing_input_denies(tmp_path: Path) -> None:
    handle = _handle(tmp_path)
    try:
        transport, receipt, request = _mint_attached()
        with pytest.raises(FlattenHmacGenerationError, match="REQUEST_MISSING"):
            generate_flatten_authenticated_headers_v1(
                transport,
                receipt,
                None,
                handle=handle,
                wire_send=_wire_send(),
                origin_main_sha=ORIGIN_SHA,
                instrument_id=TARGET,
                exact_envelope_id=ENVELOPE_ID,
            )
        with pytest.raises(Exception, match="OKX_ACCESS_TIMESTAMP_FORMAT_INVALID"):
            construct_okx_signing_input_v1(
                timestamp="not-an-okx-timestamp",
                method="POST",
                url=request.url,
                body=request.body_text,
            )
        with pytest.raises(FlattenHmacGenerationError, match="AUTH_HANDLE_MISSING"):
            generate_flatten_authenticated_headers_v1(
                transport,
                receipt,
                request,
                handle=None,
                wire_send=_wire_send(),
                origin_main_sha=ORIGIN_SHA,
                instrument_id=TARGET,
                exact_envelope_id=ENVELOPE_ID,
            )
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_invalid_timestamp_denies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    handle = _handle(tmp_path)
    try:
        transport, receipt, request = _mint_attached()

        def _bad_ts(*_a: Any, **_k: Any) -> str:
            return "not-an-okx-timestamp"

        monkeypatch.setattr(
            "src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1.format_okx_access_timestamp_iso_ms_v1",
            _bad_ts,
        )
        with pytest.raises(
            FlattenHmacGenerationError,
            match="OKX_ACCESS_TIMESTAMP_FORMAT_INVALID",
        ):
            generate_flatten_authenticated_headers_v1(
                transport,
                receipt,
                request,
                handle=handle,
                wire_send=_wire_send(),
                origin_main_sha=ORIGIN_SHA,
                instrument_id=TARGET,
                exact_envelope_id=ENVELOPE_ID,
            )
        assert receipt.send_lease.consumed is False
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_duplicate_hmac_does_not_consume_replay_is_send_lease(tmp_path: Path) -> None:
    handle = _handle(tmp_path)
    try:
        transport, receipt, request = _mint_attached()
        wire = _wire_send()
        first = generate_flatten_authenticated_headers_v1(
            transport,
            receipt,
            request,
            handle=handle,
            wire_send=wire,
            origin_main_sha=ORIGIN_SHA,
            instrument_id=TARGET,
            exact_envelope_id=ENVELOPE_ID,
        )
        second = generate_flatten_authenticated_headers_v1(
            transport,
            receipt,
            request,
            handle=handle,
            wire_send=wire,
            origin_main_sha=ORIGIN_SHA,
            instrument_id=TARGET,
            exact_envelope_id=ENVELOPE_ID,
        )
        assert first.body_text == second.body_text
        assert first.request_identity == second.request_identity
        assert receipt.send_lease.consumed is False
        assert wire["consumed"] is False
        receipt.send_lease.consumed = True
        with pytest.raises(FlattenHmacGenerationError, match="RECEIPT_LEASE_ALREADY_CONSUMED"):
            generate_flatten_authenticated_headers_v1(
                transport,
                receipt,
                request,
                handle=handle,
                wire_send=wire,
                origin_main_sha=ORIGIN_SHA,
                instrument_id=TARGET,
                exact_envelope_id=ENVELOPE_ID,
            )
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_secret_not_in_repr_audit_or_error(tmp_path: Path) -> None:
    handle = _handle(tmp_path)
    try:
        transport, receipt, request = _mint_attached()
        artifact = generate_flatten_authenticated_headers_v1(
            transport,
            receipt,
            request,
            handle=handle,
            wire_send=_wire_send(),
            origin_main_sha=ORIGIN_SHA,
            instrument_id=TARGET,
            exact_envelope_id=ENVELOPE_ID,
        )
        rendered = repr(artifact)
        audit = str(artifact.to_dict())
        for secret in (FIXTURE_KEY, FIXTURE_SECRET, FIXTURE_PASS):
            assert secret not in rendered
            assert secret not in audit
        try:
            generate_flatten_authenticated_headers_v1(
                transport,
                None,
                request,
                handle=handle,
                wire_send=_wire_send(),
                origin_main_sha=ORIGIN_SHA,
                instrument_id=TARGET,
                exact_envelope_id=ENVELOPE_ID,
            )
        except FlattenHmacGenerationError as exc:
            text = str(exc)
            for secret in (FIXTURE_KEY, FIXTURE_SECRET, FIXTURE_PASS):
                assert secret not in text
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_wire_send_mismatch_and_missing_authority_deny(tmp_path: Path) -> None:
    handle = _handle(tmp_path)
    try:
        transport, receipt, request = _mint_attached()
        with pytest.raises(
            FlattenHmacGenerationError, match="HMAC_WIRE_SEND_AUTHORITY_NOT_ACCEPTED"
        ):
            generate_flatten_authenticated_headers_v1(
                transport,
                receipt,
                request,
                handle=handle,
                wire_send=None,
                origin_main_sha=ORIGIN_SHA,
                instrument_id=TARGET,
                exact_envelope_id=ENVELOPE_ID,
            )
        with pytest.raises(
            FlattenHmacGenerationError, match="HMAC_WIRE_SEND_AUTHORITY_NOT_ACCEPTED"
        ):
            generate_flatten_authenticated_headers_v1(
                transport,
                receipt,
                request,
                handle=handle,
                wire_send=_wire_send(origin_main_sha=STALE_SHA),
                origin_main_sha=ORIGIN_SHA,
                instrument_id=TARGET,
                exact_envelope_id=ENVELOPE_ID,
            )
        with pytest.raises(
            FlattenHmacGenerationError, match="HMAC_WIRE_SEND_AUTHORITY_NOT_ACCEPTED"
        ):
            generate_flatten_authenticated_headers_v1(
                transport,
                receipt,
                request,
                handle=handle,
                wire_send=_wire_send(exact_envelope_id="deadbeef" * 8),
                origin_main_sha=ORIGIN_SHA,
                instrument_id=TARGET,
                exact_envelope_id=ENVELOPE_ID,
            )
        with pytest.raises(
            FlattenHmacGenerationError, match="HMAC_WIRE_SEND_AUTHORITY_NOT_ACCEPTED"
        ):
            generate_flatten_authenticated_headers_v1(
                transport,
                receipt,
                request,
                handle=handle,
                wire_send=_wire_send(consumed=True),
                origin_main_sha=ORIGIN_SHA,
                instrument_id=TARGET,
                exact_envelope_id=ENVELOPE_ID,
            )
        assert receipt.send_lease.consumed is False
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_send_path_does_not_generate_hmac() -> None:
    text = SEND_SRC.read_text(encoding="utf-8")
    send_at = text.find("def send(self, request: LiveCanaryHttpRequestV1)")
    urllib_at = text.find("open_productive_flatten_urllib_post_v1", send_at)
    gated_send = text[send_at:urllib_at]
    assert "build_okx_live_canary_auth_headers_v1(" not in gated_send
    assert "attach_authenticated_headers_via_existing_signer_v1" not in gated_send
    assert "generate_flatten_authenticated_headers_v1" not in gated_send


def test_closed_receipt_missing_and_durable_consume_still_imported() -> None:
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.durable_consume_success_object_v1 import (
        FlattenProductiveSendSuccessObjectV1,
        mint_flatten_productive_send_success_object_v1,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.receipt_missing_v1 import (
        FIRST_DENY_AFTER_ATTACHED_RECEIPT,
        mint_flatten_pre_send_attachable_receipt_v1 as mint,
    )

    assert mint is not None
    assert FIRST_DENY_AFTER_ATTACHED_RECEIPT == "UNSIGNED_PRODUCTIVE_HEADERS"
    assert mint_flatten_productive_send_success_object_v1 is not None
    assert FlattenProductiveSendSuccessObjectV1 is not None
    assert isinstance(FlattenPreSendGateReceiptV1, type)


def test_hmac_generation_spec_non_execution() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_HMAC_GENERATION_V1" in text
    assert "HMAC_GENERATION=PROVEN" in text
    assert "HMAC_GENERATION_WIRED=true" in text
    assert "HMAC_GENERATION_ON_SEND_PATH=false" in text
    assert "HMAC_GENERATION_REQUIRES_WIRE_SEND_AUTHORITY_VERIFY_ACCEPT=true" in text
    assert "LEASE_CONSUMED=false" in text
    assert "POST_PERFORMED=false" in text
    assert "WIRE_SEND_EXECUTED=false" in text
    assert "REAL_GET_COUNT=0" in text
    assert "REAL_POST_COUNT=0" in text
    assert "CURRENT_CANONICAL_BOUNDARY=PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED" in text
    assert "NEXT_OWNER_AUTHORITY_REQUIRED=PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED" in text
    assert "FINAL_STATUS=HMAC_GENERATION_PROVEN_NO_POST" in text
