"""Full-Core productive READ-ONLY GET transport for Fresh Pretrade.

GET only. No POST. Does not construct LiveExecutionPort. Does not import
canary instrument authority. Signer reuse is transport plumbing only.
"""

from __future__ import annotations

import hashlib
import json
import socket
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    METHOD_GET,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
    FreshPretradeGetTransportResultV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    parse_json_object_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    build_okx_live_canary_auth_headers_v1,
)

AUTHORIZED_HOST = "eea.okx.com"
REST_BASE = f"https://{AUTHORIZED_HOST}"
USER_AGENT = "PeakTrade-FullCore-CZ-Productive-ReadOnly-GET/1"
DEFAULT_TIMEOUT_SECONDS = 20.0
CONNECT_TIMEOUT_SECONDS = 10.0
FORBIDDEN_METHODS = frozenset({"POST", "PUT", "DELETE", "PATCH"})
FORBIDDEN_ENDPOINTS = (
    "/api/v5/trade/order",
    "/api/v5/trade/cancel-order",
    "/api/v5/asset/withdrawal",
    "/api/v5/asset/transfer",
)


class FullCoreProductiveReadOnlyGetError(RuntimeError):
    """Fail-closed productive GET-only transport violation."""


class FullCoreProductiveReadOnlyGetTransportV1:
    """GET-only Full-Core venue transport. Never POST. No wire-send of orders."""

    def __init__(
        self,
        *,
        handle: Any | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_request_count: int = 16,
    ) -> None:
        self._handle = handle
        self.timeout_seconds = float(timeout_seconds)
        self.max_request_count = int(max_request_count)
        self.request_count = 0
        self.methods_used: list[str] = []
        self.venue_live_contact = False
        self.transport_class = TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET
        self._cache: dict[str, FreshPretradeGetTransportResultV1] = {}
        self.payloads_by_path: dict[str, Any] = {}

    def get(
        self,
        *,
        endpoint: str,
        auth_required: bool,
        pretrade_decision_id: str,
    ) -> FreshPretradeGetTransportResultV1:
        del pretrade_decision_id
        cached = self._cache.get(str(endpoint))
        if cached is not None:
            return cached
        if self.request_count >= self.max_request_count:
            raise FullCoreProductiveReadOnlyGetError("MAX_REQUEST_COUNT_EXCEEDED")
        path = str(endpoint or "").split("?", 1)[0]
        if path in FORBIDDEN_ENDPOINTS:
            raise FullCoreProductiveReadOnlyGetError("FORBIDDEN_ENDPOINT")
        url = endpoint if str(endpoint).startswith("https://") else f"{REST_BASE}{endpoint}"
        parsed = urlparse(url)
        if parsed.scheme != "https" or str(parsed.hostname or "") != AUTHORIZED_HOST:
            raise FullCoreProductiveReadOnlyGetError("HOST_NOT_EEA_OKX")
        if "www.okx.com" in str(parsed.hostname or ""):
            raise FullCoreProductiveReadOnlyGetError("WWW_OKX_FORBIDDEN")
        headers: dict[str, str] = {"Accept": "application/json", "User-Agent": USER_AGENT}
        auth_sent = False
        if auth_required:
            if self._handle is None:
                raise FullCoreProductiveReadOnlyGetError("PRIVATE_GET_REQUIRES_CREDENTIAL_HANDLE")
            headers = build_okx_live_canary_auth_headers_v1(
                handle=self._handle, url=url, method=METHOD_GET
            )
            headers["User-Agent"] = USER_AGENT
            auth_sent = True
        req = Request(url, method=METHOD_GET, headers=headers)
        opener = build_opener(ProxyHandler({}))
        body = b""
        status = 0
        error_class = ""
        payload: Any = None
        try:
            socket.setdefaulttimeout(CONNECT_TIMEOUT_SECONDS)
            with opener.open(req, timeout=self.timeout_seconds) as resp:  # noqa: S310
                status = int(getattr(resp, "status", 200))
                body = bytes(resp.read() or b"")
                loc_host = str(urlparse(str(getattr(resp, "url", url) or url)).hostname or "")
                if loc_host and loc_host != AUTHORIZED_HOST:
                    raise FullCoreProductiveReadOnlyGetError("REDIRECT_OFF_HOST_FORBIDDEN")
            self.venue_live_contact = True
        except FullCoreProductiveReadOnlyGetError:
            raise
        except TimeoutError:
            error_class = "TIMEOUT"
        except HTTPError as exc:
            status = int(getattr(exc, "code", 0) or 0)
            body = bytes(exc.read() or b"") if hasattr(exc, "read") else b""
            error_class = "AUTH_FAILURE" if status in {401, 403} else "HTTP_ERROR"
        except (URLError, OSError, socket.timeout) as exc:
            error_class = type(exc).__name__[:80]
        finally:
            socket.setdefaulttimeout(None)
        self.request_count += 1
        self.methods_used.append(METHOD_GET)
        if any(method in FORBIDDEN_METHODS for method in self.methods_used):
            raise FullCoreProductiveReadOnlyGetError("NON_GET_FORBIDDEN")
        if body:
            try:
                payload = parse_json_object_v1(body)
            except (ValueError, json.JSONDecodeError):
                error_class = error_class or "MALFORMED_JSON"
                payload = None
        result = FreshPretradeGetTransportResultV1(
            get_performed=status == 200 and payload is not None,
            method=METHOD_GET,
            endpoint=endpoint,
            http_status=status,
            payload=payload,
            auth_header_sent=auth_sent,
            transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
            venue_live_contact=bool(self.venue_live_contact and status == 200),
            historical_reuse=False,
            error_class=error_class,
            body_sha256=hashlib.sha256(body).hexdigest() if body else "",
        )
        self._cache[str(endpoint)] = result
        path_only = str(endpoint).split("?", 1)[0]
        self.payloads_by_path[path_only] = payload
        return result
