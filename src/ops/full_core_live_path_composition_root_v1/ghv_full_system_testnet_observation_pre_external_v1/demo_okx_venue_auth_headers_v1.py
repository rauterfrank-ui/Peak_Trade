"""Demo-only OKX venue auth headers for GHV Testnet Observation (separate from Live K1).

Private Demo GET requires x-simulated-trading:1. Live K1 builder remains demo-header forbidden.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urlparse
from uuid import uuid4

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1BoundVenueAuthHandleV1,
    assert_k1_okx_access_timestamp_iso_ms_v1,
    format_k1_okx_access_timestamp_iso_ms_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.constants_v1 import (
    CREDENTIAL_CLASS,
    PRIVATE_DEMO_HEADER_NAME,
    PRIVATE_DEMO_HEADER_VALUE,
)

_OKX_ISO_MS_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
_SESSION_FIELDS: dict[str, tuple[str, str, str]] = {}
_FORBIDDEN_HANDLE_ID_TOKENS = ("secret", "passphrase", "api_key", "apikey", "private_key")


class GhvDemoOkxVenueAuthError(RuntimeError):
    """Fail-closed Demo venue-auth header builder violation."""


@dataclass(frozen=True)
class FullCoreDemoBoundVenueAuthHandleV1:
    """Demo Testnet observation handle. Not interchangeable with K1 live handle."""

    handle_id: str
    credential_class: str
    bound: bool
    can_sign: bool
    material_loaded: bool = False

    def __post_init__(self) -> None:
        token = str(self.handle_id or "").lower()
        for forbidden in _FORBIDDEN_HANDLE_ID_TOKENS:
            if forbidden in token:
                raise GhvDemoOkxVenueAuthError("SECRET_TOKEN_IN_HANDLE_ID")
        if self.material_loaded is True:
            raise GhvDemoOkxVenueAuthError("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
        if self.bound is not True:
            raise GhvDemoOkxVenueAuthError("DEMO_VENUE_AUTH_HANDLE_NOT_BOUND")
        if str(self.credential_class or "") != CREDENTIAL_CLASS:
            raise GhvDemoOkxVenueAuthError("DEMO_CREDENTIAL_CLASS_MISMATCH")


def bind_already_held_demo_venue_auth_session_v1(
    *,
    api_key: str,
    api_secret: str,
    passphrase: str,
    credential_class: str = CREDENTIAL_CLASS,
) -> FullCoreDemoBoundVenueAuthHandleV1:
    if str(credential_class or "") != CREDENTIAL_CLASS:
        raise GhvDemoOkxVenueAuthError("DEMO_CREDENTIAL_CLASS_REJECTED")
    key = str(api_key or "").strip()
    secret = str(api_secret or "").strip()
    phrase = str(passphrase or "").strip()
    if not key or not secret or not phrase:
        raise GhvDemoOkxVenueAuthError("CREDENTIAL_FIELDS_INCOMPLETE")
    handle = FullCoreDemoBoundVenueAuthHandleV1(
        handle_id=f"demo-vah-{uuid4().hex}",
        credential_class=CREDENTIAL_CLASS,
        bound=True,
        can_sign=True,
        material_loaded=False,
    )
    _SESSION_FIELDS[handle.handle_id] = (key, secret, phrase)
    return handle


def release_demo_venue_auth_session_v1(handle: FullCoreDemoBoundVenueAuthHandleV1) -> None:
    if not isinstance(handle, FullCoreDemoBoundVenueAuthHandleV1):
        raise GhvDemoOkxVenueAuthError("DEMO_VENUE_AUTH_HANDLE_TYPE_FORBIDDEN")
    _SESSION_FIELDS.pop(handle.handle_id, None)


def build_demo_okx_venue_auth_headers_v1(
    *,
    handle: FullCoreDemoBoundVenueAuthHandleV1,
    url: str,
    method: str,
    body: str = "",
    require_demo_header: bool = True,
) -> dict[str, str]:
    if isinstance(handle, FullCoreK1BoundVenueAuthHandleV1):
        raise GhvDemoOkxVenueAuthError("LIVE_K1_HANDLE_IN_DEMO_BIND_REJECTED")
    if not isinstance(handle, FullCoreDemoBoundVenueAuthHandleV1):
        raise GhvDemoOkxVenueAuthError("DEMO_VENUE_AUTH_HANDLE_TYPE_FORBIDDEN")
    method_u = str(method or "").strip().upper()
    if method_u != "GET":
        raise GhvDemoOkxVenueAuthError(f"DEMO_SIGNER_METHOD_FORBIDDEN:{method_u or '<empty>'}")
    if body:
        raise GhvDemoOkxVenueAuthError("SIGNER_BODY_FORBIDDEN_FOR_GET")
    if require_demo_header is not True:
        raise GhvDemoOkxVenueAuthError("DEMO_PRIVATE_GET_REQUIRES_DEMO_HEADER")

    key, secret, phrase = _borrow_session_fields_v1(handle)
    try:
        timestamp = assert_k1_okx_access_timestamp_iso_ms_v1(
            format_k1_okx_access_timestamp_iso_ms_v1()
        )
        request_path = _sign_request_path_from_url(url)
        sign = _sign_okx_request_v1(
            secret=secret,
            timestamp=timestamp,
            method=method_u,
            request_path=request_path,
            body=body,
        )
        return {
            "OK-ACCESS-KEY": key,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": phrase,
            "Content-Type": "application/json",
            PRIVATE_DEMO_HEADER_NAME: PRIVATE_DEMO_HEADER_VALUE,
        }
    finally:
        key = None
        secret = None
        phrase = None


def build_demo_okx_public_headers_v1() -> dict[str, str]:
    """Public market GET: no auth, no demo simulation header."""

    return {"Accept": "application/json"}


def assert_demo_private_headers_include_simulation_v1(headers: Mapping[str, str]) -> None:
    value = str(
        headers.get(PRIVATE_DEMO_HEADER_NAME) or headers.get(PRIVATE_DEMO_HEADER_NAME.lower()) or ""
    )
    if value.strip() != PRIVATE_DEMO_HEADER_VALUE:
        raise GhvDemoOkxVenueAuthError("DEMO_PRIVATE_GET_WITHOUT_DEMO_HEADER_REJECTED")


def _borrow_session_fields_v1(handle: FullCoreDemoBoundVenueAuthHandleV1) -> tuple[str, str, str]:
    fields = _SESSION_FIELDS.get(handle.handle_id)
    if fields is None:
        raise GhvDemoOkxVenueAuthError("EPHEMERAL_MATERIAL_GONE")
    return fields


def _sign_request_path_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or ""
    query = parsed.query or ""
    return f"{path}?{query}" if query else path


def _sign_okx_request_v1(
    *,
    secret: str,
    timestamp: str,
    method: str,
    request_path: str,
    body: str,
) -> str:
    if not _OKX_ISO_MS_Z_RE.fullmatch(str(timestamp or "")):
        raise GhvDemoOkxVenueAuthError("OKX_ACCESS_TIMESTAMP_FORMAT_INVALID")
    prehash = f"{timestamp}{method.upper()}{request_path}{body}"
    digest = hmac.new(secret.encode("utf-8"), prehash.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")
