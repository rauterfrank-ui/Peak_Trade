"""Constants for §11.13.4 LIVE_DRY_RUN_ORDER_PLAN."""

from __future__ import annotations

CAPABILITY_ID = "SECTION_11_13_4_LIVE_DRY_RUN_ORDER_PLAN_V1"
PACKAGE_MARKER = "SECTION_11_13_4_LIVE_DRY_RUN_ORDER_PLAN_V1=true"
OWNER = "ops.section_11_13_4_live_dry_run_order_plan_v1"
CONTRACT_VERSION = "v1"
SCHEMA_VERSION = "section_11_13_4_live_dry_run_order_plan.v1"
CONFIG_VERSION = "section_11_13_4_live_dry_run_order_plan_config.v1"
EVIDENCE_CONTRACT_VERSION = "section_11_13_4_live_dry_run_order_plan_proven.v1"

OWNER_GO_EXECUTE = "OWNER_GO_LIVE_DRY_RUN_ORDER_PLAN"
AUTHORIZATION_SCOPE = "LIVE_DRY_RUN_ORDER_PLAN"
AUTHORIZATION_SCOPE_ALIASES_FORBIDDEN: tuple[str, ...] = (
    "LIVE_AUTHORIZED",
    "LIVE_PRIVATE_READ_ONLY",
    "LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION",
    "LIVE_CANARY_MINIMUM_EXPOSURE",
    "LIVE_BOUNDED_SINGLE_FUTURE",
    "LIVE_BOUNDED_MULTI_SESSION",
    "LIVE_AUTONOMOUS_SINGLE_FUTURE",
    "SECTION_11_13_LIVE_ACTIVATION",
)

LIVE_DRY_RUN_ORDER_PLAN_AUTHORIZED_DEFAULT = False
LIVE_AUTHORIZED = False
LIVE_ENABLED = False
LIVE_ARMED = False
LIVE_ORDER_AUTHORIZED = False
ENABLE_LIVE_TRADING = False
FULLY_AUTONOMOUS_LIVE_TRADING_READY = False
FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE = False
TESTNET_AUTHORIZED = False
ORDERS_AUTHORIZED = False
CANARY_AUTHORIZED = False

CAPABILITY_11_7_REMAINS_CONTRACTS_ONLY = True
CAPABILITY_11_8_REMAINS_FIXTURE_ONLY = True
CAPABILITY_11_8_LIVE_DRY_RUN_ORDER_PLAN_ACTIVATED = False

PREDECESSOR_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN_REQUIRED = True
PREDECESSOR_LIVE_PRIVATE_READ_ONLY_PROVEN_REQUIRED = True

REQUIRED_ENVIRONMENT = "LIVE"
FORBIDDEN_ENVIRONMENTS: tuple[str, ...] = (
    "DEMO",
    "TESTNET",
    "PAPER",
    "SIMULATED",
    "SHADOW",
    "FIXTURE",
)
REQUIRED_CREDENTIAL_CLASS = "LIVE_DRY_RUN_ORDER_PLAN_READ_ONLY_API_KEY"
FORBIDDEN_CREDENTIAL_CLASS_MARKERS: tuple[str, ...] = (
    "DEMO",
    "TESTNET",
    "SIMULATED",
    "PAPER",
    "OKX_DEMO",
    "OKX_EEA_DEMO",
    "KRKEN_DEMO",
    "KRAKEN_DEMO",
)
SECRETREF_URI_PREFIX = "secretref://"
SECRETREF_LIVE_PATH_MARKER = "/live"
SECRETREF_DRY_RUN_PATH_MARKER = "/live-dry-run-order-plan"
SECRETREF_FORBIDDEN_CROSS_PACKAGE_MARKERS: tuple[str, ...] = (
    "/live-private-ro",
    "/live-shadow-recon",
)
SECRETREF_FORBIDDEN_PATH_MARKERS: tuple[str, ...] = (
    "/demo",
    "/testnet",
    "/simulated",
    "/paper",
)
SECRETREF_CONVENTION_EXAMPLE = "secretref://vault/peak-trade/live-dry-run-order-plan/<venue>"

FORBIDDEN_HOST_MARKERS: tuple[str, ...] = (
    "demo-futures.kraken.com",
    "demo.",
    "testnet.",
    "sandbox.",
    "simulated",
    "paper-",
)
OWNER_SUPPLIED_LIVE_HOST_REQUIRED = True
HARDCODED_PRODUCTION_HOST = ""

METHOD_ALLOWLIST: tuple[str, ...] = ("GET",)
FORBIDDEN_HTTP_METHODS: tuple[str, ...] = (
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "HEAD",
    "OPTIONS",
    "TRACE",
    "CONNECT",
)
ENDPOINT_ALLOWLIST: tuple[str, ...] = (
    "/api/v5/account/balance",
    "/api/v5/account/config",
    "/api/v5/account/positions",
    "/api/v5/trade/orders-pending",
    "/api/v5/market/ticker",
)
REQUIRED_ACCOUNT_IDENTITY_ENDPOINTS: tuple[str, ...] = (
    "/api/v5/account/config",
    "/api/v5/account/balance",
)
REQUIRED_RECONCILIATION_SNAPSHOT_ENDPOINTS: tuple[str, ...] = (
    "/api/v5/account/config",
    "/api/v5/account/balance",
    "/api/v5/account/positions",
    "/api/v5/trade/orders-pending",
)
PUBLIC_REFERENCE_PRICE_ENDPOINT = "/api/v5/market/ticker"
FORBIDDEN_MUTATION_ENDPOINT_MARKERS: tuple[str, ...] = (
    "/api/v5/trade/order",
    "/trade/cancel",
    "/trade/amend",
    "/trade/batch",
    "/trade/close-position",
    "/asset/withdrawal",
    "/asset/transfer",
    "/users/subaccount",
    "/account/set-",
    "sendorder",
    "cancelorder",
    "editorder",
    "batchorder",
    "withdraw",
    "transfer",
)
FORBIDDEN_ORDER_API_METHODS: tuple[str, ...] = (
    "place_order",
    "submit_order",
    "cancel_order",
    "amend_order",
    "close_position",
    "set_leverage",
    "set_position_mode",
    "transfer",
    "withdraw",
)

