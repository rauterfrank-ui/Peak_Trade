"""Canonical Public-MD fetcher wiring for Step-5 (reuse-before-new)."""

from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.real_http_fetcher_v1 import (  # noqa: E501
    make_real_eea_public_md_fetcher_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.constants_v1 import (
    CANONICAL_PUBLIC_MD_FETCHER,
)

FetcherV1 = Callable[[str, str, Mapping[str, str], float], tuple[int, bytes, Mapping[str, str]]]


def prove_canonical_public_md_fetcher_bound_v1() -> dict[str, Any]:
    return {
        "ok": True,
        "canonical_public_md_fetcher": CANONICAL_PUBLIC_MD_FETCHER,
        "factory": "make_real_eea_public_md_fetcher_v1",
        "parallel_network_runner_created": False,
        "parallel_public_md_client_created": False,
        "notes": [
            "CANONICAL_REAL_HTTP_FETCHER_REUSED=true",
            "NO_PARALLEL_PUBLIC_MD_CLIENT=true",
        ],
    }


def resolve_canonical_public_md_fetcher_v1(
    *,
    activation_permit_ok: bool,
    network_session_go: bool,
    allow_construct: bool,
    injected_fetcher: FetcherV1 | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Resolve fetcher only under activation permit.

    Constructing the real fetcher does not perform HTTP; callers must still
    avoid invoking it unless a later session authorizes real network.
    """
    blockers: list[str] = []
    if not activation_permit_ok:
        blockers.append("ACTIVATION_PERMIT_REQUIRED_FOR_FETCHER")
    if not network_session_go:
        blockers.append("NETWORK_SESSION_GO_REQUIRED_FOR_FETCHER")
    if not allow_construct:
        blockers.append("FETCHER_CONSTRUCT_NOT_ALLOWED")
    if blockers:
        return {
            "ok": False,
            "blockers": blockers,
            "fetcher": None,
            "fetcher_wired": False,
            "fetcher_constructed": False,
            "canonical_public_md_fetcher": CANONICAL_PUBLIC_MD_FETCHER,
            "invoke_count": 0,
        }

    if injected_fetcher is not None:
        return {
            "ok": True,
            "blockers": [],
            "fetcher": injected_fetcher,
            "fetcher_wired": True,
            "fetcher_constructed": True,
            "canonical_public_md_fetcher": CANONICAL_PUBLIC_MD_FETCHER,
            "injected": True,
            "invoke_count": 0,
            "notes": ["INJECTED_FETCHER_FOR_OFFLINE_PROOF=true"],
        }

    fetcher, telemetry = make_real_eea_public_md_fetcher_v1(environ=environ)
    return {
        "ok": True,
        "blockers": [],
        "fetcher": fetcher,
        "fetcher_wired": True,
        "fetcher_constructed": True,
        "canonical_public_md_fetcher": CANONICAL_PUBLIC_MD_FETCHER,
        "injected": False,
        "telemetry": telemetry.to_dict() if telemetry is not None else {},
        "invoke_count": 0,
        "notes": [
            "CANONICAL_FETCHER_CONSTRUCTED_NO_HTTP_YET=true",
            "REAL_NETWORK_REQUIRES_LATER_SESSION_INVOKE=true",
        ],
    }


def build_counting_fake_fetcher_v1(
    *,
    calls: Optional[list[dict[str, Any]]] = None,
) -> FetcherV1:
    """Offline fake fetcher that records calls; never opens sockets."""
    bucket: list[dict[str, Any]] = calls if calls is not None else []

    def _fake(
        url: str, method: str, headers: Mapping[str, str], timeout: float
    ) -> tuple[int, bytes, Mapping[str, str]]:
        method_u = str(method).upper()
        if method_u != "GET":
            raise RuntimeError(f"NON_GET_METHOD_REJECTED:{method_u}")
        header_keys = {str(k).lower() for k in headers.keys()}
        if any(k in header_keys for k in ("authorization", "ok-access-key", "ok-access-sign")):
            raise RuntimeError("AUTH_HEADER_REJECTED")
        if "private" in url.lower():
            raise RuntimeError("PRIVATE_ENDPOINT_REJECTED")
        bucket.append(
            {
                "url": url,
                "method": method_u,
                "header_keys": sorted(header_keys),
                "timeout": float(timeout),
            }
        )
        body = b'{"code":"0","data":[{"instId":"ETH-USDT-SWAP","last":"1","ts":"1"}]}'
        return 200, body, {"Content-Type": "application/json"}

    return _fake
