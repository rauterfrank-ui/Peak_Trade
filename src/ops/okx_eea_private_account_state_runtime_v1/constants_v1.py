"""OKX_EEA_PRIVATE_ACCOUNT_STATE_RUNTIME_V1 — observation-only private state plane."""

from __future__ import annotations

CAPABILITY_ID = "OKX_EEA_PRIVATE_ACCOUNT_STATE_RUNTIME_V1"
PACKAGE_MARKER = "OKX_EEA_PRIVATE_ACCOUNT_STATE_RUNTIME_V1=true"
SCHEMA_VERSION = "okx_eea_private_account_state_runtime.v1"
OWNER = "ops.okx_eea_private_account_state_runtime_v1"

POLICY_CONFIG_RELATIVE = "config/governance/okx_eea_private_account_state_runtime_v1_policy_v1.json"

CREDENTIAL_CLASS = "OKX_EEA_PRIVATE_OBSERVATION_READ_V1"
FORBIDDEN_TRADE_CREDENTIAL_CLASSES = frozenset(
    {
        "LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY",
        "OKX_EEA_TRADE_API_KEY",
    }
)

EEA_REST_HOST = "eea.okx.com"
EEA_REST_BASE = "https://eea.okx.com"
EEA_PRIVATE_WS_BASE = "wss://wseea.okx.com:8443/ws/v5/private"
DEMO_ONLY_PRIVATE_WS_HOST = "wseeapap.okx.com"
FORBIDDEN_PRODUCTION_PRIVATE_WS_HOSTS = frozenset({"wseeapap.okx.com"})

REST_WS_DISAGREEMENT = "RECONCILIATION_REQUIRED_FAIL_CLOSED"
SAFE_ADOPT_EXCHANGE_TRUTH = False
PRIVATE_STATE_GLOBAL_TTL_SECONDS = None

PRIVATE_WS_ORDER_SEND_AUTHORIZED = False
PRIVATE_WS_AMEND_AUTHORIZED = False
PRIVATE_WS_CANCEL_AUTHORIZED = False
REST_POST_PERMIT_CHANGE = False

SELECTION_AUTHORITY = "NONE"
STRATEGY_AUTHORITY = "NONE"
RANKING_AUTHORITY = "NONE"
EXECUTION_AUTHORITY = "NONE"
WIRE_AUTHORITY = "NONE"

WP_B_STRATEGY_AUTHORITY = False
WP_B_RANKING_AUTHORITY = False
WP_B_SELECTION_AUTHORITY = False

PRIVATE_BALANCE_EQUITY_OBSERVATION_ALLOWED = True
PRIVATE_STATE_PLANE_EQUITY_SIZING_AUTHORITY = False
RUNNING_ACCOUNT_EQUITY_MINT_ALLOWED = False

MULTI_FUTURE_RUNTIME_AUTHORIZED = False
MAX_POSITIONS_EFFECTIVE = 1
K2_ABSENT = True

DEDICATED_FILLS_WS_REQUIRED = False
DEDICATED_FILLS_WS_OPTIONAL = True

FRESH_PRETRADE_FRESHNESS_POLICY = "FRESH_GET_PER_PRETRADE_DECISION"
POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS = 5000

BASELINE_REST_GET_ALLOWLIST = frozenset(
    {
        "/api/v5/account/config",
        "/api/v5/account/balance",
        "/api/v5/account/positions",
        "/api/v5/trade/orders-pending",
        "/api/v5/trade/orders-history",
        "/api/v5/trade/fills",
        "/api/v5/account/leverage-info",
        "/api/v5/account/max-size",
    }
)

BASELINE_REST_RECOVERY_ALLOWLIST = frozenset(
    {
        "/api/v5/account/config",
        "/api/v5/account/balance",
        "/api/v5/account/positions",
        "/api/v5/trade/orders-pending",
        "/api/v5/trade/orders-history",
        "/api/v5/trade/fills",
    }
)

FRESH_PRETRADE_ONLY_GET_PATHS = frozenset(
    {
        "/api/v5/account/leverage-info",
        "/api/v5/account/max-size",
        "/api/v5/account/config",
    }
)

OBSERVATION_WS_CHANNELS_V1 = frozenset(
    {
        "account",
        "positions",
        "orders",
        "balance_and_position",
    }
)

OPTIONAL_FILLS_WS_CHANNEL = "fills"

FORBIDDEN_WS_MUTATION_OPS = frozenset(
    {
        "order",
        "batch-orders",
        "cancel-order",
        "batch-cancel-orders",
        "amend-order",
        "batch-amend-orders",
        "mass-cancel",
    }
)

DEFAULT_MAX_RECONNECT_ATTEMPTS = 10
DEFAULT_HEARTBEAT_SECONDS = 5.0
DEFAULT_BACKOFF_INITIAL_SECONDS = 1.0
DEFAULT_BACKOFF_MAX_SECONDS = 30.0

STATE_STORE_SCHEMA = "okx_eea_private_state_record.v1"

QUALITY_CURRENT = "CURRENT"
QUALITY_STALE = "STALE"
QUALITY_UNKNOWN = "UNKNOWN"
QUALITY_RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
QUALITY_INVALID = "INVALID"
