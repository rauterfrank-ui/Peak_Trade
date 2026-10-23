"""GET-only signer for the read-only observation path.

The accepted method set is exactly {GET}. This module does not import the
trade signer, the POST transport, or a vault.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import datetime, timezone
from urllib.parse import urlparse

from src.ops.current_read_only_observation_get_path_v1.constants_v1 import (
    ALLOWED_ENDPOINTS,
    ALLOWED_METHODS,
    AUTHORIZED_HOST,
    USER_AGENT,
)
from src.ops.current_read_only_observation_get_path_v1.errors_v1 import (
    ReadOnlyObservationGetError,
)
from src.ops.current_read_only_observation_get_path_v1.handle_v1 import (
    ReadOnlyObservationGetHandleV1,
    borrow_read_only_observation_session_v1,
)


def _request_path_v1(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or ""
    query = parsed.query or ""
    return f"{path}?{query}" if query else path


def _timestamp_v1(*, now: datetime | None) -> str:
    dt = datetime.now(timezone.utc) if now is None else now
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    ms = dt.microsecond // 1000
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ms:03d}Z"


def build_read_only_observation_get_headers_v1(
    *,
    handle: ReadOnlyObservationGetHandleV1,
    url: str,
    method: str,
    body: str = "",
    now: datetime | None = None,
) -> dict[str, str]:
    method_u = str(method or "").strip().upper()
    if method_u not in ALLOWED_METHODS or method_u != "GET":
        raise ReadOnlyObservationGetError(f"SIGNER_METHOD_FORBIDDEN:{method_u or '<empty>'}")
    if str(body or ""):
        raise ReadOnlyObservationGetError("SIGNER_BODY_FORBIDDEN_FOR_GET")
    parsed = urlparse(url)
    if parsed.scheme != "https" or str(parsed.hostname or "") != AUTHORIZED_HOST:
        raise ReadOnlyObservationGetError("HOST_NOT_EEA_OKX")
    if parsed.path not in ALLOWED_ENDPOINTS:
        raise ReadOnlyObservationGetError("ENDPOINT_FORBIDDEN")
    key = secret = phrase = ""
    try:
        key, secret, phrase = borrow_read_only_observation_session_v1(handle)
        timestamp = _timestamp_v1(now=now)
        request_path = _request_path_v1(url)
        prehash = f"{timestamp}GET{request_path}"
        digest = hmac.new(secret.encode("utf-8"), prehash.encode("utf-8"), hashlib.sha256).digest()
        sign = base64.b64encode(digest).decode("ascii")
        return {
            "OK-ACCESS-KEY": key,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": phrase,
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
    finally:
        key = ""
        secret = ""
        phrase = ""


__all__ = ["build_read_only_observation_get_headers_v1"]
