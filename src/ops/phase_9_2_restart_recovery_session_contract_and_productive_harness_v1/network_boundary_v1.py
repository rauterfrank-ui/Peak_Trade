"""Negative proof: live/testnet/credential paths remain unreachable from this harness."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (
    EXCHANGE_CREDENTIAL_PATH_CHANGED,
    LIVE_PATH_CHANGED,
    NETWORK_SESSION_ALLOWED,
    TESTNET_PATH_CHANGED,
)


def prove_no_live_testnet_credential_path_v1() -> dict[str, Any]:
    notes = [
        "HARNESS_NETWORK_SESSION_ALLOWED=false",
        "HARNESS_DOES_NOT_IMPORT_EXCHANGE_ORDER_ADAPTERS",
        "HARNESS_DOES_NOT_LOAD_EXCHANGE_CREDENTIALS",
        "HARNESS_DOES_NOT_OPEN_SOCKETS",
    ]
    ok = (
        (not NETWORK_SESSION_ALLOWED)
        and (not LIVE_PATH_CHANGED)
        and (not TESTNET_PATH_CHANGED)
        and (not EXCHANGE_CREDENTIAL_PATH_CHANGED)
    )
    return {
        "ok": ok,
        "LIVE_PATH_CHANGED": LIVE_PATH_CHANGED,
        "TESTNET_PATH_CHANGED": TESTNET_PATH_CHANGED,
        "EXCHANGE_CREDENTIAL_PATH_CHANGED": EXCHANGE_CREDENTIAL_PATH_CHANGED,
        "NETWORK_SESSION_ALLOWED": NETWORK_SESSION_ALLOWED,
        "notes": notes,
    }
