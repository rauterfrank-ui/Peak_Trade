"""Kraken Futures Demo credential presence-only contract (v0).

Tracks ENV key names and non-authorizing policy flags only. Does not read secret
values, does not authorize private API, network, orders, or futures execute.
"""

from __future__ import annotations

from typing import Any

PACKAGE_MARKER = "KRAKEN_FUTURES_DEMO_CREDENTIAL_PRESENCE_CONTRACT_V0=true"

KRAKEN_FUTURES_DEMO_API_KEY_ENV_NAME = "KRAKEN_FUTURES_DEMO_API_KEY"
KRAKEN_FUTURES_DEMO_API_SECRET_ENV_NAME = "KRAKEN_FUTURES_DEMO_API_SECRET"

REQUIRED_CREDENTIAL_ENV_KEYS: tuple[str, ...] = (
    KRAKEN_FUTURES_DEMO_API_KEY_ENV_NAME,
    KRAKEN_FUTURES_DEMO_API_SECRET_ENV_NAME,
)

# Spot / live / generic testnet gates — must not satisfy futures demo presence.
FORBIDDEN_ALTERNATE_ENV_KEYS: frozenset[str] = frozenset(
    {
        "KRAKEN_TESTNET_API_KEY",
        "KRAKEN_TESTNET_API_SECRET",
        "PEAK_TRADE_TESTNET_OPERATOR_GATE_ACK",
        "PEAK_TRADE_TESTNET_CONFIG_DECLARED",
        "KRAKEN_API_KEY",
        "KRAKEN_API_SECRET",
    }
)

CREDENTIAL_NAMESPACE = "kraken_futures_demo_only"

CONFIRM_TOKEN_PRESENCE_ONLY_MANUAL = "I_ACCEPT_KRAKEN_FUTURES_DEMO_PRESENCE_ONLY_MANUAL_CHECK"


def build_checker_boundary_v0() -> dict[str, Any]:
    return {
        "non_authorizing": True,
        "credential_namespace": CREDENTIAL_NAMESPACE,
        "futures_execute_authorized": False,
        "futures_validate_only_authorized": False,
        "futures_private_api_authorized": False,
        "futures_session_authorized_now": False,
        "credential_read_authorized": False,
        "credential_presence_check_authorized": False,
        "private_api_authorized": False,
        "next_execute_allowed": False,
        "live_not_authorized": True,
        "preflight_remains_blocked": True,
        "ready_for_operator_arming": False,
        "order_submission_authorized": False,
        "checker_does_not_connect_to_exchange": True,
        "checker_does_not_validate_credentials": True,
        "checker_does_not_read_credential_values": True,
        "checker_does_not_hash_credential_values": True,
    }
