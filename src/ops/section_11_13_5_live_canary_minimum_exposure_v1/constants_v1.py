"""Constants for §11.13.5 LIVE_CANARY_MINIMUM_EXPOSURE productive surface."""

from __future__ import annotations

CAPABILITY_ID = "SECTION_11_13_5_LIVE_CANARY_MINIMUM_EXPOSURE_V1"
PACKAGE_MARKER = "SECTION_11_13_5_LIVE_CANARY_MINIMUM_EXPOSURE_V1=true"
OWNER = "ops.section_11_13_5_live_canary_minimum_exposure_v1"
CONTRACT_VERSION = "v1"
SCHEMA_VERSION = "section_11_13_5_live_canary_minimum_exposure.v1"
CONFIG_VERSION = "section_11_13_5_live_canary_minimum_exposure_config.v1"
EVIDENCE_CONTRACT_VERSION = "section_11_13_5_live_canary_minimum_exposure_proven.v1"
FORENSIC_EVIDENCE_CONTRACT_VERSION = "section_11_13_5_live_canary_forensic_reconciliation.v1"

OWNER_GO_EXECUTE = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
OWNER_GO_AUTHORING = "OWNER_GO_SECTION_11_13_LIVE_CANARY_PRODUCTIVE_SURFACE_AUTHORING"
AUTHORIZATION_SCOPE = "LIVE_CANARY_MINIMUM_EXPOSURE"
AUTHORIZATION_SCOPE_ALIASES_FORBIDDEN: tuple[str, ...] = (
    "LIVE_AUTHORIZED",
    "LIVE_PRIVATE_READ_ONLY",
    "LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION",
    "LIVE_DRY_RUN_ORDER_PLAN",
    "LIVE_BOUNDED_SINGLE_FUTURE",
    "LIVE_BOUNDED_MULTI_SESSION",
    "LIVE_AUTONOMOUS_SINGLE_FUTURE",
    "SECTION_11_13_LIVE_ACTIVATION",
    "SECTION_11_13_LIVE_CANARY_PRODUCTIVE_SURFACE_AUTHORING",
)

LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED_DEFAULT = False
LIVE_AUTHORIZED = False
LIVE_ENABLED = False
LIVE_ARMED = False
LIVE_ORDER_AUTHORIZED = False
ENABLE_LIVE_TRADING = False
FULLY_AUTONOMOUS_LIVE_TRADING_READY = False
FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE = False
TESTNET_AUTHORIZED = False
ORDERS_AUTHORIZED = False

CAPABILITY_11_9_REMAINS_FIXTURE_ONLY = True
CAPABILITY_11_9_LIVE_CANARY_ACTIVATED = False
CAPABILITY_11_8_REMAINS_FIXTURE_ONLY = True
CAPABILITY_11_7_REMAINS_CONTRACTS_ONLY = True

PREDECESSOR_LIVE_DRY_RUN_ORDER_PLAN_PROVEN_REQUIRED = True
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
REQUIRED_CREDENTIAL_CLASS = "LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY"
FORBIDDEN_CREDENTIAL_CLASS_MARKERS: tuple[str, ...] = (
    "DEMO",
    "TESTNET",
    "SIMULATED",
    "PAPER",
    "OKX_DEMO",
    "OKX_EEA_DEMO",
    "LIVE_DRY_RUN_ORDER_PLAN_READ_ONLY",
    "LIVE_PRIVATE_RO",
    "LIVE_SHADOW_RECON",
)
SECRETREF_URI_PREFIX = "secretref://"
SECRETREF_CANARY_PATH_MARKER = "/live-canary-minimum-exposure"
SECRETREF_FORBIDDEN_CROSS_PACKAGE_MARKERS: tuple[str, ...] = (
    "/live-private-ro",
    "/live-shadow-recon",
    "/live-dry-run-order-plan",
)
SECRETREF_FORBIDDEN_PATH_MARKERS: tuple[str, ...] = (
    "/demo",
    "/testnet",
    "/simulated",
    "/paper",
)
SECRETREF_CONVENTION_EXAMPLE = "secretref://vault/peak-trade/live-canary-minimum-exposure/<venue>"

FORBIDDEN_HOST_MARKERS: tuple[str, ...] = (
    "demo-futures.kraken.com",
    "demo.",
    "testnet.",
    "sandbox.",
    "simulated",
    "paper-",
)

