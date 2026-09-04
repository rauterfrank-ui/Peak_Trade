"""Fail-closed AUTHENTICATED_PRODUCTIVE_TRANSPORT offline contract.

Wires existing HMAC signing onto the productive flatten path without a new
signing ontology. Does not GET, POST, flatten, issue a runtime permit, open a
network session, or use live credentials. Unsigned User-Agent-only headers are
not authenticated transport. Fixture HMAC in tests is not credential use.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse

from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.bound_testnet_http_client_v1 import (
    assert_okx_access_timestamp_iso_ms_v1,
    sign_okx_request_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_SUBMIT,
    FORBIDDEN_DEMO_SIMULATION_HEADERS,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpRequestV1,
    LiveCanaryHttpResponseV1,
    sanitize_redirect_location_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    LiveCanaryEphemeralCredentialHandleV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.no_additional_owner_decision_required_v1 import (
    PASS_OFFLINE_CONTRACT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    LiveCanarySignerError,
    build_okx_live_canary_auth_headers_v1,
)

APT_IMPLEMENTATION_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_AUTHENTICATED_PRODUCTIVE_TRANSPORT_MAXIMUM_SAFE_LEVERAGE_V1"
)
PRODUCTIVE_SIGNING_COMPONENT = "build_okx_live_canary_auth_headers_v1"
TRANSPORT_CLASS_AUTHENTICATED_PRODUCTIVE_FLATTEN_GATED = "AUTHENTICATED_PRODUCTIVE_FLATTEN_GATED"
TRANSPORT_CLASS_AUTHENTICATED_PRODUCTIVE_FLATTEN_RECORDING = (
    "AUTHENTICATED_PRODUCTIVE_FLATTEN_RECORDING"
)
REQUIRED_OKX_ACCESS_HEADERS: tuple[str, ...] = (
    "OK-ACCESS-KEY",
    "OK-ACCESS-SIGN",
    "OK-ACCESS-TIMESTAMP",
    "OK-ACCESS-PASSPHRASE",
)
NAMED_REMAINING_AFTER_AUTHENTICATED_PRODUCTIVE_TRANSPORT: tuple[str, ...] = (
    "SEND_TIME_POSITION_REOBSERVATION",
    "BOUNDED_RUNTIME_PERMIT_ISSUANCE",
    "FLATTEN_EXECUTE",
    "NETWORK_SESSION",
)
NAMED_REMAINING_AFTER_AUTHENTICATED_PRODUCTIVE_TRANSPORT_SET = frozenset(
    NAMED_REMAINING_AFTER_AUTHENTICATED_PRODUCTIVE_TRANSPORT
)

REASON_STP_NOT_PASS = "STP_NOT_PASS_OFFLINE_CONTRACT"
REASON_MISSING_STP = "STP_STATUS_MISSING"
REASON_MISSING_REMAINING = "REMAINING_AFTER_AUTHENTICATED_PRODUCTIVE_TRANSPORT_SET_MISSING"
REASON_REMAINING_MISMATCH = "REMAINING_AFTER_AUTHENTICATED_PRODUCTIVE_TRANSPORT_SET_MISMATCH"
REASON_DEDICATED_AUTH_TRANSPORT_REQUIRED = (
    "AUTHENTICATED_PRODUCTIVE_TRANSPORT_DEDICATED_CLASS_REQUIRED"
)
REASON_SIGNING_COMPONENT_MISMATCH = "PRODUCTIVE_SIGNING_COMPONENT_MUST_REUSE_EXISTING_SIGNER"
REASON_SIGNING_ONTOLOGY_INVENTED = "NEW_SIGNING_ONTOLOGY_FORBIDDEN"
REASON_HMAC_REORDERED_BEFORE_08 = "HMAC_HANDLE_MUST_NOT_REORDER_BEFORE_08"
REASON_UNSIGNED_ACCEPTED = "UNSIGNED_HEADERS_MUST_NOT_COUNT_AS_AUTHENTICATED"
REASON_RUNTIME_AUTH_CLAIM = "AUTHENTICATED_PRODUCTIVE_TRANSPORT_MUST_NOT_CLAIM_RUNTIME_PROVEN"
REASON_NETWORK_PROVEN_CLAIM = "AUTHENTICATED_PRODUCTIVE_TRANSPORT_MUST_NOT_CLAIM_NETWORK_PROVEN"
REASON_CREDENTIAL_USE_CLAIM = (
    "AUTHENTICATED_PRODUCTIVE_TRANSPORT_MUST_NOT_CLAIM_CREDENTIAL_USE_PROVEN"
)
REASON_PRIVATE_GET_CLAIM = "AUTHENTICATED_PRODUCTIVE_TRANSPORT_MUST_NOT_CLAIM_PRIVATE_GET_PROVEN"
REASON_POST_PROVEN_CLAIM = "AUTHENTICATED_PRODUCTIVE_TRANSPORT_MUST_NOT_CLAIM_POST_PROVEN"
REASON_LIVE_AUTHORIZED_SUBSTITUTE = (
    "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_AUTHENTICATED_PRODUCTIVE_TRANSPORT"
)
REASON_RUNTIME_PERMIT = "AUTHENTICATED_PRODUCTIVE_TRANSPORT_MUST_NOT_ISSUE_RUNTIME_PERMIT"
REASON_FLATTEN_EXECUTE = "AUTHENTICATED_PRODUCTIVE_TRANSPORT_MUST_NOT_AUTHORIZE_FLATTEN_EXECUTE"
REASON_NETWORK_SESSION = "AUTHENTICATED_PRODUCTIVE_TRANSPORT_MUST_NOT_AUTHORIZE_NETWORK_SESSION"
REASON_POST = "AUTHENTICATED_PRODUCTIVE_TRANSPORT_MUST_NOT_POST"
REASON_GET = "AUTHENTICATED_PRODUCTIVE_TRANSPORT_MUST_NOT_GET"
REASON_IMPLEMENTATION_GO_AS_EXECUTE = "IMPLEMENTATION_GO_USED_AS_FLATTEN_EXECUTE"
REASON_LINEAGE_MISMATCH = "AUTHENTICATED_PRODUCTIVE_TRANSPORT_PREDECESSOR_LINEAGE_MISMATCH"


class AuthenticatedProductiveTransportError(RuntimeError):
    """Fail-closed AUTHENTICATED_PRODUCTIVE_TRANSPORT contract violation."""


def _require_typed_gate_receipt(receipt: Any) -> Any:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
        FlattenPreSendGateReceiptV1,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
        LiveCanaryFlattenProductiveTransportError,
    )

    if receipt is None:
        raise LiveCanaryFlattenProductiveTransportError("RECEIPT_MISSING")
    if not isinstance(receipt, FlattenPreSendGateReceiptV1):
        raise LiveCanaryFlattenProductiveTransportError("RECEIPT_MISSING")
    if not bool(receipt.allowed):
        raise LiveCanaryFlattenProductiveTransportError("RECEIPT_NOT_ALLOWED")
    if not str(receipt.approved_request_identity or "").strip():
        raise LiveCanaryFlattenProductiveTransportError("RECEIPT_REQUEST_IDENTITY_MISSING")
    if not isinstance(receipt.request_body, dict) or not receipt.request_body:
        raise LiveCanaryFlattenProductiveTransportError("RECEIPT_REQUEST_IDENTITY_MISSING")
    return receipt


def _consume_receipt_lease(receipt: Any) -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
        LiveCanaryFlattenProductiveTransportError,
    )

    if receipt.send_lease.consumed:
        raise LiveCanaryFlattenProductiveTransportError("DUPLICATE_POST_FORBIDDEN")
    receipt.send_lease.consumed = True


def _synthetic_response(
    *,
    request: LiveCanaryHttpRequestV1,
    status_code: int,
    body: bytes,
    elapsed_seconds: float = 0.01,
    response_headers_safe: dict[str, str] | None = None,
) -> LiveCanaryHttpResponseV1:
    wire = request.body_text.encode("utf-8") if request.body_text else b""
    return LiveCanaryHttpResponseV1(
        status_code=status_code,
        body_bytes=body,
        elapsed_seconds=elapsed_seconds,
        endpoint=request.endpoint,
        method=request.method,
        send_attempted=True,
        wire_body_sha256=hashlib.sha256(wire).hexdigest(),
        wire_body_byte_len=len(wire),
        redirect_followed=False,
        redirect_status=None,
        redirect_location=sanitize_redirect_location_v1(None),
        response_headers_safe=dict(response_headers_safe or {}),
    )


@dataclass(frozen=True)
class OkxSigningInputV1:
    """Canonical HMAC prehash inputs. Contains no secret and no signature."""

    timestamp: str
    method: str
    request_path: str
    body: str
    prehash: str


def okx_request_path_from_url_v1(url: str) -> str:
    parsed = urlparse(str(url or ""))
    path = parsed.path or ""
    query = parsed.query or ""
    return f"{path}?{query}" if query else path


def construct_okx_signing_input_v1(
    *,
    timestamp: str,
    method: str,
    url: str,
    body: str = "",
) -> OkxSigningInputV1:
    """Build the OKX HMAC prehash without using a secret."""
    ts = assert_okx_access_timestamp_iso_ms_v1(str(timestamp or "").strip())
    method_u = str(method or "").strip().upper()
    if method_u not in {"GET", "POST"}:
        raise AuthenticatedProductiveTransportError(
            f"SIGNER_METHOD_FORBIDDEN:{method_u or '<empty>'}"
        )
    if method_u == "GET" and str(body or ""):
        raise AuthenticatedProductiveTransportError("SIGNER_BODY_FORBIDDEN_FOR_GET")
    request_path = okx_request_path_from_url_v1(url)
    body_text = str(body or "")
    prehash = f"{ts}{method_u}{request_path}{body_text}"
    return OkxSigningInputV1(
        timestamp=ts,
        method=method_u,
        request_path=request_path,
        body=body_text,
        prehash=prehash,
    )


def sign_okx_signing_input_v1(*, secret: str, signing_input: OkxSigningInputV1) -> str:
    """HMAC a previously constructed signing input. Caller supplies the secret."""
    if not str(secret or "").strip():
        raise AuthenticatedProductiveTransportError("SIGNING_SECRET_MISSING")
    return sign_okx_request_v1(
        secret=secret,
        timestamp=signing_input.timestamp,
        method=signing_input.method,
        request_path=signing_input.request_path,
        body=signing_input.body,
    )


def _header_map(headers: Mapping[str, str] | None) -> dict[str, str]:
    if not headers:
        return {}
    return {str(k): str(v) for k, v in headers.items()}


def _header_lookup(headers: Mapping[str, str]) -> dict[str, str]:
    return {str(k).strip().upper(): str(v) for k, v in headers.items()}


def assert_no_demo_simulation_headers_v1(headers: Mapping[str, str] | None) -> None:
    for key, value in _header_map(headers).items():
        key_l = str(key).strip().lower()
        if key_l in FORBIDDEN_DEMO_SIMULATION_HEADERS:
            raise AuthenticatedProductiveTransportError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key}")
        if str(value).strip() in {"1", "true", "yes"} and "simul" in key_l:
            raise AuthenticatedProductiveTransportError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key}")


def assert_authenticated_productive_headers_v1(headers: Mapping[str, str] | None) -> dict[str, str]:
    """Presence contract only. Does not verify HMAC against a secret."""
    mapped = _header_map(headers)
    if not mapped:
        raise AuthenticatedProductiveTransportError("UNSIGNED_PRODUCTIVE_HEADERS")
    assert_no_demo_simulation_headers_v1(mapped)
    lookup = _header_lookup(mapped)
    missing = [
        name
        for name in REQUIRED_OKX_ACCESS_HEADERS
        if name not in lookup or not lookup[name].strip()
    ]
    if missing:
        raise AuthenticatedProductiveTransportError("UNSIGNED_PRODUCTIVE_HEADERS")
    if not str(lookup.get("USER-AGENT") or "").strip():
        raise AuthenticatedProductiveTransportError("AUTHENTICATED_USER_AGENT_MISSING")
    return mapped


def attach_authenticated_headers_via_existing_signer_v1(
    *,
    handle: LiveCanaryEphemeralCredentialHandleV1 | None,
    url: str,
    method: str,
    body: str = "",
    extra_headers: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Reuse build_okx_live_canary_auth_headers_v1. Missing handle fails closed."""
    if handle is None:
        raise AuthenticatedProductiveTransportError("AUTH_HANDLE_MISSING")
    if not isinstance(handle, LiveCanaryEphemeralCredentialHandleV1):
        raise AuthenticatedProductiveTransportError("AUTH_HANDLE_TYPE_MISMATCH")
    try:
        headers = build_okx_live_canary_auth_headers_v1(
            handle=handle,
            url=url,
            method=method,
            body=body,
            extra_headers=extra_headers,
        )
    except LiveCanarySignerError as exc:
        raise AuthenticatedProductiveTransportError(str(exc)) from exc
    return assert_authenticated_productive_headers_v1(headers)


