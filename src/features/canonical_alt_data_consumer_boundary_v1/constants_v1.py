"""Constants for EG-ALT-CONSUMER read-only consumer-boundary v1.

Forensic matrix / fail-closed verifier only. Not a second feature, suitability,
selection, or regime/meta owner. Does not wire I04/I05/I55 into trading.

KEEP_RESEARCH_FEEDER_NO_CANONICAL_CONSUMER_YET is the ratified target for
this pass. Presence of alt-data is not eligibility, regime, promotion, or
trading authority.
"""

from __future__ import annotations

CAPABILITY_ID = "CANONICAL_ALT_DATA_CONSUMER_BOUNDARY_V1"
PACKAGE_MARKER = "CANONICAL_ALT_DATA_CONSUMER_BOUNDARY_V1=true"
CONTRACT_ID = "canonical_alt_data_consumer_boundary"
CONTRACT_VERSION = "canonical_alt_data_consumer_boundary/v1"
CONTRACT_OWNER = "features.canonical_alt_data_consumer_boundary_v1"
CONTRACT_CONFIG_REL_PATH = "config/governance/canonical_alt_data_consumer_boundary_v1.json"
CANONICAL_SERIALIZATION_VERSION = "canonical_alt_data_consumer_boundary_canonical_json_v1"

REMEDIATION_ID = "EG-ALT-CONSUMER"
SOURCE_GAP_IDS = ("EG-ALT-CONSUMER", "I04", "I05", "I55")
SOURCE_INTENTS = ("I04", "I05", "I55")
CURRENT_BOUND_ROLE = "RESEARCH_FEEDER"
RUNBOOK_REQUIRED_EVIDENCE = "CONSUMER_MATRIX"
DONE_CRITERION = "KEEP_RESEARCH_FEEDER_NO_CANONICAL_CONSUMER_YET"
TARGET_BINDING = "KEEP_RESEARCH_FEEDER_NO_CANONICAL_CONSUMER_YET"

R1_FEATURE_OWNER = "features.canonical_feature_data_contract_layer_v1"
R2_SUITABILITY_OWNER = "trading.master_v2.suitability_binding_v1"
R2_REGISTRY_OWNER = "src.strategies.registry"
R3_REGIME_META_OWNER = "regime.canonical_regime_meta_gated_selection_v1.gate_v1"
R3_REGIME_LABEL_OWNER = "src.regime.base.RegimeLabel"

I04_FEATURE_ID = "I04_SENTIMENT_NEWS_ONCHAIN"
I05_FEATURE_ID = "I05_ORDERBOOK_TICK"
I55_FEATURE_ID = "I55_MACRO_REGIMES"

I04_PRODUCER = "NONE_UNWIRED"
I05_PRODUCER = "NONE_UNWIRED_TRUE_TICK_L2"
I55_PRODUCER = "src.macro_regimes.loader"
I55_OUTPUT_SCHEMA = "config/macro_regimes/schema.toml"
I55_PRODUCER_PATH = "src/macro_regimes/loader.py"
I55_SCHEMA_PATH = "config/macro_regimes/schema.toml"
I55_CURRENT_TOML_PATH = "config/macro_regimes/current.toml"

CORE_LOGIC_CHANGE = False
RUNTIME_EFFECT = False
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORITY_IMPACT = "NONE"
ACTIVATED = False
PRODUCTIVE_CALLER_EXISTS = False
CONSUMER_WIRING_PRESENT = False
ALT_DATA_PRESENCE_IS_STRATEGY_ELIGIBILITY = False
ALT_DATA_PRESENCE_IS_REGIME_AUTHORITY = False
ALT_DATA_PRESENCE_IS_PROMOTION_ELIGIBILITY = False
ALT_DATA_PRESENCE_IS_TRADING_AUTHORITY = False
DIRECT_RESEARCH_TO_INTENT_PATH = False
DIRECT_RESEARCH_TO_ORDER_PATH = False
I05_EXECUTION_AUTHORITY = False
I55_REPLACES_R3 = False
I55_REPLACES_MASTER_V2 = False
I55_REPLACES_DOUBLE_PLAY = False
G14_NON_AUTHORITATIVE_UNTIL_PROMOTION = True
DASHBOARD_AUTHORITY = False
LLM_TRADING_AUTHORITY = "PERMANENT_NON_AUTHORITY"

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

LIVE_AUTHORIZED = False
TESTNET_AUTHORIZED = False
CANARY_EXECUTE = False
NETWORK_EFFECT = False
ORDER_EFFECT = False

UNKNOWN_PRODUCER_PACKAGES = (
    "src.sentiment",
    "src.news",
    "src.onchain",
    "src.features.sentiment",
    "src.features.news",
    "src.features.onchain",
)
UNKNOWN_PRODUCER_DIRS = (
    "src/sentiment",
    "src/news",
    "src/onchain",
)
I55_ALLOWED_IMPORT_RELPATHS = (
    "src/macro_regimes/__init__.py",
    "src/macro_regimes/loader.py",
)
