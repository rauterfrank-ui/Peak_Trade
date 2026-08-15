"""Constants for the UQ6 canonical Feature/Data Contract Layer v1.

Contract-layer authority only. Not trading, regime, promotion, dashboard,
Live, Testnet, or execution authority.

MAX_AGE is Owner-bound WATCHDOG_ONLY / NON_ENFORCING. It must not become a
productive trading, risk, selection, execution, promotion, or canary gate.
Typed-volatility / presence / data-contract topics stay separate.
"""

from __future__ import annotations

CAPABILITY_ID = "CANONICAL_FEATURE_DATA_CONTRACT_LAYER_V1"
PACKAGE_MARKER = "CANONICAL_FEATURE_DATA_CONTRACT_LAYER_V1=true"
CONTRACT_ID = "canonical_feature_data_contract_layer"
CONTRACT_VERSION = "canonical_feature_data_contract_layer/v1"
CONTRACT_OWNER = "features.canonical_feature_data_contract_layer_v1"
CONTRACT_CONFIG_REL_PATH = "config/governance/canonical_feature_data_contract_layer_v1.json"
CANONICAL_SERIALIZATION_VERSION = "canonical_feature_data_contract_layer_canonical_json_v1"

REMEDIATION_ID = "R1_UQ6_FEATURE_DATA_CONTRACT_LAYER"
SOURCE_GAP_IDS = ("EG-I03-CLASSC", "IG-I03-ENGINE", "UQ6")
UQ6_STATUS = "RATIFIED_FEATURE_DATA_CONTRACT_LAYER_REQUIRED"
I03_CONTRACT_ROLE = "CANONICAL_AUTHORITY"
I03_ENGINE_ROLE = "GOVERNED_SUPPORTING"
STAGING_ORDER = (
    "CONTRACTS_SCHEMAS_LINEAGE",
    "SELECTIVE_PRODUCER_NORMALIZATION",
    "ENGINE_ONLY_WHERE_JUSTIFIED",
)

CORE_LOGIC_CHANGE = False
RUNTIME_EFFECT = False
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
AUTHORITY_EFFECT = "NONE"
ACTIVATED = False
PRODUCTIVE_CALLER_EXISTS = False
VOLATILITY_NUMERIC_MAX_AGE_ENFORCING = False
MAX_AGE_ENFORCEMENT_ENABLED = False
MAX_AGE_ROLE = "WATCHDOG_ONLY"
NUMERIC_MAX_AGE_EFFECT = "WATCHDOG_ONLY"
MAX_AGE_CAN_BLOCK_TRADING = False
MAX_AGE_CAN_BLOCK_CANARY = False
MAX_AGE_CAN_CHANGE_SELECTION = False
MAX_AGE_CAN_CHANGE_RISK_DECISIONS = False
MAX_AGE_CAN_CHANGE_EXECUTION = False
MAX_AGE_CAN_CHANGE_PROMOTION = False
MAX_AGE_PRODUCTIVE_GATE = False
MAX_AGE_ALLOWED_USES = (
    "OBSERVATION_OF_DATA_AGE_STALENESS",
    "DIAGNOSTIC_TELEMETRY",
    "LOGGING_AUDIT",
    "EVIDENCE_COLLECTION",
    "WARNINGS_HEALTH_SIGNALS",
    "RESEARCH_FORENSIC_USE",
)
IMPLICIT_DEFAULT_ALLOWED = False
DASHBOARD_AUTHORITY = False
REGIME_CLASSIFIER_AUTHORITY = False
EXECUTION_AUTHORITY = False
PROMOTION_AUTHORITY = False
SSOT_BYPASS_ALLOWED = False
ALT_DATA_CORE_CONSUMER_ALLOWED = False
PLACEHOLDER_SRC_FEATURES_DISPOSABLE = False
EMBEDDED_TA_EQUIVALENT_TO_CONTRACT_LAYER = False
LIVE_AUTHORIZED = False
TESTNET_AUTHORIZED = False
CANARY_EXECUTE = False
NETWORK_EFFECT = False
ORDER_EFFECT = False

I25_FEATURE_ID = "I25_VOLATILITY_ESTIMATE"
I25_CONTRACT_OWNER = "trading.master_v2.canonical_volatility_estimate_feature_contract_v1"
I25_CONTRACT_CONFIG_REL_PATH = (
    "config/governance/canonical_volatility_estimate_feature_contract_v1.json"
)
CMC_FEATURE_ID = "CMC_MARKET_CONTEXT_FEATURE_CONTRACT"
CMC_FEATURE_CONTRACT_VERSION = "canonical_market_context_feature_contract_v1"

JUSTIFIED_PRODUCER_IDS = (I25_FEATURE_ID, CMC_FEATURE_ID)

UQ6_AFFECTED_FEATURE_IDS = (
    "I03_FEATURE_CONTRACT_LAYER",
    "I03_FEATURE_ENGINE_STAGED",
    "I07_MAX_AGE_DIAGNOSTIC",
    I25_FEATURE_ID,
    "I04_SENTIMENT_NEWS_ONCHAIN",
    "I05_ORDERBOOK_TICK",
    "I38_WS_MARKET_STREAMS",
    "I40_REGIME_ADAPTIVE_PARAMS",
    "I55_MACRO_REGIMES",
    "I76_PSYCHOLOGY_FEATURES",
    CMC_FEATURE_ID,
)

CLASS_A_DECISION_SURFACES = (
    "Market Context",
    "Master V2 Orchestration (Integrated Replay)",
    "Bull Directional Assessment",
    "Bear Directional Assessment",
    "Double Play Composition",
    "Dynamic Scope (init / events / state)",
    "Survival Assessment",
    "Strategy Suitability Binding",
    "Entry/Exit Policy",
    "Canonical Trading Decision Evidence",
    "Capital / Risk / Sizing (combined, Slice B)",
    "Canonical Order Intent",
    "Intent Compatibility Firewall",
)

RESEARCH_FEEDER_IDS = (
    "I04_SENTIMENT_NEWS_ONCHAIN",
    "I05_ORDERBOOK_TICK",
    "I55_MACRO_REGIMES",
    "I76_PSYCHOLOGY_FEATURES",
)
