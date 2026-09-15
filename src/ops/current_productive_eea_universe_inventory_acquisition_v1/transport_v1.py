"""GET-only EEA public universe inventory transport. No credentials. No POST.

Does not reuse Phase-9.2 / paper-shadow / canary transports because those
require instId and import foreign instrument authority.
"""

from __future__ import annotations

import hashlib
import json
import socket
from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import ProxyHandler, Request, build_opener

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    AUTHORIZED_HOST,
    CONNECT_TIMEOUT_SECONDS,
    FORBIDDEN_HOSTS,
    METHOD_GET,
    READ_TIMEOUT_SECONDS,
    REST_BASE,
    USER_AGENT,
)


class EeaUniverseAcquisitionError(RuntimeError):
    """Fail-closed universe-inventory acquisition violation."""


class EeaPublicUniverseGetPortV1(Protocol):
    def get(self, *, path: str, query: Mapping[str, str]) -> "EeaPublicGetResultV1": ...


@dataclass(frozen=True)
class EeaPublicGetResultV1:
    url: str
    path: str
    query: str
    host: str
    method: str
    http_status: int
    payload: Any
    body_sha256: str
    ts: str
    error_class: str
    venue_live_contact: bool


def _assert_get_url_v1(*, url: str, path: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise EeaUniverseAcquisitionError("NON_HTTPS_FORBIDDEN")
    host = str(parsed.hostname or "").strip().lower()
    if host != AUTHORIZED_HOST:
        raise EeaUniverseAcquisitionError("HOST_NOT_EEA_OKX")
    if host in FORBIDDEN_HOSTS or "www.okx.com" in host:
        raise EeaUniverseAcquisitionError("WWW_OKX_FORBIDDEN")
    if str(parsed.path or "") != path:
        raise EeaUniverseAcquisitionError("PATH_MISMATCH")


class UrllibEeaPublicUniverseGetTransportV1:
    """Minimal urllib HTTPS GET. No redirects off-host. No retries. No credentials."""

    def __init__(
        self,
        *,
        timeout_seconds: float = READ_TIMEOUT_SECONDS,
        connect_timeout_seconds: float = CONNECT_TIMEOUT_SECONDS,
    ) -> None:
        self.timeout_seconds = float(timeout_seconds)
        self.connect_timeout_seconds = float(connect_timeout_seconds)
        self.request_count = 0
        self.methods_used: list[str] = []
        self.venue_live_contact = False

    def get(self, *, path: str, query: Mapping[str, str]) -> EeaPublicGetResultV1:
        if self.request_count >= 4:
            raise EeaUniverseAcquisitionError("MAX_REQUEST_COUNT_EXCEEDED")
        query_text = urlencode(dict(query))
        url = f"{REST_BASE}{path}?{query_text}"
        _assert_get_url_v1(url=url, path=path)
        req = Request(
            url,
            method=METHOD_GET,
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        )
        opener = build_opener(ProxyHandler({}))
        body = b""
        status = 0
        error_class = ""
        payload: Any = None
        try:
            socket.setdefaulttimeout(self.connect_timeout_seconds)
            with opener.open(req, timeout=self.timeout_seconds) as resp:  # noqa: S310
                status = int(getattr(resp, "status", 200))
                body = bytes(resp.read() or b"")
                location = str(getattr(resp, "url", url) or url)
                loc_host = str(urlparse(location).hostname or "").strip().lower()
                if loc_host and loc_host != AUTHORIZED_HOST:
                    raise EeaUniverseAcquisitionError("REDIRECT_OFF_HOST_FORBIDDEN")
            self.venue_live_contact = True
        except EeaUniverseAcquisitionError:
            raise
        except TimeoutError:
            error_class = "TIMEOUT"
        except HTTPError as exc:
            status = int(getattr(exc, "code", 0) or 0)
            body = bytes(exc.read() or b"") if hasattr(exc, "read") else b""
            error_class = "HTTP_ERROR"
        except (URLError, OSError, socket.timeout) as exc:
            error_class = type(exc).__name__[:80]
        finally:
            socket.setdefaulttimeout(None)
        self.request_count += 1
        self.methods_used.append(METHOD_GET)
        if body:
            try:
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                error_class = error_class or "MALFORMED_JSON"
                payload = None
        ts = ""
        if isinstance(payload, dict):
            ts = str(payload.get("ts") or "").strip()
        return EeaPublicGetResultV1(
            url=url,
            path=path,
            query=query_text,
            host=AUTHORIZED_HOST,
            method=METHOD_GET,
            http_status=status,
            payload=payload,
            body_sha256=hashlib.sha256(body).hexdigest() if body else "",
            ts=ts,
            error_class=error_class,
            venue_live_contact=bool(self.venue_live_contact and status == 200),
        )
