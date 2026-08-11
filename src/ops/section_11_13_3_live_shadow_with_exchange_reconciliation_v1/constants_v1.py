"""Constants for §11.13.3 LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION preparation surface.

Preparation-only defaults: no Live activation, no Cap-11.7 network unlock,
no productive proven claim from fixtures.
"""

from __future__ import annotations

CAPABILITY_ID = "SECTION_11_13_3_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_V1"
PACKAGE_MARKER = "SECTION_11_13_3_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_V1=true"
OWNER = "ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1"
CONTRACT_VERSION = "v1"
SCHEMA_VERSION = "section_11_13_3_live_shadow_with_exchange_reconciliation.v1"
CONFIG_VERSION = "section_11_13_3_live_shadow_with_exchange_reconciliation_config.v1"
EVIDENCE_CONTRACT_VERSION = "section_11_13_3_live_shadow_with_exchange_reconciliation_proven.v1"

OWNER_GO_PREPARATION = "OWNER_GO_AUTHOR_SINGLE_PREPARATION_PR_SECTION_11_13_3_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_SURFACE"
OWNER_GO_PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING = (
    "OWNER_GO_SECTION_11_13_3_PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING"
)
OWNER_GO_EXECUTE = "OWNER_GO_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION"
AUTHORIZATION_SCOPE = "LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION"
AUTHORIZATION_SCOPE_ALIASES_FORBIDDEN: tuple[str, ...] = (
    "LIVE_AUTHORIZED",
    "LIVE_PRIVATE_READ_ONLY",
    "LIVE_DRY_RUN_ORDER_PLAN",
    "LIVE_CANARY_MINIMUM_EXPOSURE",
    "LIVE_BOUNDED_SINGLE_FUTURE",
    "LIVE_BOUNDED_MULTI_SESSION",
    "LIVE_AUTONOMOUS_SINGLE_FUTURE",
    "SECTION_11_13_LIVE_ACTIVATION",
)

# Standing safety defaults (preparation + execute both keep these false unless
# separately Owner-authorized outside this package).
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_AUTHORIZED_DEFAULT = False
LIVE_AUTHORIZED = False
LIVE_ENABLED = False
LIVE_ARMED = False
LIVE_ORDER_AUTHORIZED = False
ENABLE_LIVE_TRADING = False
FULLY_AUTONOMOUS_LIVE_TRADING_READY = False
FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE = False
TESTNET_AUTHORIZED = False
ORDERS_AUTHORIZED = False
SHADOW_AUTHORIZED = False
CANARY_AUTHORIZED = False
NETWORK_SESSION_AUTHORIZED_DEFAULT = False
CREDENTIAL_MATERIAL_LOAD_AUTHORIZED_DEFAULT = False

# Cap 11.7 remains contracts-only; this package must not unlock it.
CAPABILITY_11_7_REMAINS_CONTRACTS_ONLY = True
CAPABILITY_11_7_NETWORK_UNLOCK_FORBIDDEN = True
CAPABILITY_11_7_LIVE_PRIVATE_READONLY_ACTIVATED = False
CAPABILITY_11_7_LIVE_SHADOW_RECONCILIATION_ACTIVATED = False

# Predecessor §11.13.2 must already be proven before a later productive execute.
PREDECESSOR_LIVE_PRIVATE_READ_ONLY_PROVEN_REQUIRED = True

# Environment / credential isolation.
REQUIRED_ENVIRONMENT = "LIVE"
FORBIDDEN_ENVIRONMENTS: tuple[str, ...] = (
    "DEMO",
    "TESTNET",
    "PAPER",
    "SIMULATED",
    "SHADOW",
    "FIXTURE",
)
REQUIRED_CREDENTIAL_CLASS = "LIVE_SHADOW_RECONCILIATION_READ_ONLY_API_KEY"
FORBIDDEN_CREDENTIAL_CLASS_MARKERS: tuple[str, ...] = (
    "DEMO",
    "TESTNET",
    "SIMULATED",
    "PAPER",
    "OKX_DEMO",
    "OKX_EEA_DEMO",
    "KRKEN_DEMO",
    "KRAKEN_DEMO",
    "BINANCE_TESTNET",
)
SECRETREF_URI_PREFIX = "secretref://"
SECRETREF_LIVE_PATH_MARKER = "/live"
SECRETREF_SHADOW_PATH_MARKER = "/live-shadow-recon"
SECRETREF_FORBIDDEN_CROSS_PACKAGE_MARKERS: tuple[str, ...] = ("/live-private-ro",)
SECRETREF_FORBIDDEN_PATH_MARKERS: tuple[str, ...] = (
    "/demo",
    "/testnet",
    "/simulated",
    "/paper",
)
SECRETREF_CONVENTION_EXAMPLE = "secretref://vault/peak-trade/live-shadow-recon/<venue>"

# Known non-LIVE hosts that must never be accepted for §11.13.3.
FORBIDDEN_HOST_MARKERS: tuple[str, ...] = (
    "demo-futures.kraken.com",
    "demo.",
    "testnet.",
    "sandbox.",
    "simulated",
    "paper-",
)
# Owner must supply the exact productive REST host at execute time.
# No production host is hard-wired in this preparation package.
OWNER_SUPPLIED_LIVE_HOST_REQUIRED = True
HARDCODED_PRODUCTION_HOST = ""

