"""LIVE private read-only OKX request signing for §11.13.4.

Reuses pure signing/timestamp primitives from the Testnet unlock package.
Does NOT reuse BoundOkxTestnetHttpClientV1. GET-only. No simulation headers.
"""

from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.bound_testnet_http_client_v1 import (
    assert_okx_access_timestamp_iso_ms_v1,
    format_okx_access_timestamp_iso_ms_v1,
    sign_okx_request_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.constants_v1 import (
    FORBIDDEN_DEMO_SIMULATION_HEADERS,
    METHOD_ALLOWLIST,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.live_credential_ephemeral_v1 import (
    LiveEphemeralCredentialHandleV1,
    LiveDryRunOrderPlanCredentialError,
    borrow_live_ephemeral_material_for_session_auth_v1,
    parse_okx_live_ro_material_v1,
)


class LiveDryRunOrderPlanSignerError(RuntimeError):
    """Fail-closed LIVE dry-run-order-plan signer violation."""


def _sign_request_path_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or ""
    query = parsed.query or ""
    return f"{path}?{query}" if query else path


def build_okx_live_ro_get_auth_headers_v1(
    *,
    handle: LiveEphemeralCredentialHandleV1,
    url: str,
    method: str = "GET",
    body: str = "",
    extra_headers: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build OKX auth headers for a single GET. Secrets discarded before return."""
    method_u = str(method or "").strip().upper()
    if method_u not in METHOD_ALLOWLIST:
        raise LiveDryRunOrderPlanSignerError(f"SIGNER_METHOD_FORBIDDEN:{method_u or '<empty>'}")
    if body:
        raise LiveDryRunOrderPlanSignerError("SIGNER_BODY_FORBIDDEN_FOR_GET")
    if extra_headers:
        for key in extra_headers:
            if str(key).strip().lower() in FORBIDDEN_DEMO_SIMULATION_HEADERS:
                raise LiveDryRunOrderPlanSignerError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key}")

    material: str | None = None
    creds: dict[str, str] | None = None
    try:
        material = borrow_live_ephemeral_material_for_session_auth_v1(handle)
        creds = parse_okx_live_ro_material_v1(material)
        timestamp = assert_okx_access_timestamp_iso_ms_v1(format_okx_access_timestamp_iso_ms_v1())
        request_path = _sign_request_path_from_url(url)
        sign = sign_okx_request_v1(
            secret=creds["api_secret"],
            timestamp=timestamp,
            method=method_u,
            request_path=request_path,
            body="",
        )
        headers = {
            "OK-ACCESS-KEY": creds["api_key"],
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": creds["passphrase"],
            "Content-Type": "application/json",
            "User-Agent": "PeakTrade-Section-11-13-3-LiveDryRunOrderPlan/1",
        }
    except LiveDryRunOrderPlanCredentialError as exc:
        raise LiveDryRunOrderPlanSignerError(str(exc)) from exc
    finally:
        material = None
        creds = None

    if extra_headers:
        merged = dict(extra_headers)
        merged.update(headers)
        return merged
    return headers


def auth_headers_presence_doc_v1(headers: Mapping[str, str]) -> dict[str, Any]:
    """Redacted presence doc — never includes header values."""
    keys = {str(k).upper() for k in headers}
    return {
        "OK-ACCESS-KEY_PRESENT": "OK-ACCESS-KEY" in keys,
        "OK-ACCESS-SIGN_PRESENT": "OK-ACCESS-SIGN" in keys,
        "OK-ACCESS-TIMESTAMP_PRESENT": "OK-ACCESS-TIMESTAMP" in keys,
        "OK-ACCESS-PASSPHRASE_PRESENT": "OK-ACCESS-PASSPHRASE" in keys,
        "SIMULATION_HEADER_PRESENT": any(
            str(k).strip().lower() in FORBIDDEN_DEMO_SIMULATION_HEADERS for k in headers
        ),
        "method_allowlist": list(METHOD_ALLOWLIST),
    }