FORBIDDEN_DEMO_SIMULATION_HEADERS: tuple[str, ...] = (
    "x-simulated-trading",
    "x-simulation",
    "ok-simulated-trading",
)

DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_RETRIES = 2
MAX_RETRIES_HARD_CAP = 3
DEFAULT_MAX_REQUEST_COUNT = 5
MAX_REQUEST_COUNT_HARD_CAP = 8
RETRY_BACKOFF_SECONDS = 0.25

TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP = "LIVE_PRODUCTIVE_HTTP"
TRANSPORT_CLASS_GOVERNED_FIXTURE = "GOVERNED_FIXTURE"
TRANSPORT_CLASS_PREFLIGHT_NO_NETWORK = "PREFLIGHT_NO_NETWORK"

EVIDENCE_ROOT_TEMPLATE = "evidence/ops/section_11_13_4_live_dry_run_order_plan_proven_v1/<RUN_ID>/"
EVIDENCE_DIRNAME = "section_11_13_4_live_dry_run_order_plan_proven_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
CLAIMS_FILENAME = "claims.json"
SUMMARY_FILENAME = "SUMMARY.json"
PROOF_FILENAME = "LIVE_DRY_RUN_ORDER_PLAN_PROOF.json"
ORDER_PLAN_FILENAME = "ORDER_PLAN.json"
CONFIG_DIGEST_FILENAME = "config_digest.json"
AUTHORIZATION_FILENAME = "authorization_binding.json"
ZERO_WRITE_FILENAME = "zero_write_assertions.json"
REDACTION_FILENAME = "redaction_check.json"
RECONCILIATION_FILENAME = "RECONCILIATION_LAYER_EVALUATION.json"
EXCHANGE_SNAPSHOT_FILENAME = "EXCHANGE_SNAPSHOT.sanitized.json"
LOCAL_EXPECTED_STATE_FILENAME = "LOCAL_EXPECTED_STATE.sanitized.json"
MUTATION_BOUNDARY_FILENAME = "MUTATION_BOUNDARY.json"

CANONICAL_NEXT_STEP_AFTER_PROVEN = "OWNER_GO_REQUIRED_SEPARATE_FOR_LIVE_CANARY_MINIMUM_EXPOSURE"
CANONICAL_NEXT_STEP_AFTER_PREPARATION_MERGE = "OWNER_GO_LIVE_DRY_RUN_ORDER_PLAN"
CURRENT_CANONICAL_NEXT_STEP_AUTHORITY = "SECTION_11_13_4"

LIVE_DRY_RUN_ORDER_PLAN_PROVEN = False
LIVE_DRY_RUN_ORDER_PLAN_EXECUTED = False
PREPARATION_SURFACE_READY = True
PRODUCTIVE_EXECUTE_PATH_READY = True
CORE_LOGIC_CHANGE = False
ORDER_EFFECT = "NONE"
NETWORK_EFFECT_DEFAULT = "NONE"
CREDENTIAL_ACCESS_DEFAULT = "NONE"
REQUIRED_PERMISSION_ATTESTATION = {"READ": True, "TRADE": False, "WITHDRAW": False}

LIVE_RECONCILIATION_PROVEN = False
BLOCKS_NEW_ENTRY = True
UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY = True
DRY_RUN_MARKER = True
SUBMIT_FORBIDDEN = True
EXECUTION_MODE_ALLOWED = "LIVE_DRY_RUN"
LIFECYCLE_STATE_ALLOWED = "PRE_SUBMIT_VALIDATED"
LIFECYCLE_STATES_FORBIDDEN: tuple[str, ...] = (
    "SUBMIT_PENDING",
    "SUBMITTED",
    "ACKED",
    "PARTIAL_FILL",
    "FILLED",
    "CANCEL_PENDING",
    "CANCELED",
)

DEFAULT_INSTRUMENT_ID = "BTC-USDT-SWAP"
DEFAULT_SIDE = "BUY"
DEFAULT_ORDER_TYPE = "LIMIT"
DEFAULT_QUANTITY = "1"
DEFAULT_TD_MODE = "cross"
DEFAULT_FEE_BPS_ASSUMPTION = "2.0"
DEFAULT_SLIPPAGE_BPS_ASSUMPTION = "5.0"
MIN_NOTIONAL_USDT_ASSUMPTION = "5.0"

REUSED_SECTION_11_13_3_BINDING_SOURCE = "evidence/ops/section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1/20260811T211828Z/"
REUSED_SECTION_11_13_3_BINDING_VENUE = "OKX"
REUSED_SECTION_11_13_3_BINDING_ENTITY = "OKX Europe Limited"
REUSED_SECTION_11_13_3_BINDING_REGION = "EEA/DE"
REUSED_SECTION_11_13_3_BINDING_REST_HOST = "eea.okx.com"
REUSED_SECTION_11_13_3_BINDING_ACCOUNT_SCOPE = "856964404452495999"
REUSED_SECTION_11_13_3_DRY_RUN_SECRETREF_URI = (
    "secretref://vault/peak-trade/live-dry-run-order-plan/okx"
)
