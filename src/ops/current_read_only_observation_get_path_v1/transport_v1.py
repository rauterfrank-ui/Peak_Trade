"""HTTPS GET transport for the read-only observation path.

Prepares an allowlisted GET and refuses to open a socket. Network send stays
unauthorized while PRIVATE_GET_GO is false. Redirect targets are checked when
a test sender returns a final URL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urlparse

from src.ops.current_read_only_observation_get_path_v1.constants_v1 import (
    ALLOWED_ENDPOINTS,
    ALLOWED_METHODS,
    AUTHORIZED_HOST,
    NETWORK_SEND_AUTHORIZED,
    REST_BASE,
)
from src.ops.current_read_only_observation_get_path_v1.errors_v1 import (
    ReadOnlyObservationGetError,
)
from src.ops.current_read_only_observation_get_path_v1.handle_v1 import (
    ReadOnlyObservationGetHandleV1,
)
from src.ops.current_read_only_observation_get_path_v1.signer_v1 import (
    build_read_only_observation_get_headers_v1,
)


@dataclass(frozen=True)
class PreparedReadOnlyObservationGetV1:
    method: str
    url: str
    endpoint_path: str
    headers: Mapping[str, str]

    def __repr__(self) -> str:
        return "PreparedReadOnlyObservationGetV1(redacted)"


@dataclass(frozen=True)
class ReadOnlyObservationSenderResultV1:
    """Test double result. final_url is the URL after any redirect."""

    final_url: str
    http_status: int
    body: bytes = b""


def assert_network_send_disabled_v1() -> None:
    if NETWORK_SEND_AUTHORIZED is not False:
        raise ReadOnlyObservationGetError("NETWORK_SEND_PIN_FORBIDDEN_TRUE")


def _absolute_url_v1(endpoint: str) -> str:
    raw = str(endpoint or "").strip()
    if not raw:
        raise ReadOnlyObservationGetError("ENDPOINT_REQUIRED")
    if raw.startswith("https://") or raw.startswith("http://"):
        return raw
    if not raw.startswith("/"):
        raise ReadOnlyObservationGetError("ENDPOINT_FORBIDDEN")
    return f"{REST_BASE}{raw}"


def prepare_read_only_observation_get_v1(
    *,
    handle: ReadOnlyObservationGetHandleV1,
    endpoint: str,
    method: str = "GET",
    body: str = "",
) -> PreparedReadOnlyObservationGetV1:
    assert_network_send_disabled_v1()
    method_u = str(method or "").strip().upper()
    if method_u not in ALLOWED_METHODS or method_u != "GET":
        raise ReadOnlyObservationGetError(f"METHOD_FORBIDDEN:{method_u or '<empty>'}")
    if str(body or ""):
        raise ReadOnlyObservationGetError("BODY_FORBIDDEN_FOR_GET")
    url = _absolute_url_v1(endpoint)
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ReadOnlyObservationGetError("SCHEME_FORBIDDEN")
    if str(parsed.hostname or "") != AUTHORIZED_HOST:
        raise ReadOnlyObservationGetError("HOST_NOT_EEA_OKX")
    if parsed.path not in ALLOWED_ENDPOINTS:
        raise ReadOnlyObservationGetError("ENDPOINT_FORBIDDEN")
    headers = build_read_only_observation_get_headers_v1(
        handle=handle,
        url=url,
        method="GET",
        body="",
    )
    return PreparedReadOnlyObservationGetV1(
        method="GET",
        url=url,
        endpoint_path=parsed.path,
        headers=headers,
    )


def complete_read_only_observation_get_v1(
    *,
    prepared: PreparedReadOnlyObservationGetV1,
    sender_result: ReadOnlyObservationSenderResultV1 | None,
) -> ReadOnlyObservationSenderResultV1:
    """Accept a prepared GET result and reject off-host redirects.

    No socket is opened. A missing sender result fail-closes before any send.
    """

    assert_network_send_disabled_v1()
    if prepared.method != "GET":
        raise ReadOnlyObservationGetError("METHOD_FORBIDDEN")
    if sender_result is None:
        raise ReadOnlyObservationGetError("NETWORK_NOT_AUTHORIZED")
    final = urlparse(str(sender_result.final_url or ""))
    if final.scheme != "https" or str(final.hostname or "") != AUTHORIZED_HOST:
        raise ReadOnlyObservationGetError("REDIRECT_OFF_HOST_FORBIDDEN")
    if final.path not in ALLOWED_ENDPOINTS:
        raise ReadOnlyObservationGetError("REDIRECT_ENDPOINT_FORBIDDEN")
    return sender_result


__all__ = [
    "PreparedReadOnlyObservationGetV1",
    "ReadOnlyObservationSenderResultV1",
    "assert_network_send_disabled_v1",
    "complete_read_only_observation_get_v1",
    "prepare_read_only_observation_get_v1",
]
