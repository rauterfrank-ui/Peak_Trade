"""Constants for Surface-B Owner/STA regime-coverage STA open-inputs closeout v1.

PRODUCER_REIMPLEMENTATION=false
CONSUMER_WIRING=false
PT1M_ADAPTER=false
PACK_MATERIALIZATION=false
CAMPAIGN_START=false
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
PRODUCTIVE_THRESHOLDS_LOOKBACKS=false
TRADING_LOGIC_CHANGE=false
DASHBOARD_AUTHORITY_EFFECT=NONE
ORDERS_AUTHORIZED=false
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

CAPABILITY_ID = (
    "CAPABILITY_PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_V1"
)
CAPABILITY_SCOPE = "SURFACE_B_OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT"
PACKAGE_MARKER = (
    "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_V1=true"
)
OWNER = (
    "ops.productive_pure_stack_stage2_surface_b_owner_sta_"
    "regime_coverage_sta_open_inputs_closeout_v1"
)
SCHEMA_VERSION = (
    "productive_pure_stack_stage2_surface_b_owner_sta_"
    "regime_coverage_sta_open_inputs_closeout_decisions/v1"
)
DOCUMENT_TYPE = "OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_DECISIONS_MANIFEST"
STATUS_CLOSEOUT_RATIFIED = "OWNER_STA_STA_OPEN_INPUTS_CLOSEOUT_RATIFIED"

DECISION_ID = "DEC_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT"
DECISION_STATUS_RATIFIED = "RATIFIED"
OWNER_GO = "OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_V1"
OWNER_GO_BASE_SHA = "75ea4dc594a7f27b1fb490477e824a8c0a66d779"
AUTHORITY_SURFACE = "B"

VERSIONED_PRODUCER_ID = "productive_pure_stack_stage2_surface_b_regime_coverage_producer/v1"
THRESHOLD_AUTHORITY_UNSET = "OWNER_NUMERIC_THRESHOLD_AUTHORITY_UNSET_V1"
LOOKBACK_AUTHORITY_UNSET = "OWNER_NUMERIC_LOOKBACK_AUTHORITY_UNSET_V1"

CLOSED_INPUTS: tuple[str, ...] = (
    "non_invented_coverage_counts",
    "provable_eth_usdt_swap_compatibility",
)

COUNTABLE_LABELS_WHILE_UNSET: tuple[str, ...] = ("missing", "unknown")
FORBIDDEN_LABELS_WHILE_UNSET: tuple[str, ...] = ("low", "mid", "high")

REQUIRED_INSTRUMENT_BINDING_V1: dict[str, str] = {
    "venue": "okx",
    "canonical_instrument_id": "inst-eth-usdt-perp",
    "venue_instrument_id": "ETH-USDT-SWAP",
    "contract_type": "perpetual",
    "market_type": "futures",
    "quote_currency": "USDT",
    "settlement_currency": "USDT",
}

INSTRUMENT_BINDING_FIELDS: tuple[str, ...] = tuple(REQUIRED_INSTRUMENT_BINDING_V1.keys())

OWNER_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_V1.md"
)
DECISIONS_MANIFEST_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_DECISIONS_V1.json"
)
SCHEMA_REL = (
    "docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_"
    "regime_coverage_sta_open_inputs_closeout_decisions_v1.schema.json"
)
CYBERSECURITY_MIRROR_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_CYBERSECURITY_MIRROR_V1.md"
)
PARENT_REGIME_COVERAGE_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "REGIME_COVERAGE_PRODUCER_DECISION_V1.md"
)
PARENT_REGIME_COVERAGE_MANIFEST_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "REGIME_COVERAGE_PRODUCER_DECISIONS_V1.json"
)
PARENT_TRIAD_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md"
)
PARENT_TRIAD_MANIFEST_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISIONS_V1.json"
)
PARENT_RAW_INPUT_PACK_OWNER_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md"
)
PRODUCER_PACKAGE_REL = "src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/"
DIGEST_CONTRACT_REL = (
    "src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/"
    "digest_contract_v1.py"
)
PIT_RULES_REL = (
    "src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/pit_rules_v1.py"
)
LABEL_SEMANTICS_REL = (
    "src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/"
    "label_semantics_v1.py"
)

REQUIRED_MANIFEST_TOP_KEYS: tuple[str, ...] = (
    "schema_version",
    "document_type",
    "capability_scope",
    "status",
    "decision_id",
    "decision_status",
    "owner_go",
    "owner_go_base_sha",
    "authority_surface",
    "closed_inputs",
    "sta_open_external_inputs_remaining",
    "non_invented_coverage_counts",
    "provable_eth_usdt_swap_compatibility",
    "authority_refs",
    "non_effects",
    "decisions",
)

NON_EFFECT_FALSE_KEYS: tuple[str, ...] = (
    "producer_reimplementation",
    "consumer_wiring",
    "pt1m_adapter",
    "pack_materialization",
    "campaign_start",
    "input_authority",
    "runtime_implemented",
    "regime_coverage_producer_available",
    "productive_thresholds_lookbacks",
    "trading_logic_change",
    "orders_authorized",
    "testnet_authorized",
    "live_authorized",
)
