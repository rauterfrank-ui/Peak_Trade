"""Dedicated productive flatten transport classes.

Distinct from RecordingFakeCanaryTransportV1 and UrllibLiveCanaryTransportV1.
Default: no network session. Send requires an attached passing pre-send receipt.
This slice never authorizes urllib/network send.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Protocol

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpError,
    LiveCanaryHttpRequestV1,
    LiveCanaryHttpResponseV1,
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
) -> LiveCanaryHttpResponseV1:
    wire = request.body_text.encode("utf-8") if request.body_text else b""
    return LiveCanaryHttpResponseV1(
        status_code=status_code,
        body_bytes=body,
        elapsed_seconds=0.01,
        endpoint=request.endpoint,
        method=request.method,
        send_attempted=True,
        wire_body_sha256=hashlib.sha256(wire).hexdigest(),
        wire_body_byte_len=len(wire),
        redirect_followed=False,
        redirect_status=None,
        redirect_location=sanitize_redirect_location_v1(None),
        response_headers_safe={},
    )


@dataclass
class RecordingProductiveFlattenTransportV1:
    """Test double of the productive flatten class. Records send; no network."""

    is_productive_flatten_transport: bool = True
    is_fake_offline_flatten_transport: bool = False
    transport_class: str = TRANSPORT_CLASS_PRODUCTIVE_FLATTEN_GATED_RECORDING
    venue_live_contact: bool = False
    network_session_authorized: bool = False
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

    Even with a passing gate receipt, urllib is not opened unless
    network_session_authorized is independently True. This wiring slice
    never sets that flag.
    """

    is_productive_flatten_transport: bool = True
    is_fake_offline_flatten_transport: bool = False
    transport_class: str = TRANSPORT_CLASS_PRODUCTIVE_FLATTEN_GATED
    venue_live_contact: bool = True
    network_session_authorized: bool = False
    _receipt: FlattenPreSendReceiptLike | None = field(default=None, init=False, repr=False)
    _sent: bool = field(default=False, init=False, repr=False)

    def attach_pre_send_receipt(self, receipt: FlattenPreSendReceiptLike) -> None:
        if receipt is None or not bool(receipt.allowed):
            raise LiveCanaryFlattenProductiveTransportError("PRODUCTIVE_SEND_RECEIPT_NOT_ALLOWED")
        self._receipt = receipt

    def send(self, request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
        del request
        if self._receipt is None or not bool(self._receipt.allowed):
            raise LiveCanaryFlattenProductiveTransportError("PRODUCTIVE_SEND_WITHOUT_GATE_RECEIPT")
        if self._sent:
            raise LiveCanaryFlattenProductiveTransportError("DUPLICATE_POST_FORBIDDEN")
        self._sent = True
        if not self.network_session_authorized:
            raise LiveCanaryFlattenProductiveTransportError(
                "PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED"
            )
        raise LiveCanaryHttpError("PRODUCTIVE_FLATTEN_URLLIB_NOT_AUTHORIZED_BY_WIRING_SLICE")
