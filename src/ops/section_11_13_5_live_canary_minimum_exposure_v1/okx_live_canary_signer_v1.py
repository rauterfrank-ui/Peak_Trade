"""LIVE canary OKX signing for §11.13.5 (GET+POST). No simulation headers.

Reuses pure signing/timestamp primitives from the Testnet unlock package.
Does NOT reuse BoundOkxTestnetHttpClientV1.
"""

from __future__ import annotations

import json
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.bound_testnet_http_client_v1 import (
    assert_okx_access_timestamp_iso_ms_v1,
    format_okx_access_timestamp_iso_ms_v1,
    sign_okx_request_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    FORBIDDEN_DEMO_SIMULATION_HEADERS,
    USER_AGENT_CANARY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    LiveCanaryCredentialError,
    LiveCanaryEphemeralCredentialHandleV1,
    borrow_live_canary_ephemeral_material_for_session_auth_v1,
    parse_okx_live_canary_material_v1,
)


class LiveCanarySignerError(RuntimeError):
    """Fail-closed LIVE canary signer violation."""


def _sign_request_path_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or ""
    query = parsed.query or ""
    return f"{path}?{query}" if query else path


def _assert_no_demo_headers(headers: Mapping[str, str] | None) -> None:
    if not headers:
        return
    for key, value in headers.items():
        key_l = str(key).strip().lower()
        if key_l in FORBIDDEN_DEMO_SIMULATION_HEADERS:
            raise LiveCanarySignerError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key}")
        if str(value).strip() in {"1", "true", "yes"} and "simul" in key_l:
            raise LiveCanarySignerError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key}")


def build_okx_live_canary_auth_headers_v1(
    *,
    handle: LiveCanaryEphemeralCredentialHandleV1,
    url: str,
    method: str,
    body: str = "",
    extra_headers: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build OKX auth headers. Secrets discarded before return."""
    method_u = str(method or "").strip().upper()
    if method_u not in {"GET", "POST"}:
        raise LiveCanarySignerError(f"SIGNER_METHOD_FORBIDDEN:{method_u or '<empty>'}")
    if method_u == "GET" and body:
        raise LiveCanarySignerError("SIGNER_BODY_FORBIDDEN_FOR_GET")
    _assert_no_demo_headers(extra_headers)

    material: str | None = None
    creds: dict[str, str] | None = None
    try:
        material = borrow_live_canary_ephemeral_material_for_session_auth_v1(handle)
        creds = parse_okx_live_canary_material_v1(material)
        timestamp = assert_okx_access_timestamp_iso_ms_v1(format_okx_access_timestamp_iso_ms_v1())
        request_path = _sign_request_path_from_url(url)
        sign = sign_okx_request_v1(
            secret=creds["api_secret"],
            timestamp=timestamp,
            method=method_u,
            request_path=request_path,
            body=body,
        )
        headers = {
            "OK-ACCESS-KEY": creds["api_key"],
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": creds["passphrase"],
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT_CANARY,
        }
    except LiveCanaryCredentialError as exc:
        raise LiveCanarySignerError(str(exc)) from exc
    finally:
        material = None
        creds = None

    if extra_headers:
        merged = dict(extra_headers)
        merged.update(headers)
        _assert_no_demo_headers(merged)
        return merged
    return headers


def serialize_signed_post_body_v1(payload: Mapping[str, Any]) -> str:
    return json.dumps(dict(payload), separators=(",", ":"), ensure_ascii=True)


def auth_headers_presence_doc_v1(headers: Mapping[str, str]) -> dict[str, Any]:
    keys = {str(k).upper() for k in headers}
    return {
        "OK-ACCESS-KEY_PRESENT": "OK-ACCESS-KEY" in keys,
        "OK-ACCESS-SIGN_PRESENT": "OK-ACCESS-SIGN" in keys,
        "OK-ACCESS-TIMESTAMP_PRESENT": "OK-ACCESS-TIMESTAMP" in keys,
        "OK-ACCESS-PASSPHRASE_PRESENT": "OK-ACCESS-PASSPHRASE" in keys,
        "SIMULATION_HEADER_PRESENT": any(
            str(k).strip().lower() in FORBIDDEN_DEMO_SIMULATION_HEADERS for k in headers
        ),
        "method_allowlist": ["GET", "POST"],
    }
