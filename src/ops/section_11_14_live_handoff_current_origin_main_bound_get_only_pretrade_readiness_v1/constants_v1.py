"""Fail-closed constants for the current-origin/main GET-only pretrade surface."""

from __future__ import annotations

CAPABILITY_ID = (
    "SECTION_11_14_LIVE_HANDOFF_CURRENT_ORIGIN_MAIN_BOUND_GET_ONLY_"
    "PRETRADE_ACCOUNT_NETWORK_AND_INSTRUMENT_READINESS_V1"
)
CONTRACT_VERSION = "v1"
SCHEMA_VERSION = "section_11_14_current_origin_main_bound_get_only_pretrade_readiness.v1"
OWNER = "ops.section_11_14_live_handoff_current_origin_main_bound_get_only_pretrade_readiness_v1"
THIS_SLICE = (
    "11.14.LIVE_HANDOFF_CURRENT_ORIGIN_MAIN_BOUND_GET_ONLY_"
    "PRETRADE_ACCOUNT_NETWORK_AND_INSTRUMENT_READINESS"
)
PREDECESSOR_WORKPACKAGE = (
    "SECTION_11_14_LIVE_HANDOFF_EXACT_SINGLE_LIVE_EXECUTION_READINESS_AND_AUTHORIZATION_ENVELOPE_V2"
)
LAST_CANONICALLY_CLOSED_STEP = (
    "SECTION_11_14_LIVE_HANDOFF_EXACT_SINGLE_LIVE_IDENTITY_BOUND_"
    "VENUE_FILL_THEN_CONTEMPORANEOUS_PRE_RESTART_CAPTURE"
)

USER_AGENT = "PeakTrade-Section-11-14-GetOnlyPretrade/1"
REST_SCHEME_HOST = "https://eea.okx.com"
METHOD_ALLOWLIST: tuple[str, ...] = ("GET",)
FORBIDDEN_HTTP_METHODS: tuple[str, ...] = (
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "HEAD",
    "OPTIONS",
    "CONNECT",
    "TRACE",
)

PATH_ACCOUNT_CONFIG = "/api/v5/account/config"
PATH_ACCOUNT_BALANCE = "/api/v5/account/balance"
PATH_ACCOUNT_POSITIONS = "/api/v5/account/positions"
PATH_ACCOUNT_LEVERAGE_INFO = "/api/v5/account/leverage-info"
PATH_ACCOUNT_MAX_SIZE = "/api/v5/account/max-size"
PATH_ACCOUNT_TRADE_FEE = "/api/v5/account/trade-fee"
PATH_PUBLIC_INSTRUMENTS = "/api/v5/public/instruments"
PATH_PUBLIC_PRICE_LIMIT = "/api/v5/public/price-limit"
PATH_MARKET_TICKER = "/api/v5/market/ticker"

