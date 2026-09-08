"""§11.14 HMAC_GENERATION: receipt-bound offline HMAC header artifact.

Reuses attach_authenticated_headers_via_existing_signer_v1 /
build_okx_live_canary_auth_headers_v1. Requires an attached
FlattenPreSendGateReceiptV1 and wire-send verify/accept. Does not consume
the send lease or OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1. Does not HTTP
GET or POST. Does not set network_session_authorized. Does not mutate
standing Live flags. HMAC is not generated on the send() urllib path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.bound_testnet_http_client_v1 import (
    BoundTestnetHttpClientError,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    PRODUCTIVE_SIGNING_COMPONENT,
    AuthenticatedGatedProductiveFlattenTransportV1,
    AuthenticatedProductiveTransportError,
    attach_authenticated_headers_via_existing_signer_v1,
    construct_okx_signing_input_v1,
    okx_request_path_from_url_v1,
    signing_input_digest_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateReceiptV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    LiveCanaryFlattenProductiveTransportError,
    assert_request_matches_flatten_receipt_v1,
    live_canary_http_request_from_flatten_receipt_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpRequestV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    LiveCanaryCredentialError,
    LiveCanaryEphemeralCredentialHandleV1,
    assert_no_plaintext_in_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    LiveCanarySignerError,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_wire_send_authority_v1 import (
    FlattenProductiveWireSendAuthorityError,
    verify_owner_productive_wire_send_authority_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

HMAC_SOURCE = "generate_flatten_authenticated_headers_v1"
FIRST_DENY_AFTER_HMAC_SIGNED_SEND = "PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED"


class FlattenHmacGenerationError(RuntimeError):
    """Fail-closed HMAC_GENERATION contract violation."""


def _require_standing_live_flags_false() -> None:
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenHmacGenerationError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")


def _wrap_transport_error(exc: Exception) -> FlattenHmacGenerationError:
    return FlattenHmacGenerationError(str(exc))


@dataclass(frozen=True)
class AuthenticatedProductiveFlattenHeadersV1:
    """Request-identity-bound HMAC header artifact. Secrets omitted from repr/audit."""

    request_identity: str
    method: str
    url: str
    request_path: str
    body_text: str
    timestamp: str
    signing_input_digest: str
    signing_component: str
    wire_send_authority_id: str
    wire_send_accepted: bool
    lease_consumed: bool
    headers: Mapping[str, str] = field(repr=False)

    def to_dict(self) -> dict[str, Any]:
        lookup = {str(k).strip().upper(): str(v) for k, v in self.headers.items()}
        payload = {
            "request_identity": self.request_identity,
            "method": self.method,
            "url": self.url,
            "request_path": self.request_path,
            "body_text": self.body_text,
            "timestamp": self.timestamp,
            "signing_input_digest": self.signing_input_digest,
            "signing_component": self.signing_component,
            "wire_send_authority_id": self.wire_send_authority_id,
            "wire_send_accepted": self.wire_send_accepted,
            "lease_consumed": self.lease_consumed,
            "OK-ACCESS-KEY_PRESENT": bool(str(lookup.get("OK-ACCESS-KEY") or "").strip()),
            "OK-ACCESS-SIGN_PRESENT": bool(str(lookup.get("OK-ACCESS-SIGN") or "").strip()),
            "OK-ACCESS-TIMESTAMP_PRESENT": bool(
                str(lookup.get("OK-ACCESS-TIMESTAMP") or "").strip()
            ),
            "OK-ACCESS-PASSPHRASE_PRESENT": bool(
                str(lookup.get("OK-ACCESS-PASSPHRASE") or "").strip()
            ),
            "SECRET_VALUES_INCLUDED": False,
            "HMAC_GENERATION_ON_SEND_PATH": False,
            "WIRE_SEND_CONSUMED": False,
        }
        assert_no_plaintext_in_payload_v1(payload)
        return payload


def hmac_signed_request_from_artifact_v1(
    receipt: FlattenPreSendGateReceiptV1,
    artifact: AuthenticatedProductiveFlattenHeadersV1,
) -> LiveCanaryHttpRequestV1:
    """Build a new frozen request. Does not mutate the receipt body."""
    if not isinstance(receipt, FlattenPreSendGateReceiptV1):
        raise FlattenHmacGenerationError("RECEIPT_MISSING")
    if not isinstance(artifact, AuthenticatedProductiveFlattenHeadersV1):
        raise FlattenHmacGenerationError("HMAC_ARTIFACT_TYPE_INVALID")
    if artifact.request_identity != receipt.approved_request_identity:
        raise FlattenHmacGenerationError("REQUEST_IDENTITY_MISMATCH")
    if artifact.body_text != (receipt.approved_body_text or ""):
        raise FlattenHmacGenerationError("BODY_CHANGED_AFTER_GATE")
    return live_canary_http_request_from_flatten_receipt_v1(
        receipt,
        headers=dict(artifact.headers),
    )


def generate_flatten_authenticated_headers_v1(
    transport: AuthenticatedGatedProductiveFlattenTransportV1,
    receipt: FlattenPreSendGateReceiptV1 | None,
    request: LiveCanaryHttpRequestV1 | None,
    *,
    handle: LiveCanaryEphemeralCredentialHandleV1 | None,
    wire_send: Mapping[str, Any] | None,
    origin_main_sha: str,
    instrument_id: str,
    exact_envelope_id: str,
) -> AuthenticatedProductiveFlattenHeadersV1:
    """Mint a typed HMAC artifact. Offline. Fail-closed. No POST. No consume."""
    _require_standing_live_flags_false()
    if not isinstance(transport, AuthenticatedGatedProductiveFlattenTransportV1):
        raise FlattenHmacGenerationError("TRANSPORT_TYPE_INVALID")
    if receipt is None or not isinstance(receipt, FlattenPreSendGateReceiptV1):
        raise FlattenHmacGenerationError("RECEIPT_MISSING")
    if receipt.allowed is not True:
        raise FlattenHmacGenerationError("RECEIPT_NOT_ALLOWED")
    if not str(receipt.approved_request_identity or "").strip():
        raise FlattenHmacGenerationError("RECEIPT_REQUEST_IDENTITY_MISSING")
    if getattr(transport, "_receipt", None) is not receipt:
        raise FlattenHmacGenerationError("RECEIPT_NOT_ATTACHED")
    if receipt.send_lease.consumed is True:
        raise FlattenHmacGenerationError("RECEIPT_LEASE_ALREADY_CONSUMED")
    if request is None or not isinstance(request, LiveCanaryHttpRequestV1):
        raise FlattenHmacGenerationError("REQUEST_MISSING")
    try:
        assert_request_matches_flatten_receipt_v1(receipt, request)
    except LiveCanaryFlattenProductiveTransportError as exc:
        raise _wrap_transport_error(exc) from exc
    if str(request.body_text or "") != str(receipt.approved_body_text or ""):
        raise FlattenHmacGenerationError("BODY_CHANGED_AFTER_GATE")
    if wire_send is None:
        raise FlattenHmacGenerationError("HMAC_WIRE_SEND_AUTHORITY_NOT_ACCEPTED")
    try:
        verdict = verify_owner_productive_wire_send_authority_v1(
            issuance=wire_send,
            origin_main_sha=origin_main_sha,
            instrument_id=instrument_id,
            exact_envelope_id=exact_envelope_id,
        )
    except FlattenProductiveWireSendAuthorityError as exc:
        raise FlattenHmacGenerationError(str(exc)) from exc
    if verdict.get("accepted") is not True:
        raise FlattenHmacGenerationError("HMAC_WIRE_SEND_AUTHORITY_NOT_ACCEPTED")
    if wire_send.get("consumed") is True or verdict.get("consumed") is True:
        raise FlattenHmacGenerationError("HMAC_WIRE_SEND_AUTHORITY_NOT_ACCEPTED")
    bound_inst = str((receipt.request_body or {}).get("instId") or "").strip()
    if bound_inst and bound_inst != str(instrument_id or "").strip():
        raise FlattenHmacGenerationError("HMAC_INSTRUMENT_MISMATCH")
    if handle is None:
        raise FlattenHmacGenerationError("AUTH_HANDLE_MISSING")
    if not isinstance(handle, LiveCanaryEphemeralCredentialHandleV1):
        raise FlattenHmacGenerationError("AUTH_HANDLE_TYPE_MISMATCH")
    method_u = str(request.method or "").strip().upper()
    url = str(request.url or "").strip()
    body_text = str(request.body_text or "")
    try:
        headers = attach_authenticated_headers_via_existing_signer_v1(
            handle=handle,
            url=url,
            method=method_u,
            body=body_text,
        )
    except AuthenticatedProductiveTransportError as exc:
        raise FlattenHmacGenerationError(str(exc)) from exc
    except LiveCanarySignerError as exc:
        raise FlattenHmacGenerationError(str(exc)) from exc
    except LiveCanaryCredentialError as exc:
        raise FlattenHmacGenerationError(str(exc)) from exc
    except BoundTestnetHttpClientError as exc:
        raise FlattenHmacGenerationError(str(exc)) from exc
    lookup = {str(k).strip().upper(): str(v) for k, v in headers.items()}
    timestamp = str(lookup.get("OK-ACCESS-TIMESTAMP") or "").strip()
    try:
        signing_input = construct_okx_signing_input_v1(
            timestamp=timestamp,
            method=method_u,
            url=url,
            body=body_text,
        )
    except AuthenticatedProductiveTransportError as exc:
        raise FlattenHmacGenerationError(str(exc)) from exc
    except BoundTestnetHttpClientError as exc:
        raise FlattenHmacGenerationError(str(exc)) from exc
    if signing_input.body != body_text or signing_input.body != receipt.approved_body_text:
        raise FlattenHmacGenerationError("BODY_CHANGED_AFTER_GATE")
    if signing_input.method != method_u:
        raise FlattenHmacGenerationError("REQUEST_IDENTITY_MISMATCH")
    if signing_input.request_path != okx_request_path_from_url_v1(url):
        raise FlattenHmacGenerationError("REQUEST_IDENTITY_MISMATCH")
    if receipt.send_lease.consumed is True:
        raise FlattenHmacGenerationError("LEASE_CONSUMED_ON_HMAC_GENERATION")
    if wire_send.get("consumed") is True:
        raise FlattenHmacGenerationError("HMAC_WIRE_SEND_AUTHORITY_CONSUMED")
    artifact = AuthenticatedProductiveFlattenHeadersV1(
        request_identity=str(receipt.approved_request_identity),
        method=method_u,
        url=url,
        request_path=signing_input.request_path,
        body_text=body_text,
        timestamp=timestamp,
        signing_input_digest=signing_input_digest_v1(signing_input),
        signing_component=PRODUCTIVE_SIGNING_COMPONENT,
        wire_send_authority_id=str(verdict.get("authority_id") or ""),
        wire_send_accepted=True,
        lease_consumed=False,
        headers=dict(headers),
    )
    assert_no_plaintext_in_payload_v1(artifact.to_dict())
    return artifact


def first_deny_after_hmac_signed_send_v1(
    transport: AuthenticatedGatedProductiveFlattenTransportV1,
    receipt: FlattenPreSendGateReceiptV1,
    artifact: AuthenticatedProductiveFlattenHeadersV1,
) -> str:
    """Send the HMAC-signed request. Must stop before lease consume and urllib."""
    _require_standing_live_flags_false()
    if not isinstance(transport, AuthenticatedGatedProductiveFlattenTransportV1):
        raise FlattenHmacGenerationError("TRANSPORT_TYPE_INVALID")
    signed = hmac_signed_request_from_artifact_v1(receipt, artifact)
    if signed.body_text != artifact.body_text:
        raise FlattenHmacGenerationError("BODY_CHANGED_AFTER_GATE")
    try:
        transport.send(signed)
    except LiveCanaryFlattenProductiveTransportError as exc:
        deny = str(exc)
        if receipt.send_lease.consumed is True:
            raise FlattenHmacGenerationError("LEASE_CONSUMED_ON_PRE_WIRE_DENY") from exc
        if transport.last_wire_attempted is True or getattr(transport, "_sent", False) is True:
            raise FlattenHmacGenerationError("WIRE_ATTEMPTED_ON_PRE_WIRE_DENY") from exc
        if deny == "UNSIGNED_PRODUCTIVE_HEADERS":
            raise FlattenHmacGenerationError("HMAC_HEADERS_NOT_ACCEPTED_ON_SEND") from exc
        if deny == "RECEIPT_MISSING":
            raise FlattenHmacGenerationError("RECEIPT_MISSING_AFTER_HMAC") from exc
        return deny
    raise FlattenHmacGenerationError("SEND_SUCCEEDED_WITHOUT_POST_AUTHORITY")
