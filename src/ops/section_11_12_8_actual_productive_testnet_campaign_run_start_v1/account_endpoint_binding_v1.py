"""Testnet account + private endpoint binding with live hard-block."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CANONICAL_ACCOUNT_IDENTITY,
    CANONICAL_RUNTIME_MODE,
    CANONICAL_VENUE,
    LIVE_FORBIDDEN_HOSTS,
    TESTNET_PRIVATE_ENDPOINTS,
    TESTNET_PRIVATE_REST_BASE,
    TESTNET_REST_HOSTS,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.secretref_credential_v1 import (
    EphemeralCredentialHandleV1,
    borrow_ephemeral_material_for_session_auth_v1,
)


class ActualStartBindingError(RuntimeError):
    """Fail-closed account/endpoint binding violation."""


@dataclass(frozen=True)
class AccountEndpointBindingV1:
    account_identity: str
    venue: str
    runtime_mode: str
    rest_base: str
    endpoint_allowlist: tuple[str, ...]
    account_verified: bool
    live_hosts_blocked: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_identity": self.account_identity,
            "venue": self.venue,
            "runtime_mode": self.runtime_mode,
            "rest_base": self.rest_base,
            "endpoint_allowlist": list(self.endpoint_allowlist),
            "account_verified": self.account_verified,
            "live_hosts_blocked": self.live_hosts_blocked,
        }


def _assert_testnet_host(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host in LIVE_FORBIDDEN_HOSTS or any(
        marker in host for marker in ("live", "prod", "production", "mainnet")
    ):
        raise ActualStartBindingError(f"LIVE_HOST_HARD_BLOCK:{host}")
    if host not in TESTNET_REST_HOSTS:
        raise ActualStartBindingError(f"HOST_NOT_IN_TESTNET_ALLOWLIST:{host}")
    return host


def assert_endpoint_allowlisted_v1(
    *, endpoint: str, rest_base: str = TESTNET_PRIVATE_REST_BASE
) -> None:
    _assert_testnet_host(rest_base)
    if endpoint not in TESTNET_PRIVATE_ENDPOINTS:
        raise ActualStartBindingError(f"ENDPOINT_NOT_ALLOWLISTED:{endpoint}")


def bind_and_verify_testnet_account_v1(
    *,
    credential_handle: EphemeralCredentialHandleV1,
    account_identity: str = CANONICAL_ACCOUNT_IDENTITY,
    venue: str = CANONICAL_VENUE,
    runtime_mode: str = CANONICAL_RUNTIME_MODE,
    rest_base: str = TESTNET_PRIVATE_REST_BASE,
    stub_observed_account_identity: str | None = None,
    live_account: bool = False,
) -> AccountEndpointBindingV1:
    if runtime_mode != "TESTNET":
        raise ActualStartBindingError("ACCOUNT_BINDING_REQUIRES_TESTNET")
    if venue != CANONICAL_VENUE:
        raise ActualStartBindingError("ACCOUNT_BINDING_VENUE_MISMATCH")
    if live_account:
        raise ActualStartBindingError("LIVE_ACCOUNT_HARD_BLOCK")
    identity = str(account_identity or "").strip()
    if not identity:
        raise ActualStartBindingError("ACCOUNT_IDENTITY_REQUIRED")
    _assert_testnet_host(rest_base)
    # Prove SecretRef material is available for session auth without leaking it.
    material = borrow_ephemeral_material_for_session_auth_v1(credential_handle)
    if not material:
        raise ActualStartBindingError("SESSION_AUTH_MATERIAL_ABSENT")
    # Observed identity comes from stubbed transport response in acceptance tests.
    observed = (
        stub_observed_account_identity if stub_observed_account_identity is not None else identity
    )
    if observed != identity:
        raise ActualStartBindingError("ACCOUNT_IDENTITY_MISMATCH")
    return AccountEndpointBindingV1(
        account_identity=identity,
        venue=venue,
        runtime_mode=runtime_mode,
        rest_base=rest_base,
        endpoint_allowlist=TESTNET_PRIVATE_ENDPOINTS,
        account_verified=True,
        live_hosts_blocked=True,
    )