# HTTP guards.
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
# Minimal private read-only endpoint allowlist for exchange snapshot GETs.
ENDPOINT_ALLOWLIST: tuple[str, ...] = (
    "/api/v5/account/balance",
    "/api/v5/account/config",
    "/api/v5/account/positions",
    "/api/v5/trade/orders-pending",
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
# Mutation markers must not false-positive on GET /trade/orders-pending.
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

# §11.5 reconciliation layers / outcomes (Live shadow stage contract).
RECONCILIATION_LAYERS: tuple[str, ...] = (
    "credential_and_account_identity",
    "venue_instrument_and_contract_metadata",
    "open_orders",
    "recent_orders_and_trades",
    "positions",
    "balances_equity_and_available_margin",
    "local_portfolio_and_accounting",
    "risk_reservations",
    "pending_commands",
    "evidence_and_commit_cursors",
)
RECONCILIATION_OUTCOMES: tuple[str, ...] = (
    "MATCH",
    "SAFE_REBUILD",
    "SAFE_ADOPT_EXCHANGE_TRUTH",
    "CANCEL_UNKNOWN_ORDERS",
    "EXIT_ONLY",
    "REDUCE_ONLY",
    "CANCEL_ALL_AND_HALT",
    "HARD_STOP_OWNER_REVIEW",
)
RECONCILIATION_BEFORE_ALPHA = True
RECONCILIATION_CONTINUOUS = True
UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY = True
EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY = True
SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN = True
NO_AUTOMATIC_STAGE_PROMOTION = True
NO_LIVE_ORDER_FROM_SHADOW_RECONCILIATION = True
NO_ACCOUNT_MUTATION_FROM_SHADOW_RECONCILIATION = True
SECTION_11_13_LIVE_SHADOW_CANARY_PROGRESSION_STARTED = False
LIVE_RECONCILIATION_PROVEN = False
FORBIDDEN_DEMO_SIMULATION_HEADERS: tuple[str, ...] = (
    "x-simulated-trading",
    "x-simulation",
    "ok-simulated-trading",
)

# Bounds.
DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_RETRIES = 2
MAX_RETRIES_HARD_CAP = 3
DEFAULT_MAX_REQUEST_COUNT = 4
MAX_REQUEST_COUNT_HARD_CAP = 6
RETRY_BACKOFF_SECONDS = 0.25

# Transport classes.
TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP = "LIVE_PRODUCTIVE_HTTP"
TRANSPORT_CLASS_GOVERNED_FIXTURE = "GOVERNED_FIXTURE"
TRANSPORT_CLASS_PREFLIGHT_NO_NETWORK = "PREFLIGHT_NO_NETWORK"

# Evidence root contract.
EVIDENCE_ROOT_TEMPLATE = (
    "evidence/ops/section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1/<RUN_ID>/"
)
EVIDENCE_DIRNAME = "section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
CLAIMS_FILENAME = "claims.json"
SUMMARY_FILENAME = "SUMMARY.json"
PROOF_FILENAME = "LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROOF.json"
CONFIG_DIGEST_FILENAME = "config_digest.json"
AUTHORIZATION_FILENAME = "authorization_binding.json"
ZERO_WRITE_FILENAME = "zero_write_assertions.json"
REDACTION_FILENAME = "redaction_check.json"
RECONCILIATION_FILENAME = "RECONCILIATION_LAYER_EVALUATION.json"
EXCHANGE_SNAPSHOT_FILENAME = "EXCHANGE_SNAPSHOT.sanitized.json"
LOCAL_EXPECTED_STATE_FILENAME = "LOCAL_EXPECTED_STATE.sanitized.json"

# Next stage after a later successful productive proof (not claimed here).
CANONICAL_NEXT_STEP_AFTER_PROVEN = "OWNER_GO_REQUIRED_SEPARATE_FOR_LIVE_DRY_RUN_ORDER_PLAN"
CANONICAL_NEXT_STEP_AFTER_PREPARATION_MERGE = "OWNER_GO_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION"
CURRENT_CANONICAL_NEXT_STEP_AUTHORITY = "SECTION_11_13_3"

# Explicit non-claims for preparation / unlock authoring (merge != execute).
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN = False
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_EXECUTED = False
PREPARATION_SURFACE_READY = True
PRODUCTIVE_EXECUTE_PATH_READY = True
PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING_BOUND = True
CORE_LOGIC_CHANGE = False
ORDER_EFFECT = "NONE"
NETWORK_EFFECT_DEFAULT = "NONE"
CREDENTIAL_ACCESS_DEFAULT = "NONE"
REQUIRED_PERMISSION_ATTESTATION = {"READ": True, "TRADE": False, "WITHDRAW": False}

# Proven §11.13.2 binding reuse metadata (non-secret; Owner-authorized for later execute).
REUSED_SECTION_11_13_2_BINDING_SOURCE = (
    "evidence/ops/section_11_13_2_live_private_read_only_proven_v1/20260811T170310Z/"
)
REUSED_SECTION_11_13_2_BINDING_VENUE = "OKX"
REUSED_SECTION_11_13_2_BINDING_ENTITY = "OKX Europe Limited"
REUSED_SECTION_11_13_2_BINDING_REGION = "EEA/DE"
REUSED_SECTION_11_13_2_BINDING_REST_HOST = "eea.okx.com"
REUSED_SECTION_11_13_2_BINDING_ACCOUNT_SCOPE = "856964404452495999"
REUSED_SECTION_11_13_2_SHADOW_SECRETREF_URI = "secretref://vault/peak-trade/live-shadow-recon/okx"
