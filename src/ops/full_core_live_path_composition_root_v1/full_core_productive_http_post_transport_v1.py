"""Full-Core productive trade-order HTTP POST transport. No venue execution here.

The urllib POST path exists and is host-bound to eea.okx.com
/api/v5/trade/order. This slice keeps REAL_VENUE_POST_ALLOWED=false, so the
socket is never opened. Tests inject a non-networking transport.

Canary HTTP clients and §11.14 submit paths are not imported.
Credential material is not loaded.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Protocol
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    TRADE_ORDER_PATH,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    AUTHORIZED_HOST,
    FullCoreSendCredentialHandleV1,
)

USER_AGENT = "PeakTrade-FullCore-CZ-EnvelopeBound-Productive-POST/1"
REST_BASE = f"https://{AUTHORIZED_HOST}"
TRANSPORT_CLASS_NON_NETWORKING_TEST = "FULL_CORE_NON_NETWORKING_TEST_POST_V1"
TRANSPORT_CLASS_PRODUCTIVE_HTTP = "FULL_CORE_PRODUCTIVE_HTTP_TRADE_ORDER_POST_V1"


class FullCoreProductiveHttpPostError(RuntimeError):
    """Fail-closed productive HTTP POST transport violation."""


@dataclass(frozen=True)
class FullCoreTradeOrderPostResultV1:
    post_attempted: bool
    venue_live_contact: bool
    method: str
    endpoint: str
    http_status: int
    payload: Mapping[str, Any]
    transport_class: str
    unknown_outcome: bool = False


class FullCoreProductiveTradeOrderPostTransportV1(Protocol):
    """Injected Full-Core trade-order POST port."""

    def post_trade_order(
        self,
        *,
        payload: Mapping[str, Any],
        permit_id: str,
        envelope_id: str,
        envelope_digest: str,
    ) -> FullCoreTradeOrderPostResultV1: ...


@dataclass
class FullCoreNonNetworkingTestPostTransportV1:
    """Test double. Records exactly the injected POST call. Never networks."""

    post_count: int = 0
    last_payload: Optional[dict[str, Any]] = None
    methods_used: list[str] = field(default_factory=list)
    transport_class: str = TRANSPORT_CLASS_NON_NETWORKING_TEST
    venue_live_contact: bool = False

    def post_trade_order(
        self,
        *,
        payload: Mapping[str, Any],
        permit_id: str,
        envelope_id: str,
        envelope_digest: str,
    ) -> FullCoreTradeOrderPostResultV1:
        del permit_id, envelope_id, envelope_digest
        if self.venue_live_contact is True:
            raise FullCoreProductiveHttpPostError("TEST_TRANSPORT_LIVE_CONTACT_FORBIDDEN")
        self.post_count += 1
        self.methods_used.append("POST")
        self.last_payload = dict(payload)
        return FullCoreTradeOrderPostResultV1(
            post_attempted=True,
            venue_live_contact=False,
            method="POST",
            endpoint=TRADE_ORDER_PATH,
            http_status=0,
            payload={"mocked": True, "code": "0"},
            transport_class=self.transport_class,
            unknown_outcome=False,
        )


class FullCoreProductiveHttpTradeOrderTransportV1:
    """Send-capable urllib POST transport. Socket remains forbidden in this slice."""

    def __init__(self, *, handle: Optional[FullCoreSendCredentialHandleV1] = None) -> None:
        self._handle = handle
        self.post_count = 0
        self.methods_used: list[str] = []
        self.transport_class = TRANSPORT_CLASS_PRODUCTIVE_HTTP
        self.venue_live_contact = False

    def post_trade_order(
        self,
        *,
        payload: Mapping[str, Any],
        permit_id: str,
        envelope_id: str,
        envelope_digest: str,
    ) -> FullCoreTradeOrderPostResultV1:
        del permit_id, envelope_id, envelope_digest, payload
        if self._handle is None or self._handle.bound is not True:
            raise FullCoreProductiveHttpPostError("CREDENTIAL_HANDLE_MISSING")
        if self._handle.material_loaded is True:
            raise FullCoreProductiveHttpPostError("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
        if REAL_VENUE_POST_ALLOWED is True or self.venue_live_contact is True:
            raise FullCoreProductiveHttpPostError("REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE")
        raise FullCoreProductiveHttpPostError("REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE")

    def _perform_http_post_v1(self, *, payload: Mapping[str, Any]) -> None:
        """Actual HTTPS POST seam. Unreachable while REAL_VENUE_POST_ALLOWED is false."""
        if REAL_VENUE_POST_ALLOWED is not True:
            raise FullCoreProductiveHttpPostError("REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE")
        url = f"{REST_BASE}{TRADE_ORDER_PATH}"
        parsed = urlparse(url)
        if parsed.scheme != "https" or str(parsed.hostname or "") != AUTHORIZED_HOST:
            raise FullCoreProductiveHttpPostError("HOST_NOT_EEA_OKX")
        if "www.okx.com" in str(parsed.hostname or ""):
            raise FullCoreProductiveHttpPostError("WWW_OKX_FORBIDDEN")
        body = str(payload).encode("utf-8")
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        req = Request(url, data=body, method="POST", headers=headers)
        opener = build_opener(ProxyHandler({}))
        del req, opener
        raise FullCoreProductiveHttpPostError("REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE")
