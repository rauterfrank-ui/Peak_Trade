"""Constants for §11.13.2 LIVE_PRIVATE_READ_ONLY preparation surface.

Preparation-only defaults: no Live activation, no Cap-11.7 network unlock,
no productive proven claim from fixtures.
"""

from __future__ import annotations

CAPABILITY_ID = "SECTION_11_13_2_LIVE_PRIVATE_READ_ONLY_V1"
PACKAGE_MARKER = "SECTION_11_13_2_LIVE_PRIVATE_READ_ONLY_V1=true"
OWNER = "ops.section_11_13_2_live_private_read_only_v1"
CONTRACT_VERSION = "v1"
SCHEMA_VERSION = "section_11_13_2_live_private_read_only.v1"
CONFIG_VERSION = "section_11_13_2_live_private_read_only_config.v1"
EVIDENCE_CONTRACT_VERSION = "section_11_13_2_live_private_read_only_proven.v1"

OWNER_GO_PREPARATION = (
    "OWNER_GO_AUTHOR_SINGLE_PREPARATION_PR_SECTION_11_13_2_LIVE_PRIVATE_READ_ONLY_SURFACE"
)
OWNER_GO_PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING = (
    "OWNER_GO_SECTION_11_13_2_PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING"
)
OWNER_GO_EXECUTE = "OWNER_GO_LIVE_PRIVATE_READ_ONLY"
AUTHORIZATION_SCOPE = "LIVE_PRIVATE_READ_ONLY"
AUTHORIZATION_SCOPE_ALIASES_FORBIDDEN: tuple[str, ...] = (
    "LIVE_AUTHORIZED",
    "LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION",
    "LIVE_DRY_RUN_ORDER_PLAN",
    "LIVE_CANARY_MINIMUM_EXPOSURE",
    "LIVE_BOUNDED_SINGLE_FUTURE",
    "SECTION_11_13_LIVE_ACTIVATION",
)

# Standing safety defaults (preparation + execute both keep these false unless
# separately Owner-authorized outside this package).
LIVE_PRIVATE_READ_ONLY_AUTHORIZED_DEFAULT = False
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
REQUIRED_CREDENTIAL_CLASS = "LIVE_PRIVATE_READ_ONLY_API_KEY"
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
SECRETREF_FORBIDDEN_PATH_MARKERS: tuple[str, ...] = (
    "/demo",
    "/testnet",
    "/simulated",
    "/paper",
)
SECRETREF_CONVENTION_EXAMPLE = "secretref://vault/peak-trade/live-private-ro/<venue>"

# Known non-LIVE hosts that must never be accepted for §11.13.2.
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
# Minimal private read-only endpoint allowlist (logical path names).
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
FORBIDDEN_MUTATION_ENDPOINT_MARKERS: tuple[str, ...] = (
    "/trade/order",
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
EVIDENCE_ROOT_TEMPLATE = "evidence/ops/section_11_13_2_live_private_read_only_proven_v1/<RUN_ID>/"
EVIDENCE_DIRNAME = "section_11_13_2_live_private_read_only_proven_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
CLAIMS_FILENAME = "claims.json"
SUMMARY_FILENAME = "SUMMARY.json"
PROOF_FILENAME = "LIVE_PRIVATE_READ_ONLY_PROOF.json"
CONFIG_DIGEST_FILENAME = "config_digest.json"
AUTHORIZATION_FILENAME = "authorization_binding.json"
ZERO_WRITE_FILENAME = "zero_write_assertions.json"
REDACTION_FILENAME = "redaction_check.json"

# Next stage after a later successful productive proof (not claimed here).
CANONICAL_NEXT_STEP_AFTER_PROVEN = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION"
)
CANONICAL_NEXT_STEP_AFTER_PREPARATION_MERGE = "OWNER_GO_LIVE_PRIVATE_READ_ONLY"
CURRENT_CANONICAL_NEXT_STEP_AUTHORITY = "SECTION_11_13_2"

# Explicit non-claims for preparation / unlock authoring (merge != execute).
LIVE_PRIVATE_READ_ONLY_PROVEN = False
LIVE_PRIVATE_READ_ONLY_EXECUTED = False
PREPARATION_SURFACE_READY = True
PRODUCTIVE_EXECUTE_PATH_READY = True
PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING_BOUND = True
CORE_LOGIC_CHANGE = False
ORDER_EFFECT = "NONE"
NETWORK_EFFECT_DEFAULT = "NONE"
CREDENTIAL_ACCESS_DEFAULT = "NONE"

# Owner permission attestation required for productive execute evidence.
REQUIRED_PERMISSION_ATTESTATION = {"READ": True, "TRADE": False, "WITHDRAW": False}