# Preflight/forensic remain GET-only. Productive submit path is gated separately.
METHOD_ALLOWLIST_PREFLIGHT: tuple[str, ...] = ("GET",)
METHOD_ALLOWLIST_SUBMIT: tuple[str, ...] = ("GET", "POST")
FORBIDDEN_HTTP_METHODS_OUTSIDE_GATED_SUBMIT: tuple[str, ...] = (
    "PUT",
    "PATCH",
    "DELETE",
    "HEAD",
    "OPTIONS",
    "TRACE",
    "CONNECT",
)
ENDPOINT_ACCOUNT_MAX_SIZE = "/api/v5/account/max-size"
ENDPOINT_PUBLIC_PRICE_LIMIT = "/api/v5/public/price-limit"
ENDPOINT_ACCOUNT_LEVERAGE_INFO = "/api/v5/account/leverage-info"
ENDPOINT_ACCOUNT_CONFIG = "/api/v5/account/config"
ENDPOINT_ACCOUNT_POSITIONS = "/api/v5/account/positions"
ENDPOINT_ACCOUNT_POSITIONS_HISTORY = "/api/v5/account/positions-history"
ENDPOINT_ACCOUNT_POSITION_RISK = "/api/v5/account/account-position-risk"
ENDPOINT_ACCOUNT_BALANCE = "/api/v5/account/balance"
ENDPOINT_ASSET_BALANCES = "/api/v5/asset/balances"
ENDPOINT_ALLOWLIST_READ: tuple[str, ...] = (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_ACCOUNT_POSITIONS_HISTORY,
    ENDPOINT_ACCOUNT_POSITION_RISK,
    ENDPOINT_ACCOUNT_MAX_SIZE,
    ENDPOINT_ACCOUNT_LEVERAGE_INFO,
    ENDPOINT_ASSET_BALANCES,
    "/api/v5/trade/orders-pending",
    "/api/v5/market/ticker",
    "/api/v5/public/instruments",
    ENDPOINT_PUBLIC_PRICE_LIMIT,
)
ENDPOINT_SUBMIT = "/api/v5/trade/order"
ENDPOINT_CANCEL = "/api/v5/trade/cancel-order"
FORBIDDEN_MUTATION_ENDPOINT_MARKERS: tuple[str, ...] = (
    "/asset/withdrawal",
    "/asset/transfer",
    "/users/subaccount",
    "/account/set-",
    "withdraw",
    "transfer",
    "/trade/close-position",
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
DEFAULT_MAX_REQUEST_COUNT = 12
MAX_REQUEST_COUNT_HARD_CAP = 20
RETRY_BACKOFF_SECONDS = 0.25
SUBMIT_TIMEOUT_SECONDS = 15.0
UNKNOWN_SUBMIT_POLL_TIMEOUT_SECONDS = 60.0
CLOSEOUT_TIMEOUT_SECONDS = 120.0

TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP = "LIVE_PRODUCTIVE_HTTP"
TRANSPORT_CLASS_GOVERNED_FIXTURE = "GOVERNED_FIXTURE"
TRANSPORT_CLASS_PREFLIGHT_NO_NETWORK = "PREFLIGHT_NO_NETWORK"
TRANSPORT_CLASS_FORENSIC_SEALED_ONLY = "FORENSIC_SEALED_EVIDENCE_ONLY"

EVIDENCE_ROOT_TEMPLATE = (
    "evidence/ops/section_11_13_5_live_canary_minimum_exposure_proven_v1/<RUN_ID>/"
)
EVIDENCE_DIRNAME = "section_11_13_5_live_canary_minimum_exposure_proven_v1"
FORENSIC_EVIDENCE_DIRNAME = "section_11_13_5_live_canary_forensic_reconciliation_v1"
MANIFEST_FILENAME = "MANIFEST.sha256"
CLAIMS_FILENAME = "claims.json"
SUMMARY_FILENAME = "SUMMARY.json"
PROOF_FILENAME = "LIVE_CANARY_MINIMUM_EXPOSURE_PROOF.json"
CONFIG_DIGEST_FILENAME = "config_digest.json"
AUTHORIZATION_FILENAME = "authorization_binding.json"
REDACTION_FILENAME = "redaction_check.json"
RECONCILIATION_FILENAME = "RECONCILIATION_LAYER_EVALUATION.json"
FORENSIC_CLASSIFICATION_FILENAME = "FORENSIC_LAYER_CLASSIFICATION.json"
EXCHANGE_SNAPSHOT_FILENAME = "EXCHANGE_SNAPSHOT.sanitized.json"
LOCAL_EXPECTED_STATE_FILENAME = "LOCAL_EXPECTED_STATE.sanitized.json"
SUBMIT_GATE_FILENAME = "SUBMIT_GATE_EVALUATION.json"
TRADE_PERMISSION_FORENSIC_FILENAME = "TRADE_PERMISSION_FORENSIC.json"
ZERO_WRITE_FILENAME = "zero_write_assertions.json"
MUTATION_BOUNDARY_FILENAME = "MUTATION_BOUNDARY.json"

CANONICAL_NEXT_STEP_AFTER_AUTHORING_MERGE = (
    "OWNER_ACTIONS_RESOLVE_TRADE_ATTESTATION_AND_EXCHANGE_TRUTH_ADOPTION_THEN_"
    "NEW_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
)
CURRENT_CANONICAL_NEXT_STEP_AUTHORITY = "SECTION_11_13_5"

LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN = False
LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED = False
PREPARATION_SURFACE_READY = True
PRODUCTIVE_EXECUTE_PATH_READY = True
CANARY_SUBMIT_TRANSPORT_IMPLEMENTED = True
CANARY_SUBMIT_TRANSPORT_SCOPE = "SECTION_11_13_5_LIVE_CANARY_MINIMUM_EXPOSURE_ONLY"
CANARY_SUBMIT_TRANSPORT_ACTIVATED = False
GENERAL_LIVE_SUBMIT_UNLOCKED = False
SUBMIT_UNLOCKED = False
CORE_LOGIC_CHANGE = False
ORDER_EFFECT = "NONE"
NETWORK_EFFECT_DEFAULT = "NONE"
CREDENTIAL_ACCESS_DEFAULT = "NONE"
USER_AGENT_CANARY = "PeakTrade-Section-11-13-5-LiveCanary/1"
REQUIRED_SECRETREF_URI = "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"

# Standing SSOT facts (updated only when a governed Owner-GO proves them).
# §11.13.5.E proves LIVE_RECONCILIATION_PROVEN after exchange economic-baseline
# adoption + productive private-read match; BLOCKS_NEW_ENTRY clears with that proof.
# OKX temp-security clearance remains a separate canary cybersecurity blocker.
LIVE_RECONCILIATION_PROVEN = True
BLOCKS_NEW_ENTRY = False
UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY = False

REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT = {
    "READ": True,
    "TRADE": True,
    "WITHDRAW": False,
}
PRIOR_DRY_RUN_PERMISSION_ATTESTATION = {"READ": True, "TRADE": False, "WITHDRAW": False}

# Live EEA canary instrument binding (preparation only; not execute).
# BTC-USDT-SWAP remains historically rejected for this EEA canary path.
# BTC-USD_UM_XPERP-310328 remains Demo/historical and must not alias here.
# BTC-USD_UM_XPERP-310404 is the superseded historical canonical identity
# and must fail closed if supplied as the current target. It is not a fallback.
DEFAULT_INSTRUMENT_ID = "SUI-USD_UM_XPERP-310404"
CANARY_INSTRUMENT = DEFAULT_INSTRUMENT_ID
DEFAULT_INST_TYPE = "FUTURES"
CANARY_INST_TYPE = DEFAULT_INST_TYPE
DEFAULT_RULE_TYPE = "xperp"
PRODUCT_RULE_TYPE = DEFAULT_RULE_TYPE
DEFAULT_INST_FAMILY = "SUI-USD_UM_XPERP"
CANARY_INST_FAMILY = DEFAULT_INST_FAMILY
SETTLEMENT_ACCOUNT_TRUTH = "USDC"
HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID = "BTC-USD_UM_XPERP-310404"
HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID = "BTC-USDT-SWAP"
DEMO_XPERP_INSTRUMENT_ID = "BTC-USD_UM_XPERP-310328"
REJECTED_CANARY_INSTRUMENT_IDS: frozenset[str] = frozenset(
    {
        HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID,
        DEMO_XPERP_INSTRUMENT_ID,
    }
)
REJECTED_CANARY_INST_TYPES: frozenset[str] = frozenset({"SWAP"})
DEFAULT_SIDE = "BUY"
DEFAULT_ORDER_TYPE = "LIMIT"
DEFAULT_TD_MODE = "cross"


class LiveCanaryInstrumentBindingError(RuntimeError):
    """Fail-closed live canary instrument/type binding violation."""


def public_instruments_query_path_v1(
    *,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    inst_type: str = DEFAULT_INST_TYPE,
) -> str:
    assert_live_canary_instrument_binding_v1(instrument_id=instrument_id, inst_type=inst_type)
    return f"/api/v5/public/instruments?instType={inst_type}&instId={instrument_id}"


def assert_live_canary_instrument_binding_v1(
    *,
    instrument_id: str,
    inst_type: str | None = None,
    rule_type: str | None = None,
) -> None:
    iid = str(instrument_id or "").strip()
    if not iid:
        raise LiveCanaryInstrumentBindingError("INSTRUMENT_ID_REQUIRED")
    if iid in REJECTED_CANARY_INSTRUMENT_IDS:
        raise LiveCanaryInstrumentBindingError(f"REJECTED_CANARY_INSTRUMENT:{iid}")
    if iid != DEFAULT_INSTRUMENT_ID:
        raise LiveCanaryInstrumentBindingError(f"INSTRUMENT_BINDING_MISMATCH:{iid}")
    if inst_type is not None:
        itype = str(inst_type or "").strip().upper()
        if itype in REJECTED_CANARY_INST_TYPES:
            raise LiveCanaryInstrumentBindingError(f"REJECTED_CANARY_INST_TYPE:{itype}")
        if itype != DEFAULT_INST_TYPE:
            raise LiveCanaryInstrumentBindingError(f"INST_TYPE_BINDING_MISMATCH:{itype}")
    if rule_type is not None and str(rule_type or "").strip():
        rtype = str(rule_type).strip()
        if rtype != DEFAULT_RULE_TYPE:
            raise LiveCanaryInstrumentBindingError(f"RULE_TYPE_BINDING_MISMATCH:{rtype}")


POSITION_COUNT_LIMIT = 1
ORDER_COUNT_LIMIT = 1
MINIMUM_RATIFIED_NOTIONAL_ONLY = True
# Cap 11.9 fixture sample is not a productive exposure authorization.
CAP_11_9_FIXTURE_MAX_NOTIONAL_SAMPLE = "1"
CONFIRM_TOKEN_CANONICAL = "I_KNOW_WHAT_I_AM_DOING"
CLORDID_PREFIX = "pt-canary-"
CLORDID_WIRE_ALPHANUMERIC_PREFIX = "ptcanary"
IDEMPOTENCY_POLICY = "ONE_SHOT_CLORDID_PER_OWNER_GO_BINDING"
ENDPOINT_ORDERS_HISTORY = "/api/v5/trade/orders-history"
ENDPOINT_ORDER_GET = "/api/v5/trade/order"
ENDPOINT_ORDERS_ALGO_PENDING = "/api/v5/trade/orders-algo-pending"
GET_ENDPOINTS_PUBLIC: tuple[str, ...] = (
    "/api/v5/public/instruments",
    "/api/v5/market/ticker",
    ENDPOINT_PUBLIC_PRICE_LIMIT,
)
GET_ENDPOINTS_PRIVATE: tuple[str, ...] = (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_ACCOUNT_POSITIONS_HISTORY,
    ENDPOINT_ACCOUNT_POSITION_RISK,
    ENDPOINT_ACCOUNT_MAX_SIZE,
    ENDPOINT_ACCOUNT_LEVERAGE_INFO,
    ENDPOINT_ASSET_BALANCES,
    "/api/v5/trade/orders-pending",
    ENDPOINT_ORDERS_ALGO_PENDING,
    "/api/v5/trade/orders-history",
    "/api/v5/trade/order",
)
POST_ENDPOINTS_GATED: tuple[str, ...] = (
    "/api/v5/trade/order",
    "/api/v5/trade/cancel-order",
)

REUSED_SECTION_11_13_4_BINDING_SOURCE = (
    "evidence/ops/section_11_13_4_live_dry_run_order_plan_proven_v1/20260811T230805Z/"
)
REUSED_SECTION_11_13_3_BINDING_SOURCE = (
    "evidence/ops/section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1/"
    "20260811T211828Z/"
)
REUSED_BINDING_VENUE = "OKX"
REUSED_BINDING_ENTITY = "OKX Europe Limited"
REUSED_BINDING_REGION = "EEA/DE"
REUSED_BINDING_REST_HOST = "eea.okx.com"
REUSED_BINDING_ACCOUNT_SCOPE = "856964404452495999"

POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1 = (
    "POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1"
)
POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1 = "POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1"
POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1 = (
    "POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1"
)

FORENSIC_CLASSIFICATION_CODES: tuple[str, ...] = (
    "A_STALE_OR_LOCAL_DATA_MISMATCH",
    "B_SEMANTIC_OR_UNIT_MISMATCH",
    "C_EXPECTED_BENIGN_OPERATIONAL_DIFFERENCE",
    "D_REAL_UNRESOLVED_ECONOMIC_DIVERGENCE",
    "E_IMPLEMENTATION_DEFECT",
)

HARD_STOP_OWNER_REVIEW_LAYERS: tuple[str, ...] = (
    "venue_instrument_and_contract_metadata",
    "balances_equity_and_available_margin",
    "local_portfolio_and_accounting",
)
