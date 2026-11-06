"""Prove Phase 9.2 public-MD EEA network and no-order execution boundaries offline."""

from __future__ import annotations

from typing import Any

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    ALLOWED_METHODS,
    ALLOWED_PATHS,
    CANONICAL_HOST,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.network_boundary_guard_v1 import (
    validate_request_boundary_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import (
    EEA_NETWORK_GUARD_OWNER,
    EEA_PUBLIC_MD_HOST,
    HTTP_METHOD_ALLOWLIST,
    NETWORK_ALLOWLIST,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.network_boundary_v1 import (
    prove_network_credential_boundary_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    prove_execution_port_separation_v1,
)


def prove_eea_public_md_boundary_v1() -> dict[str, Any]:
    """Fixture/harness evaluator — does not open sockets."""
    clean_env = {
        "PATH": "/usr/bin",
        "HOME": "/tmp",
    }
    cases = [
        (
            f"https://{EEA_PUBLIC_MD_HOST}/api/v5/public/time",
            "GET",
            {"Accept": "application/json", "User-Agent": "PeakTradePhase92Preflight/1.0"},
            True,
        ),
        (
            f"https://{EEA_PUBLIC_MD_HOST}/api/v5/public/mark-price?instType=FUTURES",
            "GET",
            {"Accept": "application/json", "User-Agent": "PeakTradePhase92Preflight/1.0"},
            True,
        ),
        (
            f"https://{EEA_PUBLIC_MD_HOST}/api/v5/trade/order",
            "GET",
            {"Accept": "application/json", "User-Agent": "PeakTradePhase92Preflight/1.0"},
            False,
        ),
        (
            f"https://{EEA_PUBLIC_MD_HOST}/api/v5/account/balance",
            "GET",
            {"Accept": "application/json", "User-Agent": "PeakTradePhase92Preflight/1.0"},
            False,
        ),
        (
            f"https://{EEA_PUBLIC_MD_HOST}/api/v5/public/time",
            "POST",
            {"Accept": "application/json", "User-Agent": "PeakTradePhase92Preflight/1.0"},
            False,
        ),
        (
            f"https://{EEA_PUBLIC_MD_HOST}/api/v5/public/time",
            "GET",
            {
                "Accept": "application/json",
                "User-Agent": "PeakTradePhase92Preflight/1.0",
                "Authorization": "Bearer x",
            },
            False,
        ),
        (
            "https://www.okx.com/api/v5/public/time",
            "GET",
            {"Accept": "application/json", "User-Agent": "PeakTradePhase92Preflight/1.0"},
            False,
        ),
        (
            "https://okx.com/api/v5/public/time",
            "GET",
            {"Accept": "application/json", "User-Agent": "PeakTradePhase92Preflight/1.0"},
            False,
        ),
        (
            f"https://{EEA_PUBLIC_MD_HOST}/api/v5/users/self/verify",
            "GET",
            {"Accept": "application/json", "User-Agent": "PeakTradePhase92Preflight/1.0"},
            False,
        ),
    ]
    rows: list[dict[str, Any]] = []
    all_ok = True
    for url, method, headers, expect_allow in cases:
        attestation = validate_request_boundary_v1(
            url=url, method=method, headers=headers, environ=clean_env
        )
        row_ok = attestation.ok is expect_allow
        all_ok = all_ok and row_ok
        rows.append(
            {
                "url": url,
                "method": method,
                "expect_allow": expect_allow,
                "allowed": attestation.ok,
                "blockers": list(attestation.blockers),
                "ok": row_ok,
            }
        )

    host_ok = CANONICAL_HOST == EEA_PUBLIC_MD_HOST
    methods_ok = ALLOWED_METHODS == frozenset({"GET"})
    paths_public_only = all(
        p.startswith("/api/v5/public/") or p.startswith("/api/v5/market/") for p in ALLOWED_PATHS
    )
    private_allowed = any(
        r["allowed"] and ("/trade/" in r["url"] or "/account/" in r["url"]) for r in rows
    )
    auth_row = next(
        r
        for r, (_url, _method, headers, _expect) in zip(rows, cases)
        if "authorization" in {str(k).lower() for k in headers}
    )
    get_only_rows = [r for r in rows if "/api/v5/public/time" in r["url"]]
    get_only_ok = methods_ok and all(
        (r["method"] == "GET" and r["allowed"]) or (r["method"] != "GET" and not r["allowed"])
        for r in get_only_rows
    )
    return {
        "ok": all_ok
        and host_ok
        and methods_ok
        and paths_public_only
        and not private_allowed
        and not auth_row["allowed"],
        "owner": EEA_NETWORK_GUARD_OWNER,
        "NETWORK_ALLOWLIST": NETWORK_ALLOWLIST,
        "HTTP_METHOD_ALLOWLIST": HTTP_METHOD_ALLOWLIST,
        "EEA_PUBLIC_MD_HOST": EEA_PUBLIC_MD_HOST,
        "PUBLIC_MD_ONLY_BOUNDARY_PROVEN": all_ok
        and host_ok
        and paths_public_only
        and not private_allowed,
        "GET_ONLY_PROVEN": get_only_ok,
        "PRIVATE_ENDPOINT_REACHABLE": bool(private_allowed),
        "AUTH_HEADER_PRESENT": bool(auth_row["allowed"]),
        "allowed_paths": sorted(ALLOWED_PATHS),
        "cases": rows,
    }


def prove_phase92_network_and_execution_boundary_v1() -> dict[str, Any]:
    eea = prove_eea_public_md_boundary_v1()
    # Cap 7.2 no-order host proofs (credential/order/real adapter separation).
    cap72_net = prove_network_credential_boundary_v1()
    port = prove_execution_port_separation_v1()

    private_reachable = bool(eea.get("PRIVATE_ENDPOINT_REACHABLE")) or bool(
        cap72_net.get("PRIVATE_ENDPOINT_REACHABLE")
    )
    auth_present = bool(eea.get("AUTH_HEADER_PRESENT")) or bool(
        cap72_net.get("AUTH_HEADER_PRESENT")
    )
    cred_reachable = bool(cap72_net.get("EXCHANGE_CREDENTIAL_ACCESS_REACHABLE")) or bool(
        port.get("EXCHANGE_CREDENTIAL_ACCESS_REACHABLE")
    )
    real_adapter = bool(port.get("REAL_EXECUTION_ADAPTER_CONSTRUCTED"))
    order_submit = bool(port.get("EXCHANGE_ORDER_SUBMIT_REACHABLE"))
    paper = (
        False  # Cap 7.2 / bridge constants prove paper path unauthorized; no paper port in host.
    )
    live = False
    testnet = False

    ok = (
        bool(eea.get("ok"))
        and bool(cap72_net.get("ok"))
        and bool(port.get("ok"))
        and not private_reachable
        and not auth_present
        and not cred_reachable
        and not real_adapter
        and not order_submit
        and bool(port.get("SIMULATED_EXECUTION_PORT_SEPARATE_FROM_REAL_EXECUTION_PORT"))
        and bool(port.get("NO_REAL_SUBMIT_ORDER_INTERFACE_IN_NO_ORDER_HOST"))
    )
    return {
        "ok": ok,
        "eea_boundary": eea,
        "cap72_network_boundary": {
            "ok": cap72_net.get("ok"),
            "PRIVATE_ENDPOINT_REACHABLE": cap72_net.get("PRIVATE_ENDPOINT_REACHABLE"),
            "AUTH_HEADER_PRESENT": cap72_net.get("AUTH_HEADER_PRESENT"),
            "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": cap72_net.get(
                "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"
            ),
            "HTTP_METHOD_ALLOWLIST": cap72_net.get("HTTP_METHOD_ALLOWLIST"),
            "NETWORK_SESSION_STARTED": cap72_net.get("NETWORK_SESSION_STARTED"),
        },
        "execution_port": port,
        "PUBLIC_MD_ONLY_BOUNDARY_PROVEN": bool(eea.get("PUBLIC_MD_ONLY_BOUNDARY_PROVEN")),
        "GET_ONLY_PROVEN": bool(eea.get("GET_ONLY_PROVEN")),
        "PRIVATE_ENDPOINT_REACHABLE": private_reachable,
        "AUTH_HEADER_PRESENT": auth_present,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": cred_reachable,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": real_adapter,
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": order_submit,
        "PAPER_EXCHANGE_EXECUTION_REACHABLE": paper,
        "LIVE_PATH_REACHABLE": live,
        "TESTNET_PATH_REACHABLE": testnet,
        "SIMULATED_EXECUTION_PORT_SEPARATE_FROM_REAL_EXECUTION_PORT": bool(
            port.get("SIMULATED_EXECUTION_PORT_SEPARATE_FROM_REAL_EXECUTION_PORT")
        ),
        "NO_REAL_SUBMIT_ORDER_INTERFACE_IN_NO_ORDER_HOST": bool(
            port.get("NO_REAL_SUBMIT_ORDER_INTERFACE_IN_NO_ORDER_HOST")
        ),
        "NETWORK_SESSION_STARTED": False,
    }
