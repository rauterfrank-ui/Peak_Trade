"""GET-only HTTP client for current-origin/main pretrade readiness.

Structurally refuses POST and mutation endpoints. No redirect follow. No timeout retry.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from src.ops.section_11_14_live_handoff_current_origin_main_bound_get_only_pretrade_readiness_v1.constants_v1 import (
    ENDPOINT_PATH_ALLOWLIST,
    FORBIDDEN_DEMO_SIMULATION_HEADERS,
    FORBIDDEN_HTTP_METHODS,
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS,
    MAX_GET_REQUEST_COUNT,
    METHOD_ALLOWLIST,
    REST_SCHEME_HOST,
    TIMEOUT_SECONDS,
    USER_AGENT,
)


class GetOnlyHttpError(RuntimeError):
    """Fail-closed GET-only HTTP violation."""


def endpoint_path_v1(endpoint: str) -> str:
    text = str(endpoint or "").strip()
    if not text:
        raise GetOnlyHttpError("ENDPOINT_REQUIRED")
    return text.split("?", 1)[0]


def assert_method_allowlisted_v1(method: str) -> str:
    m = str(method or "").strip().upper()
    if m in FORBIDDEN_HTTP_METHODS or m not in METHOD_ALLOWLIST:
        raise GetOnlyHttpError(f"HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE:{m or '<empty>'}")
    return m


def assert_endpoint_allowlisted_v1(endpoint: str) -> str:
    ep = str(endpoint or "").strip()
    if not ep:
        raise GetOnlyHttpError("ENDPOINT_REQUIRED")
    lowered = ep.lower()
    for marker in FORBIDDEN_MUTATION_ENDPOINT_MARKERS:
        if marker in lowered:
            raise GetOnlyHttpError(f"MUTATION_ENDPOINT_HARD_BLOCK:{ep}")
    path = endpoint_path_v1(ep)
    if path not in ENDPOINT_PATH_ALLOWLIST:
        raise GetOnlyHttpError(f"ENDPOINT_NOT_ALLOWLISTED:{ep}")
    return ep


def assert_no_demo_simulation_headers_v1(headers: Mapping[str, str] | None) -> None:
    if not headers:
        return
    for key, value in headers.items():
        key_l = str(key).strip().lower()
        if key_l in FORBIDDEN_DEMO_SIMULATION_HEADERS:
            raise GetOnlyHttpError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key_l}")
        if str(value).strip().lower() in {"1", "true", "yes"} and "simul" in key_l:
            raise GetOnlyHttpError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key_l}")


def classify_http_result_v1(status_code: int) -> str:
    if status_code == 200:
        return "HTTP_200_OK"
    if status_code == 401:
        return "HTTP_401_UNAUTHORIZED"
    if status_code == 403:
        return "HTTP_403_FORBIDDEN"
    if 400 <= status_code < 500:
        return f"HTTP_{status_code}_CLIENT_ERROR"
    if status_code >= 500:
        return f"HTTP_{status_code}_SERVER_ERROR"
    return f"HTTP_{status_code}"


@dataclass(frozen=True)
class GetOnlyHttpRequestV1:
    method: str
    url: str
    host: str
    endpoint: str
    headers: Mapping[str, str]
    timeout_seconds: float


@dataclass(frozen=True)
class GetOnlyHttpResponseV1:
    status_code: int
    body_bytes: bytes
    elapsed_seconds: float
    endpoint: str
    method: str


class GetOnlyTransportV1(Protocol):
    def send(self, request: GetOnlyHttpRequestV1) -> GetOnlyHttpResponseV1:
        """Send exactly one GET."""


@dataclass
class GetOnlyRequestCountersV1:
    request_count: int = 0
    get_request_count: int = 0
    write_request_count: int = 0
    methods_used: list[str] = field(default_factory=list)
    endpoints_used: list[str] = field(default_factory=list)
    http_result_classes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "REQUEST_COUNT": self.request_count,
            "GET_REQUEST_COUNT": self.get_request_count,
            "WRITE_REQUEST_COUNT": self.write_request_count,
            "methods_used": list(self.methods_used),
            "endpoints_used": list(self.endpoints_used),
            "http_result_classes": list(self.http_result_classes),
        }


@dataclass
class GetOnlyHttpClientV1:
    transport: GetOnlyTransportV1
    rest_base: str = REST_SCHEME_HOST
    timeout_seconds: float = TIMEOUT_SECONDS
    max_request_count: int = MAX_GET_REQUEST_COUNT
    counters: GetOnlyRequestCountersV1 = field(default_factory=GetOnlyRequestCountersV1)

    def _build_request(
        self,
        *,
        method: str,
        endpoint: str,
        headers: Mapping[str, str] | None = None,
    ) -> GetOnlyHttpRequestV1:
        m = assert_method_allowlisted_v1(method)
        ep = assert_endpoint_allowlisted_v1(endpoint)
        hdrs = {str(k): str(v) for k, v in dict(headers or {}).items()}
        if "User-Agent" not in hdrs and "user-agent" not in {k.lower() for k in hdrs}:
            hdrs["User-Agent"] = USER_AGENT
        assert_no_demo_simulation_headers_v1(hdrs)
        url = f"{self.rest_base.rstrip('/')}{ep}"
        host = urlparse(url).hostname or ""
        expected_host = urlparse(self.rest_base).hostname or ""
        if host != expected_host:
            raise GetOnlyHttpError(f"HOST_MISMATCH:{host}!={expected_host}")
        return GetOnlyHttpRequestV1(
            method=m,
            url=url,
            host=host,
            endpoint=ep,
            headers=hdrs,
            timeout_seconds=self.timeout_seconds,
        )

    def get(
        self,
        *,
        endpoint: str,
        headers: Mapping[str, str] | None = None,
    ) -> GetOnlyHttpResponseV1:
        if self.counters.request_count >= self.max_request_count:
            raise GetOnlyHttpError("MAX_REQUEST_COUNT_EXCEEDED")
        request = self._build_request(method="GET", endpoint=endpoint, headers=headers)
        started = time.monotonic()
        try:
            response = self.transport.send(request)
        except TimeoutError as exc:
            raise GetOnlyHttpError("INDETERMINATE_TIMEOUT") from exc
        elapsed = time.monotonic() - started
        if response.method != "GET":
            raise GetOnlyHttpError("TRANSPORT_RETURNED_NON_GET")
        self.counters.request_count += 1
        self.counters.get_request_count += 1
        self.counters.methods_used.append("GET")
        self.counters.endpoints_used.append(endpoint)
        self.counters.http_result_classes.append(classify_http_result_v1(response.status_code))
        return GetOnlyHttpResponseV1(
            status_code=response.status_code,
            body_bytes=response.body_bytes,
            elapsed_seconds=elapsed,
            endpoint=endpoint,
            method="GET",
        )

    def post(self, *, endpoint: str, **_: Any) -> None:
        raise GetOnlyHttpError(f"HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE:POST:{endpoint}")

    def request(self, *, method: str, endpoint: str, **_: Any) -> GetOnlyHttpResponseV1:
        m = str(method or "").strip().upper()
        if m != "GET":
            raise GetOnlyHttpError(f"HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE:{m or '<empty>'}")
        return self.get(endpoint=endpoint)


@dataclass
class RecordingFakeGetOnlyTransportV1:
    """Unit transport: no real network."""

    status_code: int = 200
    body: bytes = b'{"code":"0","data":[]}'
    calls: list[GetOnlyHttpRequestV1] = field(default_factory=list)
    bodies_by_path: dict[str, bytes] = field(default_factory=dict)
    raise_timeout_paths: set[str] = field(default_factory=set)

    def send(self, request: GetOnlyHttpRequestV1) -> GetOnlyHttpResponseV1:
        self.calls.append(request)
        if request.method != "GET":
            raise GetOnlyHttpError("FAKE_TRANSPORT_GET_ONLY")
        path = endpoint_path_v1(request.endpoint)
        if path in self.raise_timeout_paths:
            raise TimeoutError("fake-timeout")
        body = self.bodies_by_path.get(path, self.body)
        return GetOnlyHttpResponseV1(
            status_code=self.status_code,
            body_bytes=body,
            elapsed_seconds=0.01,
            endpoint=request.endpoint,
            method="GET",
        )


class _RejectRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise GetOnlyHttpError(f"REDIRECT_FORBIDDEN:{code}")


@dataclass
class UrllibGetOnlyTransportV1:
    """Real urllib GET transport. Redirects forbidden. No POST."""

    def send(self, request: GetOnlyHttpRequestV1) -> GetOnlyHttpResponseV1:
        if request.method != "GET":
            raise GetOnlyHttpError("URLLIB_TRANSPORT_GET_ONLY")
        req = Request(request.url, method="GET", headers=dict(request.headers))
        opener = build_opener(_RejectRedirectHandler)
        started = time.monotonic()
        try:
            with opener.open(req, timeout=request.timeout_seconds) as resp:  # noqa: S310
                body = resp.read()
                status = int(getattr(resp, "status", 200))
        except GetOnlyHttpError:
            raise
        except HTTPError as exc:
            body = exc.read() if hasattr(exc, "read") else b""
            status = int(exc.code)
        except TimeoutError as exc:
            raise TimeoutError("URLLIB_GET_TIMEOUT") from exc
        except URLError as exc:
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, TimeoutError):
                raise TimeoutError("URLLIB_GET_TIMEOUT") from exc
            raise GetOnlyHttpError(f"NETWORK_ERROR:{type(reason).__name__}") from exc
        elapsed = time.monotonic() - started
        return GetOnlyHttpResponseV1(
            status_code=status,
            body_bytes=body,
            elapsed_seconds=elapsed,
            endpoint=request.endpoint,
            method="GET",
        )


def parse_json_object_v1(body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GetOnlyHttpError("MALFORMED_NON_JSON_RESPONSE") from exc
    if not isinstance(payload, dict):
        raise GetOnlyHttpError("RESPONSE_NOT_JSON_OBJECT")
    return payload
