"""Public-MD network boundary proofs for Step-5 binding.

Reuses the wallclock network_boundary_guard owner. No parallel transport authority.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.network_boundary_guard_v1 import (
    assert_headers_allowed_v1,
    assert_no_okx_credentials_in_env_v1,
    validate_request_boundary_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    EEA_PUBLIC_MD_HOST,
    FAULT_SESSION_ALLOWED,
    HTTP_METHOD_ALLOWLIST,
    NETWORK_ALLOWLIST,
    NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
)


def prove_public_md_network_boundary_v1(
    *,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    env = dict(environ or {})
    blockers: list[str] = []
    blockers.extend(assert_no_okx_credentials_in_env_v1(environ=env))

    allow = validate_request_boundary_v1(
        url=(f"https://{EEA_PUBLIC_MD_HOST}/api/v5/market/ticker?instId={CANONICAL_INSTRUMENT_ID}"),
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "peak-trade-phase92-step5/1"},
        environ=env,
    )
    if not allow.ok:
        blockers.extend([f"PUBLIC_MD_ALLOWLIST_FAILED:{b}" for b in allow.blockers])

    for method in ("POST", "PUT", "DELETE", "PATCH"):
        att = validate_request_boundary_v1(
            url=(
                f"https://{EEA_PUBLIC_MD_HOST}/api/v5/market/ticker"
                f"?instId={CANONICAL_INSTRUMENT_ID}"
            ),
            method=method,
            headers={"Accept": "application/json", "User-Agent": "peak-trade-phase92-step5/1"},
            environ=env,
        )
        if att.ok:
            blockers.append(f"NON_GET_METHOD_ACCEPTED:{method}")

    for bad_url in (
        f"https://{EEA_PUBLIC_MD_HOST}/api/v5/trade/order",
        f"https://{EEA_PUBLIC_MD_HOST}/api/v5/account/balance",
        f"https://www.okx.com/api/v5/market/ticker?instId={CANONICAL_INSTRUMENT_ID}",
    ):
        att = validate_request_boundary_v1(
            url=bad_url,
            method="GET",
            headers={"Accept": "application/json", "User-Agent": "peak-trade-phase92-step5/1"},
            environ=env,
        )
        if att.ok:
            blockers.append(f"PRIVATE_OR_NON_EEA_ACCEPTED:{bad_url}")

    header_blockers = assert_headers_allowed_v1(
        {"Authorization": "Bearer x", "OK-ACCESS-KEY": "x", "Accept": "application/json"}
    )
    if not header_blockers:
        blockers.append("AUTH_HEADER_NOT_REJECTED")

    ok = (
        not blockers
        and (not NETWORK_SESSION_ALLOWED)
        and (not FAULT_SESSION_ALLOWED)
        and (not PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED)
    )
    return {
        "ok": ok,
        "blockers": blockers,
        "PUBLIC_MD_ONLY_BOUND": True,
        "GET_ONLY_BOUND": HTTP_METHOD_ALLOWLIST == "GET_ONLY",
        "NETWORK_ALLOWLIST": NETWORK_ALLOWLIST,
        "PRIVATE_ENDPOINT_REACHABLE": False,
        "AUTH_HEADER_PRESENT": False,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "ORDER_SIDE_EFFECT_OCCURRED": False,
        "PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED": (
            PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED
        ),
        "notes": [
            "REUSES_WALLCLOCK_NETWORK_BOUNDARY_GUARD",
            "NO_PARALLEL_TRANSPORT_AUTHORITY",
            "BINDING_CAPABILITY_DOES_NOT_START_NETWORK",
        ],
    }
