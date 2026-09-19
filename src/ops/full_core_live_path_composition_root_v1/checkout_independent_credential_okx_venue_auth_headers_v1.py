"""K1-owned CURRENT OKX venue auth-header builder.

Completes the existing K1 credential authority with the CURRENT GET/POST
header contract. Does not load credentials, access Keychain, resolve
SecretRef, or open a network session. Signing capability is not send
authority and does not mint a permit.

OWNER_GO=OWNER_GO_K1_CURRENT_OKX_VENUE_AUTH_HEADERS_V1
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from urllib.parse import urlparse
from uuid import uuid4

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_canonical_okx_post_body_serialize_v1 import (
    serialize_canonical_okx_post_body_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
)

OWNER_GO = "OWNER_GO_K1_CURRENT_OKX_VENUE_AUTH_HEADERS_V1"
THIS_SLICE = "K1_CURRENT_OKX_VENUE_AUTH_HEADERS_V1"
CONTRACT_VERSION = "v1"
JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_K1_OKX_VENUE_AUTH_HEADERS_SEAM_V1"
USER_AGENT_K1_VENUE_AUTH = "PeakTrade-FullCore-K1-Venue-Auth/1"
REAL_KEYCHAIN_ACCESS_AUTHORIZED = False
MATERIAL_LOADED = False
MAY_PERFORM_GET = False
MAY_POST = False
SIGNING_IMPLIES_SEND_AUTHORITY = False
SIGNING_IMPLIES_NETWORK_AUTHORIZATION = False
PRODUCTIVE_PROVIDER_ACTIVE = False
V5_JOINED = False

FORBIDDEN_DEMO_SIMULATION_HEADERS: tuple[str, ...] = (
    "x-simulated-trading",
    "x-simulation",
    "ok-simulated-trading",
)
_OKX_ISO_MS_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
_FORBIDDEN_HANDLE_ID_TOKENS = (
    "secret",
    "passphrase",
    "api_key",
    "apikey",
    "private_key",
)
_SESSION_FIELDS: dict[str, tuple[str, str, str]] = {}

FALSE_TOKEN = "false"
TRUE_TOKEN = "true"


class FullCoreK1OkxVenueAuthError(RuntimeError):
    """Fail-closed K1 venue-auth header builder violation."""


@dataclass(frozen=True)
class FullCoreK1BoundVenueAuthHandleV1:
    """Already-bound K1 venue-auth handle. Never carries plaintext fields."""

    handle_id: str
    bound: bool
    can_sign: bool
    material_loaded: bool = False

    def __post_init__(self) -> None:
        token = str(self.handle_id or "").lower()
        for forbidden in _FORBIDDEN_HANDLE_ID_TOKENS:
            if forbidden in token:
                raise FullCoreK1OkxVenueAuthError("SECRET_TOKEN_IN_HANDLE_ID")
        if self.material_loaded is True:
            raise FullCoreK1OkxVenueAuthError("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
        if self.bound is not True:
            raise FullCoreK1OkxVenueAuthError("K1_VENUE_AUTH_HANDLE_NOT_BOUND")

    def to_dict(self) -> dict[str, str]:
        return {
            "handle_id": self.handle_id,
            "bound": TRUE_TOKEN if self.bound else FALSE_TOKEN,
            "can_sign": TRUE_TOKEN if self.can_sign else FALSE_TOKEN,
            "material_loaded": FALSE_TOKEN,
            "plaintext_present": FALSE_TOKEN,
        }


def format_k1_okx_access_timestamp_iso_ms_v1(*, now: datetime | None = None) -> str:
    """Return OKX-compatible OK-ACCESS-TIMESTAMP (UTC ISO-8601 with milliseconds)."""
    dt = datetime.now(timezone.utc) if now is None else now
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    ms = dt.microsecond // 1000
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ms:03d}Z"


def assert_k1_okx_access_timestamp_iso_ms_v1(timestamp: str) -> str:
    if not _OKX_ISO_MS_Z_RE.fullmatch(str(timestamp or "")):
        raise FullCoreK1OkxVenueAuthError("OKX_ACCESS_TIMESTAMP_FORMAT_INVALID")
    return timestamp


def serialize_k1_signed_post_body_v1(payload: Mapping[str, Any]) -> str:
    return serialize_canonical_okx_post_body_v1(payload)


def bind_already_held_k1_venue_auth_session_v1(
    *,
    api_key: str,
    api_secret: str,
    passphrase: str,
) -> FullCoreK1BoundVenueAuthHandleV1:
    """Bind already-held session fields into a K1 handle.

    Does not acquire from Keychain, SecretRef, vault, or file. The handle
    object keeps material_loaded=false.
    """
    _assert_standing_pins_v1()
    key = str(api_key or "").strip()
    secret = str(api_secret or "").strip()
    phrase = str(passphrase or "").strip()
    if not key or not secret or not phrase:
        raise FullCoreK1OkxVenueAuthError("CREDENTIAL_FIELDS_INCOMPLETE")
    handle = FullCoreK1BoundVenueAuthHandleV1(
        handle_id=f"k1-vah-{uuid4().hex}",
        bound=True,
        can_sign=True,
        material_loaded=False,
    )
    _SESSION_FIELDS[handle.handle_id] = (key, secret, phrase)
    return handle


def release_k1_venue_auth_session_v1(handle: FullCoreK1BoundVenueAuthHandleV1) -> None:
    if not isinstance(handle, FullCoreK1BoundVenueAuthHandleV1):
        raise FullCoreK1OkxVenueAuthError("K1_VENUE_AUTH_HANDLE_TYPE_FORBIDDEN")
    _SESSION_FIELDS.pop(handle.handle_id, None)


def build_k1_okx_venue_auth_headers_v1(
    *,
    handle: FullCoreK1BoundVenueAuthHandleV1,
    url: str,
    method: str,
    body: str = "",
    extra_headers: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build OKX auth headers from an already-bound K1 handle."""
    _assert_standing_pins_v1()
    if not isinstance(handle, FullCoreK1BoundVenueAuthHandleV1):
        raise FullCoreK1OkxVenueAuthError("K1_VENUE_AUTH_HANDLE_TYPE_FORBIDDEN")
    if handle.bound is not True:
        raise FullCoreK1OkxVenueAuthError("K1_VENUE_AUTH_HANDLE_NOT_BOUND")
    if handle.can_sign is not True:
        raise FullCoreK1OkxVenueAuthError("K1_VENUE_AUTH_CAN_SIGN_REQUIRED")
    if handle.material_loaded is True:
        raise FullCoreK1OkxVenueAuthError("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
    method_u = str(method or "").strip().upper()
    if method_u not in {"GET", "POST"}:
        raise FullCoreK1OkxVenueAuthError(f"SIGNER_METHOD_FORBIDDEN:{method_u or '<empty>'}")
    if method_u == "GET" and body:
        raise FullCoreK1OkxVenueAuthError("SIGNER_BODY_FORBIDDEN_FOR_GET")
    _assert_no_demo_headers(extra_headers)

    key: str | None = None
    secret: str | None = None
    phrase: str | None = None
    try:
        key, secret, phrase = _borrow_session_fields_v1(handle)
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
        headers = {
            "OK-ACCESS-KEY": key,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": phrase,
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT_K1_VENUE_AUTH,
        }
    finally:
        key = None
        secret = None
        phrase = None

    if extra_headers:
        merged = dict(extra_headers)
        merged.update(headers)
        _assert_no_demo_headers(merged)
        return merged
    return headers


def prove_k1_signing_does_not_authorize_network_v1() -> dict[str, str]:
    _assert_standing_pins_v1()
    return {
        "SIGNING_IMPLIES_SEND_AUTHORITY": FALSE_TOKEN,
        "SIGNING_IMPLIES_NETWORK_AUTHORIZATION": FALSE_TOKEN,
        "MAY_PERFORM_GET": FALSE_TOKEN,
        "MAY_POST": FALSE_TOKEN,
        "MATERIAL_LOADED": FALSE_TOKEN,
        "REAL_KEYCHAIN_ACCESS_AUTHORIZED": FALSE_TOKEN,
        "EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "PRODUCTIVE_PROVIDER_ACTIVE": FALSE_TOKEN,
        "V5_JOINED": FALSE_TOKEN,
    }


def _assert_standing_pins_v1() -> None:
    if REAL_KEYCHAIN_ACCESS_AUTHORIZED is True:
        raise FullCoreK1OkxVenueAuthError("REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNAUTHORIZED")
    if MATERIAL_LOADED is True:
        raise FullCoreK1OkxVenueAuthError("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
    if MAY_PERFORM_GET is True or MAY_POST is True:
        raise FullCoreK1OkxVenueAuthError("GET_AND_POST_MUST_REMAIN_UNAUTHORIZED")
    if SIGNING_IMPLIES_SEND_AUTHORITY is True:
        raise FullCoreK1OkxVenueAuthError("SIGNING_MUST_NOT_IMPLY_SEND_AUTHORITY")
    if SIGNING_IMPLIES_NETWORK_AUTHORIZATION is True:
        raise FullCoreK1OkxVenueAuthError("SIGNING_MUST_NOT_IMPLY_NETWORK")
    if PRODUCTIVE_PROVIDER_ACTIVE is True:
        raise FullCoreK1OkxVenueAuthError("PRODUCTIVE_PROVIDER_MUST_REMAIN_INACTIVE")
    if V5_JOINED is True:
        raise FullCoreK1OkxVenueAuthError("V5_MUST_NOT_JOIN_K1_SIGNER")
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        raise FullCoreK1OkxVenueAuthError("STANDING_EXTERNAL_EFFECT_MUST_REMAIN_FALSE")


def _assert_no_demo_headers(headers: Mapping[str, str] | None) -> None:
    if not headers:
        return
    for key, value in headers.items():
        key_l = str(key).strip().lower()
        if key_l in FORBIDDEN_DEMO_SIMULATION_HEADERS:
            raise FullCoreK1OkxVenueAuthError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key}")
        if str(value).strip() in {"1", "true", "yes"} and "simul" in key_l:
            raise FullCoreK1OkxVenueAuthError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key}")


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
    prehash = f"{timestamp}{method.upper()}{request_path}{body}"
    digest = hmac.new(secret.encode("utf-8"), prehash.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def _borrow_session_fields_v1(
    handle: FullCoreK1BoundVenueAuthHandleV1,
) -> tuple[str, str, str]:
    fields = _SESSION_FIELDS.get(handle.handle_id)
    if fields is None:
        raise FullCoreK1OkxVenueAuthError("EPHEMERAL_MATERIAL_GONE")
    return fields
