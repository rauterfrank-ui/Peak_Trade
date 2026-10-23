"""Constants for the isolated read-only observation GET path.

RUNTIME_AUTHORIZATION_EFFECT=NONE
PRIVATE_GET_GO is not consumed. POST and external effect stay false.
"""

from __future__ import annotations

CREDENTIAL_CLASS = "READ_ONLY_OBSERVATION_API_KEY"
SECRETREF_URI = "secretref://vault/peak-trade/read-only-observation/okx"
FORBIDDEN_TRADE_CREDENTIAL_CLASS = "LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY"
FORBIDDEN_TRADE_SECRETREF_URI = "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"
K1_KEYCHAIN_SERVICE = "peak-trade.full-core.venue-credentials"
K1_KEYCHAIN_ACCOUNT = "okx-eea.productive"
K1_SOURCE_CREDENTIAL_CLASS = "FULL_CORE_VENUE_AUTH_CLASS"
K1_SOURCE_REF_URI = "fullcore-cred://provider-ref/okx-eea-productive"

AUTHORIZED_HOST = "eea.okx.com"
REST_BASE = f"https://{AUTHORIZED_HOST}"
ALLOWED_METHODS = frozenset({"GET"})
USER_AGENT = "PeakTrade-ReadOnly-Observation-GET/1"

ALLOWED_ENDPOINTS = frozenset(
    {
        "/api/v5/account/config",
        "/api/v5/account/positions",
        "/api/v5/account/balance",
        "/api/v5/account/max-size",
        "/api/v5/account/leverage-info",
        "/api/v5/trade/orders-pending",
    }
)

POST_ALLOWED = False
EXTERNAL_EFFECT_AUTHORIZED = False
NETWORK_SEND_AUTHORIZED = False
ORDERS_AUTHORIZED = False
SELECTION_PRODUCER_INVOKED = False
PRODUCTIVE_CYCLE_INVOKED = False

__all__ = [
    "ALLOWED_ENDPOINTS",
    "ALLOWED_METHODS",
    "AUTHORIZED_HOST",
    "CREDENTIAL_CLASS",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "FORBIDDEN_TRADE_CREDENTIAL_CLASS",
    "FORBIDDEN_TRADE_SECRETREF_URI",
    "K1_KEYCHAIN_ACCOUNT",
    "K1_KEYCHAIN_SERVICE",
    "K1_SOURCE_CREDENTIAL_CLASS",
    "K1_SOURCE_REF_URI",
    "NETWORK_SEND_AUTHORIZED",
    "ORDERS_AUTHORIZED",
    "POST_ALLOWED",
    "PRODUCTIVE_CYCLE_INVOKED",
    "REST_BASE",
    "SECRETREF_URI",
    "SELECTION_PRODUCER_INVOKED",
    "USER_AGENT",
]
