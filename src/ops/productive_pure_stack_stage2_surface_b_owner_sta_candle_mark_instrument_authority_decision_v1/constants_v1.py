"""Constants for Surface-B Owner/STA candle/mark/instrument authority decision v1.

INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
CANDLE_AUTHORITY_RATIFIED=false
MARK_AUTHORITY_RATIFIED=false
INSTRUMENT_BINDING_RATIFIED=false
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false
CAMPAIGN_START_AUTHORIZED=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
DASHBOARD_AUTHORITY_EFFECT=NONE
NOTION_SSOT=false
"""

from __future__ import annotations

CAPABILITY_ID = (
    "CAPABILITY_PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1"
)
CAPABILITY_SCOPE = "SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION"
PACKAGE_MARKER = (
    "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1=true"
)
OWNER = (
    "ops.productive_pure_stack_stage2_surface_b_owner_sta_"
    "candle_mark_instrument_authority_decision_v1"
)
SCHEMA_VERSION = (
    "productive_pure_stack_stage2_surface_b_owner_sta_candle_mark_instrument_authority_decisions/v1"
)
DOCUMENT_TYPE = "OWNER_STA_AUTHORITY_DECISIONS_MANIFEST"
STATUS_SURFACE_OPEN = "OWNER_STA_DECISION_SURFACE_OPEN_INSTANCE_VALUES_NULL"

BASELINE_ORIGIN_MAIN_SHA = "3b6b75bc4fa4b3ba6887ed055fa7fb88dd3d87b7"
AUTHORITY_SURFACE = "B"
SOLE_TRADING_AUTHORITY = "run_integrated_offline_trading_logic_replay_v1"
STA_PRODUCER_ID = "sta_pt1m_finalized_ohlcv_shadow_calibration_producer_v1"
BAR_INTERVAL = "PT1M"
PT1M_SECONDS = 60
JOIN_KEY = "PT1M_BUCKET_OPEN_EVENT_TIME"

INPUT_AUTHORITY = False
RUNTIME_IMPLEMENTED = False
CANDLE_AUTHORITY_RATIFIED = False
MARK_AUTHORITY_RATIFIED = False
INSTRUMENT_BINDING_RATIFIED = False
CAMPAIGN_START_AUTHORIZED = False
RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED = False
RAW_INPUT_PACK_CREATED = False
CAMPAIGN_STARTED = False
PRODUCTIVE_NUMERIC_VALUES_SET = 0
PRODUCTIVE_CALIBRATION_AUTHORIZED = False
DASHBOARD_AUTHORITY_EFFECT = "NONE"
NOTION_SSOT = False
REPOSITORY_IS_SSOT = True
O4_UNCHANGED = True
O4_PT1H_AS_PT1M_FORBIDDEN = True

OWNER_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md"
)
DECISIONS_MANIFEST_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISIONS_V1.json"
)
SCHEMA_REL = (
    "docs/ops/schemas/productive_pure_stack_stage2_surface_b_owner_sta_"
    "candle_mark_instrument_authority_decisions_v1.schema.json"
)
CYBERSECURITY_MIRROR_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
    "CANDLE_MARK_INSTRUMENT_AUTHORITY_CYBERSECURITY_MIRROR_V1.md"
)
PARENT_RAW_INPUT_PACK_OWNER_DECISION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md"
)
PARENT_SURFACE_B_RATIFICATION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_OWNER_RATIFICATION_V1.md"
)

# Proposed (not ratified) venue-native source refs from repo discovery.
PROPOSED_CANDLE_SOURCE_REF = "venue://okx/public/rest/v5/market/history-candles?bar=1m&confirm=1"
PROPOSED_MARK_SOURCE_REF = (
    "venue://okx/public/rest/v5/market/history-mark-price-candles?bar=1m&confirm=1"
)

ALLOWED_CANDLE_SOURCE_REF_CANDIDATES: tuple[str, ...] = (PROPOSED_CANDLE_SOURCE_REF,)
ALLOWED_MARK_SOURCE_REF_CANDIDATES: tuple[str, ...] = (PROPOSED_MARK_SOURCE_REF,)

FORBIDDEN_CANDLE_SOURCE_REFS: tuple[str, ...] = (
    "venue://okx/public/rest/v5/market/candles",  # may include open tip
    "o4_pt1h_as_pt1m_authority",
    "dashboard_readmodel",
    "webui",
    "notion",
    "fixture",
    "demo",
    "sta_producer_as_raw_source_authority",
)

