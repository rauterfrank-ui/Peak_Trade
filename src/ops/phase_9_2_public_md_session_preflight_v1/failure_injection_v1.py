"""Offline failure-injection proofs for Phase 9.2 preflight (no network)."""

from __future__ import annotations

from typing import Any

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.network_boundary_guard_v1 import (
    validate_request_boundary_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import EEA_PUBLIC_MD_HOST
from src.ops.phase_9_2_public_md_session_preflight_v1.models_v1 import SmokeSessionContractV1
from src.ops.phase_9_2_public_md_session_preflight_v1.smoke_session_contract_v1 import (
    SmokeContractError,
    validate_smoke_session_contract_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_rate_limit_policy_v1 import (
    PublicMdRequestPacingPolicyV1,
)


def run_failure_injections_v1(*, contract: SmokeSessionContractV1) -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    # Zero-interval burst rejected.
    zero_ok = False
    try:
        PublicMdRequestPacingPolicyV1(
            minimum_interval_seconds=0.0,
            maximum_requests_per_session=10,
            maximum_requests_per_cycle=1,
            maximum_consecutive_rate_limits=1,
            retry_after_max_seconds=10.0,
            backoff_initial_seconds=1.0,
            backoff_multiplier=2.0,
            backoff_max_seconds=4.0,
            jitter_fraction=0.0,
        ).validate()
    except Exception:  # noqa: BLE001
        zero_ok = True
    results.append({"case": "ZERO_INTERVAL_BURST", "ok": zero_ok})

    # Private endpoint rejected.
    private = validate_request_boundary_v1(
        url=f"https://{EEA_PUBLIC_MD_HOST}/api/v5/trade/order",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "PeakTradePhase92Preflight/1.0"},
        environ={"PATH": "/usr/bin", "HOME": "/tmp"},
    )
    results.append({"case": "PRIVATE_ENDPOINT", "ok": not private.ok})

    # Auth header rejected.
    auth = validate_request_boundary_v1(
        url=f"https://{EEA_PUBLIC_MD_HOST}/api/v5/public/time",
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": "PeakTradePhase92Preflight/1.0",
            "Authorization": "Bearer x",
        },
        environ={"PATH": "/usr/bin", "HOME": "/tmp"},
    )
    results.append({"case": "AUTH_HEADER", "ok": not auth.ok})

    # Non-EEA host rejected.
    www = validate_request_boundary_v1(
        url="https://www.okx.com/api/v5/public/time",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "PeakTradePhase92Preflight/1.0"},
        environ={"PATH": "/usr/bin", "HOME": "/tmp"},
    )
    results.append({"case": "NON_EEA_HOST", "ok": not www.ok})

    # Smoke contract with network pre-auth rejected.
    bad = SmokeSessionContractV1(**{**contract.to_dict(), "network_session_authorized": True})
    gaps = validate_smoke_session_contract_v1(bad)
    results.append(
        {"case": "NETWORK_PREAUTH_IN_CONTRACT", "ok": "NETWORK_SESSION_PREAUTHORIZED" in gaps}
    )

    # Unbounded reconnect rejected.
    bad2_dict = contract.to_dict()
    bad2_dict["reconnect_attempt_limit"] = 0
    bad2 = SmokeSessionContractV1(**bad2_dict)
    gaps2 = validate_smoke_session_contract_v1(bad2)
    results.append({"case": "UNBOUNDED_RECONNECT", "ok": "UNBOUNDED_OR_EMPTY_RECONNECT" in gaps2})

    ok = all(bool(r["ok"]) for r in results)
    return {"ok": ok, "cases": results, "SmokeContractError": SmokeContractError.__name__}
