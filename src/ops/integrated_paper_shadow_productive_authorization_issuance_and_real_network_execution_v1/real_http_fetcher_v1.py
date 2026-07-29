"""Canonical real HTTPS fetcher for OKX-EEA public MD (no redirects, no proxy, TLS verify)."""

from __future__ import annotations

import ipaddress
import json
import socket
import ssl
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import (
    HTTPErrorProcessor,
    HTTPSHandler,
    OpenerDirector,
    Request,
)

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    ALLOWED_PATHS,
    CANONICAL_HOST,
    USER_AGENT,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportV1,
    HttpFetcher,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.network_boundary_guard_v1 import (
    NetworkBoundaryError,
    validate_request_boundary_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.constants_v1 import (  # noqa: E501
    DEFAULT_CONNECT_TIMEOUT_SECONDS,
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_READ_TIMEOUT_SECONDS,
)


class RealHttpFetcherError(RuntimeError):
    """Fail-closed real HTTP fetcher error."""


@dataclass
class RealHttpFetcherTelemetryV1:
    attempts: int = 0
    last_status: int = 0
    last_host: str = ""
    last_path: str = ""
    bytes_read: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempts": self.attempts,
            "last_status": self.last_status,
            "last_host": self.last_host,
            "last_path": self.last_path,
            "bytes_read": self.bytes_read,
            "events": list(self.events),
            "redacted": True,
            "no_credentials": True,
        }


def _is_private_or_loopback(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise RealHttpFetcherError(f"DNS_RESOLUTION_FAILED:{exc}") from exc
    for info in infos:
        sockaddr = info[4]
        ip = sockaddr[0]
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            continue
        if (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
            or addr.is_multicast
            or addr.is_unspecified
        ):
            return True
    return False


class _RefuseRedirects(HTTPErrorProcessor):
    def http_response(self, request, response):  # noqa: ANN001
        code = getattr(response, "code", None) or getattr(response, "status", None)
        if code in {301, 302, 303, 307, 308}:
            raise RealHttpFetcherError(f"REDIRECT_FORBIDDEN:HTTP_{code}")
        return response

    https_response = http_response


def _build_no_redirect_opener() -> OpenerDirector:
    ctx = ssl.create_default_context()
    opener = OpenerDirector()
    opener.add_handler(HTTPSHandler(context=ctx))
    opener.add_handler(_RefuseRedirects())
    return opener


def make_real_eea_public_md_fetcher_v1(
    *,
    connect_timeout_seconds: float = DEFAULT_CONNECT_TIMEOUT_SECONDS,
    read_timeout_seconds: float = DEFAULT_READ_TIMEOUT_SECONDS,
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    environ: Optional[Mapping[str, str]] = None,
    sleep: Callable[[float], None] = time.sleep,
    resolve_private_check: bool = True,
) -> tuple[HttpFetcher, RealHttpFetcherTelemetryV1]:
    """Return a boundary-enforcing HTTPS GET fetcher for eea.okx.com only."""
    del sleep  # retries handled by EeaPublicMdTransportV1
    telemetry = RealHttpFetcherTelemetryV1()
    opener = _build_no_redirect_opener()
    timeout = float(connect_timeout_seconds) + float(read_timeout_seconds)

    def fetcher(url: str, method: str, headers: Mapping[str, str], _timeout: float):
        telemetry.attempts += 1
        boundary = validate_request_boundary_v1(
            url=url, method=method, headers=headers, environ=environ, allow_proxy=False
        )
        if not boundary.ok:
            raise NetworkBoundaryError(",".join(boundary.blockers))

        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        path = parsed.path or ""
        if host != CANONICAL_HOST:
            raise NetworkBoundaryError(f"HOST_FORBIDDEN:{host}")
        if path not in ALLOWED_PATHS:
            raise NetworkBoundaryError(f"PATH_NOT_ALLOWED:{path}")
        if resolve_private_check and _is_private_or_loopback(host):
            raise NetworkBoundaryError("PRIVATE_OR_LOOPBACK_TARGET_FORBIDDEN")

        telemetry.last_host = host
        telemetry.last_path = path
        telemetry.events.append(
            {
                "event": "fetch_attempt",
                "host": host,
                "path": path,
                "method": str(method).upper(),
                "attempt": telemetry.attempts,
            }
        )

        req_headers = {
            "Accept": "application/json",
            "User-Agent": headers.get("User-Agent") or USER_AGENT,
        }
        for key, value in headers.items():
            if key.lower() in {"accept", "user-agent"}:
                req_headers[key] = value

        request = Request(url=url, method="GET", headers=req_headers)
        try:
            with opener.open(request, timeout=timeout) as resp:
                status = int(getattr(resp, "status", None) or resp.getcode())
                telemetry.last_status = status
                content_type = str(resp.headers.get("Content-Type") or "")
                if content_type and "json" not in content_type.lower():
                    raise RealHttpFetcherError(f"CONTENT_TYPE_FORBIDDEN:{content_type}")
                chunks: list[bytes] = []
                total = 0
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_response_bytes:
                        raise RealHttpFetcherError("RESPONSE_TOO_LARGE")
                    chunks.append(chunk)
                body = b"".join(chunks)
                telemetry.bytes_read += len(body)
                try:
                    json.loads(body.decode("utf-8"))
                except Exception as exc:  # noqa: BLE001
                    raise RealHttpFetcherError(f"INVALID_JSON:{exc}") from exc
                return status, body, dict(resp.headers.items())
        except RealHttpFetcherError:
            raise
        except NetworkBoundaryError:
            raise
        except HTTPError as exc:
            code = int(exc.code)
            telemetry.last_status = code
            if code in {301, 302, 303, 307, 308}:
                raise RealHttpFetcherError(f"REDIRECT_FORBIDDEN:HTTP_{code}") from exc
            body = exc.read(max_response_bytes + 1)
            if len(body) > max_response_bytes:
                raise RealHttpFetcherError("RESPONSE_TOO_LARGE") from exc
            return code, body, dict(exc.headers.items()) if exc.headers else {}
        except URLError as exc:
            raise RealHttpFetcherError(f"URL_ERROR:{exc}") from exc
        except ssl.SSLError as exc:
            raise RealHttpFetcherError(f"TLS_ERROR:{exc}") from exc
        except TimeoutError as exc:
            raise RealHttpFetcherError(f"TIMEOUT:{exc}") from exc

    return fetcher, telemetry


def build_real_eea_public_md_transport_v1(
    *,
    environ: Optional[Mapping[str, str]] = None,
    sleep: Callable[[float], None] = time.sleep,
    max_retries: int = 2,
    session_http_429_budget: int = 20,
    resolve_private_check: bool = True,
) -> tuple[EeaPublicMdTransportV1, RealHttpFetcherTelemetryV1]:
    fetcher, telemetry = make_real_eea_public_md_fetcher_v1(
        environ=environ,
        sleep=sleep,
        resolve_private_check=resolve_private_check,
    )
    transport = EeaPublicMdTransportV1(
        fetcher=fetcher,
        timeout_seconds=DEFAULT_CONNECT_TIMEOUT_SECONDS + DEFAULT_READ_TIMEOUT_SECONDS,
        max_retries=max_retries,
        session_http_429_budget=session_http_429_budget,
        sleep=sleep,
        environ=environ,
    )
    return transport, telemetry
