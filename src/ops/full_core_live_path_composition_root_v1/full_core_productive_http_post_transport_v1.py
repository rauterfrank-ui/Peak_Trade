"""Full-Core productive trade-order HTTP POST transport.

The urllib POST path is host-bound to eea.okx.com /api/v5/trade/order.
Standing REAL_VENUE_POST_ALLOWED remains false. The socket opens only when
one_shot_real_post=true is passed from an exact envelope-bound permit whose
authority_ref is a later actual-POST Owner-GO. This readiness slice never
passes that flag. Canary/§11.14 submit paths are not imported.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import OpenerDirector, ProxyHandler, Request, build_opener

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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    build_okx_live_canary_auth_headers_v1,
    serialize_signed_post_body_v1,
)

USER_AGENT = "PeakTrade-FullCore-DJ-EnvelopeBound-Productive-POST/1"
REST_BASE = f"https://{AUTHORIZED_HOST}"
TRANSPORT_CLASS_NON_NETWORKING_TEST = "FULL_CORE_NON_NETWORKING_TEST_POST_V1"
TRANSPORT_CLASS_PRODUCTIVE_HTTP = "FULL_CORE_PRODUCTIVE_HTTP_TRADE_ORDER_POST_V1"
DEFAULT_TIMEOUT_SECONDS = 20.0
CONNECT_TIMEOUT_SECONDS = 10.0


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
        one_shot_real_post: bool = False,
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
        one_shot_real_post: bool = False,
    ) -> FullCoreTradeOrderPostResultV1:
        del permit_id, envelope_id, envelope_digest, one_shot_real_post
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
    """Send-capable urllib POST transport. Socket stays closed unless one-shot."""

    def __init__(
        self,
        *,
        handle: Optional[FullCoreSendCredentialHandleV1] = None,
        signing_handle: Any | None = None,
        opener_factory: Callable[[], OpenerDirector] | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._handle = handle
        self._signing_handle = signing_handle
        self._opener_factory = opener_factory
        self.timeout_seconds = float(timeout_seconds)
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
        one_shot_real_post: bool = False,
    ) -> FullCoreTradeOrderPostResultV1:
        del permit_id, envelope_id, envelope_digest
        if self._handle is None or self._handle.bound is not True:
            raise FullCoreProductiveHttpPostError("CREDENTIAL_HANDLE_MISSING")
        if self._handle.material_loaded is True:
            raise FullCoreProductiveHttpPostError("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
        if REAL_VENUE_POST_ALLOWED is True:
            raise FullCoreProductiveHttpPostError("STANDING_REAL_VENUE_POST_FORBIDDEN")
        if one_shot_real_post is not True:
            raise FullCoreProductiveHttpPostError("REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE")
        return self._perform_http_post_v1(payload=payload)

    def _perform_http_post_v1(
        self, *, payload: Mapping[str, Any]
    ) -> FullCoreTradeOrderPostResultV1:
        if REAL_VENUE_POST_ALLOWED is True:
            raise FullCoreProductiveHttpPostError("STANDING_REAL_VENUE_POST_FORBIDDEN")
        if self._signing_handle is None:
            raise FullCoreProductiveHttpPostError("SIGNING_HANDLE_MISSING")
        url = f"{REST_BASE}{TRADE_ORDER_PATH}"
        parsed = urlparse(url)
        if parsed.scheme != "https" or str(parsed.hostname or "") != AUTHORIZED_HOST:
            raise FullCoreProductiveHttpPostError("HOST_NOT_EEA_OKX")
        if "www.okx.com" in str(parsed.hostname or ""):
            raise FullCoreProductiveHttpPostError("WWW_OKX_FORBIDDEN")
        body = serialize_signed_post_body_v1(payload)
        headers = build_okx_live_canary_auth_headers_v1(
            handle=self._signing_handle,
            url=url,
            method="POST",
            body=body,
        )
        headers["User-Agent"] = USER_AGENT
        req = Request(url, data=body.encode("utf-8"), method="POST", headers=headers)
        factory = self._opener_factory or (lambda: build_opener(ProxyHandler({})))
        opener = factory()
        raw = b""
        status = 0
        unknown = False
        try:
            socket.setdefaulttimeout(CONNECT_TIMEOUT_SECONDS)
            self.post_count += 1
            self.methods_used.append("POST")
            with opener.open(req, timeout=self.timeout_seconds) as resp:  # noqa: S310
                status = int(getattr(resp, "status", 200))
                raw = bytes(resp.read() or b"")
                loc_host = str(urlparse(str(getattr(resp, "url", url) or url)).hostname or "")
                if loc_host and loc_host != AUTHORIZED_HOST:
                    raise FullCoreProductiveHttpPostError("REDIRECT_OFF_HOST_FORBIDDEN")
            self.venue_live_contact = True
        except FullCoreProductiveHttpPostError:
            raise
        except TimeoutError as exc:
            unknown = True
            raise FullCoreProductiveHttpPostError("UNKNOWN_OUTCOME") from exc
        except HTTPError as exc:
            status = int(getattr(exc, "code", 0) or 0)
            raw = bytes(exc.read() or b"") if hasattr(exc, "read") else b""
            unknown = True
        except (URLError, OSError, socket.timeout) as exc:
            unknown = True
            raise FullCoreProductiveHttpPostError("UNKNOWN_OUTCOME") from exc
        finally:
            socket.setdefaulttimeout(None)
        parsed_payload: Mapping[str, Any]
        try:
            loaded = json.loads(raw.decode("utf-8") or "{}")
            parsed_payload = loaded if isinstance(loaded, dict) else {"raw": True}
        except (ValueError, UnicodeDecodeError):
            parsed_payload = {}
            unknown = True
        if unknown is True:
            raise FullCoreProductiveHttpPostError("UNKNOWN_OUTCOME")
        return FullCoreTradeOrderPostResultV1(
            post_attempted=True,
            venue_live_contact=True,
            method="POST",
            endpoint=TRADE_ORDER_PATH,
            http_status=status,
            payload=parsed_payload,
            transport_class=self.transport_class,
            unknown_outcome=False,
        )
