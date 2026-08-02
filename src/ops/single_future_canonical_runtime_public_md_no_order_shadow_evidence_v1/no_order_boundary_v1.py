"""No-order / public-MD-only boundary proofs for Cap 5.2."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.constants_v1 import (
    LIVE_AUTHORIZED,
    LIVE_TRADING,
    ORDERS_AUTHORIZED,
    OWNER,
    PAPER_EXECUTION_AUTHORIZED,
    PAPER_ORDER_EXECUTION_ALLOWED,
    PUBLIC_MARKET_DATA_ONLY,
    RUNTIME_ACTIVATED,
    RUNTIME_ACTIVATION_ALLOWED,
    TESTNET_AUTHORIZED,
    TESTNET_TRADING,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.constants_v1 import (
    LIVE_AUTHORIZED as BRIDGE_LIVE_AUTHORIZED,
    ORDERS_AUTHORIZED as BRIDGE_ORDERS_AUTHORIZED,
    PAPER_EXECUTION_AUTHORIZED as BRIDGE_PAPER_AUTHORIZED,
    RUNTIME_BRIDGE_LIVE_ACTIVATED,
    TESTNET_AUTHORIZED as BRIDGE_TESTNET_AUTHORIZED,
)


def prove_no_order_public_md_boundary_v1(
    *,
    authorization_consumption: Mapping[str, Any],
    public_md_capture: Mapping[str, Any],
) -> dict[str, Any]:
    package_root = Path(__file__).resolve().parent
    # Scan implementation modules only; exclude this guard module (contains deny-list literals).
    scan_names = (
        "evidence_gate_v1.py",
        "authorization_consumption_v1.py",
        "persistence_v1.py",
        "__init__.py",
        "constants_v1.py",
    )
    text = ""
    for name in scan_names:
        path = package_root / name
        if path.is_file():
            text += path.read_text(encoding="utf-8")
    # Reconstruct deny tokens so this guard file itself is not a false positive.
    hard_forbidden = ("/api/v5/" + "trade/", "/api/v5/" + "account/")
    hard_hits = [tok for tok in hard_forbidden if tok in text]
    auth_ok = bool(authorization_consumption.get("authorization_consumed")) and (
        not bool(authorization_consumption.get("orders_authorized"))
    )
    capture_ok = (
        bool(public_md_capture.get("public_market_data_only"))
        and (not bool(public_md_capture.get("private_api_used")))
        and (not bool(public_md_capture.get("orders_attempted")))
    )
    ok = (
        auth_ok
        and capture_ok
        and not hard_hits
        and PUBLIC_MARKET_DATA_ONLY
        and not ORDERS_AUTHORIZED
        and not LIVE_AUTHORIZED
        and not TESTNET_AUTHORIZED
        and not PAPER_ORDER_EXECUTION_ALLOWED
        and not PAPER_EXECUTION_AUTHORIZED
        and not LIVE_TRADING
        and not TESTNET_TRADING
        and not RUNTIME_ACTIVATED
        and not RUNTIME_ACTIVATION_ALLOWED
        and not BRIDGE_ORDERS_AUTHORIZED
        and not BRIDGE_LIVE_AUTHORIZED
        and not BRIDGE_TESTNET_AUTHORIZED
        and not BRIDGE_PAPER_AUTHORIZED
        and not RUNTIME_BRIDGE_LIVE_ACTIVATED
    )
    return {
        "ok": ok,
        "owner": OWNER,
        "NO_LIVE_ORDER_PATH": ok and not LIVE_AUTHORIZED and not BRIDGE_LIVE_AUTHORIZED,
        "NO_TESTNET_ORDER_PATH": ok and not TESTNET_AUTHORIZED and not BRIDGE_TESTNET_AUTHORIZED,
        "NO_PAPER_ORDER_PATH": ok
        and not PAPER_ORDER_EXECUTION_ALLOWED
        and not PAPER_EXECUTION_AUTHORIZED
        and not BRIDGE_PAPER_AUTHORIZED,
        "NO_ORDER_PATH": ok and not ORDERS_AUTHORIZED and not BRIDGE_ORDERS_AUTHORIZED,
        "PUBLIC_MD_NETWORK_ONLY": ok and PUBLIC_MARKET_DATA_ONLY,
        "NETWORK_ACCESS_OCCURRED": bool(public_md_capture.get("network_access_occurred")),
        "PRIVATE_API_USED": bool(public_md_capture.get("private_api_used")),
        "ORDERS_ATTEMPTED": bool(public_md_capture.get("orders_attempted")),
        "hard_forbidden_token_hits": hard_hits,
        "RUNTIME_ACTIVATED": RUNTIME_ACTIVATED,
    }
