"""Constants for §11.12.8 OKX EEA Demo XPerp venue/host/account/instrument binding.

NO_ORDER package. Does not authorize network sessions, credentials load,
preflight, orders, Testnet activation, Live, or §11.13.

Active canonical §11.12.8 derivatives path only. OKX Global Demo and
BTC-USDT-SWAP remain historical / forensic / non-active.
"""

from __future__ import annotations

CAPABILITY_ID = (
    "CAPABILITY_11_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1"
)
PACKAGE_MARKER = (
    "CAPABILITY_11_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_VENUE_HOST_ACCOUNT_INSTRUMENT_BINDING_V1=true"
)
OWNER = "ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1"
CONTRACT_VERSION = "v1"

OWNER_GO_TOKEN = (
    "OWNER_GO_CANONICAL_EEA_XPERP_REBINDING_AND_SECTION_11_12_8_CONTINUATION_PREP_NO_ORDER"
)
PREDECESSOR_PRIVATE_RO_PROOF_EVIDENCE = (
    "evidence/ops/section_11_12_8_retry_okx_eea_private_ro_xperp_verify_no_order_v1/"
    "20260810T165847Z/"
)
CANONICAL_NEXT_STEP_AFTER_MERGE = (
    "OWNER_GO_EXECUTE_BOUNDED_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN"
    "_WITH_HIDDEN_CONFIRM_AND_SECRETREF_VAULT_RUNTIME"
)
# Historical predecessor pointer (consumed; forensic only).
CANONICAL_NEXT_STEP_AFTER_BINDING_PACKAGE_HISTORICAL = (
    "OWNER_GO_EXECUTE_BOUNDED_SECTION_11_12_8_CONTINUATION_ON_OKX_EEA_DEMO_XPERP_NO_ORDER"
)
SECTION_11_12_8_STATUS = "OPEN_OKX_EEA_DEMO_XPERP_CAMPAIGN_WRITE_PATH_READY_AWAITING_OWNER_EXECUTE"

# Bound scope (exact; no silent substitution).
VENUE = "OKX_EEA_DEMO"
ENVIRONMENT = "DEMO"
RUNTIME_MODE = "TESTNET"
REST_HOST = "eea.okx.com"
REST_BASE = "https://eea.okx.com"
DEMO_MARKER_HEADER_NAME = "x-simulated-trading"
DEMO_MARKER_HEADER_VALUE = "1"
INSTRUMENT_SCOPE_EXACT = "BTC-USD_UM_XPERP-310328"
INSTRUMENT_TYPE = "FUTURES"
RULE_TYPE = "xperp"
CREDENTIAL_CLASS = "OKX_EEA_DEMO_TRADING_API_KEY_ONLY"
SECRET_REFERENCE = "secretref://vault/peak-trade/testnet-demo"
ACCOUNT_IDENTITY_PLACEHOLDER = "acct-uid-testnet-demo"

# EEA host is not the Global shared Live host; still require Demo marker.
SHARED_HOST_WITH_LIVE = False
SHARED_HOST_REQUIRES_DEMO_MARKER = True
SHARED_HOST_REQUIRES_DEMO_CREDENTIAL_CLASS = True

FORBIDDEN_SILENT_FALLBACK = True
FORBIDDEN_GENERIC_SYMBOL_SUBSTITUTION = True
FORBIDDEN_VENUE_FALLBACKS: tuple[str, ...] = (
    "okx_global",
    "OKX_GLOBAL",
    "OKX_GLOBAL_DEMO",
    "binance_usdm_testnet",
    "bybit_testnet",
    "kraken_futures_demo",
)
FORBIDDEN_HOST_FALLBACKS: tuple[str, ...] = (
    "openapi.okx.com",
    "www.okx.com",
    "okx.com",
    "aws.okx.com",
    "us.okx.com",
    "tr.okx.com",
)
# BTC-USDT-SWAP must not silently return as the active EEA derivatives instrument.
FORBIDDEN_INSTRUMENT_SUBSTITUTIONS: tuple[str, ...] = (
    "BTC-USDT-SWAP",
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
GLOBAL_CREDENTIAL_CLASS_MARKERS: tuple[str, ...] = (
    "OKX_GLOBAL",
    "OKX_DEMO_TRADING_API_KEY_ONLY",
    "GLOBAL_DEMO_API_KEY",
)

# Safety / authorization defaults for this package.
ORDER_POST_AUTHORIZED = False
ORDER_ATTEMPT_COUNT = 0
PRIVATE_WRITE_COUNT = 0
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
XPERP_PRIVATE_CAPABILITY_PROOF_BOUND = True
LEGACY_BTC_USDT_SWAP_ACTIVE_BINDING_REMOVED = True
OKX_GLOBAL_DEMO_ACTIVE_BINDING = False

PRIVATE_ENDPOINT_ALLOWLIST_NO_ORDER: tuple[str, ...] = (
    "/api/v5/account/balance",
    "/api/v5/account/config",
    "/api/v5/account/instruments",
    "/api/v5/account/positions",
    "/api/v5/trade/orders-pending",
)
ORDER_MUTATION_ENDPOINTS_HARD_BLOCKED: tuple[str, ...] = (
    "/api/v5/trade/order",
    "/api/v5/trade/cancel-order",
    "/api/v5/trade/batch-orders",
    "/api/v5/trade/cancel-batch-orders",
    "/api/v5/trade/amend-order",
)

THREAT_MODEL_DELTA_ID = (
    "THREAT_MODEL_DELTA_OKX_EEA_DEMO_XPERP_HOST_HEADER_CREDENTIAL_INSTRUMENT_ISOLATION_V1"
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
    "§11.12.8.5",
    "§11.12.8.6",
    "§11.12.9",
)

EVIDENCE_DIRNAME = "section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
THREAT_MODEL_DELTA_FILENAME = "THREAT_MODEL_DELTA.json"
BINDING_PROOF_FILENAME = "BINDING_CONTRACT_PROOF.json"