def _norm_items(values: Sequence[str] | Iterable[str] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return tuple(out)


def evaluate_authenticated_productive_transport_v1(
    *,
    stp_status: str | None,
    dedicated_authenticated_transport: bool,
    signing_component: str | None,
    signing_ontology_invented: bool,
    hmac_handle_reordered_before_08: bool,
    unsigned_headers_accepted_as_authenticated: bool,
    claimed_remaining_after_authenticated_productive_transport: Sequence[str] | None,
    runtime_authentication_proven_claim: bool = False,
    network_proven_claim: bool = False,
    credential_use_proven_claim: bool = False,
    private_get_proven_claim: bool = False,
    post_proven_claim: bool = False,
    live_authorized_claim: bool = False,
    runtime_permit_issuance_claim: bool = False,
    flatten_execute_authorized_claim: bool = False,
    network_session_authorized_claim: bool = False,
    post_performed_claim: bool = False,
    get_performed_claim: bool = False,
    flatten_execute_owner_go: str | None = None,
    predecessor_lineage_ok: bool = True,
) -> tuple[bool, tuple[str, ...]]:
    """Return (accepted, deny_reasons). Never transmits. Never borrows secrets."""
    reasons: list[str] = []
    stp = str(stp_status or "").strip()
    if not stp:
        reasons.append(REASON_MISSING_STP)
    elif stp != PASS_OFFLINE_CONTRACT:
        reasons.append(REASON_STP_NOT_PASS)
    if claimed_remaining_after_authenticated_productive_transport is None:
        reasons.append(REASON_MISSING_REMAINING)
    else:
        claimed = frozenset(_norm_items(claimed_remaining_after_authenticated_productive_transport))
        if claimed != NAMED_REMAINING_AFTER_AUTHENTICATED_PRODUCTIVE_TRANSPORT_SET:
            reasons.append(REASON_REMAINING_MISMATCH)
    if dedicated_authenticated_transport is not True:
        reasons.append(REASON_DEDICATED_AUTH_TRANSPORT_REQUIRED)
    if str(signing_component or "").strip() != PRODUCTIVE_SIGNING_COMPONENT:
        reasons.append(REASON_SIGNING_COMPONENT_MISMATCH)
    if signing_ontology_invented is True:
        reasons.append(REASON_SIGNING_ONTOLOGY_INVENTED)
    if hmac_handle_reordered_before_08 is True:
        reasons.append(REASON_HMAC_REORDERED_BEFORE_08)
    if unsigned_headers_accepted_as_authenticated is True:
        reasons.append(REASON_UNSIGNED_ACCEPTED)
    if runtime_authentication_proven_claim is True:
        reasons.append(REASON_RUNTIME_AUTH_CLAIM)
    if network_proven_claim is True:
        reasons.append(REASON_NETWORK_PROVEN_CLAIM)
    if credential_use_proven_claim is True:
        reasons.append(REASON_CREDENTIAL_USE_CLAIM)
    if private_get_proven_claim is True:
        reasons.append(REASON_PRIVATE_GET_CLAIM)
    if post_proven_claim is True:
        reasons.append(REASON_POST_PROVEN_CLAIM)
    if live_authorized_claim is True:
        reasons.append(REASON_LIVE_AUTHORIZED_SUBSTITUTE)
    if runtime_permit_issuance_claim is True:
        reasons.append(REASON_RUNTIME_PERMIT)
    if flatten_execute_authorized_claim is True:
        reasons.append(REASON_FLATTEN_EXECUTE)
    if network_session_authorized_claim is True:
        reasons.append(REASON_NETWORK_SESSION)
    if post_performed_claim is True:
        reasons.append(REASON_POST)
    if get_performed_claim is True:
        reasons.append(REASON_GET)
    execute_go = str(flatten_execute_owner_go or "").strip()
    if execute_go == APT_IMPLEMENTATION_OWNER_GO:
        reasons.append(REASON_IMPLEMENTATION_GO_AS_EXECUTE)
    if predecessor_lineage_ok is not True:
        reasons.append(REASON_LINEAGE_MISMATCH)
    return (not reasons), tuple(reasons)


def canonical_remaining_after_authenticated_productive_transport_v1() -> tuple[str, ...]:
    return NAMED_REMAINING_AFTER_AUTHENTICATED_PRODUCTIVE_TRANSPORT


def assert_runtime_authority_not_claimed_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("AUTHENTICATED_PRODUCTIVE_TRANSPORT_RUNTIME_PROVEN") is True:
        raise AuthenticatedProductiveTransportError("RUNTIME_AUTHENTICATION_CLAIMED")
    if payload.get("AUTHENTICATION_PROVEN") is True:
        raise AuthenticatedProductiveTransportError("AUTHENTICATION_PROVEN_CLAIMED")
    if payload.get("NETWORK_PROVEN") is True:
        raise AuthenticatedProductiveTransportError("NETWORK_PROVEN_CLAIMED")
    if payload.get("CREDENTIAL_USE_PROVEN") is True:
        raise AuthenticatedProductiveTransportError("CREDENTIAL_USE_PROVEN_CLAIMED")
    if payload.get("PRIVATE_GET_PROVEN") is True:
        raise AuthenticatedProductiveTransportError("PRIVATE_GET_PROVEN_CLAIMED")
    if payload.get("POST_PROVEN") is True:
        raise AuthenticatedProductiveTransportError("POST_PROVEN_CLAIMED")
    if payload.get("BOUNDED_RUNTIME_PERMIT_ISSUANCE") is True:
        raise AuthenticatedProductiveTransportError("RUNTIME_PERMIT_CLAIMED")
    if payload.get("LIVE_AUTHORIZED") is True:
        raise AuthenticatedProductiveTransportError("LIVE_AUTHORIZED_CLAIMED_TRUE")
    if payload.get("POST_PERFORMED") is True:
        raise AuthenticatedProductiveTransportError("POST_CLAIMED")


@dataclass
class RecordingAuthenticatedProductiveFlattenTransportV1:
    """No-wire authenticated flatten double. Requires HMAC header presence. No urllib."""

    is_productive_flatten_transport: bool = True
    is_authenticated_productive_flatten_transport: bool = True
    is_fake_offline_flatten_transport: bool = False
    transport_class: str = TRANSPORT_CLASS_AUTHENTICATED_PRODUCTIVE_FLATTEN_RECORDING
    venue_live_contact: bool = False
    network_session_authorized: bool = False
    last_wire_attempted: bool = False
    calls: list[LiveCanaryHttpRequestV1] = field(default_factory=list)
    post_body: bytes = (
        b'{"code":"0","data":[{"sCode":"0","ordId":"synthetic-flatten","clOrdId":"x","sz":"1"}]}'
    )
    post_status_code: int = 200
    _receipt: Any = field(default=None, init=False, repr=False)

    def attach_pre_send_receipt(self, receipt: Any) -> None:
        self._receipt = _require_typed_gate_receipt(receipt)

    def send(self, request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
        from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
            LiveCanaryFlattenProductiveTransportError,
            assert_request_matches_flatten_receipt_v1,
        )

        self.last_wire_attempted = False
        receipt = _require_typed_gate_receipt(self._receipt)
        assert_request_matches_flatten_receipt_v1(receipt, request)
        try:
            assert_authenticated_productive_headers_v1(request.headers)
        except AuthenticatedProductiveTransportError as exc:
            raise LiveCanaryFlattenProductiveTransportError(str(exc)) from exc
        _consume_receipt_lease(receipt)
        if self.calls:
            raise LiveCanaryFlattenProductiveTransportError("DUPLICATE_POST_FORBIDDEN")
        self.calls.append(request)
        return _synthetic_response(
            request=request,
            status_code=int(self.post_status_code),
            body=self.post_body,
        )


@dataclass
class AuthenticatedGatedProductiveFlattenTransportV1:
    """Authenticated productive flatten transport. Network session stays false.

    Reuses the gated flatten identity/lease contract. HMAC header presence is
    required before urllib would open. This class never sets
    network_session_authorized true and never invents a signing ontology.
    """

    is_productive_flatten_transport: bool = True
    is_authenticated_productive_flatten_transport: bool = True
    is_fake_offline_flatten_transport: bool = False
    transport_class: str = TRANSPORT_CLASS_AUTHENTICATED_PRODUCTIVE_FLATTEN_GATED
    venue_live_contact: bool = True
    network_session_authorized: bool = False
    last_wire_attempted: bool = False
    signing_component: str = PRODUCTIVE_SIGNING_COMPONENT
    _receipt: Any = field(default=None, init=False, repr=False)
    _sent: bool = field(default=False, init=False, repr=False)

    def attach_pre_send_receipt(self, receipt: Any) -> None:
        self._receipt = _require_typed_gate_receipt(receipt)

    def send(self, request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
        from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
            LiveCanaryFlattenProductiveTransportError,
            assert_request_matches_flatten_receipt_v1,
        )

        self.last_wire_attempted = False
        receipt = _require_typed_gate_receipt(self._receipt)
        assert_request_matches_flatten_receipt_v1(receipt, request)
        try:
            assert_authenticated_productive_headers_v1(request.headers)
        except AuthenticatedProductiveTransportError as exc:
            raise LiveCanaryFlattenProductiveTransportError(str(exc)) from exc
        if str(self.signing_component or "").strip() != PRODUCTIVE_SIGNING_COMPONENT:
            raise LiveCanaryFlattenProductiveTransportError("PRODUCTIVE_SIGNING_COMPONENT_MISMATCH")
        if str(request.host or "").strip() != REUSED_BINDING_REST_HOST:
            raise LiveCanaryFlattenProductiveTransportError("PRODUCTIVE_FLATTEN_HOST_MISMATCH")
        if str(request.endpoint or "").strip() != ENDPOINT_SUBMIT:
            raise LiveCanaryFlattenProductiveTransportError(
                "PRODUCTIVE_FLATTEN_ENDPOINT_NOT_ALLOWLISTED"
            )
        if self._sent or receipt.send_lease.consumed:
            raise LiveCanaryFlattenProductiveTransportError("DUPLICATE_POST_FORBIDDEN")
        _consume_receipt_lease(receipt)
        self._sent = True
        if not self.network_session_authorized:
            raise LiveCanaryFlattenProductiveTransportError(
                "PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED"
            )
        raise LiveCanaryFlattenProductiveTransportError(
            "AUTHENTICATED_PRODUCTIVE_TRANSPORT_WIRE_SEND_NOT_AUTHORIZED"
        )


def authenticated_header_presence_doc_v1(headers: Mapping[str, str] | None) -> dict[str, Any]:
    lookup = _header_lookup(_header_map(headers))
    return {
        "OK-ACCESS-KEY_PRESENT": "OK-ACCESS-KEY" in lookup
        and bool(lookup["OK-ACCESS-KEY"].strip()),
        "OK-ACCESS-SIGN_PRESENT": "OK-ACCESS-SIGN" in lookup
        and bool(lookup["OK-ACCESS-SIGN"].strip()),
        "OK-ACCESS-TIMESTAMP_PRESENT": "OK-ACCESS-TIMESTAMP" in lookup
        and bool(lookup["OK-ACCESS-TIMESTAMP"].strip()),
        "OK-ACCESS-PASSPHRASE_PRESENT": "OK-ACCESS-PASSPHRASE" in lookup
        and bool(lookup["OK-ACCESS-PASSPHRASE"].strip()),
        "SIMULATION_HEADER_PRESENT": any(
            str(k).strip().lower() in FORBIDDEN_DEMO_SIMULATION_HEADERS
            for k in _header_map(headers)
        ),
        "signing_input_secret_included": False,
        "PRODUCTIVE_SIGNING_COMPONENT": PRODUCTIVE_SIGNING_COMPONENT,
    }


def signing_input_digest_v1(signing_input: OkxSigningInputV1) -> str:
    return hashlib.sha256(signing_input.prehash.encode("utf-8")).hexdigest()
