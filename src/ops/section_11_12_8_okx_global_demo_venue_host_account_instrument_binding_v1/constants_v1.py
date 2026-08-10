"""Constants for §11.12.8 OKX Global Demo venue/host/account/instrument binding.

NO_ORDER package. Does not authorize network sessions, credentials load,
preflight, orders, Testnet activation, Live, or §11.13.
"""

from __future__ import annotations

CAPABILITY_ID = (
    "CAPABILITY_11_SECTION_11_12_8_OKX_GLOBAL_DEMO_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1"
)
PACKAGE_MARKER = (
    "CAPABILITY_11_SECTION_11_12_8_OKX_GLOBAL_DEMO_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1=true"
)
OWNER = "ops.section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1"
CONTRACT_VERSION = "v1"

OWNER_GO_TOKEN = (
    "OWNER_GO_AUTHORIZE_OKX_GLOBAL_DEMO_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_PACKAGE_NO_ORDER"
)
PREDECESSOR_OWNER_GO_SELECT = (
    "OWNER_GO_SELECT_ALTERNATE_DERIVATIVES_TESTNET_VENUE_SCOPE_FOR_SECTION_11_12_8_CONTINUATION"
)
CANONICAL_NEXT_STEP_AFTER_MERGE = (
    "OWNER_GO_EXECUTE_BOUNDED_NO_ORDER_PREFLIGHT_ON_OKX_GLOBAL_DEMO_BTC_USDT_SWAP"
)

# Bound scope (exact; no silent substitution).
VENUE = "okx_global"
ENVIRONMENT = "DEMO"
RUNTIME_MODE = "TESTNET"
REST_HOST = "openapi.okx.com"
REST_BASE = "https://openapi.okx.com"
DEMO_MARKER_HEADER_NAME = "x-simulated-trading"
DEMO_MARKER_HEADER_VALUE = "1"
INSTRUMENT_SCOPE_EXACT = "BTC-USDT-SWAP"
INSTRUMENT_TYPE = "SWAP"
CREDENTIAL_CLASS = "OKX_DEMO_TRADING_API_KEY_ONLY"
SECRET_REFERENCE = "secretref://vault/peak-trade/okx-global-demo-trading"
ACCOUNT_IDENTITY_PLACEHOLDER = "acct-uid-okx-global-demo"

# Shared-host compensating controls (Cybersecurity V2.1 §19 / §20).
SHARED_HOST_WITH_LIVE = True
SHARED_HOST_REQUIRES_DEMO_MARKER = True
SHARED_HOST_REQUIRES_DEMO_CREDENTIAL_CLASS = True

FORBIDDEN_SILENT_FALLBACK = True
FORBIDDEN_GENERIC_SYMBOL_SUBSTITUTION = True
FORBIDDEN_VENUE_FALLBACKS: tuple[str, ...] = (
    "okx_eea",
    "okx_europe",
    "binance_usdm_testnet",
    "bybit_testnet",
    "kraken_futures_demo",
)
FORBIDDEN_HOST_FALLBACKS: tuple[str, ...] = (
    "eea.okx.com",
    "www.okx.com",
    "okx.com",
    "aws.okx.com",
    "us.okx.com",
    "tr.okx.com",
)
FORBIDDEN_INSTRUMENT_SUBSTITUTIONS: tuple[str, ...] = (
    "BTC-USD-SWAP",
    "ETH-USD_UM_XPERP-310404",
    "ETH-USD_UM_XPERP-310328",
    "BTCUSDT",
    "BTC-USDT",
)
LIVE_CREDENTIAL_CLASS_MARKERS: tuple[str, ...] = (
    "OKX_LIVE",
    "LIVE_API_KEY",
    "LIVE_TRADING_API_KEY",
    "PRODUCTION_API_KEY",
    "OKX_EEA_LIVE",
)
EEA_CREDENTIAL_CLASS_MARKERS: tuple[str, ...] = (
    "OKX_EEA_DEMO",
    "OKX_EEA",
    "EEA_DEMO_API_KEY",
)

# Safety / authorization defaults for this package.
ORDER_POST_AUTHORIZED = False
ORDER_ATTEMPT_COUNT = 0
NETWORK_SESSION_AUTHORIZED = False
TESTNET_AUTHORIZED = False
LIVE_AUTHORIZED = False
SECTION_11_13_STARTED = False
PRE_LIVE_CYBERSECURITY_GATE = "NOT_PASSED"
PRE_LIVE_CYBERSECURITY_GATE_CONTRACT = "MANDATORY"
CORE_LOGIC_CHANGE = False
PRODUCTIVE_PREFLIGHT_AUTHORIZED = False
VENUE_ACTIVATED = False
CREDENTIAL_PLAINTEXT_LOADED = False
CREDENTIAL_MATERIAL_RESOLVED = False

PRIVATE_ENDPOINT_ALLOWLIST_NO_ORDER: tuple[str, ...] = (
    "/api/v5/account/balance",
    "/api/v5/account/config",
    "/api/v5/trade/orders-pending",
)
# Order mutation endpoints exist in OKX V5 but are hard-blocked by this package.
ORDER_MUTATION_ENDPOINTS_HARD_BLOCKED: tuple[str, ...] = (
    "/api/v5/trade/order",
    "/api/v5/trade/cancel-order",
    "/api/v5/trade/batch-orders",
    "/api/v5/trade/cancel-batch-orders",
    "/api/v5/trade/amend-order",
)

THREAT_MODEL_DELTA_ID = (
    "THREAT_MODEL_DELTA_OKX_GLOBAL_DEMO_SHARED_HOST_HEADER_CREDENTIAL_ISOLATION_V1"
)
CYBERSECURITY_RUNBOOK_BINDINGS: tuple[str, ...] = (
    "§4.3",
    "§19",
    "§20",
    "§21",
)
MASTER_RUNBOOK_BINDINGS: tuple[str, ...] = (
    "§4.8",
    "§4.8.1",
    "§11.12.8.3",
    "§11.12.8.4",
    "§11.12.9",
)

EVIDENCE_DIRNAME = "section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
THREAT_MODEL_DELTA_FILENAME = "THREAT_MODEL_DELTA.json"
BINDING_PROOF_FILENAME = "BINDING_CONTRACT_PROOF.json"
