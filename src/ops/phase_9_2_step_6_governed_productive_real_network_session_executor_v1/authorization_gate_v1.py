"""Authorization gate — validate-only in this binding; no consume/mint."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_ISSUANCE_ALLOWED,
    CAPABILITY_ID,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)


def validate_execution_authorization_artifact_v1(
    *,
    authorization_id: str,
    authorization_digest: str,
    expected_repository_sha: str,
    expected_capability_id: str = CAPABILITY_ID,
    expected_scope: str = SESSION_SCOPE,
    expected_session_id: str = TARGET_SESSION_ID,
    already_consumed: bool = False,
    live_trading_allowed: bool = False,
    testnet_allowed: bool = False,
    paper_exchange_orders_allowed: bool = False,
    exchange_credential_use_allowed: bool = False,
    real_capital_movement_allowed: bool = False,
) -> dict[str, Any]:
    """Structural authorization presence/scope check. Does not consume."""
    blockers: list[str] = []
    if AUTHORIZATION_ISSUANCE_ALLOWED:
        blockers.append("AUTHORIZATION_ISSUANCE_MUST_REMAIN_FALSE")
    if AUTHORIZATION_CONSUMPTION_ALLOWED:
        blockers.append("AUTHORIZATION_CONSUMPTION_MUST_REMAIN_FALSE")
    if not str(authorization_id or "").strip():
        blockers.append("AUTHORIZATION_MISSING")
        blockers.append("AUTHORIZATION_ID_MISSING")
    if not str(authorization_digest or "").strip():
        blockers.append("AUTHORIZATION_MISSING")
        blockers.append("AUTHORIZATION_DIGEST_MISSING")
    if len(str(authorization_digest or "").strip()) < 16:
        blockers.append("AUTHORIZATION_DIGEST_INVALID")
    if not str(expected_repository_sha or "").strip():
        blockers.append("REPOSITORY_SHA_INVALID")
    if already_consumed:
        blockers.append("AUTHORIZATION_ALREADY_CONSUMED")
    if live_trading_allowed:
        blockers.append("LIVE_TRADING_FORBIDDEN")
    if testnet_allowed:
        blockers.append("TESTNET_FORBIDDEN")
    if paper_exchange_orders_allowed:
        blockers.append("PAPER_EXCHANGE_ORDERS_FORBIDDEN")
    if exchange_credential_use_allowed:
        blockers.append("EXCHANGE_CREDENTIAL_USE_FORBIDDEN")
    if real_capital_movement_allowed:
        blockers.append("REAL_CAPITAL_MOVEMENT_FORBIDDEN")
    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "authorization_id": str(authorization_id or ""),
        "authorization_digest": str(authorization_digest or ""),
        "expected_capability_id": expected_capability_id,
        "expected_scope": expected_scope,
        "expected_session_id": expected_session_id,
        "authorization_consumed": False,
        "orders_disabled": True,
        "notes": [
            "AUTHORIZATION_VALIDATE_ONLY_IN_BINDING=true",
            "NO_AUTHORIZATION_CONSUMPTION_IN_BINDING=true",
        ],
    }
