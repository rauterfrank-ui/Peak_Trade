"""Constants for R3 canonical Regime/Meta gated selection v1.

Gated input contract only. Reuses R2 identity/registry/selection owners and
src.regime.base.RegimeLabel. Not trading, promotion, dashboard, Live, Testnet,
Paper, Canary, or execution authority.

MAX_AGE remains WATCHDOG_ONLY / NON_ENFORCING and must not enter this gate.
"""

from __future__ import annotations

CAPABILITY_ID = "CANONICAL_REGIME_META_GATED_SELECTION_V1"
PACKAGE_MARKER = "CANONICAL_REGIME_META_GATED_SELECTION_V1=true"
CONTRACT_ID = "canonical_regime_meta_gated_selection"
CONTRACT_VERSION = "canonical_regime_meta_gated_selection/v1"
CONTRACT_OWNER = "regime.canonical_regime_meta_gated_selection_v1"
CONTRACT_CONFIG_REL_PATH = "config/governance/canonical_regime_meta_gated_selection_v1.json"
CANONICAL_SERIALIZATION_VERSION = "canonical_regime_meta_gated_selection_canonical_json_v1"

REMEDIATION_ID = "R3_REGIME_META_GATED_SELECTION"
SOURCE_GAP_IDS = ("I40", "I83", "UQ2")
DONE_CRITERION = "META_IS_GATED_INPUT_NOT_BYPASS;LLM_REMAINS_NON_TRADING"

REGIME_LABEL_OWNER = "src.regime.base.RegimeLabel"
REGIME_RESEARCH_SWITCH_OWNER = "src.regime.switching.SimpleRegimeMappingPolicy"
REGIME_RESEARCH_SWITCH_ROLE = "RESEARCH_FEEDER_NON_AUTHORITY"
R2_IDENTITY_OWNER = "src.strategies.registry.resolve_strategy_id"
R2_REGISTRY_OWNER = "src.strategies.registry"
R2_CATALOG_SELECTION_OWNER = (
    "strategies.canonical_strategy_registry_suitability_selection_v1.selection_v1"
)
SUITABILITY_SELECTION_OWNER = (
    "trading.master_v2.suitability_binding_v1.select_strategy_deterministic"
)
GATE_OWNER = "regime.canonical_regime_meta_gated_selection_v1.gate_v1"
LLM_REGIME_STUB_OWNER = "src.ai.regimes.regime_switch_v1"
LLM_REGIME_STUB_ROLE = "ADVISORY_LLM_CONTEXT"
INFOSTREAM_OWNER = "src.meta.infostream"
INFOSTREAM_ROLE = "RESEARCH_FEEDER"
AI_ORCHESTRATION_ROLE = "GOVERNED_SUPPORTING"
BULL_BEAR_EVIDENCE_OWNER = "trading.master_v2.regime_bull_bear_switch_evidence_readmodel_v1"
BULL_BEAR_EVIDENCE_ROLE = "EVIDENCE_ONLY"

KNOWN_REGIME_LABELS = ("breakout", "ranging", "trending")
UNKNOWN_REGIME_LABEL = "unknown"
LLM_REGIME_IDENTITIES = ("UP", "DOWN", "NEUTRAL")

CORE_LOGIC_CHANGE = False
RUNTIME_EFFECT = False
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORITY_IMPACT = "NONE"
ACTIVATED = False
PRODUCTIVE_CALLER_EXISTS = False
SILENT_AUTHORITY_PROMOTION = False
SILENT_THRESHOLD_MUTATION = False
TRADING_GRANT = False
PROMOTION_AUTHORITY = False
RAW_LLM_TRADING_AUTHORITY = "PERMANENT_NON_AUTHORITY"

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
G14_NON_AUTHORITATIVE_UNTIL_PROMOTION = True

COMPETING_SURFACES_FORENSIC = (
    "src.regime.switching.SimpleRegimeMappingPolicy=RESEARCH_FEEDER_NON_AUTHORITY_SILENT_FALLBACK",
    "src.ai.regimes.regime_switch_v1=ADVISORY_LLM_DISTINCT_IDENTITY",
    "src.meta.infostream=RESEARCH_FEEDER",
    "src.ai_orchestration=GOVERNED_SUPPORTING_NOT_TRADING",
    "trading.master_v2.regime_bull_bear_switch_evidence_readmodel_v1=EVIDENCE_ONLY",
    "trading.master_v2.suitability_binding_v1.regime_id=OFFLINE_ELIGIBILITY_CONTEXT",
)