ENDPOINT_PATH_ALLOWLIST: tuple[str, ...] = (
    PATH_ACCOUNT_CONFIG,
    PATH_ACCOUNT_BALANCE,
    PATH_ACCOUNT_POSITIONS,
    PATH_ACCOUNT_LEVERAGE_INFO,
    PATH_ACCOUNT_MAX_SIZE,
    PATH_ACCOUNT_TRADE_FEE,
    PATH_PUBLIC_INSTRUMENTS,
    PATH_PUBLIC_PRICE_LIMIT,
    PATH_MARKET_TICKER,
)
PRIVATE_ENDPOINT_PATHS: frozenset[str] = frozenset(
    {
        PATH_ACCOUNT_CONFIG,
        PATH_ACCOUNT_BALANCE,
        PATH_ACCOUNT_POSITIONS,
        PATH_ACCOUNT_LEVERAGE_INFO,
        PATH_ACCOUNT_MAX_SIZE,
        PATH_ACCOUNT_TRADE_FEE,
    }
)
PUBLIC_ENDPOINT_PATHS: frozenset[str] = frozenset(
    {
        PATH_PUBLIC_INSTRUMENTS,
        PATH_PUBLIC_PRICE_LIMIT,
        PATH_MARKET_TICKER,
    }
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
FORBIDDEN_IMPORT_MARKERS: tuple[str, ...] = (
    "submit_transport_v1",
    "LiveCanaryHttpClientV1",
    "section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1",
    "post_entry_order",
    "post_flatten_order",
    "post_cancel_order",
    "pre_restart_handoff_capture_hook_v1",
    "pre_restart_handoff_capture_caller_v1",
    "run_canary_submit_transport_v1",
)

OBSOLETE_FROZEN_ORIGIN_MAIN_SHA = "6d25cd2ced346f760db26ca488183b45d19b3d73"
OBSOLETE_SHA_MUST_NOT_BE_INVOCATION_GATE = True
OWNER_GO_MUST_NOT_BE_REQUIRED = True
MAX_GET_REQUEST_COUNT = 9
TIMEOUT_SECONDS = 10.0
TIMEOUT_MUST_NOT_RETRY = True
REDIRECT_FOLLOW_FORBIDDEN = True
SOURCE_EVIDENCE_CURRENT = "CURRENT_ORIGIN_MAIN_BOUND_GET_ONLY_PRETRADE_READINESS_V1"

DEFAULT_VAULT_RELATIVE = (
    ".ops_local/section_11_13_5_live_canary_minimum_exposure/secrets/secretref_vault.json"
)
EVIDENCE_RELATIVE_ROOT = (
    "evidence/ops/section_11_14_live_handoff_current_origin_main_bound_"
    "get_only_pretrade_readiness_v1"
)
SUMMARY_FILENAME = "SUMMARY.json"
CLAIMS_FILENAME = "claims.json"
ADJUDICATION_FILENAME = "ADJUDICATION.json"
CENSUS_FILENAME = "CENSUS.json"
GET_LOG_FILENAME = "GET_RESULTS.sanitized.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
LINEAGE_FILENAME = "LINEAGE.json"

ACCOUNT_MODE_REQUIRED_VALUE = "2"
POS_MODE_REQUIRED_VALUE = "net_mode"
PLANNED_TD_MODE = "cross"
LEVERAGE_EXPECTED_MGN_MODE = "cross"
SIDE = "BUY"
ORDER_TYPE = "LIMIT"
ORDER_QTY = "1"
ORDER_QTY_UNIT = "CONTRACTS_SZ"
INSTRUMENT_STATE_REQUIRED = "live"
MAX_SUBMIT_ATTEMPTS = 1
MAX_SUCCESSFUL_SUBMITS = 1

EXISTING_SURFACE_CENSUS: tuple[dict[str, str], ...] = (
    {
        "path": (
            "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "private_read_only_gets_v1.py"
        ),
        "endpoints": "/api/v5/account/config,/api/v5/account/balance",
        "get_only_endpoints": "true",
        "client_post_reachable": "true",
        "owner_go_required": "true",
        "obsolete_expected_origin_main_sha": OBSOLETE_FROZEN_ORIGIN_MAIN_SHA,
        "submit_import": "false",
        "flags_mutated": "false",
        "current_main_invocable": "false",
        "disposition": "REJECT_FOR_THIS_WP",
    },
    {
        "path": ("src/ops/section_11_13_5_p08_read_only_closure_v1/"),
        "endpoints": "frozen P08 private GET pack",
        "get_only_endpoints": "true",
        "client_post_reachable": "false",
        "owner_go_required": "true",
        "obsolete_expected_origin_main_sha": "ac2ea2d4_frozen_p08",
        "submit_import": "false",
        "flags_mutated": "false",
        "current_main_invocable": "false",
        "disposition": "REJECT_FOR_THIS_WP",
    },
    {
        "path": "src/ops/section_11_13_2_live_private_read_only_v1/http_client_v1.py",
        "endpoints": "/api/v5/account/config,/api/v5/account/balance,/api/v5/account/positions",
        "get_only_endpoints": "true",
        "client_post_reachable": "false",
        "owner_go_required": "cli_execute_yes_http_client_no",
        "obsolete_expected_origin_main_sha": "cli_execute_frozen",
        "submit_import": "false",
        "flags_mutated": "false",
        "current_main_invocable": "false_incomplete_allowlist",
        "disposition": "REUSE_PATTERN_NOT_INVOKE_CLI",
    },
    {
        "path": ("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"),
        "endpoints": "pretrade GET mixed with POST /api/v5/trade/order",
        "get_only_endpoints": "false",
        "client_post_reachable": "true",
        "owner_go_required": "true",
        "obsolete_expected_origin_main_sha": "n/a",
        "submit_import": "true",
        "flags_mutated": "false",
        "current_main_invocable": "false_forbidden_mixed_transport",
        "disposition": "REJECT_FOR_THIS_WP",
    },
    {
        "path": ("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/http_client_v1.py"),
        "endpoints": "GET and POST",
        "get_only_endpoints": "false",
        "client_post_reachable": "true",
        "owner_go_required": "n/a",
        "obsolete_expected_origin_main_sha": "n/a",
        "submit_import": "true",
        "flags_mutated": "false",
        "current_main_invocable": "false_forbidden_mixed_client",
        "disposition": "REJECT_FOR_THIS_WP",
    },
)
