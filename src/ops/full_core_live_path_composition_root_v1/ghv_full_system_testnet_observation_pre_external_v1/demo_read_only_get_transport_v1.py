"""GET-only Demo transport for GHV Full-System Testnet Observation Fresh-Pretrade."""

from __future__ import annotations

import hashlib
import json
import socket
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener

from src.data.safety import DataSourceKind
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    METHOD_GET,
    FreshPretradeGetTransportResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.constants_v1 import (
    FORBIDDEN_HTTP_METHODS,
    PRIVATE_GET_CATALOG_PATHS,
    PUBLIC_MARKET_HOST,
    TRANSPORT_CLASS_DEMO_READ_ONLY_GET,
    USER_AGENT_DEMO_READ_ONLY_GET,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.demo_okx_venue_auth_headers_v1 import (
    FullCoreDemoBoundVenueAuthHandleV1,
    build_demo_okx_public_headers_v1,
    build_demo_okx_venue_auth_headers_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FORBIDDEN_ENDPOINTS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    parse_json_object_v1,
)

AUTHORIZED_HOST = PUBLIC_MARKET_HOST
REST_BASE = f"https://{AUTHORIZED_HOST}"
DEFAULT_TIMEOUT_SECONDS = 20.0
CONNECT_TIMEOUT_SECONDS = 10.0

HttpOpenerFactory = Callable[[], Any]


class GhvDemoReadOnlyGetTransportError(RuntimeError):
    """Fail-closed Demo GET-only transport violation."""


class GhvDemoReadOnlyGetTransportV1:
    """Demo private GET + GHV public GET. Structurally GET-only (no write methods)."""

    def __init__(
        self,
        *,
        handle: FullCoreDemoBoundVenueAuthHandleV1 | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_request_count: int = 16,
        http_opener_factory: HttpOpenerFactory | None = None,
    ) -> None:
        self._handle = handle
        self.timeout_seconds = float(timeout_seconds)
        self.max_request_count = int(max_request_count)
        self.request_count = 0
        self.methods_used: list[str] = []
        self.venue_live_contact = False
        self.transport_class = TRANSPORT_CLASS_DEMO_READ_ONLY_GET
        self._cache: dict[str, FreshPretradeGetTransportResultV1] = {}
        self.payloads_by_path: dict[str, Any] = {}
        self._http_opener_factory = http_opener_factory

    def get(
        self,
        *,
        endpoint: str,
        auth_required: bool,
        pretrade_decision_id: str,
        get_cache_policy: str = GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
    ) -> FreshPretradeGetTransportResultV1:
        del pretrade_decision_id
        cacheable = get_cache_policy == GET_CACHE_POLICY_CACHEABLE_SNAPSHOT
        if get_cache_policy not in (
            GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
            GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        ):
            raise GhvDemoReadOnlyGetTransportError("INVALID_GET_CACHE_POLICY")
        cached = self._cache.get(str(endpoint)) if cacheable else None
        if cached is not None:
            return cached
        if self.request_count >= self.max_request_count:
            raise GhvDemoReadOnlyGetTransportError("MAX_REQUEST_COUNT_EXCEEDED")
        path = str(endpoint or "").split("?", 1)[0]
        if path in FORBIDDEN_ENDPOINTS:
            raise GhvDemoReadOnlyGetTransportError("FORBIDDEN_ENDPOINT")
        if auth_required and path not in PRIVATE_GET_CATALOG_PATHS:
            raise GhvDemoReadOnlyGetTransportError("PRIVATE_GET_PATH_NOT_IN_DEMO_CATALOG")
        url = endpoint if str(endpoint).startswith("https://") else f"{REST_BASE}{endpoint}"
        parsed = urlparse(url)
        if parsed.scheme != "https" or str(parsed.hostname or "") != AUTHORIZED_HOST:
            raise GhvDemoReadOnlyGetTransportError("HOST_NOT_EEA_OKX")
        headers: dict[str, str]
        auth_sent = False
        if auth_required:
            if self._handle is None:
                raise GhvDemoReadOnlyGetTransportError(
                    "PRIVATE_GET_REQUIRES_DEMO_CREDENTIAL_HANDLE"
                )
            headers = build_demo_okx_venue_auth_headers_v1(
                handle=self._handle,
                url=url,
                method=METHOD_GET,
                require_demo_header=True,
            )
            headers["User-Agent"] = USER_AGENT_DEMO_READ_ONLY_GET
            auth_sent = True
        else:
            headers = build_demo_okx_public_headers_v1()
            headers["User-Agent"] = USER_AGENT_DEMO_READ_ONLY_GET

        req = Request(url, method=METHOD_GET, headers=headers)
        opener = (
            self._http_opener_factory()
            if self._http_opener_factory is not None
            else build_opener(ProxyHandler({}))
        )
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
                    raise GhvDemoReadOnlyGetTransportError("REDIRECT_OFF_HOST_FORBIDDEN")
            self.venue_live_contact = True
        except GhvDemoReadOnlyGetTransportError:
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
        if body:
            try:
                payload = parse_json_object_v1(body)
            except (ValueError, json.JSONDecodeError):
                error_class = error_class or "MALFORMED_JSON"
                payload = None
        get_performed = status == 200 and payload is not None
        venue_live_contact = bool(self.venue_live_contact and status == 200)
        data_safety_source_kind = (
            DataSourceKind.REAL.value if get_performed and venue_live_contact else None
        )
        result = FreshPretradeGetTransportResultV1(
            get_performed=get_performed,
            method=METHOD_GET,
            endpoint=endpoint,
            http_status=status,
            payload=payload,
            auth_header_sent=auth_sent,
            transport_class=TRANSPORT_CLASS_DEMO_READ_ONLY_GET,
            venue_live_contact=venue_live_contact,
            historical_reuse=False,
            error_class=error_class,
            body_sha256=hashlib.sha256(body).hexdigest() if body else "",
            data_safety_source_kind=data_safety_source_kind,
        )
        if cacheable:
            self._cache[str(endpoint)] = result
        self.payloads_by_path[path] = payload
        return result


def reject_non_get_http_method_v1(method: str) -> None:
    method_u = str(method or "").strip().upper()
    if method_u in FORBIDDEN_HTTP_METHODS:
        raise GhvDemoReadOnlyGetTransportError(f"NON_GET_FORBIDDEN:{method_u}")
