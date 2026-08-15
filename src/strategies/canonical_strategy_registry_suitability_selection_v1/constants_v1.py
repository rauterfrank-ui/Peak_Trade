"""Constants for R2 canonical Strategy Registry / Suitability / Selection v1.

Contract-layer authority only. Reuses existing catalog, identity, Phase 9.1
classification, and offline suitability owners. Not trading, regime, promotion,
dashboard, Live, Testnet, Paper, Canary, or execution authority.

MAX_AGE is Owner-bound WATCHDOG_ONLY / NON_ENFORCING and must not enter
suitability or selection.
"""

from __future__ import annotations

CAPABILITY_ID = "CANONICAL_STRATEGY_REGISTRY_SUITABILITY_SELECTION_V1"
PACKAGE_MARKER = "CANONICAL_STRATEGY_REGISTRY_SUITABILITY_SELECTION_V1=true"
CONTRACT_ID = "canonical_strategy_registry_suitability_selection"
CONTRACT_VERSION = "canonical_strategy_registry_suitability_selection/v1"
CONTRACT_OWNER = "strategies.canonical_strategy_registry_suitability_selection_v1"
CONTRACT_CONFIG_REL_PATH = (
    "config/governance/canonical_strategy_registry_suitability_selection_v1.json"
)
CANONICAL_SERIALIZATION_VERSION = (
    "canonical_strategy_registry_suitability_selection_canonical_json_v1"
)

REMEDIATION_ID = "R2_STRATEGY_REGISTRY_SUITABILITY_SELECTION"
SOURCE_GAP_IDS = ("EG-REG-CALLERS", "G14", "I15")
DONE_CRITERION = "TIERED_REGISTRY_CLOSED_NON_AUTHORITATIVE_UNTIL_PROMOTION"

CATALOG_OWNER = "src.strategies.registry"
IDENTITY_OWNER = "src.strategies.registry.resolve_strategy_id"
CLASSIFICATION_OWNER = "ops.phase_9_1_strategy_registry_closure_v1.classifications_v1"
SUITABILITY_OWNER = "trading.master_v2.suitability_binding_v1"
SUITABILITY_ADAPTER_OWNER = "src.strategies.suitability_registry_adapter_v1"
SUITABILITY_SELECTION_OWNER = (
    "trading.master_v2.suitability_binding_v1.select_strategy_deterministic"
)
CATALOG_SELECTION_OWNER = (
    "strategies.canonical_strategy_registry_suitability_selection_v1.selection_v1"
)
INSTRUMENT_SELECTION_OWNER = "SINGLE_SELECTED_FUTURE"

CORE_LOGIC_CHANGE = False
RUNTIME_EFFECT = False
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
AUTHORITY_EFFECT = "NONE"
ACTIVATED = False
PRODUCTIVE_CALLER_EXISTS = False
SILENT_AUTHORITY_PROMOTION = False
TRADING_GRANT = False
REGISTRY_IS_LIVE_PERMISSION = False
METADATA_EQUALS_AUTHORITY = False

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
PAPER_SHADOW_AUTHORIZED = False
NETWORK_EFFECT = False
ORDER_EFFECT = False
REGIME_META_ACTIVATED = False
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
MULTI_VENUE_ACTIVATED = False
PROMOTION_AUTHORITY = False
DASHBOARD_AUTHORITY = False
SSOT_BYPASS_ALLOWED = False

HOST_COMPOSITION_STUB_ID = "strat-momentum-v1"
AUTHORITY_NON_STRATEGY_IDS = ("master_v2", "double_play")

COMPETING_SURFACES_FORENSIC = (
    "src.strategies.registry:_STRATEGY_REGISTRY=CANONICAL_CATALOG",
    "src.strategies.__init__:STRATEGY_REGISTRY=DEPRECATED_LOADER_VIEW",
    "config/strategy_tiering.toml=DUAL_SOURCE_POLICY_NOT_CATALOG",
    "trading.master_v2.suitability_binding_v1:SuitabilityStrategyRegistryV1=OFFLINE_SNAPSHOT",
    "ops.phase_9_1_strategy_registry_closure_v1=CLASSIFICATION_MATRIX_NOT_CATALOG",
    "src.webui.in_memory_strategies=NON_AUTHORITY",
    "src.experiments.strategy_profiles=RESEARCH_NON_AUTHORITY",
)
