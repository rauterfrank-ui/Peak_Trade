"""Public-MD-only network boundary (reuses preregistered allowlists)."""

from __future__ import annotations

from typing import Mapping
from urllib.parse import urlparse

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    PUBLIC_MARKET_DATA_ONLY,
    REUSED_PUBLIC_MD_ENDPOINT_ALLOWLIST,
    REUSED_PUBLIC_MD_HOST,
    REUSED_PUBLIC_MD_METHOD_ALLOWLIST,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    AdditionalEvidenceS03SessionExecutionOwnerError,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_source_v1 import (
    assert_public_get_allowlist_v1,
)


def assert_public_md_request_allowed_v1(*, url: str, method: str = "GET") -> str:
    if not PUBLIC_MARKET_DATA_ONLY:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("public_md_only_disabled")
    method_u = str(method).upper()
    if method_u not in REUSED_PUBLIC_MD_METHOD_ALLOWLIST:
        raise AdditionalEvidenceS03SessionExecutionOwnerError(f"non_get_rejected:{method_u}")
    if method_u != "GET":
        raise AdditionalEvidenceS03SessionExecutionOwnerError(f"non_get_rejected:{method_u}")
    # Reuse existing preregistered allowlist assertion.
    path = assert_public_get_allowlist_v1(url=url, method=method_u)
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    expected_host = urlparse(REUSED_PUBLIC_MD_HOST).hostname or "eea.okx.com"
    if host != expected_host:
        raise AdditionalEvidenceS03SessionExecutionOwnerError(f"host_not_allowlisted:{host}")
    if path not in REUSED_PUBLIC_MD_ENDPOINT_ALLOWLIST:
        raise AdditionalEvidenceS03SessionExecutionOwnerError(f"path_not_allowlisted:{path}")
    if path.startswith("/api/v5/trade") or "order" in path or "/account" in path:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("private_endpoint_rejected")
    return path


def assert_no_credentials_v1(headers: Mapping[str, str] | None = None) -> None:
    headers = headers or {}
    for key in headers:
        if str(key).lower() in {
            "authorization",
            "ok-access-key",
            "ok-access-sign",
            "ok-access-passphrase",
            "ok-access-timestamp",
        }:
            raise AdditionalEvidenceS03SessionExecutionOwnerError("credentials_rejected")
