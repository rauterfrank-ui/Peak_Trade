"""WEBUI_LOCAL_ADMIN_WRITE_SURFACE_AUTH_GATE_V1 — local-admin write/trigger auth.

Fail-closed authentication for administrative WebUI write and trigger surfaces.
Not a general application auth framework. Not remote-internet-grade identity.

Canonical consumers wire ``require_local_admin_write_auth`` via FastAPI ``Depends``.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Any

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

CAPABILITY_ID = "WEBUI_LOCAL_ADMIN_WRITE_SURFACE_AUTH_GATE_V1"
CONTRACT_ID = "webui_local_admin_write_auth_v1"
AUTH_TOKEN_ENV_NAME = "PEAK_TRADE_WEBUI_LOCAL_ADMIN_TOKEN"
AUTH_HEADER_NAME = "X-Peak-Trade-Local-Admin-Token"

REASON_NOT_CONFIGURED = "LOCAL_ADMIN_AUTH_NOT_CONFIGURED"
REASON_MISSING = "LOCAL_ADMIN_AUTH_MISSING"
REASON_INVALID = "LOCAL_ADMIN_AUTH_INVALID"


def owner_identity() -> dict[str, str]:
    """Machine-readable owner identity for uniqueness / reuse contracts."""
    return {
        "capability_id": CAPABILITY_ID,
        "contract_id": CONTRACT_ID,
        "module": "src.webui.local_admin_write_auth_v1",
        "auth_token_env_name": AUTH_TOKEN_ENV_NAME,
        "auth_header_name": AUTH_HEADER_NAME,
    }


def configured_server_token() -> str | None:
    """Return the configured server token, or None when absent/empty/whitespace."""
    raw = os.environ.get(AUTH_TOKEN_ENV_NAME)
    if raw is None:
        return None
    if not isinstance(raw, str):
        return None
    if raw.strip() == "":
        return None
    return raw


def extract_request_token(request: Request) -> str | None:
    """Extract the local-admin token from the single allowed request header.

    Query parameters, path segments, cookies, and form fields are ignored.
    """
    headers = request.headers
    # Starlette headers are case-insensitive.
    value = headers.get(AUTH_HEADER_NAME)
    if value is None:
        # Also accept exact lower-case lookup for explicitness in tests.
        value = headers.get(AUTH_HEADER_NAME.lower())
    if value is None:
        return None
    return value


def tokens_match(*, provided: str, expected: str) -> bool:
    """Constant-time credential comparison via SHA-256 digests + hmac.compare_digest."""
    provided_digest = hashlib.sha256(provided.encode("utf-8")).digest()
    expected_digest = hashlib.sha256(expected.encode("utf-8")).digest()
    return hmac.compare_digest(provided_digest, expected_digest)


def _deny(status_code: int, reason: str, message: str) -> None:
    """Raise a non-secret HTTP denial. Never include credential material."""
    logger.info("local_admin_write_auth denied reason=%s", reason)
    raise HTTPException(
        status_code=status_code,
        detail={
            "error": reason,
            "message": message,
            "capability_id": CAPABILITY_ID,
        },
    )


def require_local_admin_write_auth(request: Request) -> None:
    """FastAPI dependency: authorize the current local-admin write/trigger operation.

    Semantics:
    - missing / empty / whitespace server token => 503 LOCAL_ADMIN_AUTH_NOT_CONFIGURED
    - missing / empty request header => 401 LOCAL_ADMIN_AUTH_MISSING
    - invalid request token => 403 LOCAL_ADMIN_AUTH_INVALID
    - valid token => returns None (authorized for this call only)
    """
    expected = configured_server_token()
    if expected is None:
        _deny(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            REASON_NOT_CONFIGURED,
            "Local-admin write authentication is not configured",
        )

    provided = extract_request_token(request)
    if provided is None or provided == "":
        _deny(
            status.HTTP_401_UNAUTHORIZED,
            REASON_MISSING,
            "Local-admin authentication proof is missing",
        )

    if not tokens_match(provided=provided, expected=expected):
        _deny(
            status.HTTP_403_FORBIDDEN,
            REASON_INVALID,
            "Local-admin authentication proof is invalid",
        )


def denial_detail_is_safe(detail: Any, *, synthetic_token: str) -> bool:
    """Test helper: ensure a denial payload does not echo a synthetic token."""
    blob = detail if isinstance(detail, str) else repr(detail)
    return synthetic_token not in blob