FORBIDDEN_MARK_SOURCE_REFS: tuple[str, ...] = (
    "venue://okx/public/rest/v5/public/mark-price",  # snapshot, not historical series
    "previous_candle_close",
    "candle_close_as_mark",
    "trade_as_mark",
    "last_as_mark",
    "index_as_mark",
    "dashboard_readmodel",
    "webui",
    "notion",
    "fixture",
    "demo",
    "o4_pt1h_as_pt1m_authority",
)

REQUIRED_INSTRUMENT_FIELDS: tuple[str, ...] = (
    "venue",
    "canonical_instrument_id",
    "venue_instrument_id",
    "contract_type",
    "market_type",
    "quote_currency",
    "settlement_currency",
)

# Competing IDs discovered in-repo; Owner must choose explicitly. BTC test bindings excluded.
INSTRUMENT_CANDIDATE_IDS: tuple[str, ...] = (
    "CAND_ETH_USDT_SWAP_RESEARCH_STAGING",
    "CAND_ADA_USDT_SWAP_CAP24_EVIDENCE",
    "CAND_SOL_USDT_SWAP_RANKING_EVIDENCE",
    "CAND_ETH_USD_XPERP_OKX_EUROPE_BINDING",
)

EXCLUDED_INSTRUMENT_CANDIDATE_IDS: tuple[str, ...] = ("EXCL_BTC_USDT_SWAP_TEST_FIXTURE",)

REGIME_COVERAGE_PRODUCER_AVAILABLE = False
REGIME_COVERAGE_STATUS = "SEMANTICALLY_UNRESOLVED"

NULL_INSTANCE_KEYS: tuple[str, ...] = (
    "campaign_id",
    "dataset_id",
    "scenario_id",
    "seed",
    "partition_boundaries",
    "fold_ids",
    "bootstrap_seeds",
    "purge",
    "embargo",
    "fold_sizes",
)

OWNER_DECISION_TABLE_IDS: tuple[str, ...] = (
    "DEC_CANDLE_SOURCE_REF",
    "DEC_CANDLE_EVENT_TIME_SEMANTICS",
    "DEC_CANDLE_VENUE_FINALIZED_MAPPING",
    "DEC_CANDLE_OPEN_TIP_EXCLUSION",
    "DEC_CANDLE_PAGINATION_DEDUP_ORDER_GAP",
    "DEC_CANDLE_PIT_NO_LOOKAHEAD",
    "DEC_CANDLE_RAW_PROVENANCE_REBUILD",
    "DEC_MARK_SOURCE_REF",
    "DEC_MARK_BUCKET_SEMANTICS",
    "DEC_MARK_NO_CANDLE_CLOSE_FALLBACK",
    "DEC_MARK_MISSING_DUPLICATE_LATE_NONFINAL",
    "DEC_MARK_PIT_NO_LOOKAHEAD",
    "DEC_MARK_RAW_PROVENANCE",
    "DEC_INSTRUMENT_BINDING_VENUE",
    "DEC_INSTRUMENT_BINDING_CANONICAL_ID",
    "DEC_INSTRUMENT_BINDING_VENUE_ID",
    "DEC_INSTRUMENT_BINDING_CONTRACT_TYPE",
    "DEC_INSTRUMENT_BINDING_MARKET_TYPE",
    "DEC_INSTRUMENT_BINDING_QUOTE_CURRENCY",
    "DEC_INSTRUMENT_BINDING_SETTLEMENT_CURRENCY",
    "DEC_REGIME_COVERAGE_PRODUCER",
)

REQUIRED_MANIFEST_TOP_KEYS: tuple[str, ...] = (
    "schema_version",
    "document_type",
    "capability_scope",
    "status",
    "baseline_origin_main_sha",
    "authority_surface",
    "input_authority",
    "runtime_implemented",
    "candle_authority_ratified",
    "mark_authority_ratified",
    "instrument_binding_ratified",
    "campaign_start_authorized",
    "raw_input_pack_materialization_authorized",
    "raw_input_pack_created",
    "campaign_started",
    "productive_numeric_values_set",
    "regime_coverage_producer_available",
    "regime_coverage_status",
    "candle_source_authority",
    "mark_source_authority",
    "instrument_binding",
    "owner_decision_table",
    "open_null_instance_fields",
    "decisions",
)

FORBIDDEN_SOURCE_TOKENS: tuple[str, ...] = (
    "fixture",
    "demo",
    "scenario_scalar",
    "dashboard",
    "webui",
    "notion",
    "cmc_volatility",
    "resultv1",
    "survivalresultv1",
    "suitabilityresultv1",
    "o4_pt1h_as_pt1m",
    "candle_close_as_mark",
    "previous_candle_close",
    "trade_as_mark",
    "parallel_arithmetic_kernel",
    "parallel_survival_kernel",
)
