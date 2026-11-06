"""GET-only HTTP client for the §11.14 flatten SELL preflight.

Structurally refuses POST and exact Place-Order paths. orders-pending GET is
allowlisted and is not treated as /trade/order mutation.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    ENDPOINT_PATH_ALLOWLIST,
    FORBIDDEN_DEMO_SIMULATION_HEADERS,
    FORBIDDEN_EXACT_POST_PATHS,
    FORBIDDEN_HTTP_METHODS,
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS,
    MAX_GET_REQUEST_COUNT,
    METHOD_ALLOWLIST,
    REST_SCHEME_HOST,
    TIMEOUT_SECONDS,
    USER_AGENT,
)


class FlattenGetOnlyHttpError(RuntimeError):
    """Fail-closed flatten GET-only HTTP violation."""


def endpoint_path_v1(endpoint: str) -> str:
    text = str(endpoint or "").strip()
    if not text:
        raise FlattenGetOnlyHttpError("ENDPOINT_REQUIRED")
    return text.split("?", 1)[0]


def assert_method_allowlisted_v1(method: str) -> str:
    m = str(method or "").strip().upper()
    if m in FORBIDDEN_HTTP_METHODS or m not in METHOD_ALLOWLIST:
        raise FlattenGetOnlyHttpError(f"HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE:{m or '<empty>'}")
    return m


def assert_endpoint_allowlisted_v1(endpoint: str) -> str:
    ep = str(endpoint or "").strip()
    if not ep:
        raise FlattenGetOnlyHttpError("ENDPOINT_REQUIRED")
    path = endpoint_path_v1(ep)
    if path in FORBIDDEN_EXACT_POST_PATHS:
        raise FlattenGetOnlyHttpError(f"MUTATION_ENDPOINT_HARD_BLOCK:{ep}")
    lowered = ep.lower()
    for marker in FORBIDDEN_MUTATION_ENDPOINT_MARKERS:
        if marker in lowered:
            raise FlattenGetOnlyHttpError(f"MUTATION_ENDPOINT_HARD_BLOCK:{ep}")
    if path not in ENDPOINT_PATH_ALLOWLIST:
        raise FlattenGetOnlyHttpError(f"ENDPOINT_NOT_ALLOWLISTED:{ep}")
    return ep


def assert_no_demo_simulation_headers_v1(headers: Mapping[str, str] | None) -> None:
    if not headers:
        return
    for key, value in headers.items():
        key_l = str(key).strip().lower()
        if key_l in FORBIDDEN_DEMO_SIMULATION_HEADERS:
            raise FlattenGetOnlyHttpError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key_l}")
        if str(value).strip().lower() in {"1", "true", "yes"} and "simul" in key_l:
            raise FlattenGetOnlyHttpError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key_l}")


@dataclass(frozen=True)
class FlattenGetOnlyHttpRequestV1:
    method: str
    url: str
    host: str
    endpoint: str
    headers: Mapping[str, str]
    timeout_seconds: float


@dataclass(frozen=True)
class FlattenGetOnlyHttpResponseV1:
    status_code: int
    body_bytes: bytes
    elapsed_seconds: float
    endpoint: str
    method: str


class FlattenGetOnlyTransportV1(Protocol):
    def send(self, request: FlattenGetOnlyHttpRequestV1) -> FlattenGetOnlyHttpResponseV1:
        """Send exactly one GET."""


@dataclass
class FlattenGetOnlyRequestCountersV1:
    request_count: int = 0
    get_request_count: int = 0
    write_request_count: int = 0
    methods_used: list[str] = field(default_factory=list)
    endpoints_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "REQUEST_COUNT": self.request_count,
            "GET_REQUEST_COUNT": self.get_request_count,
            "WRITE_REQUEST_COUNT": self.write_request_count,
            "methods_used": list(self.methods_used),
            "endpoints_used": list(self.endpoints_used),
        }


@dataclass
class FlattenGetOnlyHttpClientV1:
    transport: FlattenGetOnlyTransportV1
    rest_base: str = REST_SCHEME_HOST
    timeout_seconds: float = TIMEOUT_SECONDS
    max_request_count: int = MAX_GET_REQUEST_COUNT
    counters: FlattenGetOnlyRequestCountersV1 = field(
        default_factory=FlattenGetOnlyRequestCountersV1
    )

    def _build_request(
        self,
        *,
        method: str,
        endpoint: str,
        headers: Mapping[str, str] | None = None,
    ) -> FlattenGetOnlyHttpRequestV1:
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
            raise FlattenGetOnlyHttpError(f"HOST_MISMATCH:{host}!={expected_host}")
        return FlattenGetOnlyHttpRequestV1(
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
    ) -> FlattenGetOnlyHttpResponseV1:
        if self.counters.request_count >= self.max_request_count:
            raise FlattenGetOnlyHttpError("MAX_REQUEST_COUNT_EXCEEDED")
        request = self._build_request(method="GET", endpoint=endpoint, headers=headers)
        started = time.monotonic()
        try:
            response = self.transport.send(request)
        except TimeoutError as exc:
            raise FlattenGetOnlyHttpError("INDETERMINATE_TIMEOUT") from exc
        elapsed = time.monotonic() - started
        if response.method != "GET":
            raise FlattenGetOnlyHttpError("TRANSPORT_RETURNED_NON_GET")
        self.counters.request_count += 1
        self.counters.get_request_count += 1
        self.counters.methods_used.append("GET")
        self.counters.endpoints_used.append(endpoint)
        return FlattenGetOnlyHttpResponseV1(
            status_code=response.status_code,
            body_bytes=response.body_bytes,
            elapsed_seconds=elapsed,
            endpoint=endpoint,
            method="GET",
        )

    def post(self, *, endpoint: str, **_: Any) -> None:
        raise FlattenGetOnlyHttpError(f"HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE:POST:{endpoint}")


@dataclass
class RecordingFakeFlattenGetOnlyTransportV1:
    status_code: int = 200
    body: bytes = b'{"code":"0","data":[]}'
    calls: list[FlattenGetOnlyHttpRequestV1] = field(default_factory=list)
    bodies_by_path: dict[str, bytes] = field(default_factory=dict)
    raise_timeout_paths: set[str] = field(default_factory=set)

    def send(self, request: FlattenGetOnlyHttpRequestV1) -> FlattenGetOnlyHttpResponseV1:
        self.calls.append(request)
        if request.method != "GET":
            raise FlattenGetOnlyHttpError("FAKE_TRANSPORT_GET_ONLY")
        path = endpoint_path_v1(request.endpoint)
        if path in self.raise_timeout_paths:
            raise TimeoutError("fake-timeout")
        body = self.bodies_by_path.get(path, self.body)
        return FlattenGetOnlyHttpResponseV1(
            status_code=self.status_code,
            body_bytes=body,
            elapsed_seconds=0.01,
            endpoint=request.endpoint,
            method="GET",
        )


class _RejectRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise FlattenGetOnlyHttpError(f"REDIRECT_FORBIDDEN:{code}")


@dataclass
class UrllibFlattenGetOnlyTransportV1:
    def send(self, request: FlattenGetOnlyHttpRequestV1) -> FlattenGetOnlyHttpResponseV1:
        if request.method != "GET":
            raise FlattenGetOnlyHttpError("URLLIB_TRANSPORT_GET_ONLY")
        req = Request(request.url, method="GET", headers=dict(request.headers))
        opener = build_opener(_RejectRedirectHandler)
        started = time.monotonic()
        try:
            with opener.open(req, timeout=request.timeout_seconds) as resp:  # noqa: S310
                body = resp.read()
                status = int(getattr(resp, "status", 200))
        except FlattenGetOnlyHttpError:
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
            raise FlattenGetOnlyHttpError(f"NETWORK_ERROR:{type(reason).__name__}") from exc
        elapsed = time.monotonic() - started
        return FlattenGetOnlyHttpResponseV1(
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
        raise FlattenGetOnlyHttpError("MALFORMED_NON_JSON_RESPONSE") from exc
    if not isinstance(payload, dict):
        raise FlattenGetOnlyHttpError("RESPONSE_NOT_JSON_OBJECT")
    return payload
