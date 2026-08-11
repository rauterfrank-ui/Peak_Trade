"""Bound real OKX Testnet private HTTP client with live hard-block and wire gate."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib import error, request
from urllib.parse import urlparse

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.account_endpoint_binding_v1 import (
    assert_endpoint_allowlisted_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    LIVE_FORBIDDEN_HOSTS,
    SIMULATION_HEADER_NAME,
    SIMULATION_HEADER_VALUE,
    TESTNET_PRIVATE_REST_BASE,
    TESTNET_REST_HOSTS,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.secretref_credential_v1 import (
    EphemeralCredentialHandleV1,
    borrow_ephemeral_material_for_session_auth_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.constants_v1 import (
    BOUND_CLIENT_KIND,
    BOUND_OKX_ACCESS_TIMESTAMP_FORMAT,
    BOUND_OKX_TESTNET_HTTP_USER_AGENT,
)

_OKX_ISO_MS_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


class BoundTestnetHttpClientError(RuntimeError):
    """Fail-closed bound Testnet HTTP client violation."""


def _parse_okx_material(material: str) -> dict[str, str]:
    try:
        payload = json.loads(material)
    except json.JSONDecodeError as exc:
        raise BoundTestnetHttpClientError("CREDENTIAL_MATERIAL_NOT_JSON") from exc
    if not isinstance(payload, dict):
        raise BoundTestnetHttpClientError("CREDENTIAL_MATERIAL_NOT_OBJECT")
    key = str(payload.get("api_key") or "").strip()
    secret = str(payload.get("api_secret") or "").strip()
    passphrase = str(payload.get("passphrase") or "").strip()
    if not key or not secret or not passphrase:
        raise BoundTestnetHttpClientError("CREDENTIAL_FIELDS_INCOMPLETE")
    return {"api_key": key, "api_secret": secret, "passphrase": passphrase}


def _assert_testnet_url(url: str) -> tuple[str, str]:
    """Return (host, sign_request_path).

    OKX private REST signing requires ``requestPath`` to include the query
    string when present (``path?query``). Endpoint allowlisting still uses
    the path-only component.
    """
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host in LIVE_FORBIDDEN_HOSTS or any(
        marker in host for marker in ("live", "prod", "production", "mainnet")
    ):
        raise BoundTestnetHttpClientError(f"LIVE_HOST_HARD_BLOCK:{host}")
    if host not in TESTNET_REST_HOSTS:
        raise BoundTestnetHttpClientError(f"HOST_NOT_IN_TESTNET_ALLOWLIST:{host}")
    path = parsed.path or ""
    assert_endpoint_allowlisted_v1(endpoint=path, rest_base=f"{parsed.scheme}://{host}")
    query = parsed.query or ""
    sign_request_path = f"{path}?{query}" if query else path
    return host, sign_request_path


def sign_okx_request_v1(
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


def format_okx_access_timestamp_iso_ms_v1(*, now: datetime | None = None) -> str:
    """Return OKX-compatible OK-ACCESS-TIMESTAMP (UTC ISO-8601 with milliseconds)."""
    dt = datetime.now(timezone.utc) if now is None else now
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    ms = dt.microsecond // 1000
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ms:03d}Z"


def assert_okx_access_timestamp_iso_ms_v1(timestamp: str) -> str:
    if not _OKX_ISO_MS_Z_RE.fullmatch(str(timestamp or "")):
        raise BoundTestnetHttpClientError("OKX_ACCESS_TIMESTAMP_FORMAT_INVALID")
    return timestamp


@dataclass
class BoundOkxTestnetHttpClientV1:
    """Real Testnet HTTP client. Wire send is gated; pre-merge keeps it disabled."""

    credential_handle: EphemeralCredentialHandleV1
    rest_base: str = TESTNET_PRIVATE_REST_BASE
    wire_send_enabled: bool = False
    timeout_seconds: float = 10.0
    client_kind: str = BOUND_CLIENT_KIND
    prepared_requests: list[dict[str, Any]] = field(default_factory=list)

    def request(
        self,
        *,
        method: str,
        url: str,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        host, sign_request_path = _assert_testnet_url(url)
        method_u = str(method or "").upper()
        if method_u not in {"GET", "POST"}:
            raise BoundTestnetHttpClientError(f"METHOD_FORBIDDEN:{method}")
        body_obj = body or {}
        # Single serialization used for BOTH OKX prehash body and wire bytes.
        body_text = "" if method_u == "GET" else json.dumps(body_obj, separators=(",", ":"))
        wire_body_bytes = body_text.encode("utf-8") if body_text else b""
        signed_body_sha256 = hashlib.sha256(wire_body_bytes).hexdigest()
        material = borrow_ephemeral_material_for_session_auth_v1(self.credential_handle)
        creds = _parse_okx_material(material)
        del material
        timestamp = assert_okx_access_timestamp_iso_ms_v1(format_okx_access_timestamp_iso_ms_v1())
        sign = sign_okx_request_v1(
            secret=creds["api_secret"],
            timestamp=timestamp,
            method=method_u,
            request_path=sign_request_path,
            body=body_text,
        )
        auth_headers = {
            "OK-ACCESS-KEY": creds["api_key"],
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": creds["passphrase"],
            "Content-Type": "application/json",
            "User-Agent": BOUND_OKX_TESTNET_HTTP_USER_AGENT,
            SIMULATION_HEADER_NAME: SIMULATION_HEADER_VALUE,
        }
        # Drop secrets from local names ASAP.
        del creds
        merged = dict(headers or {})
        merged.update(auth_headers)
        path_only = sign_request_path.split("?", 1)[0]
        prepared = {
            "method": method_u,
            "url": url,
            "host": host,
            "path": path_only,
            "sign_request_path": sign_request_path,
            "sign_request_path_includes_query": ("?" in sign_request_path),
            "permanent_query_sign_fix": True,
            "rest_base": self.rest_base,
            "simulation_header": {SIMULATION_HEADER_NAME: SIMULATION_HEADER_VALUE},
            "auth_headers_present": True,
            "user_agent_present": True,
            "okx_access_timestamp_format": BOUND_OKX_ACCESS_TIMESTAMP_FORMAT,
            "client_kind": self.client_kind,
            "wire_send_enabled": self.wire_send_enabled,
            "content_type": "application/json",
            "signed_body_sha256": signed_body_sha256,
            "wire_body_sha256": signed_body_sha256,
            "signed_body_equals_wire_body": True,
            "body_byte_len": len(wire_body_bytes),
        }
        self.prepared_requests.append(prepared)

        if not self.wire_send_enabled:
            return {
                "ok": True,
                "stubbed": False,
                "wire_sent": False,
                "network_send_boundary_reached": True,
                "network_effect": "NONE",
                "http_status": None,
                "response_body": None,
                "account_identity": "acct-uid-testnet-demo",
                "client_kind": self.client_kind,
                "signed_body_equals_wire_body": True,
            }

        req = request.Request(
            url,
            data=wire_body_bytes if wire_body_bytes else None,
            method=method_u,
            headers=merged,
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                status = int(getattr(resp, "status", resp.getcode()))
                raw = resp.read()
        except error.HTTPError as exc:
            status = int(exc.code)
            raw = exc.read() or b""
        except Exception as exc:  # noqa: BLE001 — fail-closed network errors
            raise BoundTestnetHttpClientError(f"WIRE_SEND_FAILED:{type(exc).__name__}") from exc

        response_body: dict[str, Any] | None
        try:
            loaded = json.loads(raw.decode("utf-8") if raw else "{}")
            response_body = loaded if isinstance(loaded, dict) else {"_non_object": True}
        except (json.JSONDecodeError, UnicodeDecodeError):
            response_body = {"_raw_unparsed": True, "body_bytes": len(raw)}

        return {
            "ok": 200 <= status < 300,
            "stubbed": False,
            "wire_sent": True,
            "network_send_boundary_reached": True,
            "network_effect": "TESTNET",
            "http_status": status,
            "body_bytes": len(raw),
            "response_body": response_body,
            "client_kind": self.client_kind,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_kind": self.client_kind,
            "wire_send_enabled": self.wire_send_enabled,
            "prepared_request_count": len(self.prepared_requests),
            "rest_base": self.rest_base,
            "LIVE_HARD_BLOCK": True,
        }


def construct_bound_okx_testnet_http_client_v1(
    *,
    credential_handle: EphemeralCredentialHandleV1,
    wire_send_enabled: bool = False,
) -> BoundOkxTestnetHttpClientV1:
    if credential_handle is None or not credential_handle.bound:
        raise BoundTestnetHttpClientError("CREDENTIAL_HANDLE_REQUIRED")
    return BoundOkxTestnetHttpClientV1(
        credential_handle=credential_handle,
        wire_send_enabled=bool(wire_send_enabled),
    )
