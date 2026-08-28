"""Dedicated productive flatten transport classes.

Distinct from RecordingFakeCanaryTransportV1 and UrllibLiveCanaryTransportV1.
Default: no network session. Send requires an attached passing pre-send receipt.
Urllib opens only after that receipt, one-shot protection, and an independently
true network_session_authorized flag. This module never sets that flag true.
Authenticated OKX header construction is not wired here.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_SUBMIT,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    CanaryPostRedirectBlockedError,
    CanaryPostRedirectFailClosedHandler,
    LiveCanaryHttpError,
    LiveCanaryHttpRequestV1,
    LiveCanaryHttpResponseV1,
    safe_response_headers_v1,
    sanitize_redirect_location_v1,
)

TRANSPORT_CLASS_PRODUCTIVE_FLATTEN_GATED = "PRODUCTIVE_FLATTEN_GATED"
TRANSPORT_CLASS_PRODUCTIVE_FLATTEN_GATED_RECORDING = "PRODUCTIVE_FLATTEN_GATED_RECORDING"


class FlattenPreSendReceiptLike(Protocol):
    allowed: bool
    gate_digest: str


class LiveCanaryFlattenProductiveTransportError(RuntimeError):
    """Fail-closed productive flatten transport violation."""


def _response(
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


def _headers_mapping(headers: Any) -> dict[str, str]:
    if headers is None:
        return {}
    if hasattr(headers, "items"):
        return {str(k): str(v) for k, v in headers.items()}
    return {}


def assert_productive_flatten_post_request_v1(request: LiveCanaryHttpRequestV1) -> None:
    """Fail-closed allowlist for the already-bound flatten POST contract."""
    method = str(request.method or "").strip().upper()
    host = str(request.host or "").strip()
    endpoint = str(request.endpoint or "").strip()
    url = str(request.url or "").strip()
    if method != "POST":
        raise LiveCanaryFlattenProductiveTransportError("PRODUCTIVE_FLATTEN_METHOD_NOT_POST")
    if host != REUSED_BINDING_REST_HOST:
        raise LiveCanaryFlattenProductiveTransportError("PRODUCTIVE_FLATTEN_HOST_MISMATCH")
    if endpoint != ENDPOINT_SUBMIT:
        raise LiveCanaryFlattenProductiveTransportError(
            "PRODUCTIVE_FLATTEN_ENDPOINT_NOT_ALLOWLISTED"
        )
    if "close-position" in endpoint or "close-position" in url:
        raise LiveCanaryFlattenProductiveTransportError("CLOSE_POSITION_ENDPOINT_FORBIDDEN")
    if "/trade/cancel-order" in endpoint or "/trade/cancel-order" in url:
        raise LiveCanaryFlattenProductiveTransportError("CANCEL_ENDPOINT_FORBIDDEN")
    expected_url = f"https://{REUSED_BINDING_REST_HOST}{ENDPOINT_SUBMIT}"
    if url.rstrip("/") != expected_url:
        raise LiveCanaryFlattenProductiveTransportError("PRODUCTIVE_FLATTEN_URL_MISMATCH")


def open_productive_flatten_urllib_post_v1(
    request: LiveCanaryHttpRequestV1,
) -> LiveCanaryHttpResponseV1:
    """POST opener for productive flatten. Redirects fail closed. No canary permit.

    Sends the caller-supplied request as constructed. This is not OKX auth
    construction and not canary entry POST.
    """
    assert_productive_flatten_post_request_v1(request)
    wire_bytes = request.body_text.encode("utf-8") if request.body_text else b""
    data = wire_bytes if wire_bytes else None
    req = Request(request.url, data=data, method="POST", headers=dict(request.headers))
    started = time.monotonic()
    opener = build_opener(ProxyHandler({}), CanaryPostRedirectFailClosedHandler())
    header_src: Any = None
    try:
        with opener.open(req, timeout=request.timeout_seconds) as resp:  # noqa: S310
            body = resp.read()
            status = int(getattr(resp, "status", 200))
            header_src = getattr(resp, "headers", None)
    except CanaryPostRedirectBlockedError:
        raise
    except HTTPError as exc:
        body = exc.read() if hasattr(exc, "read") else b""
        status = int(exc.code)
        header_src = getattr(exc, "headers", None)
    elapsed = time.monotonic() - started
    raw_headers = _headers_mapping(header_src)
    return LiveCanaryHttpResponseV1(
        status_code=status,
        body_bytes=body if isinstance(body, (bytes, bytearray)) else b"",
        elapsed_seconds=elapsed,
        endpoint=request.endpoint,
        method="POST",
        send_attempted=True,
        wire_body_sha256=hashlib.sha256(wire_bytes).hexdigest(),
        wire_body_byte_len=len(wire_bytes),
        redirect_followed=False,
        redirect_status=None,
        redirect_location=sanitize_redirect_location_v1(None),
        response_headers_safe=safe_response_headers_v1(raw_headers),
    )


@dataclass
class RecordingProductiveFlattenTransportV1:
    """Test double of the productive flatten class. Records send; no network."""

    is_productive_flatten_transport: bool = True
    is_fake_offline_flatten_transport: bool = False
    transport_class: str = TRANSPORT_CLASS_PRODUCTIVE_FLATTEN_GATED_RECORDING
    venue_live_contact: bool = False
    network_session_authorized: bool = False
    last_wire_attempted: bool = False
    calls: list[LiveCanaryHttpRequestV1] = field(default_factory=list)
    post_body: bytes = (
        b'{"code":"0","data":[{"sCode":"0","ordId":"synthetic-flatten","clOrdId":"x","sz":"1"}]}'
    )
    post_status_code: int = 200
    _receipt: FlattenPreSendReceiptLike | None = field(default=None, init=False, repr=False)

    def attach_pre_send_receipt(self, receipt: FlattenPreSendReceiptLike) -> None:
        if receipt is None or not bool(receipt.allowed):
            raise LiveCanaryFlattenProductiveTransportError("PRODUCTIVE_SEND_RECEIPT_NOT_ALLOWED")
        self._receipt = receipt

    def send(self, request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
        self.last_wire_attempted = False
        if self._receipt is None or not bool(self._receipt.allowed):
            raise LiveCanaryFlattenProductiveTransportError("PRODUCTIVE_SEND_WITHOUT_GATE_RECEIPT")
        if self.calls:
            raise LiveCanaryFlattenProductiveTransportError("DUPLICATE_POST_FORBIDDEN")
        self.calls.append(request)
        return _response(
            request=request,
            status_code=int(self.post_status_code),
            body=self.post_body,
        )


@dataclass
class GatedProductiveFlattenTransportV1:
    """Productive flatten transport. Network session defaults unauthorized.

    This class never sets network_session_authorized true. Urllib opens only
    when that flag is independently True after a passing receipt and one-shot
    protection. Request signing is not performed here.
    """

    is_productive_flatten_transport: bool = True
    is_fake_offline_flatten_transport: bool = False
    transport_class: str = TRANSPORT_CLASS_PRODUCTIVE_FLATTEN_GATED
    venue_live_contact: bool = True
    network_session_authorized: bool = False
    last_wire_attempted: bool = False
    _receipt: FlattenPreSendReceiptLike | None = field(default=None, init=False, repr=False)
    _sent: bool = field(default=False, init=False, repr=False)

    def attach_pre_send_receipt(self, receipt: FlattenPreSendReceiptLike) -> None:
        if receipt is None or not bool(receipt.allowed):
            raise LiveCanaryFlattenProductiveTransportError("PRODUCTIVE_SEND_RECEIPT_NOT_ALLOWED")
        self._receipt = receipt

    def send(self, request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
        self.last_wire_attempted = False
        if self._receipt is None or not bool(self._receipt.allowed):
            raise LiveCanaryFlattenProductiveTransportError("PRODUCTIVE_SEND_WITHOUT_GATE_RECEIPT")
        if self._sent:
            raise LiveCanaryFlattenProductiveTransportError("DUPLICATE_POST_FORBIDDEN")
        self._sent = True
        if not self.network_session_authorized:
            raise LiveCanaryFlattenProductiveTransportError(
                "PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED"
            )
        assert_productive_flatten_post_request_v1(request)
        self.last_wire_attempted = True
        try:
            return open_productive_flatten_urllib_post_v1(request)
        except CanaryPostRedirectBlockedError as exc:
            raise LiveCanaryFlattenProductiveTransportError(
                f"POST_REDIRECT_FAIL_CLOSED:{exc.status_code}"
            ) from exc
        except TimeoutError as exc:
            raise LiveCanaryFlattenProductiveTransportError(
                "PRODUCTIVE_FLATTEN_WIRE_TIMEOUT"
            ) from exc
        except LiveCanaryHttpError as exc:
            raise LiveCanaryFlattenProductiveTransportError(str(exc)) from exc
        except (URLError, OSError) as exc:
            raise LiveCanaryFlattenProductiveTransportError(
                f"PRODUCTIVE_FLATTEN_WIRE_ERROR:{exc}"
            ) from exc
